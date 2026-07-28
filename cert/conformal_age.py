#!/usr/bin/env python3
"""Phase 21 / Lesson 21.3 - fit q_hat and validate coverage.

This is the first Phase 21 lesson that requires a calibration/test split:
split conformal needs the test score to be exchangeable with, not included in,
the calibration scores used to compute q_hat.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Sequence

import numpy as np
import pandas as pd


ALPHA = 0.10
SEED_SPLIT = 7000
SEED_PICK = 7100
N_REPEAT = 200
TOL_H3 = 0.02
TOL_H4 = 0.05


class CellIndex:
    """Pre-sort once by ``(cell, score)`` so repeated splits are cheap."""

    def __init__(self, df: pd.DataFrame, score_col: str = "s_vs_a1", cell_cols: Sequence[str] = ("z_bin",)):
        full = df[df.block_full].copy()
        cell = np.zeros(len(full), dtype=np.int64)
        for col in cell_cols:
            cell = cell * 100 + full[col].to_numpy(dtype=np.int64)
        score = full[score_col].to_numpy(dtype=np.float64)
        block = full["block_id"].to_numpy(dtype=np.int64)

        self.cells = np.unique(cell)
        self.blocks = np.unique(block)
        self.bpos = {int(b): i for i, b in enumerate(self.blocks)}
        block_i = np.array([self.bpos[int(b)] for b in block], dtype=np.int32)

        order = np.lexsort((score, cell))
        self.s = score[order]
        self.blk = block_i[order]
        self.cell = cell[order]
        starts = np.searchsorted(self.cell, self.cells)
        self.slices = {
            int(c): slice(int(starts[i]), int(starts[i + 1]) if i + 1 < len(starts) else len(self.cell))
            for i, c in enumerate(self.cells)
        }
        self.n_blocks = int(len(self.blocks))


def conformal_level(n_eff: int, alpha: float) -> float | None:
    k = int(np.ceil((int(n_eff) + 1) * (1.0 - float(alpha))))
    return None if k > int(n_eff) else k / int(n_eff)


def split_blocks(n_blocks: int, frac: float = 0.5, seed: int = SEED_SPLIT) -> np.ndarray:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(int(n_blocks))
    flag = np.zeros(int(n_blocks), dtype=bool)
    flag[perm[: int(round(float(frac) * int(n_blocks)))]] = True
    return flag


def fit_eval(
    ix: CellIndex,
    calib_flag: np.ndarray,
    alpha: float = ALPHA,
    variant: str = "B",
    seed: int = SEED_PICK,
) -> tuple[dict[int, float], dict[int, float], dict[int, int]]:
    """Fit q_hat per cell on calib blocks and evaluate coverage on test blocks."""
    rng = np.random.default_rng(seed)
    qhat: dict[int, float] = {}
    coverage: dict[int, float] = {}
    n_blocks: dict[int, int] = {}
    for cell, sl in ix.slices.items():
        values = ix.s[sl]
        blocks = ix.blk[sl]
        calib_mask = calib_flag[blocks]
        if not calib_mask.any():
            qhat[cell] = float("inf")
            coverage[cell] = 1.0
            n_blocks[cell] = 0
            continue

        n_eff = int(np.unique(blocks[calib_mask]).size)
        n_blocks[cell] = n_eff
        level = conformal_level(n_eff, alpha)
        if level is None:
            qhat[cell] = float("inf")
            coverage[cell] = 1.0
            continue

        if variant == "B":
            csum = np.cumsum(calib_mask)
            rank = int(np.ceil(level * csum[-1]))
            idx = int(np.searchsorted(csum, rank))
            qhat[cell] = float(values[min(idx, len(values) - 1)])
        elif variant == "A":
            reps = []
            for block in np.unique(blocks[calib_mask]):
                where = np.flatnonzero(calib_mask & (blocks == block))
                reps.append(values[rng.choice(where)])
            reps = np.sort(np.asarray(reps, dtype=float))
            k = int(np.ceil((n_eff + 1) * (1.0 - alpha)))
            qhat[cell] = float(reps[k - 1])
        elif variant == "C":
            reps = np.sort(
                np.array([values[calib_mask & (blocks == block)].max() for block in np.unique(blocks[calib_mask])])
            )
            k = int(np.ceil((n_eff + 1) * (1.0 - alpha)))
            qhat[cell] = float(reps[k - 1])
        else:
            raise ValueError("unknown variant %r" % variant)

        test_mask = ~calib_mask
        coverage[cell] = float((values[test_mask] <= qhat[cell]).mean()) if test_mask.any() else float("nan")
    return qhat, coverage, n_blocks


def v3_variance_control(ix: CellIndex, alpha: float = ALPHA, repeats: int = N_REPEAT) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Positive control: sample leakage should collapse coverage variance."""
    cells = sorted(ix.slices)
    cov_block = np.empty((int(repeats), len(cells)), dtype=float)
    cov_sample = np.empty((int(repeats), len(cells)), dtype=float)
    for r in range(int(repeats)):
        flag = split_blocks(ix.n_blocks, seed=SEED_SPLIT + r)
        _, cov, _ = fit_eval(ix, flag, alpha, "B")
        cov_block[r] = [cov[c] for c in cells]

        rng = np.random.default_rng(90_000 + r)
        sample_mask = rng.random(len(ix.s)) < 0.5
        for j, cell in enumerate(cells):
            sl = ix.slices[cell]
            values = ix.s[sl]
            mask = sample_mask[sl]
            level = conformal_level(int(mask.sum()), alpha)
            if level is None:
                cov_sample[r, j] = float("nan")
                continue
            csum = np.cumsum(mask)
            rank = int(np.ceil(level * csum[-1]))
            idx = int(np.searchsorted(csum, rank))
            q = values[min(idx, len(values) - 1)]
            cov_sample[r, j] = float((values[~mask] <= q).mean())
    return cov_block, cov_sample, cells


def v3c_leave_one_trace_out(df: pd.DataFrame, ix: CellIndex, alpha: float = ALPHA, variant: str = "B") -> dict[int, dict[int, float]]:
    """Calibrate on four traces and test on the held-out trace."""
    full = df[df.block_full]
    trace_of_block = full.groupby("block_id")["trace_id"].first()
    trace = np.array([trace_of_block[int(b)] for b in ix.blocks])
    out: dict[int, dict[int, float]] = {}
    for test_trace in np.unique(trace):
        flag = trace != test_trace
        _, cov, _ = fit_eval(ix, flag, alpha, variant)
        out[int(test_trace)] = cov
    return out


def _prov(argv: Sequence[str]) -> dict:
    def sh(*cmd: str) -> str:
        try:
            return subprocess.check_output(cmd, text=True).strip()
        except Exception:
            return "unknown"

    return {
        "git_hash": sh("git", "rev-parse", "HEAD"),
        "git_dirty": bool(sh("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script": "cert/conformal_age.py",
        "argv": list(argv),
        "n_repeat": N_REPEAT,
        "seed_split": SEED_SPLIT,
        "seed_pick": SEED_PICK,
    }


def report(
    df: pd.DataFrame,
    score: str = "s_vs_a1",
    cell_cols: Sequence[str] = ("z_bin",),
    alpha: float = ALPHA,
    out_json: str | None = None,
    argv: Sequence[str] = (),
) -> dict:
    ix = CellIndex(df, score, cell_cols)
    result = {
        "provenance": _prov(argv),
        "score": score,
        "cell_cols": list(cell_cols),
        "alpha": float(alpha),
        "n_blocks": int(ix.n_blocks),
    }
    flag = split_blocks(ix.n_blocks)
    print(f"\n{'=' * 76}")
    print(
        f"SPLIT: {flag.sum()} block calib | {(~flag).sum()} block test "
        f"| score={score} | o={'x'.join(cell_cols)}"
    )

    print("\n=== BA BIEN THE q_hat (Amendment 3 A3.2) ===")
    level_ref = conformal_level(int(flag.sum()), alpha)
    upper_a = 1.0 - alpha + 1.0 / (int(flag.sum()) + 1)
    print(f"  muc phan vi tham chieu cho (B): {level_ref:.5f}   can tren cho (A): {upper_a:.5f}")
    best = None
    best_dev = float("inf")
    for variant in ("A", "B", "C"):
        qhat, cov, _nblk = fit_eval(ix, flag, alpha, variant)
        cov_values = np.array([cov[c] for c in sorted(cov)], dtype=float)
        marginal = float(np.nanmean(cov_values))
        target = level_ref if variant == "B" else (1.0 - alpha)
        dev = abs(marginal - target)
        h4_pass = bool(np.all(np.abs(cov_values - (1.0 - alpha)) <= TOL_H4))
        result[f"variant_{variant}"] = {
            "qhat": {int(k): float(v) for k, v in qhat.items()},
            "coverage": {int(k): float(v) for k, v in cov.items()},
            "marginal": marginal,
            "target": float(target),
            "H4_pass": h4_pass,
        }
        print(
            f"  ({variant}) bien={marginal:.5f}  muc tieu={target:.5f}  "
            f"lech={dev:.5f}  H4={'PASS' if h4_pass else 'FAIL'}  "
            f"q_hat={[round(qhat[c], 1) for c in sorted(qhat)]}"
        )
        if h4_pass and dev < best_dev:
            best = variant
            best_dev = dev
    print(f"  -> BIEN THE CHINH (quy tac A3.2) = ({best})")
    result["primary_variant"] = best

    qhat, cov, nblk = fit_eval(ix, flag, alpha, best)
    cov_values = np.array([cov[c] for c in sorted(cov)], dtype=float)
    marginal = float(np.nanmean(cov_values))
    print(f"\n=== H3 (bao phu BIEN) | H4 (tung o) - bien the ({best}) ===")
    print(f"{'o':>8} {'n_blk calib':>12} {'q_hat':>10} {'bao phu':>9} {'lech':>8}")
    for cell in sorted(cov):
        print(f"{cell:>8} {nblk[cell]:>12} {qhat[cell]:>10.3f} {cov[cell]:>9.5f} {cov[cell]-(1-alpha):>+8.5f}")
    h3_pass = bool(abs(marginal - (1.0 - alpha)) <= TOL_H3)
    h4_pass = bool(np.all(np.abs(cov_values - (1.0 - alpha)) <= TOL_H4))
    print(f"  H3: |{marginal:.5f} - 0.90| = {abs(marginal - 0.9):.5f} <= {TOL_H3} -> {'PASS' if h3_pass else 'FAIL'}")
    print(f"  H4: moi o trong 0.90 +- {TOL_H4} -> {'PASS' if h4_pass else 'FAIL'}")
    result["H3"] = {"marginal": marginal, "pass": h3_pass}
    result["H4"] = {"pass": h4_pass}

    print("\n=== H6 (kiem HUONG): q_hat(alpha/K) PHAI > q_hat(alpha) ===")
    qhat_k, _, _ = fit_eval(ix, flag, alpha / 4.0, best)
    h6_pass = all(qhat_k[c] > qhat[c] for c in qhat)
    for cell in sorted(qhat):
        print(f"  o {cell}: q(a)={qhat[cell]:9.3f}  q(a/K)={qhat_k[cell]:9.3f}  {'OK' if qhat_k[cell] > qhat[cell] else '<-- DAO DAU!'}")
    print(f"  H6 -> {'PASS' if h6_pass else 'FAIL'}")
    result["H6"] = {"pass": bool(h6_pass), "qhat_alpha_over_k": {int(k): float(v) for k, v in qhat_k.items()}}

    print(f"\n=== V3 DOI CHUNG DUONG ({N_REPEAT} lan chia moi loai) ===")
    cov_block, cov_sample, cells = v3_variance_control(ix, alpha)
    print(f"{'o':>8} {'BLOCK: TB':>11} {'SD':>9} {'MAU: TB':>10} {'SD':>9} {'ty le SD':>9}")
    ratios = []
    result["V3_cells"] = {}
    for j, cell in enumerate(cells):
        sd_block = float(np.nanstd(cov_block[:, j]))
        sd_sample = float(np.nanstd(cov_sample[:, j]))
        ratio = sd_sample / max(sd_block, 1e-12)
        ratios.append(ratio)
        result["V3_cells"][int(cell)] = {
            "block_mean": float(np.nanmean(cov_block[:, j])),
            "block_sd": sd_block,
            "sample_mean": float(np.nanmean(cov_sample[:, j])),
            "sample_sd": sd_sample,
            "sample_over_block_sd": float(ratio),
        }
        print(
            f"{cell:>8} {np.nanmean(cov_block[:, j]):>11.5f} {sd_block:>9.5f} "
            f"{np.nanmean(cov_sample[:, j]):>10.5f} {sd_sample:>9.5f} {1.0 / max(ratio, 1e-12):>8.2f}x"
        )
    v3_pass = bool(np.nanmean(ratios) < 0.5)
    print(
        f"  SD(mau)/SD(block) trung binh = {np.nanmean(ratios):.3f} < 0.5 -> "
        f"{'PASS (thay dung trieu chung ro ri)' if v3_pass else 'FAIL -> DIEU TRA'}"
    )
    result["V3"] = {"sd_ratio_mean": float(np.nanmean(ratios)), "pass": v3_pass}

    print("\n=== V3c LEAVE-ONE-TRACE-OUT (kha hoan doi o muc TRACE) ===")
    loto = v3c_leave_one_trace_out(df, ix, alpha, best)
    print(f"{'test trace':>11} " + " ".join(f"{'o'+str(c):>9}" for c in sorted(cells)))
    all_cov = []
    result["V3c_folds"] = {}
    for trace in sorted(loto):
        row = [loto[trace][c] for c in sorted(cells)]
        all_cov.extend(row)
        result["V3c_folds"][int(trace)] = {int(c): float(loto[trace][c]) for c in sorted(cells)}
        print(f"{trace:>11} " + " ".join(f"{x:>9.5f}" for x in row))
    span = float(np.nanmax(all_cov) - np.nanmin(all_cov))
    v3c_pass = bool(span <= 0.05)
    print(f"  bien do qua 5 fold = {span:.5f} <= 0.05 -> {'PASS' if v3c_pass else 'FAIL -> ghi vao Limitations'}")
    result["V3c"] = {"span": span, "pass": v3c_pass}

    if out_json:
        os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True, default=str)
            f.write("\n")
        print(f"\n[ghi] {out_json}")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    argv = sys.argv if argv is None else list(argv)
    parser = argparse.ArgumentParser(description="Phase 21.3 conformal coverage by age")
    parser.add_argument("--calib", required=True)
    parser.add_argument("--score", default="s_vs_a1")
    parser.add_argument("--cells", default="z_bin", help="example: z_bin or z_bin,u_bin")
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args(argv[1:])

    df = pd.read_parquet(args.calib)
    report(df, args.score, tuple(part.strip() for part in args.cells.split(",") if part.strip()), args.alpha, args.out_json, argv)


if __name__ == "__main__":
    main()

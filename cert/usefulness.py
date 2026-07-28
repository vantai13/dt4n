#!/usr/bin/env python3
"""Phase 21 / Lesson 21.4 - risk-coverage frontier and ablation.

Central question:
  "Is the trust gate only a threshold on gap_twin?"

The ablation replaces the adaptive Mondrian threshold q_hat(z) with one
constant threshold c, calibrated on D_CALIB to match adaptive calibration
coverage. Both gates are then evaluated on D_TEST.

Baselines:
  B0 always trust (anchor)
  B1 random acceptance at the same calibration coverage
  B2 constant threshold on gap_twin
  B3 oracle upper bound

Bootstrap CIs use paired block resampling on D_TEST with common random numbers
across every gate and epsilon.
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
SEED_BOOT = 21400
N_BOOT = 1000
EPS_GRID = [0, 2, 5, 10, 15, 20, 30, 40, 50, 70, 100, 140, 200]


def conformal_level(n_eff: int, alpha: float) -> float | None:
    k = int(np.ceil((int(n_eff) + 1) * (1.0 - float(alpha))))
    return None if k > int(n_eff) else k / int(n_eff)


def fit_qhat_B(sub: pd.DataFrame, alpha: float = ALPHA, score: str = "s_vs_a1") -> dict[int, float]:
    """Variant B: pool samples, but inflate the quantile level by block count."""
    out: dict[int, float] = {}
    for cell, group in sub.groupby("z_bin"):
        n_eff = int(group.block_id.nunique())
        level = conformal_level(n_eff, alpha)
        values = group[score].to_numpy(dtype=float)
        out[int(cell)] = float("inf") if level is None else float(np.quantile(values, level, method="higher"))
    return out


def gate_metrics(d: pd.DataFrame, acc: np.ndarray) -> dict[str, float | int]:
    """Metrics for one accept mask on a dataframe."""
    n_accept = int(acc.sum())
    coverage = float(acc.mean())
    if n_accept < 30:
        return {
            "coverage": coverage,
            "n_accept": n_accept,
            "err_accept": float("nan"),
            "d_sla_accept": float("nan"),
            "regret_accept_ms": float("nan"),
        }
    sub = d.loc[acc]
    return {
        "coverage": coverage,
        "n_accept": n_accept,
        "err_accept": float(sub.wrong.mean()),
        "d_sla_accept": float(sub.viol_twin.mean() - sub.viol_opt.mean()),
        "regret_accept_ms": float(sub.regret.mean()),
    }


def build_gates(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    qhat: dict[int, float],
    eps_grid: Sequence[float] = EPS_GRID,
    seed: int = SEED_BOOT,
) -> list[dict]:
    """Create accept masks on D_TEST, matching coverage on D_CALIB."""
    rng = np.random.default_rng(seed)
    gap_calib = calib.gap_twin.to_numpy(dtype=float)
    q_calib = calib.z_bin.map(qhat).to_numpy(dtype=float)
    gap_test = test.gap_twin.to_numpy(dtype=float)
    q_test = test.z_bin.map(qhat).to_numpy(dtype=float)
    u_random = rng.random(len(test))

    rows: list[dict] = []
    for eps in eps_grid:
        eps = float(eps)
        acc_adaptive = gap_test >= q_test - eps
        p_star = float((gap_calib >= q_calib - eps).mean())

        if p_star <= 0:
            c_const = float("inf")
        elif p_star >= 1:
            c_const = float("-inf")
        else:
            c_const = float(np.quantile(gap_calib, 1.0 - p_star))
        acc_const = gap_test >= c_const
        acc_random = u_random < p_star

        need = int(round(p_star * len(test)))
        ok = ~test.wrong.to_numpy(dtype=bool)
        acc_oracle = np.zeros(len(test), dtype=bool)
        idx_ok = np.flatnonzero(ok)
        if need <= len(idx_ok):
            acc_oracle[idx_ok[:need]] = True
        else:
            acc_oracle[idx_ok] = True
            rest = np.flatnonzero(~ok)
            order = np.argsort(test.regret.to_numpy(dtype=float)[rest])
            acc_oracle[rest[order[: need - len(idx_ok)]]] = True

        rows.append(
            {
                "eps_ms": eps,
                "p_star_calib": p_star,
                "c_const": c_const,
                "adaptive": acc_adaptive,
                "const": acc_const,
                "random": acc_random,
                "oracle": acc_oracle,
            }
        )
    return rows


def _block_sums(test: pd.DataFrame, acc: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-block aggregates for fast paired block bootstrap."""
    block_values, inv = np.unique(test.block_id.to_numpy(), return_inverse=True)
    n_rows = np.bincount(inv, minlength=len(block_values)).astype(float)
    acc_f = acc.astype(float)
    n_acc = np.bincount(inv, weights=acc_f, minlength=len(block_values)).astype(float)
    wrong_acc = np.bincount(
        inv,
        weights=acc_f * test.wrong.to_numpy(dtype=float),
        minlength=len(block_values),
    ).astype(float)
    dsla = test.viol_twin.to_numpy(dtype=float) - test.viol_opt.to_numpy(dtype=float)
    dsla_acc = np.bincount(inv, weights=acc_f * dsla, minlength=len(block_values)).astype(float)
    return n_rows, n_acc, wrong_acc, dsla_acc


def bootstrap_frontier(
    test: pd.DataFrame,
    gates: Sequence[dict],
    n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
) -> dict[str, dict[str, np.ndarray]]:
    """Paired block bootstrap using common resampled blocks for all gates."""
    blocks = np.sort(test.block_id.unique())
    rng = np.random.default_rng(seed + 1)
    picks = rng.integers(0, len(blocks), (int(n_boot), len(blocks)))
    keys = ("adaptive", "const", "random", "oracle")
    out = {
        key: {
            "cov": np.empty((int(n_boot), len(gates)), dtype=float),
            "err": np.empty((int(n_boot), len(gates)), dtype=float),
            "dsla": np.empty((int(n_boot), len(gates)), dtype=float),
        }
        for key in keys
    }

    for j, gate in enumerate(gates):
        for key in keys:
            n_rows, n_acc, wrong_acc, dsla_acc = _block_sums(test, gate[key])
            row_den = n_rows[picks].sum(axis=1)
            acc_den = n_acc[picks].sum(axis=1)
            out[key]["cov"][:, j] = acc_den / row_den
            valid = acc_den > 30
            out[key]["err"][:, j] = np.nan
            out[key]["dsla"][:, j] = np.nan
            out[key]["err"][valid, j] = wrong_acc[picks][valid].sum(axis=1) / acc_den[valid]
            out[key]["dsla"][valid, j] = dsla_acc[picks][valid].sum(axis=1) / acc_den[valid]
    return out


def report(
    df: pd.DataFrame,
    score: str = "s_vs_a1",
    alpha: float = ALPHA,
    out_json: str | None = None,
    argv: Sequence[str] = (),
) -> dict:
    full = df[df.block_full].reset_index(drop=True)
    blocks = np.sort(full.block_id.unique())
    rng = np.random.default_rng(SEED_SPLIT)
    perm = rng.permutation(len(blocks))
    n_calib = int(round(0.5 * len(blocks)))
    cal_blocks = set(blocks[perm[:n_calib]])
    is_calib = full.block_id.isin(cal_blocks)
    calib = full[is_calib].reset_index(drop=True)
    test = full[~is_calib].reset_index(drop=True)

    qhat = fit_qhat_B(calib, alpha, score)
    anchor = gate_metrics(test, np.ones(len(test), dtype=bool))
    result = {
        "provenance": _prov(argv),
        "qhat": qhat,
        "anchor": anchor,
        "n_calib_blocks": len(cal_blocks),
        "n_test_blocks": int(test.block_id.nunique()),
        "n_test_rows": len(test),
    }

    print(f"\n{'=' * 80}")
    print(f"q_hat(z) on CALIB: {[round(qhat[k], 2) for k in sorted(qhat)]}")
    print(
        "ANCHOR (test): cov=1.0000  "
        f"err={anchor['err_accept']:.4f}  "
        f"d_sla={anchor['d_sla_accept']:.5f}  "
        f"regret={anchor['regret_accept_ms']:.3f} ms"
    )

    gates = build_gates(calib, test, qhat)
    bs = bootstrap_frontier(test, gates)

    print(f"\n{'=' * 80}")
    print("ABLATION: ADAPTIVE q_hat(z) vs CONSTANT THRESHOLD")
    print(f"{'eps':>5} {'c_const':>9} | {'--- ADAPTIVE ---':^27} | {'--- CONSTANT ---':^27} | {'DELTA err':>18}")
    print(
        f"{'':>5} {'':>9} | {'cov':>8} {'err|acc':>8} {'CI95':>10} | "
        f"{'cov':>8} {'err|acc':>8} {'CI95':>10} | {'mean':>8} {'CI95':>9}"
    )
    result["ablation"] = []
    for j, gate in enumerate(gates):
        adaptive = gate_metrics(test, gate["adaptive"])
        const = gate_metrics(test, gate["const"])
        delta_err = bs["const"]["err"][:, j] - bs["adaptive"]["err"][:, j]
        lo, hi = np.nanpercentile(delta_err, [2.5, 97.5])
        adaptive_ci = np.nanpercentile(bs["adaptive"]["err"][:, j], [2.5, 97.5])
        const_ci = np.nanpercentile(bs["const"]["err"][:, j], [2.5, 97.5])
        sig = "**" if lo > 0 else ("--" if hi < 0 else "  ")
        result["ablation"].append(
            {
                "eps_ms": gate["eps_ms"],
                "p_star_calib": gate["p_star_calib"],
                "c_const": gate["c_const"],
                "adaptive": adaptive,
                "const": const,
                "delta_err_mean": float(np.nanmean(delta_err)),
                "delta_err_ci95": [float(lo), float(hi)],
                "adaptive_better": bool(lo > 0),
            }
        )
        print(
            f"{gate['eps_ms']:>5.0f} {gate['c_const']:>9.2f} | "
            f"{adaptive['coverage']:>8.4f} {adaptive['err_accept']:>8.4f} "
            f"[{adaptive_ci[0]:.3f},{adaptive_ci[1]:.3f}] | "
            f"{const['coverage']:>8.4f} {const['err_accept']:>8.4f} "
            f"[{const_ci[0]:.3f},{const_ci[1]:.3f}] | "
            f"{np.nanmean(delta_err):>+8.4f} [{lo:>+.3f},{hi:>+.3f}]{sig}"
        )
    n_win = sum(1 for row in result["ablation"] if row["adaptive_better"])
    print("  ** = CI95 of delta excludes 0 (adaptive wins)")
    print(f"  ADAPTIVE wins decisively at {n_win}/{len(gates)} epsilon levels")
    result["ablation_wins"] = n_win

    print(f"\n{'=' * 80}")
    print("FOUR BASELINES (err|accept by coverage)")
    print(f"{'eps':>5} {'cov':>8} | {'ADAPTIVE':>10} {'CONSTANT':>9} {'RANDOM':>11} {'ORACLE':>9}")
    result["frontier"] = []
    for gate in gates:
        metrics = {key: gate_metrics(test, gate[key]) for key in ("adaptive", "const", "random", "oracle")}
        result["frontier"].append({"eps_ms": gate["eps_ms"], **metrics})
        print(
            f"{gate['eps_ms']:>5.0f} {metrics['adaptive']['coverage']:>8.4f} | "
            f"{metrics['adaptive']['err_accept']:>10.4f} {metrics['const']['err_accept']:>9.4f} "
            f"{metrics['random']['err_accept']:>11.4f} {metrics['oracle']['err_accept']:>9.4f}"
        )

    print(f"\n{'=' * 80}")
    print("EXPLOITED ORACLE HEADROOM")
    result["headroom"] = []
    for gate in gates[:6]:
        metrics = {key: gate_metrics(test, gate[key]) for key in ("adaptive", "random", "oracle")}
        span = metrics["random"]["err_accept"] - metrics["oracle"]["err_accept"]
        got = metrics["random"]["err_accept"] - metrics["adaptive"]["err_accept"]
        frac = float(got / span) if span > 0 else float("nan")
        result["headroom"].append(
            {
                "eps_ms": gate["eps_ms"],
                "coverage": metrics["adaptive"]["coverage"],
                "random_err": metrics["random"]["err_accept"],
                "adaptive_err": metrics["adaptive"]["err_accept"],
                "oracle_err": metrics["oracle"]["err_accept"],
                "exploited_fraction": frac,
            }
        )
        print(
            f"  eps={gate['eps_ms']:>5.0f} cov={metrics['adaptive']['coverage']:.4f}: "
            f"exploits {frac:>6.1%} of headroom "
            f"(random {metrics['random']['err_accept']:.4f} -> "
            f"gate {metrics['adaptive']['err_accept']:.4f} -> "
            f"oracle {metrics['oracle']['err_accept']:.4f})"
        )

    if out_json:
        os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True, default=str)
            fh.write("\n")
        print(f"\n[write] {out_json}")
    return result


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
        "script": "cert/usefulness.py",
        "argv": list(argv),
        "n_boot": N_BOOT,
        "seed_split": SEED_SPLIT,
        "seed_boot": SEED_BOOT,
        "eps_grid": EPS_GRID,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--score", default="s_vs_a1")
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args()
    report(pd.read_parquet(args.calib), args.score, args.alpha, args.out_json, sys.argv)


if __name__ == "__main__":
    main()

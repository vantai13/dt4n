#!/usr/bin/env python3
"""Phase 21 / Lesson 21.2 - characterize error versus age.

The hot path uses a rectangular tensor ``X[block, bin, C]`` and paired block
bootstrap with common random numbers. This keeps the effective sample size at
the block level while avoiding repeated DataFrame concatenation.
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
N_BOOT = 2000
ETA_BOOT = 500
SEED = 21002
C_PER_CELL = 256
FWER = 0.01


def _sh(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _prov(argv: Sequence[str]) -> dict:
    return {
        "git_hash": _sh("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_sh("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script": "cert/error_vs_age.py",
        "argv": list(argv),
        "n_boot": N_BOOT,
        "eta_boot": ETA_BOOT,
        "seed": SEED,
        "c_per_cell": C_PER_CELL,
        "fwer": FWER,
    }


def rankdata(values: Sequence[float]) -> np.ndarray:
    """Average ranks for ties, without requiring scipy."""
    arr = np.asarray(values, dtype=float)
    order = np.argsort(arr, kind="mergesort")
    ranks = np.empty(len(arr), dtype=float)
    i = 0
    while i < len(arr):
        j = i + 1
        while j < len(arr) and arr[order[j]] == arr[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + j - 1) / 2.0
        i = j
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    rx = rankdata(xs)
    ry = rankdata(ys)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def rectangularize(
    df: pd.DataFrame,
    score_col: str,
    group_col: str,
    c: int = C_PER_CELL,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert rows into ``X[block, group, c]`` using stride sampling."""
    blocks = np.sort(df["block_id"].unique())
    groups = np.sort(df[group_col].unique())
    bmap = {block: i for i, block in enumerate(blocks)}
    gmap = {group: i for i, group in enumerate(groups)}
    X = np.full((len(blocks), len(groups), int(c)), np.nan, dtype=np.float64)

    rng = np.random.default_rng(seed)
    for (block, group), sub in df.groupby(["block_id", group_col], sort=False):
        values = sub[score_col].to_numpy(dtype=float)
        n = len(values)
        if n == 0:
            continue
        if n >= c:
            take = np.linspace(0, n - 1, c).astype(int)
        else:
            take = rng.integers(0, n, c)
        X[bmap[block], gmap[group], :] = values[take]

    filled = np.isfinite(X).all(axis=2)
    if not filled.all():
        n_miss = int((~filled).sum())
        print(f"  [CANH BAO] {n_miss}/{filled.size} o (block,nhom) rong -> loai block do")
        keep = filled.all(axis=1)
        X = X[keep]
        blocks = blocks[keep]
    return X, blocks, groups


def conformal_level(n_eff: int, alpha: float) -> float | None:
    k = int(np.ceil((int(n_eff) + 1) * (1.0 - float(alpha))))
    return None if k > int(n_eff) else k / int(n_eff)


def qhat_from_tensor(X: np.ndarray, alpha: float, n_eff: int | None = None) -> np.ndarray:
    nb, ng, c = X.shape
    lvl = conformal_level(nb if n_eff is None else n_eff, alpha)
    if lvl is None:
        return np.full(ng, np.inf)
    flat = X.transpose(1, 0, 2).reshape(ng, nb * c)
    idx = min(int(np.ceil(lvl * flat.shape[1])) - 1, flat.shape[1] - 1)
    return np.partition(flat, idx, axis=1)[:, idx]


def paired_block_bootstrap(
    X: np.ndarray,
    alpha: float = ALPHA,
    n_boot: int = N_BOOT,
    seed: int = SEED,
    chunk: int = 50,
) -> np.ndarray:
    """Return bootstrap draws of q_hat for every group, preserving pairing."""
    nb, ng, c = X.shape
    lvl = conformal_level(nb, alpha)
    if lvl is None:
        raise ValueError(f"only {nb} blocks; cannot compute q_hat for alpha={alpha}")
    idx_q = min(int(np.ceil(lvl * nb * c)) - 1, nb * c - 1)

    rng = np.random.default_rng(seed)
    draws = np.empty((int(n_boot), ng), dtype=float)
    for start in range(0, int(n_boot), int(chunk)):
        m = min(int(chunk), int(n_boot) - start)
        pick = rng.integers(0, nb, (m, nb))
        sample = X[pick].transpose(0, 2, 1, 3).reshape(m, ng, nb * c)
        draws[start : start + m] = np.partition(sample, idx_q, axis=2)[:, :, idx_q]
    return draws


def ci(values: Sequence[float], alpha_ci: float) -> dict:
    arr = np.asarray(values, dtype=float)
    lo, hi = np.percentile(arr, [100 * alpha_ci / 2, 100 * (1 - alpha_ci / 2)])
    return {
        "lo": float(lo),
        "hi": float(hi),
        "mean": float(arr.mean()),
        "se": float(arr.std(ddof=1)),
    }


def eta_squared(scores: Sequence[float], groups: Sequence[int]) -> float:
    s = np.asarray(scores, dtype=float)
    g = np.asarray(groups)
    grand = s.mean()
    ss_between = 0.0
    for key in np.unique(g):
        mask = g == key
        ss_between += float(mask.sum()) * float(s[mask].mean() - grand) ** 2
    ss_total = float(((s - grand) ** 2).sum())
    return float(ss_between / ss_total) if ss_total > 0 else 0.0


def eta_squared_all(scores: Sequence[float], groups: Sequence[int]) -> dict:
    s = np.asarray(scores, dtype=float)
    return {
        "raw": eta_squared(s, groups),
        "log": eta_squared(np.log1p(np.maximum(s, 0.0)), groups),
        "rank": eta_squared(rankdata(s), groups),
    }


def eta_squared_boot(X: np.ndarray, n_boot: int = ETA_BOOT, seed: int = SEED + 1) -> np.ndarray:
    nb, ng, c = X.shape
    rng = np.random.default_rng(seed)
    out = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        pick = rng.integers(0, nb, nb)
        sample = X[pick].transpose(1, 0, 2).reshape(ng, nb * c)
        groups = np.repeat(np.arange(ng), nb * c)
        out[i] = eta_squared(sample.ravel(), groups)
    return out


def analyse(
    df: pd.DataFrame,
    score_col: str = "s_vs_a1",
    alpha: float = ALPHA,
    out_json: str | None = None,
    argv: Sequence[str] = (),
) -> dict:
    full = df[df.block_full].copy()
    result = {"provenance": _prov(argv), "score_col": score_col, "alpha": float(alpha)}

    print("\n" + "=" * 78)
    print(f"Q1 - q_hat theo BIN TUOI (score = {score_col}, alpha = {alpha})")
    X, blocks, bins = rectangularize(full, score_col, "z_bin")
    print(f"  tensor X: {X.shape}  ({len(blocks)} block x {len(bins)} bin x {X.shape[2]} mau)")

    q_point = qhat_from_tensor(X, alpha)
    draws = paired_block_bootstrap(X, alpha)
    n_diffs = max(1, len(bins) - 1)
    alpha_bonf = FWER / n_diffs

    print(f"\n{'bin':>4} {'q_hat':>10} {'CI lo':>11} {'CI hi':>11} {'p50(s)':>9} {'p90(s)':>9}")
    result["qhat"] = {}
    for i, bin_id in enumerate(bins):
        c_i = ci(draws[:, i], alpha_bonf)
        values = full.loc[full.z_bin == bin_id, score_col].to_numpy(dtype=float)
        result["qhat"][int(bin_id)] = {"point": float(q_point[i]), **c_i}
        print(
            f"{int(bin_id):>4} {q_point[i]:>10.3f} {c_i['lo']:>11.3f} {c_i['hi']:>11.3f} "
            f"{np.median(values):>9.3f} {np.percentile(values, 90):>9.3f}"
        )

    print(f"\n  {len(bins)-1} HIEU LIEN TIEP (Bonferroni -> CI{100*(1-alpha_bonf):.2f})")
    diff_draws = np.diff(draws, axis=1)
    result["diffs"] = {}
    all_pos = True
    for i in range(diff_draws.shape[1]):
        c_i = ci(diff_draws[:, i], alpha_bonf)
        ok = bool(c_i["lo"] > 0)
        all_pos = bool(all_pos and ok)
        key = f"{int(bins[i+1])}-{int(bins[i])}"
        result["diffs"][key] = {**c_i, "excludes_zero": ok}
        print(
            f"    bin{int(bins[i+1])} - bin{int(bins[i])}: {c_i['mean']:>9.3f}  "
            f"CI[{c_i['lo']:>9.3f}, {c_i['hi']:>9.3f}]  {'OK' if ok else '<-- CHUA LOAI TRU 0'}"
        )

    ratio = float(q_point[-1] / q_point[0]) if q_point[0] > 0 else float("inf")
    monotone = bool(np.all(np.diff(q_point) > 0))
    print(
        f"\n  H1: ti so q_hat(cuoi)/q_hat(dau) = {ratio:.3f} "
        f"(can >= 1.5)  {'PASS' if ratio >= 1.5 else 'FAIL'}"
    )
    print(
        f"      don dieu tang: {'PASS' if monotone else 'FAIL'}   "
        f"{len(bins)-1}/{len(bins)-1} hieu > 0: {'PASS' if all_pos else 'FAIL'}"
    )
    result["H1"] = {
        "ratio": ratio,
        "monotone": monotone,
        "all_diffs_positive": bool(all_pos),
        "pass": bool(ratio >= 1.5 and monotone and all_pos),
    }

    print("\n" + "=" * 78)
    print("Q2 - eta^2: tuoi giai thich bao nhieu phan bien thien cua s?")
    eta = eta_squared_all(full[score_col].to_numpy(dtype=float), full.z_bin.to_numpy())
    eta_boot = eta_squared_boot(X)
    eta_ci = ci(eta_boot, 0.05)
    for name, value in eta.items():
        print(f"  eta^2_{name:<5} = {value:.4f}")
    print(f"  CI95 block bootstrap (raw): [{eta_ci['lo']:.4f}, {eta_ci['hi']:.4f}]")
    print(f"  H2: eta^2 >= 0.05  ->  {'PASS' if eta['raw'] >= 0.05 else 'FAIL'}")
    spread = max(eta.values()) / max(min(eta.values()), 1e-9)
    if spread > 3:
        print(f"  [CANH BAO] ba phien ban lech {spread:.1f}x -> hieu ung co the do OUTLIER")
    result["H2"] = {**eta, "ci95_raw": eta_ci, "pass": bool(eta["raw"] >= 0.05)}

    print("\n" + "=" * 78)
    print("Q3 - hinh dang phan phoi s trong tung bin")
    print(
        f"{'bin':>4} {'p50':>9} {'p75':>9} {'p90':>9} {'p95':>9} {'p99':>10} "
        f"{'p90/p50':>8} {'qhat_quantile':>14}"
    )
    result["Q3"] = {}
    for i, bin_id in enumerate(bins):
        values = full.loc[full.z_bin == bin_id, score_col].to_numpy(dtype=float)
        p = {f"p{k}": float(np.percentile(values, k)) for k in (50, 75, 90, 95, 99)}
        q_pos = float((values <= q_point[i]).mean())
        result["Q3"][int(bin_id)] = {**p, "qhat_empirical_quantile": q_pos}
        print(
            f"{int(bin_id):>4} {p['p50']:>9.3f} {p['p75']:>9.3f} {p['p90']:>9.3f} "
            f"{p['p95']:>9.3f} {p['p99']:>10.3f} "
            f"{p['p90']/max(p['p50'], 1e-9):>8.2f} {q_pos:>14.4f}"
        )
    lvl = conformal_level(len(blocks), alpha)
    print(f"  ^ cot cuoi nen ~= {lvl:.4f} = conformal level theo so block.")

    print("\n" + "=" * 78)
    print("Q4 - bien dieu kien nao giai thich s tot hon? (EXPLORATORY)")
    result["Q4"] = {}
    for label, col in (("tuoi z", "z_bin"), ("khoang cach nguong u", "u_bin")):
        eta_col = eta_squared_all(full[score_col].to_numpy(dtype=float), full[col].to_numpy())
        result["Q4"][col] = eta_col
        print(
            f"  eta^2( s | {label:<22}) raw={eta_col['raw']:.4f}  "
            f"log={eta_col['log']:.4f}  rank={eta_col['rank']:.4f}"
        )
    cell = full.z_bin.astype(int) * 10 + full.u_bin.astype(int)
    eta_cell = eta_squared_all(full[score_col].to_numpy(dtype=float), cell.to_numpy())
    result["Q4"]["z_x_u"] = eta_cell
    print(
        f"  eta^2( s | z_bin x u_bin        ) raw={eta_cell['raw']:.4f}  "
        f"log={eta_cell['log']:.4f}  rank={eta_cell['rank']:.4f}"
    )
    print(f"  -> phan tang them khi them u: {eta_cell['raw'] - result['Q4']['z_bin']['raw']:+.4f}")

    print("\n" + "=" * 78)
    print("H7 - thu tu bin theo q_hat co khop thu tu theo err(z) khong?")
    err_by_bin = full.groupby("z_bin")["wrong"].mean().reindex(bins).to_numpy()
    rho = spearman(q_point, err_by_bin)
    print(f"  err(z_bin)   = {np.round(err_by_bin, 5)}")
    print(f"  q_hat(z_bin) = {np.round(q_point, 3)}")
    print(f"  Spearman = {rho:.4f}   (can 1.0)   {'PASS' if rho >= 0.999 else 'FAIL'}")
    print("  LUU Y: H7 la kiem tra nhat quan, khong phai bang chung doc lap.")
    result["H7"] = {"spearman": rho, "err_by_bin": err_by_bin.tolist(), "pass": bool(rho >= 0.999)}

    if out_json:
        os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True, default=str)
            f.write("\n")
        print(f"\n[ghi] {out_json}")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    argv = sys.argv if argv is None else list(argv)
    parser = argparse.ArgumentParser(description="Phase 21.2 error versus age")
    parser.add_argument("--calib", required=True)
    parser.add_argument("--score", default="s_vs_a1", choices=("s_vs_a1", "s_range", "s_maxabs"))
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args(argv[1:])

    df = pd.read_parquet(args.calib)
    analyse(df, score_col=args.score, alpha=args.alpha, out_json=args.out_json, argv=argv)


if __name__ == "__main__":
    main()

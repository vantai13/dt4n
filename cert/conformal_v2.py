#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.5 -- Mondrian split conformal by age bin.

The conformal level is computed from the effective number of calibration
blocks, not rows:

    k = ceil((n_eff + 1) * (1 - alpha))
    level = k / n_eff

Variant B, the main reported method, uses all calibration rows but uses this
block-level correction.  Variant A is the exact finite-sample anchor; Variant C
is the conservative whole-block upper bound.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np
import pandas as pd


ALPHA = 0.10
K_ACTIONS = 4
SEED_SPLIT = 7000
SEED_PICK = 9001
N_REPEAT_V3 = 20
COV_TOL_MARGINAL = 0.02
COV_TOL_PER_BIN = 0.05
V3_SD_RATIO_MAX = 0.50


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _json_clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_json_clean(v) for v in value]
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return None
    return value


def _infer_cell(path: str) -> str:
    name = os.path.basename(path)
    match = re.match(r"calib_set_(.+)_([0-9]+\.[0-9]+)(?:_V[0-9]+)?\.parquet$", name)
    if not match:
        return "unknown"
    return "%s@%.3f" % (match.group(1), float(match.group(2)))


def conformal_level(n_eff: int, alpha: float = ALPHA) -> Optional[float]:
    """Return the conservative split-conformal quantile level, or ``None``.

    ``None`` means ``q_hat = +inf``: coverage remains valid but the interval is
    useless.  This happens when ``n_eff < ceil(1/alpha)-1``.
    """
    n_eff = int(n_eff)
    if n_eff <= 0:
        return None
    k = int(np.ceil((n_eff + 1) * (1.0 - float(alpha))))
    return None if k > n_eff else k / n_eff


def empirical_qhat(values: np.ndarray, level: float) -> float:
    """Quantile with ``method='higher'`` so ``q_hat`` is a real sample point."""
    return float(np.quantile(np.asarray(values, dtype=np.float64), float(level), method="higher"))


def split_blocks(block_ids: np.ndarray, seed: int = SEED_SPLIT, frac: float = 0.5) -> np.ndarray:
    """Split whole blocks and return a row-level calibration mask."""
    blocks = np.sort(np.unique(block_ids))
    rng = np.random.default_rng(int(seed))
    perm = rng.permutation(len(blocks))
    calib = blocks[perm[: int(round(float(frac) * len(blocks)))]]
    return np.isin(block_ids, calib)


def split_rows_V3(n: int, seed: int = SEED_SPLIT) -> np.ndarray:
    """Positive control: intentionally wrong row-level split."""
    return np.random.default_rng(int(seed)).random(int(n)) < 0.5


def split_by_seed(seeds: np.ndarray, calib_seeds: Sequence[int] = (101, 102, 103)) -> np.ndarray:
    """Independent-trajectory validation: calibration and test seeds disjoint."""
    return np.isin(np.asarray(seeds), list(calib_seeds))


def _variant_qhat(c: pd.DataFrame, score: str, level: float, alpha: float, variant: str, rng: np.random.Generator) -> float:
    n_eff = int(c["block_id"].nunique())
    if variant == "B":
        return empirical_qhat(c[score].to_numpy(np.float64), level)
    if variant == "A":
        reps = (
            c.groupby("block_id", sort=True)[score]
            .apply(lambda s: s.iloc[int(rng.integers(len(s)))])
            .to_numpy(np.float64)
        )
        k = int(np.ceil((n_eff + 1) * (1.0 - float(alpha))))
        return float(np.sort(reps)[k - 1])
    if variant == "C":
        reps = np.sort(c.groupby("block_id", sort=True)[score].max().to_numpy(np.float64))
        k = int(np.ceil((n_eff + 1) * (1.0 - float(alpha))))
        return float(reps[k - 1])
    raise ValueError("variant phai la 'A', 'B' hoac 'C'")


def fit_eval(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    variant: str = "B",
    seed: int = SEED_PICK,
) -> Dict[str, Any]:
    """Fit per-bin q_hat on calibration blocks and evaluate on test rows."""
    if variant not in ("A", "B", "C"):
        raise ValueError("variant phai la 'A', 'B' hoac 'C'")
    rng = np.random.default_rng(int(seed))
    d = df.assign(_calib=np.asarray(is_calib, dtype=bool))

    qhat: Dict[int, float] = {}
    cov: Dict[int, float] = {}
    n_blk: Dict[int, int] = {}
    n_test: Dict[int, int] = {}
    levels: Dict[int, Optional[float]] = {}

    for group, sub in d.groupby(bin_col, sort=True):
        g = int(group)
        c = sub[sub["_calib"]]
        t = sub[~sub["_calib"]]
        n_eff = int(c["block_id"].nunique())
        n_blk[g] = n_eff
        n_test[g] = int(len(t))
        level = conformal_level(n_eff, alpha)
        levels[g] = level
        if level is None:
            qhat[g] = float("inf")
            cov[g] = 1.0
            continue
        qhat[g] = _variant_qhat(c, score, level, alpha, variant, rng)
        cov[g] = float((t[score] <= qhat[g]).mean()) if len(t) else 1.0

    test = d[~d["_calib"]]
    if len(test):
        q_row = test[bin_col].map(qhat).to_numpy(np.float64)
        marginal = float((test[score].to_numpy(np.float64) <= q_row).mean())
    else:
        marginal = 1.0
    finite_cov = [v for v in cov.values() if np.isfinite(v)]
    max_dev = max(abs(v - (1.0 - alpha)) for v in finite_cov) if finite_cov else 0.0
    return {
        "variant": variant,
        "alpha": float(alpha),
        "score": score,
        "bin_col": bin_col,
        "qhat": qhat,
        "coverage": cov,
        "n_calib_blocks": n_blk,
        "n_test_rows": n_test,
        "coverage_marginal": marginal,
        "level": levels,
        "pass_G3": bool(abs(marginal - (1.0 - alpha)) <= COV_TOL_MARGINAL),
        "pass_G4": bool(all(abs(v - (1.0 - alpha)) <= COV_TOL_PER_BIN for v in finite_cov)),
        "max_abs_dev_per_bin": float(max_dev),
    }


def v3_variance_control(
    df: pd.DataFrame,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    repeats: int = N_REPEAT_V3,
) -> Dict[str, Any]:
    """Positive control: leakage appears as collapsed coverage variance."""
    block_ids = df["block_id"].to_numpy()
    cov_block = []
    cov_row = []
    for r in range(int(repeats)):
        rb = fit_eval(
            df,
            split_blocks(block_ids, seed=SEED_SPLIT + r),
            score=score,
            bin_col=bin_col,
            alpha=alpha,
            variant="B",
        )
        rr = fit_eval(
            df,
            split_rows_V3(len(df), seed=SEED_SPLIT + 1000 + r),
            score=score,
            bin_col=bin_col,
            alpha=alpha,
            variant="B",
        )
        cov_block.append([rb["coverage"][g] for g in sorted(rb["coverage"])])
        cov_row.append([rr["coverage"][g] for g in sorted(rr["coverage"])])
    cb = np.asarray(cov_block, dtype=np.float64)
    cr = np.asarray(cov_row, dtype=np.float64)
    sd_b = cb.std(axis=0, ddof=0)
    sd_r = cr.std(axis=0, ddof=0)
    ratio = float(sd_r.mean() / sd_b.mean()) if sd_b.mean() > 0.0 else float("nan")
    return {
        "repeats": int(repeats),
        "coverage_mean_block": [float(x) for x in cb.mean(axis=0)],
        "coverage_mean_row": [float(x) for x in cr.mean(axis=0)],
        "coverage_sd_block": [float(x) for x in sd_b],
        "coverage_sd_row": [float(x) for x in sd_r],
        "sd_ratio_row_over_block": ratio,
        "pass_G6": bool(ratio < V3_SD_RATIO_MAX),
        "note": (
            "Chu ky cua ro ri la phuong sai sup, khong phai bao phu lech; "
            "kiem positive-control phai do SD giua cac split."
        ),
    }


def bridge_to_rms(
    df: pd.DataFrame,
    qhat: Mapping[int, float],
    score: str = "s_margin",
    bin_col: str = "z_bin",
) -> Dict[str, Any]:
    """Compare conformal q_hat to the half-normal proxy ``1.645 * rms``."""
    rows = []
    for group, sub in df.groupby(bin_col, sort=True):
        g = int(group)
        rms = float(np.sqrt(np.mean(sub[score].to_numpy(np.float64) ** 2)))
        pred = 1.6448536269514722 * rms
        q = float(qhat[g])
        rows.append(
            {
                bin_col: g,
                "qhat": q,
                "pred_1p645_rms": pred,
                "ratio": float(q / pred) if pred > 0.0 else float("nan"),
            }
        )
    return {"per_bin": rows, "all_within_5pct": bool(all(abs(r["ratio"] - 1.0) < 0.05 for r in rows))}


def _max_rel_diff(a: Mapping[int, float], b: Mapping[int, float]) -> float:
    return float(max(abs(float(a[g]) - float(b[g])) / max(abs(float(b[g])), 1e-12) for g in b))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--k-actions", type=int, default=K_ACTIONS)
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    block_ids = df["block_id"].to_numpy()
    calib_block = split_blocks(block_ids, seed=SEED_SPLIT)

    out: Dict[str, Any] = {
        "cell": _infer_cell(args.calib),
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "results": {},
        "provenance": {
            "script": "cert/conformal_v2.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "alpha": float(args.alpha),
            "seed_split": int(SEED_SPLIT),
            "seed_pick": int(SEED_PICK),
            "v3_repeats": int(N_REPEAT_V3),
        },
    }

    for bin_col in ("z_bin", "z_bin2"):
        for score in ("s_margin", "s_signed", "s_vs_a1", "s_maxabs"):
            for variant in ("A", "B", "C"):
                tag = "%s|%s|%s" % (bin_col, score, variant)
                out["results"][tag] = fit_eval(
                    df,
                    calib_block,
                    score=score,
                    bin_col=bin_col,
                    alpha=float(args.alpha),
                    variant=variant,
                )

    main_key = "z_bin|s_margin|B"
    main_result = out["results"][main_key]
    qhat_main = main_result["qhat"]
    r_alpha_over_k = fit_eval(
        df,
        calib_block,
        score="s_margin",
        bin_col="z_bin",
        alpha=float(args.alpha) / int(args.k_actions),
        variant="B",
    )
    out["G8_alpha_over_K"] = {
        "K": int(args.k_actions),
        "alpha_over_K": float(args.alpha) / int(args.k_actions),
        "qhat_alpha": qhat_main,
        "qhat_alpha_over_K": r_alpha_over_k["qhat"],
        "pass": bool(all(r_alpha_over_k["qhat"][g] > qhat_main[g] for g in qhat_main)),
    }
    out["G6_v3_positive_control"] = v3_variance_control(df, alpha=float(args.alpha))
    if "seed" in df.columns:
        out["independent_seed_validation"] = fit_eval(
            df,
            split_by_seed(df["seed"].to_numpy()),
            score="s_margin",
            bin_col="z_bin",
            alpha=float(args.alpha),
            variant="B",
        )
    out["bridge_to_rms"] = bridge_to_rms(df, qhat_main)

    qa = out["results"]["z_bin|s_margin|A"]["qhat"]
    qc = out["results"]["z_bin|s_margin|C"]["qhat"]
    out["A_vs_B"] = {
        "max_rel_diff_A_vs_B": _max_rel_diff(qa, qhat_main),
        "max_rel_diff_C_vs_B": _max_rel_diff(qc, qhat_main),
        "finite_sample_caveat": (
            "Variant A is the exact finite-sample anchor; Variant B is the main "
            "pooled-row approximation with block-level effective n."
        ),
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    print(
        json.dumps(
            _json_clean(
                {
                    "cell": out["cell"],
                    "main": main_result,
                    "G8_alpha_over_K": out["G8_alpha_over_K"],
                    "G6_v3_positive_control": out["G6_v3_positive_control"],
                    "independent_seed_validation": out.get("independent_seed_validation"),
                    "bridge_to_rms": out["bridge_to_rms"],
                    "A_vs_B": out["A_vs_B"],
                    "one_sided": out["results"]["z_bin|s_signed|B"],
                }
            ),
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

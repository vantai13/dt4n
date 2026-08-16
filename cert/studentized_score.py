#!/usr/bin/env python3
"""Phase 23 / Lesson 23.5[A] -- studentized max-score.

Status: EXPLORATORY. Do not use this as a confirmatory Phase 22 result.

Signed procedure:
  * docs/phase-22/00b-amendment-1.md, A2
  * docs/phase-23/00u-amendment-20.md

Max-score uses one qhat for all rank slots. Studentization keeps the same
simultaneous conformal guarantee but uses one scale per slot:

    qhat_j = c * sigma_j

The guarantee holds because sigma is estimated only from fold1. Conditional on
fold1, ``s -> max_j s_j / sigma_j`` is deterministic, and fold2/test remain
exchangeable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from cert.conformal_v2 import SEED_SPLIT
from cert.simultaneous_score import ALPHA, conformal_level, empirical_qhat


SEED_FOLD = 7001
FRAC_FOLD1 = 0.5
SIGMA_ESTIMATOR = "rms"
SIGMA_FLOOR = 1e-9
MIN_BLOCKS_FOLD = 9
STATUS = "EXPLORATORY"

SCALE_TAG = "cost_ms"
LEVEL_TAG = "simultaneous"


def _json_clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_json_clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_clean(value.tolist())
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return None
    return value


def slot_columns(df: pd.DataFrame) -> list[str]:
    """Return ``s_pair_1..s_pair_m`` in slot order."""
    cols = [c for c in df.columns if re.match(r"^s_pair_[0-9]+$", str(c))]
    cols.sort(key=lambda c: int(str(c).rsplit("_", 1)[1]))
    if not cols:
        raise ValueError("khong tim thay cot s_pair_1..")
    expected = ["s_pair_%d" % i for i in range(1, len(cols) + 1)]
    if cols != expected:
        raise ValueError("cot slot khong lien tiep: %s" % cols)
    return cols


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _infer_cell(path: str) -> str:
    name = os.path.basename(path)
    match = re.match(r"calib_set_v3_(.+)_([0-9]+\.[0-9]+)(?:_V[0-9]+)?\.parquet$", name)
    if not match:
        return name
    return "%s@%.3f" % (match.group(1), float(match.group(2)))


def split_folds_by_block(
    block_id: np.ndarray,
    seed: int = SEED_FOLD,
    frac_fold1: float = FRAC_FOLD1,
) -> Tuple[np.ndarray, np.ndarray]:
    """Split whole blocks into fold1/fold2 and return row-level masks."""
    ids = np.asarray(block_id)
    blocks = np.sort(np.unique(ids))
    rng = np.random.default_rng(int(seed))
    perm = rng.permutation(len(blocks))
    n1 = int(round(float(frac_fold1) * len(blocks)))
    fold1_blocks = blocks[perm[:n1]]
    mask1 = np.isin(ids, fold1_blocks)
    return mask1, ~mask1


def estimate_sigma(
    pair_s_fold1: np.ndarray,
    estimator: str = SIGMA_ESTIMATOR,
    floor: float = SIGMA_FLOOR,
) -> np.ndarray:
    """Estimate one scale per rank slot using fold1 only."""
    arr = np.asarray(pair_s_fold1, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("pair_s phai co shape (n, K-1); ndim=%d" % arr.ndim)
    if arr.shape[0] == 0:
        raise ValueError("fold1 rong: khong uoc luong duoc sigma")

    if estimator == "rms":
        sigma = np.sqrt(np.mean(arr ** 2, axis=0))
    elif estimator == "mad":
        med = np.median(arr, axis=0)
        sigma = 1.4826 * np.median(np.abs(arr - med[None, :]), axis=0)
    else:
        raise ValueError("estimator phai la 'rms' hoac 'mad'; nhan %r" % estimator)
    return np.maximum(sigma.astype(np.float64), float(floor))


def s_studentized(pair_s: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Return ``v = max_j s_j / sigma_j`` for each row."""
    arr = np.asarray(pair_s, dtype=np.float64)
    sig = np.asarray(sigma, dtype=np.float64)
    if arr.ndim != 2 or sig.shape != (arr.shape[1],):
        raise ValueError("shape khong khop: pair_s %s, sigma %s" % (arr.shape, sig.shape))
    if np.any(sig <= 0.0):
        raise ValueError("sigma phai duong o moi slot; nhan %s" % sig)
    return (arr / sig[None, :]).max(axis=1)


def qhat_studentized(
    pair_s_fold1: np.ndarray,
    pair_s_fold2: np.ndarray,
    n_blocks_fold2: int,
    alpha: float = ALPHA,
    estimator: str = SIGMA_ESTIMATOR,
    force_uniform_sigma: Optional[float] = None,
    sigma_override: Optional[np.ndarray] = None,
    sigma_source_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Fit studentized qhat for one Mondrian bin."""
    f1 = np.asarray(pair_s_fold1, dtype=np.float64)
    f2 = np.asarray(pair_s_fold2, dtype=np.float64)
    if f2.ndim != 2:
        raise ValueError("pair_s_fold2 phai co shape (n, K-1)")
    m = f2.shape[1]

    if force_uniform_sigma is not None:
        sigma = np.full(m, float(force_uniform_sigma), dtype=np.float64)
        sigma_source = "forced_uniform"
    elif sigma_override is not None:
        sigma = np.maximum(np.asarray(sigma_override, np.float64), SIGMA_FLOOR)
        sigma_source = sigma_source_override or "override"
    else:
        sigma = estimate_sigma(f1, estimator)
        sigma_source = "fold1"

    n_eff = int(n_blocks_fold2)
    if n_eff < MIN_BLOCKS_FOLD:
        raise ValueError(
            "fold2 chi co %d block (< %d): qhat se la +inf. "
            "Giam so bin hoac tang du lieu." % (n_eff, MIN_BLOCKS_FOLD)
        )

    level = conformal_level(n_eff, float(alpha))
    c = empirical_qhat(s_studentized(f2, sigma), level)
    qhat = c * sigma
    return {
        "c": float(c),
        "sigma": [float(x) for x in sigma],
        "qhat": [float(x) for x in qhat],
        "level": None if level is None else float(level),
        "alpha": float(alpha),
        "n_eff_blocks_fold2": n_eff,
        "n_rows_fold1": int(f1.shape[0]),
        "n_rows_fold2": int(f2.shape[0]),
        "estimator": str(estimator),
        "sigma_source": sigma_source,
        "sigma_ratio_max_over_min": float(sigma.max() / sigma.min()),
    }


def maxscore_on_rows(
    s_sim_rows: np.ndarray,
    n_blocks: int,
    alpha: float = ALPHA,
    m: int = 3,
) -> np.ndarray:
    """Maxscore qhat on exactly the supplied rows and block count."""
    level = conformal_level(int(n_blocks), float(alpha))
    q = empirical_qhat(np.asarray(s_sim_rows, np.float64), level)
    return np.full(int(m), float(q), dtype=np.float64)


def fit_eval_studentized(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    estimator: str = SIGMA_ESTIMATOR,
    seed_fold: int = SEED_FOLD,
    frac_fold1: float = FRAC_FOLD1,
    sigma_scope: str = "per_bin",
    force_uniform_sigma: Optional[float] = None,
    leak_sigma_from_fold2: bool = False,
) -> Dict[str, Any]:
    """Fit studentized max-score by Mondrian bin and evaluate on test rows."""
    slots = slot_columns(df)
    m = len(slots)
    if "s_sim" not in df.columns:
        raise ValueError("thieu cot s_sim")
    if "block_id" not in df.columns:
        raise ValueError("thieu cot block_id")
    if bin_col not in df.columns:
        raise ValueError("thieu cot %s" % bin_col)

    is_calib = np.asarray(is_calib, dtype=bool)
    n = len(df)
    block_ids = df["block_id"].to_numpy()
    bins = df[bin_col].to_numpy()

    calib_pos = np.flatnonzero(is_calib)
    fold1_calib, fold2_calib = split_folds_by_block(block_ids[calib_pos], seed_fold, frac_fold1)
    in_f1 = np.zeros(n, dtype=bool)
    in_f2 = np.zeros(n, dtype=bool)
    in_f1[calib_pos[fold1_calib]] = True
    in_f2[calib_pos[fold2_calib]] = True
    in_test = ~is_calib

    scores = df[slots].to_numpy(np.float64)
    sigma_global = None
    if sigma_scope == "global":
        sigma_global = estimate_sigma(scores[in_f1], estimator)
    elif sigma_scope != "per_bin":
        raise ValueError("sigma_scope phai la 'per_bin' hoac 'global'")

    qhat: Dict[int, list[float]] = {}
    per_bin: Dict[int, Dict[str, Any]] = {}
    cov_sim: Dict[int, float] = {}
    cov_point: Dict[int, list[float]] = {}

    for raw_group in sorted(np.unique(bins).tolist()):
        g = int(raw_group)
        sel = bins == raw_group
        f1 = sel & in_f1
        f2 = sel & in_f2
        te = sel & in_test

        override = None
        override_source = None
        if leak_sigma_from_fold2:
            override = estimate_sigma(scores[f2], estimator)
            override_source = "override_LEAKED_fold2"
        if sigma_global is not None and override is None:
            override = sigma_global
            override_source = "global_fold1"

        info = qhat_studentized(
            scores[f1],
            scores[f2],
            n_blocks_fold2=int(pd.unique(block_ids[f2]).size),
            alpha=alpha,
            estimator=estimator,
            force_uniform_sigma=force_uniform_sigma,
            sigma_override=override,
            sigma_source_override=override_source,
        )
        q = np.asarray(info["qhat"], dtype=np.float64)
        qhat[g] = [float(x) for x in q]
        info["n_blocks_fold1"] = int(pd.unique(block_ids[f1]).size)
        info["n_test_rows"] = int(te.sum())
        per_bin[g] = info

        if te.sum():
            ok = scores[te] <= q[None, :]
            cov_sim[g] = float(ok.all(axis=1).mean())
            cov_point[g] = [float(x) for x in ok.mean(axis=0)]
        else:
            cov_sim[g] = 1.0
            cov_point[g] = [1.0] * m

    if in_test.sum():
        q_rows = np.vstack([np.asarray(qhat[int(g)]) for g in bins[in_test]])
        ok = scores[in_test] <= q_rows
        marginal = float(ok.all(axis=1).mean())
        pointwise = [float(x) for x in ok.mean(axis=0)]
    else:
        marginal = 1.0
        pointwise = [1.0] * m

    return {
        "procedure": "studentized_maxscore",
        "status": STATUS,
        "alpha": float(alpha),
        "alpha_each": float(alpha),
        "m_comparisons": m,
        "bin_col": bin_col,
        "slots": list(slots),
        "sigma_scope": sigma_scope,
        "estimator": str(estimator),
        "seed_fold": int(seed_fold),
        "frac_fold1": float(frac_fold1),
        "qhat": qhat,
        "per_bin": per_bin,
        "coverage_simultaneous": cov_sim,
        "coverage_pointwise": cov_point,
        "coverage_marginal": marginal,
        "coverage_simultaneous_marginal": marginal,
        "coverage_pointwise_marginal": pointwise,
        "leak_sigma_from_fold2": bool(leak_sigma_from_fold2),
        "force_uniform_sigma": force_uniform_sigma,
        "metadata": {
            "scale": SCALE_TAG,
            "level": LEVEL_TAG,
            "rowset": "calib split into fold1/fold2 by block; evaluated on test",
        },
    }


def negative_control_uniform_sigma(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    seed_fold: int = SEED_FOLD,
    frac_fold1: float = FRAC_FOLD1,
) -> Dict[str, Any]:
    """NC-S-1: uniform sigma equals maxscore on fold2."""
    slots = slot_columns(df)
    is_calib = np.asarray(is_calib, bool)
    block_ids = df["block_id"].to_numpy()
    bins = df[bin_col].to_numpy()
    s_sim = df["s_sim"].to_numpy(np.float64)

    calib_pos = np.flatnonzero(is_calib)
    _, fold2_calib = split_folds_by_block(block_ids[calib_pos], seed_fold, frac_fold1)
    in_f2 = np.zeros(len(df), dtype=bool)
    in_f2[calib_pos[fold2_calib]] = True

    stud = fit_eval_studentized(
        df,
        is_calib,
        bin_col=bin_col,
        alpha=alpha,
        seed_fold=seed_fold,
        frac_fold1=frac_fold1,
        force_uniform_sigma=1.0,
    )
    diffs = {}
    for raw_group in sorted(np.unique(bins).tolist()):
        g = int(raw_group)
        f2 = (bins == raw_group) & in_f2
        ref = maxscore_on_rows(s_sim[f2], int(pd.unique(block_ids[f2]).size), alpha, len(slots))
        got = np.asarray(stud["qhat"][g], np.float64)
        diffs[g] = float(np.max(np.abs(got - ref)))
    worst = max(diffs.values()) if diffs else 0.0
    return {
        "control": "NC-S-1",
        "max_abs_diff_by_bin": diffs,
        "max_abs_diff": float(worst),
        "reference": "maxscore_on_fold2_rows",
        "pass_G23_26": bool(worst <= 1e-9),
    }


def positive_control_sigma_leak(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    subsample_blocks: Optional[int] = None,
    seed_sub: int = 23501,
) -> Dict[str, Any]:
    """PC-S-1: intentionally estimate sigma from fold2 and report detectability."""
    data = df
    ic = np.asarray(is_calib, bool)
    if subsample_blocks is not None:
        rng = np.random.default_rng(int(seed_sub))
        blocks = np.sort(pd.unique(df["block_id"]))
        keep = rng.choice(blocks, size=min(int(subsample_blocks) * 2, len(blocks)), replace=False)
        mask = df["block_id"].isin(keep).to_numpy()
        data = df[mask].reset_index(drop=True)
        ic = ic[mask]

    clean = fit_eval_studentized(data, ic, bin_col=bin_col, alpha=alpha)
    leaked = fit_eval_studentized(data, ic, bin_col=bin_col, alpha=alpha, leak_sigma_from_fold2=True)
    drop = clean["coverage_marginal"] - leaked["coverage_marginal"]
    return {
        "control": "PC-S-1",
        "subsample_blocks": subsample_blocks,
        "coverage_clean": float(clean["coverage_marginal"]),
        "coverage_leaked": float(leaked["coverage_marginal"]),
        "coverage_drop": float(drop),
        "detectable": bool(drop > 0.02),
        "note": (
            "Voi p=3 va n lon, thien lech ro ri ~ O(p/n) nam duoi do phan "
            "giai do. Bao cao la KHONG PHAT HIEN DUOC, khong phai PASS."
        ),
    }


def compare_to_maxscore(
    stud: Mapping[str, Any],
    maxscore_result: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return qhat_stud / qhat_max by bin and slot."""
    rows = []
    for raw_group in sorted(int(x) for x in stud["qhat"]):
        qs = np.asarray(stud["qhat"][raw_group], np.float64)
        qmap = maxscore_result["qhat"]
        qm = np.asarray(qmap[raw_group] if raw_group in qmap else qmap[str(raw_group)], np.float64)
        for j, (q_s, q_m) in enumerate(zip(qs, qm), start=1):
            rows.append(
                {
                    "bin": raw_group,
                    "slot": j,
                    "qhat_stud": float(q_s),
                    "qhat_max": float(q_m),
                    "ratio": float(q_s / q_m) if q_m > 0.0 else float("nan"),
                }
            )

    by_slot: Dict[int, list[float]] = {}
    for row in rows:
        by_slot.setdefault(int(row["slot"]), []).append(float(row["ratio"]))
    return {
        "per_bin_slot": rows,
        "ratio_by_slot_mean": {j: float(np.mean(v)) for j, v in by_slot.items()},
        "ratio_by_slot_min": {j: float(np.min(v)) for j, v in by_slot.items()},
        "ratio_by_slot_max": {j: float(np.max(v)) for j, v in by_slot.items()},
        "G3a_slot1_ratio": float(np.mean(by_slot[1])),
        "G3b_slot2_ratio": float(np.mean(by_slot[2])) if 2 in by_slot else None,
        "G3b_slot3_ratio": float(np.mean(by_slot[3])) if 3 in by_slot else None,
    }


def main() -> None:
    from cert.conformal_simultaneous import acceptance_diagnostics, fit_eval_simultaneous
    from cert.conformal_v2 import split_blocks

    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--bin-col", default="z_bin")
    parser.add_argument("--kappa", type=float, default=1.0)
    parser.add_argument("--pc-subsample", type=int, default=20)
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    is_calib = (
        df["is_calib"].to_numpy(bool)
        if "is_calib" in df.columns
        else split_blocks(df["block_id"].to_numpy(), seed=SEED_SPLIT)
    )

    stud = fit_eval_studentized(df, is_calib, bin_col=args.bin_col, alpha=args.alpha)
    stud_global = fit_eval_studentized(
        df,
        is_calib,
        bin_col=args.bin_col,
        alpha=args.alpha,
        sigma_scope="global",
    )
    maxscore = fit_eval_simultaneous(
        df,
        is_calib,
        "maxscore",
        bin_col=args.bin_col,
        alpha=args.alpha,
    )

    out = {
        "cell": _infer_cell(args.calib),
        "status": STATUS,
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "n_calib_blocks": int(df.loc[is_calib, "block_id"].nunique()),
        "n_test_blocks": int(df.loc[~is_calib, "block_id"].nunique()),
        "studentized_per_bin_sigma": stud,
        "studentized_global_sigma": stud_global,
        "maxscore_reference": {
            "qhat": maxscore["qhat"],
            "coverage_marginal": maxscore["coverage_marginal"],
        },
        "compare_to_maxscore": compare_to_maxscore(stud, maxscore),
        "acceptance_studentized": acceptance_diagnostics(
            df,
            is_calib,
            stud,
            bin_col=args.bin_col,
            kappa=args.kappa,
        ),
        "acceptance_maxscore": acceptance_diagnostics(
            df,
            is_calib,
            maxscore,
            bin_col=args.bin_col,
            kappa=args.kappa,
        ),
        "NC_S_1": negative_control_uniform_sigma(
            df,
            is_calib,
            bin_col=args.bin_col,
            alpha=args.alpha,
        ),
        "PC_S_1_full": positive_control_sigma_leak(
            df,
            is_calib,
            bin_col=args.bin_col,
            alpha=args.alpha,
        ),
        "PC_S_1_small_n": positive_control_sigma_leak(
            df,
            is_calib,
            bin_col=args.bin_col,
            alpha=args.alpha,
            subsample_blocks=int(args.pc_subsample),
        ),
        "provenance": {
            "script": "cert/studentized_score.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "SEED_FOLD": SEED_FOLD,
            "FRAC_FOLD1": FRAC_FOLD1,
            "SIGMA_ESTIMATOR": SIGMA_ESTIMATOR,
            "SIGMA_FLOOR": SIGMA_FLOOR,
            "MIN_BLOCKS_FOLD": MIN_BLOCKS_FOLD,
            "amendment": "docs/phase-23/00u-amendment-20.md",
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    print(json.dumps(_json_clean(out["compare_to_maxscore"]["ratio_by_slot_mean"]), indent=1))
    print("c per bin:", {g: v["c"] for g, v in stud["per_bin"].items()})
    print(
        "sigma ratio per bin:",
        {g: round(v["sigma_ratio_max_over_min"], 4) for g, v in stud["per_bin"].items()},
    )
    print("coverage:", stud["coverage_marginal"])
    print("acceptance:", out["acceptance_studentized"]["acceptance_rate"])


if __name__ == "__main__":
    main()

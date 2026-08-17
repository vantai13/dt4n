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

# One constant cannot guard two different invariants. MIN_BLOCKS_FOLD = 9 was
# locked in Amendment 23-20 D5 to stop ``qhat = +inf`` (``level is None``); it
# sits EXACTLY at the ceiling (``conformal_level(9, 0.10) = 1.0``) and never
# guarded against ``level = 1.0``, which is a different failure -- ``qhat`` is
# then the MAX of fold2 and every procedure looks identical. Named separately
# so the two are never conflated again. See Amendment 23-21 section 1.
MIN_BLOCKS_FINITE = 9
MIN_BLOCKS_FOLD = MIN_BLOCKS_FINITE  # backwards-compatible alias, D5 value

STATUS = "EXPLORATORY"

SEEDS_SUB = (23501, 23502, 23503, 23504, 23505)
PC_TARGET_BLOCKS_FOLD2 = 30
MIN_ROWS_PER_CELL = 8

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


def min_blocks_unsaturated(alpha: float = ALPHA) -> int:
    """Smallest ``n`` with ``conformal_level(n, alpha) < 1.0``.

    Below this, ``conformal_level`` returns exactly ``1.0`` and ``qhat`` is the
    MAX of the calibration fold. Coverage is then ~1.0 for every procedure, so
    any control that compares two procedures at that ``n`` is CEILING-BOUND and
    measures nothing.

    Closed form: ``level < 1`` iff ``ceil((n+1)(1-alpha)) <= n-1`` iff
    ``n >= 2/alpha - 1``. At ``alpha=0.10`` this is ``n = 19``, NOT ``11``:
    ``conformal_level(11, 0.10) = 1.0``.
    """
    n = int(np.ceil(2.0 / float(alpha) - 1.0))
    while (conformal_level(n, float(alpha)) or 1.0) >= 1.0:
        n += 1
    return int(n)


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


def _check_not_saturating(n_blocks_fold2_target: int, alpha: float) -> float:
    """Raise unless the target block count leaves ``conformal_level`` below 1."""
    n_target = int(n_blocks_fold2_target)
    level = conformal_level(n_target, float(alpha))
    if level is None or level >= 1.0:
        raise ValueError(
            "n_blocks_fold2_target=%d cho conformal_level=%s >= 1.0: doi chung se "
            "bi TRAN CHAN (qhat = max cua fold2, coverage ~ 1.0 voi MOI thu tuc, "
            "ro ri hay khong deu cho cung mot so). Can n >= %d o alpha=%.3f."
            % (n_target, level, min_blocks_unsaturated(alpha), float(alpha))
        )
    return float(level)


def _subsample_to_target(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    n_blocks_fold2_target: int,
    seed_sub: int,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Keep ``4 * target`` blocks so fold2 lands near ``target`` blocks.

    ``is_calib`` halves the blocks, then the fold split halves them again.
    """
    rng = np.random.default_rng(int(seed_sub))
    blocks = np.sort(pd.unique(df["block_id"]))
    n_keep = min(4 * int(n_blocks_fold2_target), len(blocks))
    keep = rng.choice(blocks, size=n_keep, replace=False)
    mask = df["block_id"].isin(keep).to_numpy()
    return df[mask].reset_index(drop=True), np.asarray(is_calib, bool)[mask]


def _realized_levels(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Per-bin fold2 block counts and conformal levels actually used."""
    n_eff = {g: int(v["n_eff_blocks_fold2"]) for g, v in result["per_bin"].items()}
    levels = {g: v["level"] for g, v in result["per_bin"].items()}
    worst = max((1.0 if v is None else float(v)) for v in levels.values()) if levels else 1.0
    return {
        "n_eff_blocks_fold2_by_bin": n_eff,
        "conformal_level_by_bin": levels,
        "max_level": float(worst),
        "saturated": bool(worst >= 1.0),
    }


def positive_control_sigma_leak(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    n_blocks_fold2_target: Optional[int] = None,
    seeds_sub: Tuple[int, ...] = SEEDS_SUB,
) -> Dict[str, Any]:
    """PC-S-1: estimate sigma from fold2 on purpose and report detectability.

    ``n_blocks_fold2_target`` is the WANTED number of blocks in fold2, not the
    number of blocks kept: ``blocks_kept = 4 * target`` because ``is_calib``
    halves and the fold split halves again.

    Refuses any target whose ``conformal_level`` is ``>= 1.0``. At that point
    ``qhat`` is the max of fold2 and coverage saturates near 1.0 for both the
    clean and the leaked arm, so the comparison is CEILING-BOUND and carries no
    information. See :func:`min_blocks_unsaturated`.

    With a subsample the run is repeated over ``seeds_sub`` and reported as
    ``mean +/- SD``: at ~30 blocks the coverage estimate is itself noisy.
    """
    target_level = None
    if n_blocks_fold2_target is not None:
        target_level = _check_not_saturating(n_blocks_fold2_target, alpha)

    seeds = tuple(int(s) for s in seeds_sub) if n_blocks_fold2_target is not None else (0,)
    runs = []
    for seed in seeds:
        if n_blocks_fold2_target is None:
            data, ic = df, np.asarray(is_calib, bool)
        else:
            data, ic = _subsample_to_target(df, is_calib, n_blocks_fold2_target, seed)
        clean = fit_eval_studentized(data, ic, bin_col=bin_col, alpha=alpha)
        leaked = fit_eval_studentized(
            data, ic, bin_col=bin_col, alpha=alpha, leak_sigma_from_fold2=True
        )
        realized = _realized_levels(clean)
        if realized["saturated"]:
            raise ValueError(
                "seed=%d: conformal_level thuc te = %.4f >= 1.0 -> TRAN CHAN. "
                "Tang n_blocks_fold2_target. Chi tiet: %s"
                % (seed, realized["max_level"], realized["n_eff_blocks_fold2_by_bin"])
            )
        runs.append(
            {
                "seed_sub": seed,
                "coverage_clean": float(clean["coverage_marginal"]),
                "coverage_leaked": float(leaked["coverage_marginal"]),
                "coverage_drop": float(clean["coverage_marginal"] - leaked["coverage_marginal"]),
                "realized": realized,
            }
        )

    clean_v = np.array([r["coverage_clean"] for r in runs], dtype=np.float64)
    leaked_v = np.array([r["coverage_leaked"] for r in runs], dtype=np.float64)
    drop_v = np.array([r["coverage_drop"] for r in runs], dtype=np.float64)
    sd = (lambda a: float(a.std(ddof=1)) if a.size > 1 else 0.0)
    return {
        "control": "PC-S-1",
        "n_blocks_fold2_target": n_blocks_fold2_target,
        "conformal_level_at_target": target_level,
        "n_seeds": len(runs),
        "seeds_sub": [r["seed_sub"] for r in runs],
        "coverage_clean": float(clean_v.mean()),
        "coverage_clean_sd": sd(clean_v),
        "coverage_leaked": float(leaked_v.mean()),
        "coverage_leaked_sd": sd(leaked_v),
        "coverage_drop": float(drop_v.mean()),
        "coverage_drop_sd": sd(drop_v),
        "detectable": bool(drop_v.mean() > 0.02),
        "per_seed": runs,
        "note": (
            "p=3 tham so sigma. Thien lech ro ri ~ O(p/n_eff) nam duoi do phan "
            "giai do. Ket qua la KHONG PHAT HIEN DUOC, KHONG phai PASS. Do nhay "
            "cua phep do duoc chung minh rieng bang PC-S-1d."
        ),
    }


def _cell_index(mhat_fold1: np.ndarray, mhat_all: np.ndarray, n_cells: int) -> np.ndarray:
    """Quantile-cell index of every row, with edges taken from fold1 only."""
    probs = np.linspace(0.0, 1.0, int(n_cells) + 1)[1:-1]
    edges = np.unique(np.quantile(np.asarray(mhat_fold1, np.float64), probs))
    return np.searchsorted(edges, np.asarray(mhat_all, np.float64), side="right")


def _cell_sigma(
    scores_src: np.ndarray,
    cells_src: np.ndarray,
    n_cells: int,
    m: int,
    estimator: str = SIGMA_ESTIMATOR,
) -> Tuple[np.ndarray, np.ndarray]:
    """RMS scale per ``(cell, slot)``; thin cells fall back to the bin scale."""
    fallback = estimate_sigma(scores_src, estimator)
    sigma = np.tile(fallback, (int(n_cells), 1))
    counts = np.zeros(int(n_cells), dtype=np.int64)
    for cell in range(int(n_cells)):
        sel = cells_src == cell
        n_sel = int(sel.sum())
        counts[cell] = n_sel
        if n_sel >= MIN_ROWS_PER_CELL:
            sigma[cell] = estimate_sigma(scores_src[sel], estimator)
    return np.maximum(sigma, SIGMA_FLOOR), counts


def positive_control_high_dim_sigma(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    n_mhat_cells: int = 100,
    mhat_col: str = "m_hat_1",
    estimator: str = SIGMA_ESTIMATOR,
    seed_fold: int = SEED_FOLD,
    frac_fold1: float = FRAC_FOLD1,
    n_blocks_fold2_target: Optional[int] = None,
    seed_sub: int = SEEDS_SUB[0],
) -> Dict[str, Any]:
    """PC-S-1d: high-dimensional sigma, CLEAN versus LEAKED.

    ``sigma`` is estimated per ``(m_hat_1 quantile cell, rank slot)``, so
    ``p = n_mhat_cells * m`` per Mondrian bin instead of ``m``. ``m_hat_1`` is
    observable at run time, so this sigma is deployable, not an oracle.

    CLEAN  -- sigma values from fold1. The split-conformal guarantee does NOT
              depend on sigma being right, only on sigma being a function of
              fold1, so coverage must stay near ``1 - alpha`` at ANY ``p``.
    LEAKED -- sigma values from fold2, the same rows the quantile is taken on.
              In-sample normalisation deflates the calibration scores, so the
              quantile is too small and coverage must fall.

    Cell EDGES come from fold1 in both arms. Only the sigma VALUES move, which
    isolates the in-sample-normalisation mechanism from any change of binning.

    Purpose: show the coverage measurement HAS the resolution to see a leak.
    A positive control that never fires proves nothing.
    """
    # Config first: a saturating target is a design error, report it before
    # anything about the frame.
    target_level = None
    if n_blocks_fold2_target is not None:
        target_level = _check_not_saturating(n_blocks_fold2_target, alpha)

    slots = slot_columns(df)
    m = len(slots)
    if mhat_col not in df.columns:
        raise ValueError("thieu cot %s" % mhat_col)

    data, ic = df, np.asarray(is_calib, bool)
    if n_blocks_fold2_target is not None:
        data, ic = _subsample_to_target(df, is_calib, n_blocks_fold2_target, seed_sub)

    block_ids = data["block_id"].to_numpy()
    bins = data[bin_col].to_numpy()
    scores = data[slots].to_numpy(np.float64)
    mhat = data[mhat_col].to_numpy(np.float64)

    calib_pos = np.flatnonzero(ic)
    fold1_calib, _ = split_folds_by_block(block_ids[calib_pos], seed_fold, frac_fold1)
    in_f1 = np.zeros(len(data), dtype=bool)
    in_f1[calib_pos[fold1_calib]] = True
    in_f2 = np.zeros(len(data), dtype=bool)
    in_f2[calib_pos[~fold1_calib]] = True
    in_test = ~ic

    arms: Dict[str, Dict[str, Any]] = {}
    diag: Dict[str, Any] = {}
    for arm, src_mask in (("clean", in_f1), ("leaked", in_f2)):
        ok_all = []
        per_bin: Dict[int, Dict[str, Any]] = {}
        for raw_group in sorted(np.unique(bins).tolist()):
            g = int(raw_group)
            sel = bins == raw_group
            f1, f2, te = sel & in_f1, sel & in_f2, sel & in_test
            src = sel & src_mask

            cells_all = _cell_index(mhat[f1], mhat, n_mhat_cells)
            sigma, counts = _cell_sigma(
                scores[src], cells_all[src], n_mhat_cells, m, estimator
            )
            v = (scores / sigma[cells_all]).max(axis=1)

            n_eff = int(pd.unique(block_ids[f2]).size)
            if n_eff < MIN_BLOCKS_FOLD:
                raise ValueError("fold2 bin %d chi co %d block" % (g, n_eff))
            level = conformal_level(n_eff, float(alpha))
            if level is None or level >= 1.0:
                raise ValueError(
                    "bin %d: conformal_level=%s >= 1.0 -> TRAN CHAN" % (g, level)
                )
            c = empirical_qhat(v[f2], level)
            ok = v[te] <= c
            ok_all.append(ok)

            # Coverage per m_hat cell is NOT promised by the theorem -- exact
            # conditional validity is impossible (Vovk 2012; Lei & Wasserman
            # 2014). Reported so the marginal claim is not read as more than
            # it is.
            cell_cov = []
            cells_te = cells_all[te]
            for cell in range(int(n_mhat_cells)):
                pick = cells_te == cell
                if int(pick.sum()) >= MIN_ROWS_PER_CELL:
                    cell_cov.append(float(ok[pick].mean()))
            cell_cov_arr = np.asarray(cell_cov, dtype=np.float64)

            per_bin[g] = {
                "c": float(c),
                "p_per_bin": int(n_mhat_cells * m),
                "n_rows_source": int(src.sum()),
                "n_eff_blocks_fold2": n_eff,
                "level": float(level),
                "coverage_simultaneous": float(ok.mean()) if te.sum() else 1.0,
                "median_rows_per_cell": float(np.median(counts)),
                "n_cells_below_min_rows": int((counts < MIN_ROWS_PER_CELL).sum()),
                "coverage_by_mhat_cell_min": (
                    float(cell_cov_arr.min()) if cell_cov_arr.size else None
                ),
                "coverage_by_mhat_cell_max": (
                    float(cell_cov_arr.max()) if cell_cov_arr.size else None
                ),
                "coverage_by_mhat_cell_spread": (
                    float(cell_cov_arr.max() - cell_cov_arr.min()) if cell_cov_arr.size else None
                ),
                "n_mhat_cells_scored": int(cell_cov_arr.size),
            }
            if arm == "clean":
                blocks_per_cell = [
                    int(pd.unique(block_ids[src][cells_all[src] == cell]).size)
                    for cell in range(int(n_mhat_cells))
                ]
                diag.setdefault("median_blocks_per_cell_by_bin", {})[g] = float(
                    np.median(blocks_per_cell)
                )
        joined = np.concatenate(ok_all) if ok_all else np.ones(1, dtype=bool)
        by_zbin = {g: v["coverage_simultaneous"] for g, v in per_bin.items()}
        cell_spreads = [
            v["coverage_by_mhat_cell_spread"]
            for v in per_bin.values()
            if v["coverage_by_mhat_cell_spread"] is not None
        ]
        arms[arm] = {
            "coverage_marginal": float(joined.mean()),
            "coverage_by_zbin": by_zbin,
            "coverage_by_zbin_min": float(min(by_zbin.values())) if by_zbin else None,
            "coverage_by_mhat_cell_spread_max": (
                float(max(cell_spreads)) if cell_spreads else None
            ),
            "per_bin": per_bin,
            "sigma_source": "fold1" if arm == "clean" else "fold2_LEAKED",
            "scope_note": (
                "coverage_by_zbin la dai luong dinh ly BAO DAM (bien trong tung "
                "bin Mondrian). coverage_by_mhat_cell KHONG duoc bao dam: bao phu "
                "co dieu kien chinh xac la bat kha thi (Vovk 2012; Lei & Wasserman "
                "2014). Ghi de trung thuc, khong phai de cham gate."
            ),
        }

    drop = arms["clean"]["coverage_marginal"] - arms["leaked"]["coverage_marginal"]
    p_total = int(n_mhat_cells * m * len(np.unique(bins)))
    return {
        "control": "PC-S-1d",
        "n_mhat_cells": int(n_mhat_cells),
        "mhat_col": mhat_col,
        "p_per_bin": int(n_mhat_cells * m),
        "p_total": p_total,
        "n_blocks_fold2_target": n_blocks_fold2_target,
        "conformal_level_at_target": target_level,
        "coverage_clean": arms["clean"]["coverage_marginal"],
        "coverage_leaked": arms["leaked"]["coverage_marginal"],
        "coverage_drop": float(drop),
        "detectable": bool(drop > 0.02),
        "clean_holds": bool(arms["clean"]["coverage_marginal"] >= 1.0 - float(alpha) - 0.02),
        "clean_holds_in_every_zbin": bool(
            arms["clean"]["coverage_by_zbin_min"] >= 1.0 - float(alpha) - 0.02
        ),
        "arms": arms,
        "diagnostics": diag,
        "note": (
            "CLEAN phai GIU coverage ~ 1-alpha du p lon: bao dam split-conformal "
            "khong phu thuoc sigma dung hay sai, chi phu thuoc sigma doc lap voi "
            "fold2/test. LEAKED phai VO. Neu ca hai deu giu, phep do coverage "
            "khong du do nhay o cau hinh nay."
        ),
    }


def positive_control_high_dim_sweep(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    cells_grid: Tuple[int, ...] = (10, 100, 1000),
    mhat_col: str = "m_hat_1",
) -> Dict[str, Any]:
    """PC-S-1d over a ladder of ``p``.

    One point cannot separate "the leak is small" from "the measurement is
    blind". A monotone ladder can: if the LEAKED arm degrades with ``p`` while
    the CLEAN arm does not, the measurement has resolution and the guarantee is
    insensitive to how wrong sigma is.
    """
    rungs = []
    for cells in cells_grid:
        out = positive_control_high_dim_sigma(
            df, is_calib, bin_col=bin_col, alpha=alpha,
            n_mhat_cells=int(cells), mhat_col=mhat_col,
        )
        med_rows = float(
            np.median([v["median_rows_per_cell"] for v in out["arms"]["clean"]["per_bin"].values()])
        )
        med_blocks = float(
            np.median(list(out["diagnostics"]["median_blocks_per_cell_by_bin"].values()))
        )
        rungs.append(
            {
                "n_mhat_cells": int(cells),
                "p_per_bin": out["p_per_bin"],
                "coverage_clean": out["coverage_clean"],
                "coverage_leaked": out["coverage_leaked"],
                "coverage_drop": out["coverage_drop"],
                "detectable": out["detectable"],
                "clean_holds": out["clean_holds"],
                "clean_holds_in_every_zbin": out["clean_holds_in_every_zbin"],
                "clean_coverage_by_zbin_min": out["arms"]["clean"]["coverage_by_zbin_min"],
                "clean_coverage_by_mhat_cell_spread_max": (
                    out["arms"]["clean"]["coverage_by_mhat_cell_spread_max"]
                ),
                "median_rows_per_cell": med_rows,
                "median_blocks_per_cell": med_blocks,
            }
        )

    clean = np.array([r["coverage_clean"] for r in rungs])
    leaked = np.array([r["coverage_leaked"] for r in rungs])
    return {
        "control": "PC-S-1d-sweep",
        "mhat_col": mhat_col,
        "rungs": rungs,
        "p_per_bin_grid": [r["p_per_bin"] for r in rungs],
        "clean_holds_at_every_p": bool(all(r["clean_holds"] for r in rungs)),
        "clean_holds_in_every_zbin_at_every_p": bool(
            all(r["clean_holds_in_every_zbin"] for r in rungs)
        ),
        "clean_spread": float(clean.max() - clean.min()),
        "leaked_spread": float(leaked.max() - leaked.min()),
        "leaked_is_monotone_decreasing": bool(np.all(np.diff(leaked) <= 0.0)),
        "detectable_at_any_p": bool(any(r["detectable"] for r in rungs)),
        "max_coverage_drop": float(max(r["coverage_drop"] for r in rungs)),
        "note": (
            "Do manh cua ro ri bam theo SO BLOCK moi o, khong phai so hang moi o: "
            "m_hat_1 co cau truc theo block, nen n hieu dung cua sigma la block."
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


def accept_set_contingency(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    res_a: Mapping[str, Any],
    res_b: Mapping[str, Any],
    bin_col: str = "z_bin",
    kappa: float = 1.0,
    label_a: str = "maxscore",
    label_b: str = "studentized",
) -> Dict[str, Any]:
    """Exact 2x2 table between two accept sets, with wrong-rate in each cell.

    Nesting is NOT structural, so ``err on rows ADDED by B`` must be MEASURED
    here, never inferred by differencing two acceptance rates.

    ``B`` contains ``A`` only if every row ``A`` accepts also clears B's widened
    slots. With ``qhat_a`` flat at ``q_max`` and margins sorted
    ``m_hat_1 <= m_hat_2 <= m_hat_3``, a row with ``m_hat_1 >= q_max`` clears
    slot ``j`` of B automatically when ``qhat_b_j <= q_max``. Which slot binds
    is NOT obvious a priori: ``qhat_b_3 / q_max`` is the largest ratio, but the
    slack is ``m_hat_j / qhat_b_j`` and ``m_hat_3`` is also the largest margin,
    so slot 2 can and does bind first. ``nesting_slack_binding_slot`` measures
    it rather than assuming it. Two quantities are reported:

    ``nesting_slack_min`` -- EXACT and continuous. The smallest, over rows that
    ``A`` accepts, of ``min_j m_hat_j / (kappa * qhat_b_j)``. Nesting holds iff
    this is ``>= 1``. It degrades smoothly before nesting actually breaks, so
    it is the quantity to track across Lesson 23.11.

    ``sufficient_condition_margin`` -- CHEAP and interpretable, but only
    SUFFICIENT: it compares ``max_j qhat_b_j / qhat_a_j`` against the smallest
    ``m_hat_3 / m_hat_1`` over accepted rows. Being NEGATIVE does not mean
    nesting failed, only that this coarse bound does not certify it (it mixes a
    max over bins with a min over rows pooled across bins). Read
    ``only_<label_a>`` for the fact and ``nesting_slack_min`` for the margin.

    Either way nesting is a property of the COST SPREAD between paths -- exactly
    the axis Lesson 23.11 varies -- and never a theorem.
    """
    from cert.conformal_simultaneous import _margin_cols, _qrows, _slot_cols

    slots = _slot_cols(df)
    m = len(slots)
    mh_cols = _margin_cols("m_hat", m, df)
    test = df[~np.asarray(is_calib, dtype=bool)]
    if len(test) == 0:
        return {"kappa": float(kappa), "n_test": 0}

    mh = test[mh_cols].to_numpy(np.float64)
    q_a = _qrows(test, res_a["qhat"], bin_col)
    q_b = _qrows(test, res_b["qhat"], bin_col)
    acc_a = (mh >= float(kappa) * q_a).all(axis=1)
    acc_b = (mh >= float(kappa) * q_b).all(axis=1)

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio_b_over_a = np.where(q_a > 0.0, q_b / q_a, np.nan)
        mhat_ratio = np.where(mh[:, 0] > 0.0, mh[:, -1] / mh[:, 0], np.nan)
        # Exact per-row slack against B's thresholds; >= 1 means the row clears.
        row_slack = np.nanmin(
            np.where(q_b > 0.0, mh / (float(kappa) * q_b), np.inf), axis=1
        )
    threshold = float(np.nanmax(ratio_b_over_a))
    accepted_ratio = mhat_ratio[acc_a]
    ratio_min = float(np.nanmin(accepted_ratio)) if accepted_ratio.size else float("nan")
    slack_acc = row_slack[acc_a]
    slack_min = float(np.nanmin(slack_acc)) if slack_acc.size else float("nan")
    binding_slot = (
        int(np.nanargmin(np.where(q_b > 0.0, mh / (float(kappa) * q_b), np.inf)[acc_a][
            int(np.nanargmin(slack_acc))
        ])) + 1
        if slack_acc.size
        else None
    )
    wrong = (
        test["wrong"].to_numpy(bool)
        if "wrong" in test.columns
        else np.zeros(len(test), dtype=bool)
    )

    def cell(mask: np.ndarray) -> Dict[str, Any]:
        n = int(mask.sum())
        return {
            "n": n,
            "n_wrong": int(wrong[mask].sum()),
            "p_wrong": float(wrong[mask].mean()) if n else None,
        }

    both = acc_a & acc_b
    only_a = acc_a & ~acc_b
    only_b = acc_b & ~acc_a
    neither = ~acc_a & ~acc_b
    return {
        "kappa": float(kappa),
        "label_a": label_a,
        "label_b": label_b,
        "n_test": int(len(test)),
        "nested_b_contains_a": bool(only_a.sum() == 0),
        "both": cell(both),
        "only_%s" % label_a: cell(only_a),
        "only_%s" % label_b: cell(only_b),
        "neither": cell(neither),
        "n_accept_%s" % label_a: int(acc_a.sum()),
        "n_accept_%s" % label_b: int(acc_b.sum()),
        "p_wrong_on_rows_added_by_%s" % label_b: cell(only_b)["p_wrong"],
        "p_wrong_on_rows_dropped_by_%s" % label_b: cell(only_a)["p_wrong"],
        "risk_budget_used_%s" % label_a: float((acc_a & wrong).mean()),
        "risk_budget_used_%s" % label_b: float((acc_b & wrong).mean()),
        "nesting_holds": bool(only_a.sum() == 0),
        "nesting_slack_min": slack_min,
        "nesting_slack_binding_slot": binding_slot,
        "sufficient_condition_threshold": threshold,
        "mhat_ratio_min_over_accepted": ratio_min,
        "sufficient_condition_margin": float(ratio_min - threshold),
        "nesting_is_structural": False,
        "nesting_note": (
            "nesting_slack_min >= 1 <=> tap accept cua %s chua tron tap cua %s "
            "(EXACT). sufficient_condition_margin chi la can DU: am KHONG co "
            "nghia nesting vo. Ca hai la tinh chat CUA DU LIEU (do trai chi phi "
            "giua cac duong), KHONG phai dinh ly; chung giam khi cac duong sat "
            "nhau ve cost." % (label_b, label_a)
        ),
    }


def phase22_reproduction_check(
    cell: str,
    maxscore_result: Mapping[str, Any],
    acceptance_maxscore: Mapping[str, Any],
    root: str = "results/phase-22",
) -> Dict[str, Any]:
    """Compare today's maxscore reference against the committed Phase 22 artifact.

    Phase 23 recomputes maxscore from the same parquet through the same code
    path, so any difference is an ENVIRONMENT difference, not a method one.
    This run used a different pandas/numpy/pyarrow than Phase 22, which makes
    the comparison a real portability check rather than a tautology.
    """
    name = cell.replace("@", "_").replace("0.", "0.")
    match = re.match(r"^(.+)@([0-9.]+)$", str(cell))
    if match:
        name = "%s_%.3f" % (match.group(1), float(match.group(2)))
    path = os.path.join(root, "conformal_sim_%s.json" % name)
    if not os.path.exists(path):
        return {"available": False, "path": path}

    with open(path, encoding="utf-8") as f:
        ref = json.load(f)
    try:
        ref_acc = float(ref["acceptance_kappa_1"]["maxscore"]["acceptance_rate"])
        ref_cov = float(ref["procedures"]["maxscore"]["coverage_marginal"])
        ref_q = ref["procedures"]["maxscore"]["qhat"]
    except (KeyError, TypeError):
        return {"available": False, "path": path, "reason": "khoa maxscore khong co"}

    now_acc = float(acceptance_maxscore["acceptance_rate"])
    now_cov = float(maxscore_result["coverage_marginal"])
    now_q = maxscore_result["qhat"]
    q_diff = 0.0
    for g, vals in now_q.items():
        other = ref_q.get(str(g), ref_q.get(int(g)) if isinstance(g, str) else None)
        if other is None:
            continue
        q_diff = max(q_diff, float(np.max(np.abs(np.asarray(vals, np.float64) - np.asarray(other, np.float64)))))

    return {
        "available": True,
        "path": path,
        "acceptance": {"now": now_acc, "phase22": ref_acc, "abs_diff": abs(now_acc - ref_acc)},
        "coverage": {"now": now_cov, "phase22": ref_cov, "abs_diff": abs(now_cov - ref_cov)},
        "qhat_max_abs_diff": float(q_diff),
        "bit_exact": bool(
            now_acc == ref_acc and now_cov == ref_cov and q_diff == 0.0
        ),
        "note": (
            "Chay lai duoi pandas/numpy/pyarrow KHAC Phase 22. bit_exact=true la "
            "bang chung duong ong tai lap qua mot bien moi truong."
        ),
    }


def _env_provenance() -> Dict[str, Any]:
    """Record the interpreter and the libraries that touch the numbers."""
    import platform

    env: Dict[str, Any] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    try:
        import pyarrow

        env["pyarrow"] = pyarrow.__version__
    except Exception:
        env["pyarrow"] = "unknown"
    env["note"] = "co the KHAC moi truong chay Phase 22; xem reproduction_check"
    return env


def c_invariance_by_bin(result: Mapping[str, Any]) -> Dict[str, Any]:
    """F-23.5A-1: spread of ``c`` across Mondrian bins.

    ``qhat(z, j) = c(z) * sigma(z, j)``. If ``c`` is near constant once sigma is
    per-bin, then ALL of the age dependence of ``qhat`` sits in the scale
    ``sigma(z)`` and the normalised score shape does not move with age.
    """
    c_by_bin = {int(g): float(v["c"]) for g, v in result["per_bin"].items()}
    values = np.array(list(c_by_bin.values()), dtype=np.float64)
    return {
        "c_by_bin": c_by_bin,
        "c_min": float(values.min()),
        "c_max": float(values.max()),
        "c_mean": float(values.mean()),
        "relative_spread": float((values.max() - values.min()) / values.mean()),
        "sigma_scope": result.get("sigma_scope"),
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
    parser.add_argument(
        "--pc-blocks-fold2",
        type=int,
        default=PC_TARGET_BLOCKS_FOLD2,
        help="so block MUC TIEU cua fold2 trong PC-S-1 (khong phai so block giu)",
    )
    parser.add_argument("--pc-mhat-cells", type=int, default=100)
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
            n_blocks_fold2_target=int(args.pc_blocks_fold2),
        ),
        "PC_S_1d_high_dim": positive_control_high_dim_sigma(
            df,
            is_calib,
            bin_col=args.bin_col,
            alpha=args.alpha,
            n_mhat_cells=int(args.pc_mhat_cells),
        ),
        "PC_S_1d_sweep": positive_control_high_dim_sweep(
            df,
            is_calib,
            bin_col=args.bin_col,
            alpha=args.alpha,
        ),
        "accept_set_contingency": accept_set_contingency(
            df,
            is_calib,
            maxscore,
            stud,
            bin_col=args.bin_col,
            kappa=args.kappa,
        ),
        "reproduction_check": phase22_reproduction_check(
            _infer_cell(args.calib),
            {"qhat": maxscore["qhat"], "coverage_marginal": maxscore["coverage_marginal"]},
            acceptance_diagnostics(
                df, is_calib, maxscore, bin_col=args.bin_col, kappa=1.0
            ),
        ),
        "c_invariance_per_bin_sigma": c_invariance_by_bin(stud),
        "c_invariance_global_sigma": c_invariance_by_bin(stud_global),
        "sigma3_over_sigma1_by_bin": {
            int(g): float(np.asarray(v["sigma"])[-1] / np.asarray(v["sigma"])[0])
            for g, v in stud["per_bin"].items()
        },
        "retracted": {
            "PC_S_1_small_n@subsample_blocks=20": (
                "HUY BO. Artifact 2026-08-16 giu 40 block -> fold2 con 9 block moi "
                "bin -> conformal_level = 1.0 -> qhat = max cua fold2 -> "
                "coverage ~ 0.9997 bat ke ro ri. coverage_drop 0.0010-0.0026 la "
                "TRAN CHAN, vo nghia, khong duoc trich dan. Xem Amendment 23-21."
            )
        },
        "provenance": {
            "script": "cert/studentized_score.py",
            "calib": args.calib,
            "env": _env_provenance(),
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "SEED_FOLD": SEED_FOLD,
            "FRAC_FOLD1": FRAC_FOLD1,
            "SIGMA_ESTIMATOR": SIGMA_ESTIMATOR,
            "SIGMA_FLOOR": SIGMA_FLOOR,
            "MIN_BLOCKS_FOLD": MIN_BLOCKS_FOLD,
            "MIN_ROWS_PER_CELL": MIN_ROWS_PER_CELL,
            "PC_TARGET_BLOCKS_FOLD2": int(args.pc_blocks_fold2),
            "SEEDS_SUB": list(SEEDS_SUB),
            "min_blocks_unsaturated_at_alpha": min_blocks_unsaturated(args.alpha),
            "amendment": [
                "docs/phase-23/00u-amendment-20.md",
                "docs/phase-23/00v-amendment-21.md",
            ],
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
    print("c spread per-bin sigma:", round(out["c_invariance_per_bin_sigma"]["relative_spread"], 4))
    print("c spread global sigma :", round(out["c_invariance_global_sigma"]["relative_spread"], 4))
    pc1, pcd = out["PC_S_1_small_n"], out["PC_S_1d_high_dim"]
    print(
        "PC-S-1  small_n: drop = %.5f +/- %.5f (target %d blocks, level %.4f)"
        % (
            pc1["coverage_drop"],
            pc1["coverage_drop_sd"],
            pc1["n_blocks_fold2_target"],
            pc1["conformal_level_at_target"],
        )
    )
    print(
        "PC-S-1d high-dim: clean %.5f / leaked %.5f / drop %.5f "
        "(p_per_bin=%d, p_total=%d)"
        % (
            pcd["coverage_clean"],
            pcd["coverage_leaked"],
            pcd["coverage_drop"],
            pcd["p_per_bin"],
            pcd["p_total"],
        )
    )
    print(
        "PC-S-1d sweep (p_per_bin [p_total] -> clean | leaked | drop | "
        "min cov by z_bin | max cov spread by mhat cell | blocks/cell):"
    )
    n_bins_seen = len(out["studentized_per_bin_sigma"]["qhat"])
    for rung in out["PC_S_1d_sweep"]["rungs"]:
        print(
            "  p_per_bin=%-5d [p_total=%-6d] %.5f | %.5f | %+.5f | %.5f | %.5f | %.1f"
            % (
                rung["p_per_bin"],
                rung["p_per_bin"] * n_bins_seen,
                rung["coverage_clean"],
                rung["coverage_leaked"],
                rung["coverage_drop"],
                rung["clean_coverage_by_zbin_min"],
                rung["clean_coverage_by_mhat_cell_spread_max"],
                rung["median_blocks_per_cell"],
            )
        )
    ctg = out["accept_set_contingency"]
    print(
        "accept 2x2: both=%d only_max=%d only_stud=%d | p_wrong on ADDED rows = %s"
        % (
            ctg["both"]["n"],
            ctg["only_maxscore"]["n"],
            ctg["only_studentized"]["n"],
            ctg["p_wrong_on_rows_added_by_studentized"],
        )
    )
    print(
        "nesting: holds=%s  slack_min=%.4f (slot %s, EXACT: >=1 <=> nested)  "
        "| sufficient-only margin=%+.4f"
        % (
            ctg["nesting_holds"],
            ctg["nesting_slack_min"],
            ctg["nesting_slack_binding_slot"],
            ctg["sufficient_condition_margin"],
        )
    )
    rep = out["reproduction_check"]
    print(
        "reproduction vs Phase 22: %s"
        % (
            "bit_exact=%s (acc diff %.3g, cov diff %.3g, qhat diff %.3g)"
            % (
                rep["bit_exact"],
                rep["acceptance"]["abs_diff"],
                rep["coverage"]["abs_diff"],
                rep["qhat_max_abs_diff"],
            )
            if rep.get("available")
            else "khong co artifact doi chieu"
        )
    )


if __name__ == "__main__":
    main()

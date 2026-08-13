#!/usr/bin/env python3
"""Phase 22 / Lesson 22.3 -- simultaneous conformal calibration.

The input is the v3 calibration table from :mod:`cert.build_calib_set_v3`.
Rows already contain the three rank-slot scores ``s_pair_1..3`` and their
corresponding predicted/true margins.  This module only calibrates qhat and
evaluates held-out coverage; it does not regenerate the physical data.
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

from cert.conformal_v2 import (
    N_REPEAT_V3,
    SEED_PICK,
    SEED_SPLIT,
    conformal_level,
    empirical_qhat,
    fit_eval as fit_eval_21r,
    split_blocks,
    split_by_seed,
    split_rows_V3,
)
from cert.simultaneous_score import ALPHA, alpha_bonferroni, alpha_sidak, n_comparisons


PROCEDURES = ("uncorrected", "bonferroni", "sidak", "maxscore")
COV_TOL = 0.02
V3_SD_RATIO_MAX = 0.50
N_BOOT = 200
Z_1MA = 1.6448536269514722


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
    if isinstance(value, np.ndarray):
        return [_json_clean(x) for x in value.tolist()]
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
    match = re.match(r"calib_set_v3_(.+)_([0-9]+\.[0-9]+)(?:_V[0-9]+)?\.parquet$", name)
    if not match:
        return "unknown"
    suffix = "_V3" if "_V3.parquet" in name else ""
    return "%s@%.3f%s" % (match.group(1), float(match.group(2)), suffix)


def alpha_each(procedure: str, alpha: float = ALPHA, m: int = 3) -> float:
    """Return the per-claim alpha used by one simultaneous procedure."""
    procedure = str(procedure)
    m = int(m)
    if procedure in ("uncorrected", "maxscore"):
        return float(alpha)
    if procedure == "bonferroni":
        return alpha_bonferroni(alpha, m)
    if procedure == "sidak":
        return alpha_sidak(alpha, m)
    raise ValueError("procedure phai thuoc %s; nhan %r" % (PROCEDURES, procedure))


def _slot_cols(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if re.match(r"^s_pair_[0-9]+$", str(c))]
    cols.sort(key=lambda c: int(str(c).rsplit("_", 1)[1]))
    if not cols:
        raise ValueError("khong tim thay cot s_pair_1..")
    expected = ["s_pair_%d" % i for i in range(1, len(cols) + 1)]
    if cols != expected:
        raise ValueError("cot slot khong lien tiep: %s" % cols)
    return cols


def _margin_cols(prefix: str, m: int, df: pd.DataFrame) -> list[str]:
    cols = ["%s_%d" % (prefix, j) for j in range(1, int(m) + 1)]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError("thieu cot %s" % missing)
    return cols


def _block_reduce(sub: pd.DataFrame, col: str, variant: str, rng: np.random.Generator) -> np.ndarray:
    """Reduce a score column according to Variant A/B/C."""
    if variant == "B":
        return sub[col].to_numpy(np.float64)
    grouped = sub.groupby("block_id", sort=True)[col]
    if variant == "C":
        return grouped.max().to_numpy(np.float64)
    if variant == "A":
        return grouped.apply(lambda s: s.iloc[int(rng.integers(len(s)))]).to_numpy(np.float64)
    raise ValueError("variant phai la 'A', 'B' hoac 'C'")


def _qhat_one_group(
    calib: pd.DataFrame,
    slots: Sequence[str],
    procedure: str,
    alpha: float,
    variant: str,
    rng: np.random.Generator,
) -> tuple[list[float], Optional[float], int]:
    """Fit qhat for one Mondrian bin."""
    m = len(slots)
    n_eff = int(calib["block_id"].nunique())
    a_each = alpha_each(procedure, alpha, m)
    level = conformal_level(n_eff, a_each)
    if level is None or len(calib) == 0:
        return [float("inf")] * m, None, n_eff

    if procedure == "maxscore":
        vals = _block_reduce(calib, "s_sim", variant, rng)
        q = empirical_qhat(vals, level)
        return [float(q)] * m, level, n_eff

    qhat = [empirical_qhat(_block_reduce(calib, slot, variant, rng), level) for slot in slots]
    return [float(q) for q in qhat], level, n_eff


def _qrows(test: pd.DataFrame, qhat: Mapping[int, Sequence[float]], bin_col: str) -> np.ndarray:
    return np.vstack([np.asarray(qhat[int(g)], dtype=np.float64) for g in test[bin_col].to_numpy()])


def fit_eval_simultaneous(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    procedure: str,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    variant: str = "B",
    seed: int = SEED_PICK,
) -> Dict[str, Any]:
    """Fit per-bin qhat and evaluate simultaneous coverage on test rows."""
    if procedure not in PROCEDURES:
        raise ValueError("procedure phai thuoc %s; nhan %r" % (PROCEDURES, procedure))
    if variant not in ("A", "B", "C"):
        raise ValueError("variant phai la 'A', 'B' hoac 'C'")

    slots = _slot_cols(df)
    m = len(slots)
    if n_comparisons(m + 1) != m:
        raise AssertionError("family size khong khop")
    if "s_sim" not in df.columns:
        raise ValueError("thieu cot s_sim")

    d = df.assign(_calib=np.asarray(is_calib, dtype=bool))
    rng = np.random.default_rng(int(seed))
    qhat: Dict[int, list[float]] = {}
    cov_sim: Dict[int, float] = {}
    cov_point: Dict[int, list[float]] = {}
    n_blocks: Dict[int, int] = {}
    n_test: Dict[int, int] = {}
    levels: Dict[int, Optional[float]] = {}

    for group, sub in d.groupby(bin_col, sort=True):
        g = int(group)
        c = sub[sub["_calib"]]
        t = sub[~sub["_calib"]]
        q, level, n_eff = _qhat_one_group(c, slots, procedure, float(alpha), variant, rng)
        qhat[g] = q
        levels[g] = level
        n_blocks[g] = int(n_eff)
        n_test[g] = int(len(t))
        if len(t):
            scores = t[slots].to_numpy(np.float64)
            q_arr = np.asarray(q, dtype=np.float64)
            ok = scores <= q_arr[None, :]
            cov_sim[g] = float(ok.all(axis=1).mean())
            cov_point[g] = [float(x) for x in ok.mean(axis=0)]
        else:
            cov_sim[g] = 1.0
            cov_point[g] = [1.0] * m

    test = d[~d["_calib"]]
    if len(test):
        scores = test[slots].to_numpy(np.float64)
        q = _qrows(test, qhat, bin_col)
        ok = scores <= q
        marginal = float(ok.all(axis=1).mean())
        pointwise = [float(x) for x in ok.mean(axis=0)]
    else:
        marginal = 1.0
        pointwise = [1.0] * m

    return {
        "procedure": procedure,
        "variant": variant,
        "alpha": float(alpha),
        "alpha_each": float(alpha_each(procedure, alpha, m)),
        "m_comparisons": int(m),
        "bin_col": bin_col,
        "slots": list(slots),
        "qhat": qhat,
        "coverage_simultaneous": cov_sim,
        "coverage_pointwise": cov_point,
        "coverage_marginal": marginal,
        "coverage_simultaneous_marginal": marginal,
        "coverage_pointwise_marginal": pointwise,
        "n_calib_blocks": n_blocks,
        "n_test_rows": n_test,
        "level": levels,
        "pass_G22_4": bool(procedure == "uncorrected" or marginal >= 1.0 - float(alpha) - COV_TOL),
        "metadata": {
            "scale": "cost_ms",
            "level": "margin" if procedure == "uncorrected" else "simultaneous",
            "rowset": "calib/test split supplied by is_calib",
            "negative_control": procedure == "uncorrected",
        },
    }


def reproduce_21R(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    alpha: float = ALPHA,
    bin_col: str = "z_bin",
) -> Dict[str, Any]:
    """Verify that slot 1 exactly reproduces the locked 21R margin qhat."""
    r21 = fit_eval_21r(df, is_calib, score="s_margin", bin_col=bin_col, alpha=alpha, variant="B")
    r1 = fit_eval_21r(df, is_calib, score="s_pair_1", bin_col=bin_col, alpha=alpha, variant="B")
    diffs = {int(g): float(abs(float(r21["qhat"][g]) - float(r1["qhat"][g]))) for g in r21["qhat"]}
    return {
        "qhat_21R": {int(g): float(v) for g, v in r21["qhat"].items()},
        "qhat_slot1": {int(g): float(v) for g, v in r1["qhat"].items()},
        "max_abs_diff": float(max(diffs.values())) if diffs else 0.0,
        "diff_by_bin": diffs,
        "pass_V22_6": bool(all(v == 0.0 for v in diffs.values())),
    }


def seed_validation(
    df: pd.DataFrame,
    procedure: str,
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """Validate on disjoint trajectory seeds."""
    if "seed" not in df.columns:
        raise ValueError("can cot seed de chay seed_validation")
    out = fit_eval_simultaneous(
        df,
        split_by_seed(df["seed"].to_numpy()),
        procedure,
        bin_col=bin_col,
        alpha=alpha,
        variant="B",
    )
    out["pass_seed_validation"] = bool(out["coverage_marginal"] >= 1.0 - float(alpha) - COV_TOL)
    return out


def v3_variance_control(
    df: pd.DataFrame,
    procedure: str = "maxscore",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    repeats: int = N_REPEAT_V3,
) -> Dict[str, Any]:
    """Positive control PC22-3: row splits collapse coverage variance."""
    block_ids = df["block_id"].to_numpy()
    cov_block = []
    cov_row = []
    for r in range(int(repeats)):
        rb = fit_eval_simultaneous(
            df,
            split_blocks(block_ids, seed=SEED_SPLIT + r),
            procedure,
            bin_col=bin_col,
            alpha=alpha,
            variant="B",
        )
        rr = fit_eval_simultaneous(
            df,
            split_rows_V3(len(df), seed=SEED_SPLIT + 1000 + r),
            procedure,
            bin_col=bin_col,
            alpha=alpha,
            variant="B",
        )
        cov_block.append([rb["coverage_simultaneous"][g] for g in sorted(rb["coverage_simultaneous"])])
        cov_row.append([rr["coverage_simultaneous"][g] for g in sorted(rr["coverage_simultaneous"])])

    cb = np.asarray(cov_block, dtype=np.float64)
    cr = np.asarray(cov_row, dtype=np.float64)
    sd_b = cb.std(axis=0, ddof=0)
    sd_r = cr.std(axis=0, ddof=0)
    ratio = float(sd_r.mean() / sd_b.mean()) if sd_b.mean() > 0.0 else float("nan")
    mean_diff = np.abs(cb.mean(axis=0) - cr.mean(axis=0))
    return {
        "procedure": procedure,
        "repeats": int(repeats),
        "coverage_mean_block": [float(x) for x in cb.mean(axis=0)],
        "coverage_mean_row": [float(x) for x in cr.mean(axis=0)],
        "coverage_sd_block": [float(x) for x in sd_b],
        "coverage_sd_row": [float(x) for x in sd_r],
        "coverage_mean_diff_max": float(mean_diff.max()) if mean_diff.size else 0.0,
        "sd_ratio_row_over_block": ratio,
        "pass_PC22_3": bool(ratio < V3_SD_RATIO_MAX),
    }


def bridge_to_rms(
    df: pd.DataFrame,
    result: Mapping[str, Any],
    score: str = "s_sim",
    bin_col: str = "z_bin",
) -> Dict[str, Any]:
    """Compare maxscore qhat to the score-dependent half-normal proxy."""
    rows = []
    qhat = result["qhat"]
    for group, sub in df.groupby(bin_col, sort=True):
        g = int(group)
        q_values = np.asarray(qhat[g], dtype=np.float64)
        q = float(q_values.max())
        rms = float(np.sqrt(np.mean(sub[score].to_numpy(np.float64) ** 2)))
        pred = Z_1MA * rms
        rows.append(
            {
                bin_col: g,
                "score": score,
                "qhat": q,
                "rms": rms,
                "pred_1p645_rms": pred,
                "ratio": float(q / pred) if pred > 0.0 else float("nan"),
            }
        )
    ratios = [r["ratio"] for r in rows if np.isfinite(r["ratio"])]
    return {
        "per_bin": rows,
        "ratio_min": float(min(ratios)) if ratios else float("nan"),
        "ratio_max": float(max(ratios)) if ratios else float("nan"),
        "pass_P3c_ratio_stable": bool(ratios and max(ratios) - min(ratios) < 0.01),
        "note": "P3c: 1.645*rms is score-dependent; for s_sim use ratio diagnostics, not absolute qhat.",
    }


def rms_scores(df: pd.DataFrame) -> Dict[str, float]:
    cols = _slot_cols(df) + ["s_sim"]
    return {c: float(np.sqrt(np.mean(df[c].to_numpy(np.float64) ** 2))) for c in cols}


def _reduce_block_arrays(
    arrays: Sequence[np.ndarray],
    picks: np.ndarray,
    variant: str,
    rng: np.random.Generator,
) -> np.ndarray:
    if variant == "B":
        return np.concatenate([arrays[int(i)] for i in picks])
    if variant == "C":
        return np.asarray([float(np.max(arrays[int(i)])) for i in picks], dtype=np.float64)
    if variant == "A":
        return np.asarray(
            [float(arrays[int(i)][int(rng.integers(len(arrays[int(i)])))]) for i in picks],
            dtype=np.float64,
        )
    raise ValueError("variant phai la 'A', 'B' hoac 'C'")


def _bootstrap_qvec_from_blocks(
    slot_blocks: Sequence[Sequence[np.ndarray]],
    sim_blocks: Sequence[np.ndarray],
    picks: np.ndarray,
    procedure: str,
    alpha: float,
    variant: str,
    rng: np.random.Generator,
) -> np.ndarray:
    m = len(slot_blocks)
    level = conformal_level(len(picks), alpha_each(procedure, alpha, m))
    if level is None:
        return np.full(m, float("inf"), dtype=np.float64)
    if procedure == "maxscore":
        vals = _reduce_block_arrays(sim_blocks, picks, variant, rng)
        q = empirical_qhat(vals, level)
        return np.full(m, float(q), dtype=np.float64)
    out = []
    for blocks in slot_blocks:
        vals = _reduce_block_arrays(blocks, picks, variant, rng)
        out.append(empirical_qhat(vals, level))
    return np.asarray(out, dtype=np.float64)


def _blocks_by_bin(calib: pd.DataFrame, slots: Sequence[str], bin_col: str) -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    for group, sub in calib.groupby(bin_col, sort=True):
        block_groups = list(sub.groupby("block_id", sort=True))
        out[int(group)] = {
            "slot_blocks": [
                [bg[slot].to_numpy(np.float64) for _bid, bg in block_groups]
                for slot in slots
            ],
            "sim_blocks": [bg["s_sim"].to_numpy(np.float64) for _bid, bg in block_groups],
            "n_blocks": len(block_groups),
        }
    return out


def bootstrap_qhat(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    procedure: str = "maxscore",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    variant: str = "B",
    n_boot: int = N_BOOT,
    seed: int = 7203,
) -> Dict[str, Any]:
    """Block bootstrap CIs for qhat by bin and slot."""
    slots = _slot_cols(df)
    calib = df[np.asarray(is_calib, dtype=bool)]
    by_bin = _blocks_by_bin(calib, slots, bin_col)
    rng = np.random.default_rng(int(seed))
    out: Dict[int, Any] = {}
    for g, payload in by_bin.items():
        n = int(payload["n_blocks"])
        draws = []
        for _ in range(int(n_boot)):
            picks = rng.integers(0, n, size=n)
            draws.append(
                _bootstrap_qvec_from_blocks(
                    payload["slot_blocks"],
                    payload["sim_blocks"],
                    picks,
                    procedure,
                    alpha,
                    variant,
                    rng,
                )
            )
        arr = np.asarray(draws, dtype=np.float64)
        out[g] = {
            "qhat_mean": [float(x) for x in arr.mean(axis=0)],
            "ci95_low": [float(x) for x in np.quantile(arr, 0.025, axis=0)],
            "ci95_high": [float(x) for x in np.quantile(arr, 0.975, axis=0)],
        }
    return {
        "procedure": procedure,
        "variant": variant,
        "n_boot": int(n_boot),
        "seed": int(seed),
        "by_bin": out,
    }


def paired_bootstrap_deltas(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    procedures: Sequence[str] = ("bonferroni", "sidak"),
    baseline: str = "maxscore",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    variant: str = "B",
    n_boot: int = N_BOOT,
    seed: int = 7204,
) -> Dict[str, Any]:
    """Paired block bootstrap of qhat deltas against a baseline procedure."""
    slots = _slot_cols(df)
    calib = df[np.asarray(is_calib, dtype=bool)]
    by_bin = _blocks_by_bin(calib, slots, bin_col)
    rng = np.random.default_rng(int(seed))
    out: Dict[str, Any] = {}
    for g, payload in by_bin.items():
        n = int(payload["n_blocks"])
        draws = {p: [] for p in procedures}
        for _ in range(int(n_boot)):
            picks = rng.integers(0, n, size=n)
            base = _bootstrap_qvec_from_blocks(
                payload["slot_blocks"], payload["sim_blocks"], picks, baseline, alpha, variant, rng
            )
            for p in procedures:
                q = _bootstrap_qvec_from_blocks(
                    payload["slot_blocks"], payload["sim_blocks"], picks, p, alpha, variant, rng
                )
                draws[p].append(q - base)
        out[int(g)] = {}
        for p, values in draws.items():
            arr = np.asarray(values, dtype=np.float64)
            out[int(g)][p] = {
                "delta_mean": [float(x) for x in arr.mean(axis=0)],
                "ci95_low": [float(x) for x in np.quantile(arr, 0.025, axis=0)],
                "ci95_high": [float(x) for x in np.quantile(arr, 0.975, axis=0)],
            }
    return {
        "baseline": baseline,
        "procedures": list(procedures),
        "variant": variant,
        "n_boot": int(n_boot),
        "seed": int(seed),
        "by_bin": out,
    }


def acceptance_diagnostics(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    result: Mapping[str, Any],
    bin_col: str = "z_bin",
    kappa: float = 1.0,
) -> Dict[str, Any]:
    """Operational acceptance and conditional wrong-decision rates."""
    slots = _slot_cols(df)
    m = len(slots)
    mh_cols = _margin_cols("m_hat", m, df)
    mt_cols = _margin_cols("m_true", m, df)
    test = df[~np.asarray(is_calib, dtype=bool)]
    if len(test) == 0:
        return {"kappa": float(kappa), "n_test": 0}
    q = _qrows(test, result["qhat"], bin_col)
    mh = test[mh_cols].to_numpy(np.float64)
    mt = test[mt_cols].to_numpy(np.float64)
    accept = (mh >= float(kappa) * q).all(axis=1)
    reject = mh < float(kappa) * q
    n_accept = int(accept.sum())
    wrong = test["wrong"].to_numpy(bool) if "wrong" in test.columns else np.zeros(len(test), dtype=bool)
    lose_rank2 = mt[:, 0] < 0.0
    return {
        "kappa": float(kappa),
        "n_test": int(len(test)),
        "n_accept": n_accept,
        "acceptance_rate": float(accept.mean()),
        "p_wrong_given_accept": float(wrong[accept].mean()) if n_accept else 0.0,
        "p_lose_rank2_given_accept": float(lose_rank2[accept].mean()) if n_accept else 0.0,
        "slot_reject_rates": [float(x) for x in reject.mean(axis=0)],
        "slot1_decides_share": float((reject[:, 0] == reject.any(axis=1)).mean()),
    }


def fit_report(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    alpha: float = ALPHA,
    bin_col: str = "z_bin",
    variance_repeats: int = N_REPEAT_V3,
    bootstrap: bool = False,
    bootstrap_n: int = N_BOOT,
) -> Dict[str, Any]:
    main = {
        p: fit_eval_simultaneous(df, is_calib, p, bin_col=bin_col, alpha=alpha, variant="B")
        for p in PROCEDURES
    }
    bridge = bridge_to_rms(df, main["maxscore"], bin_col=bin_col)
    variants = {
        "%s|%s" % (p, v): fit_eval_simultaneous(df, is_calib, p, bin_col=bin_col, alpha=alpha, variant=v)
        for p in ("bonferroni", "maxscore")
        for v in ("A", "C")
    }
    out: Dict[str, Any] = {
        "procedures": main,
        "variant_controls": variants,
        "reproduce_21R": reproduce_21R(df, is_calib, alpha=alpha, bin_col=bin_col),
        "bridge_to_rms": bridge,
        "rms_scores": rms_scores(df),
        "acceptance_kappa_1": {
            p: acceptance_diagnostics(df, is_calib, r, bin_col=bin_col, kappa=1.0)
            for p, r in main.items()
        },
        "gates": {
            "G22_4_corrected_coverage_ge_0p88": bool(
                all(main[p]["coverage_marginal"] >= 1.0 - float(alpha) - COV_TOL for p in PROCEDURES if p != "uncorrected")
            ),
            "G22_5_negative_control_collapses": bool(
                main["uncorrected"]["coverage_marginal"] < 1.0 - float(alpha)
                and main["bonferroni"]["coverage_marginal"] - main["uncorrected"]["coverage_marginal"] > 0.10
            ),
            "V22_6_bridge_to_21R_exact": False,
        },
    }
    out["gates"]["V22_6_bridge_to_21R_exact"] = bool(out["reproduce_21R"]["pass_V22_6"])

    if "seed" in df.columns:
        out["seed_validation"] = {
            p: seed_validation(df, p, bin_col=bin_col, alpha=alpha) for p in ("bonferroni", "maxscore")
        }
    if int(variance_repeats) > 0:
        out["PC22_3_variance_control"] = v3_variance_control(
            df, "maxscore", bin_col=bin_col, alpha=alpha, repeats=int(variance_repeats)
        )
    if bootstrap:
        out["bootstrap_qhat_maxscore"] = bootstrap_qhat(
            df,
            is_calib,
            "maxscore",
            bin_col=bin_col,
            alpha=alpha,
            n_boot=int(bootstrap_n),
        )
        out["paired_bootstrap_delta_qhat"] = paired_bootstrap_deltas(
            df,
            is_calib,
            ("bonferroni", "sidak"),
            "maxscore",
            bin_col=bin_col,
            alpha=alpha,
            n_boot=int(bootstrap_n),
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--bin-col", default="z_bin")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--bootstrap-n", type=int, default=N_BOOT)
    parser.add_argument("--variance-repeats", type=int, default=N_REPEAT_V3)
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    is_calib = (
        df["is_calib"].to_numpy(bool)
        if "is_calib" in df.columns
        else split_blocks(df["block_id"].to_numpy(), seed=SEED_SPLIT)
    )
    report = fit_report(
        df,
        is_calib,
        alpha=float(args.alpha),
        bin_col=str(args.bin_col),
        variance_repeats=int(args.variance_repeats),
        bootstrap=bool(args.bootstrap),
        bootstrap_n=int(args.bootstrap_n),
    )
    out = {
        "cell": _infer_cell(args.calib),
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "n_calib_blocks": int(df.loc[is_calib, "block_id"].nunique()),
        "n_test_blocks": int(df.loc[~is_calib, "block_id"].nunique()),
        "bin_col": str(args.bin_col),
        "alpha": float(args.alpha),
        **report,
        "provenance": {
            "script": "cert/conformal_simultaneous.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "seed_split": int(SEED_SPLIT),
            "seed_pick": int(SEED_PICK),
            "variance_repeats": int(args.variance_repeats),
            "bootstrap": bool(args.bootstrap),
            "bootstrap_n": int(args.bootstrap_n) if args.bootstrap else 0,
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean(out), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 23 / Lesson 23.3 -- baselines as rankings.

Every baseline is a score.  Sweeping a score by coverage gives a risk-coverage
curve under the same fallback semantics used in Lessons 23.1 and 23.2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from cert import fallback as FB
from cert import threshold_families as TF


BASELINE_COVERAGES = tuple(np.linspace(0.0, 1.0, 101))
DEFAULT_ARTIFACT = "results/phase-22/calib_set_v3.parquet"
DEFAULT_OUT_JSON = "results/phase-23/baseline_rankings_poisson_0.925_C3_static.json"
DEFAULT_OUT_CSV = "results/phase-23/baseline_rankings_poisson_0.925_C3_static.csv"
DEFAULT_AUDIT_JSON = "results/phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json"


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(x) for x in value]
    if isinstance(value, tuple):
        return [_json_clean(x) for x in value]
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


def _accept_at_coverage(score: np.ndarray, coverage: float) -> np.ndarray:
    s = np.asarray(score, dtype=np.float64)
    c = float(np.clip(coverage, 0.0, 1.0))
    n = len(s)
    if c <= 0.0:
        return np.zeros(n, dtype=bool)
    if c >= 1.0:
        return np.ones(n, dtype=bool)
    k = int(np.floor(c * n + 0.5))
    k = max(0, min(n, k))
    order = np.argsort(-s, kind="mergesort")
    accept = np.zeros(n, dtype=bool)
    accept[order[:k]] = True
    return accept


def score_B1_random(df: pd.DataFrame, seed: int = 23301) -> np.ndarray:
    """Negative control: a score with no information."""
    return np.random.default_rng(int(seed)).random(len(df))


def score_B2_constant_gap(df: pd.DataFrame) -> np.ndarray:
    """Raw top-2 margin, without uncertainty normalization."""
    return df["m_hat_1"].to_numpy(np.float64)


def score_B3_aoi(df: pd.DataFrame) -> np.ndarray:
    """AoI threshold: accept young rows first."""
    return -df["z_s"].to_numpy(np.float64)


def score_B4_variance_proxy(
    df: pd.DataFrame,
    tau: float = 1.0,
    rms_em: float = 1.0,
    cA2: float = 1.0,
) -> np.ndarray:
    """Degenerate with B3 when sigma_hat is a monotone function of z."""
    z = df["z_s"].to_numpy(np.float64)
    return -np.sqrt(float(rms_em) ** 2 + float(cA2) * (1.0 - np.exp(-z / float(tau))))


def score_B5_relative_margin(df: pd.DataFrame) -> np.ndarray:
    """Top-2 margin normalized by the twin cost scale of the selected path."""
    if "y_hat_a1" not in df.columns:
        raise KeyError("B5 requires y_hat_a1 in calib_set_v3; do not use a proxy")
    m = df["m_hat_1"].to_numpy(np.float64)
    base = df["y_hat_a1"].to_numpy(np.float64)
    return m / np.maximum(base, 1e-12)


def score_B6_prediction_oracle(df: pd.DataFrame) -> np.ndarray:
    """Oracle for the prediction task, not the system task."""
    return df["m_true_1"].to_numpy(np.float64)


def score_C3(df: pd.DataFrame, qhat_rows: np.ndarray) -> np.ndarray:
    """C3 multiplicative family as a ranking score."""
    return TF.score_multiplicative(
        df[list(TF.MHAT_COLS)].to_numpy(np.float64),
        np.asarray(qhat_rows, dtype=np.float64),
    )


def score_B6sys_system_oracle(
    df: pd.DataFrame,
    policy: str = "static",
    scale: str = "err",
) -> np.ndarray:
    """System oracle score: loss(fallback) - loss(twin)."""
    if policy != "static":
        raise ValueError("B6-sys ranking is implemented only for stateless static fallback")
    n = len(df)
    a_twin = df["a_twin"].to_numpy(np.int64)
    a_fb = np.full(n, FB.path_static_shortest(), dtype=np.int64)
    return FB.loss_of(df, a_fb, scale) - FB.loss_of(df, a_twin, scale)


def b6sys_closed_form(anchor: float, p1_wrong: float, both_wrong: float) -> Dict[str, Any]:
    """Closed form of B6-sys on err with static fallback."""
    m_pos = float(p1_wrong - both_wrong)
    m_neg = float(anchor - both_wrong)
    m_zero = 1.0 - m_pos - m_neg
    knees = [
        (0.0, float(p1_wrong)),
        (m_pos, float(both_wrong)),
        (m_pos + m_zero, float(both_wrong)),
        (1.0, float(anchor)),
    ]
    aurc = (
        m_pos * (float(p1_wrong) + float(both_wrong)) / 2.0
        + m_zero * float(both_wrong)
        + m_neg * (float(both_wrong) + float(anchor)) / 2.0
    )
    return {
        "mass_pos": m_pos,
        "mass_zero": m_zero,
        "mass_neg": m_neg,
        "knees": knees,
        "aurc": float(aurc),
    }


def sweep_ranking(
    df: pd.DataFrame,
    score: np.ndarray,
    coverages: Sequence[float],
    policy: str = "static",
    scales: Sequence[str] = FB.SCALES,
    label: str = "",
) -> pd.DataFrame:
    """Sweep one score on a shared coverage axis."""
    anchor = {
        scale: float(FB.loss_of(df, df["a_twin"].to_numpy(np.int64), scale).mean())
        for scale in scales
    }
    rows = []
    for coverage in coverages:
        acc = _accept_at_coverage(np.asarray(score, dtype=np.float64), float(coverage))
        result = FB.apply_fallback(df, acc, policy)
        chosen = result["a_chosen"]
        rec: Dict[str, Any] = {
            "label": str(label),
            "coverage_target": float(coverage),
            "coverage": float(acc.mean()),
            "policy": policy,
            "n_accept": int(acc.sum()),
            "n_reject": int((~acc).sum()),
        }
        for scale in scales:
            per_row = FB.loss_of(df, chosen, scale)
            rec["%s_system" % scale] = float(per_row.mean())
            rec["%s_accept" % scale] = float(per_row[acc].mean()) if acc.any() else float("nan")
            rec["%s_reject" % scale] = float(per_row[~acc].mean()) if (~acc).any() else float("nan")
            rec["%s_delta_vs_anchor" % scale] = float(per_row.mean() - anchor[scale])
        rows.append(rec)
    return pd.DataFrame(rows)


def accept_overlap(score_a: np.ndarray, score_b: np.ndarray, coverage: float) -> Dict[str, float]:
    """Overlap between two accept sets at matched coverage."""
    a = _accept_at_coverage(np.asarray(score_a, dtype=np.float64), float(coverage))
    b = _accept_at_coverage(np.asarray(score_b, dtype=np.float64), float(coverage))
    inter = float((a & b).mean())
    union = float((a | b).mean())
    coverage_a = float(a.mean())
    coverage_b = float(b.mean())
    return {
        "coverage_target": float(coverage),
        "coverage_a": coverage_a,
        "coverage_b": coverage_b,
        "intersection": inter,
        "jaccard": inter / max(union, 1e-12),
        "share_of_a": inter / max(coverage_a, 1e-12),
        "independence_reference": coverage_b,
    }


def beneficial_band(sweep: pd.DataFrame, anchor: float, scale: str = "err") -> Dict[str, float | bool]:
    """Coverage band where a system-risk curve beats the twin anchor."""
    s = sweep.sort_values("coverage")
    x = s["coverage"].to_numpy(np.float64)
    y = s["%s_system" % scale].to_numpy(np.float64)
    grid = np.linspace(0.0, 1.0, 20001)
    yy = np.interp(grid, x, y)
    gain = float(anchor) - yy
    beneficial = gain > 0.0
    if not beneficial.any():
        return {"beneficial": False, "improvement_area": 0.0}
    op = (grid >= 0.60) & (grid <= 1.0)
    partial = float(np.trapezoid(yy[op], grid[op]) / (grid[op].max() - grid[op].min()))
    return {
        "beneficial": True,
        "band_low": float(grid[beneficial].min()),
        "band_high": float(grid[beneficial].max()),
        "max_reject_share": float(1.0 - grid[beneficial].min()),
        "improvement_area": float(np.trapezoid(np.clip(gain, 0.0, None), grid)),
        "best_improvement": float(gain.max()),
        "best_coverage": float(grid[gain.argmax()]),
        "partial_aurc_060_100": partial,
        "partial_aurc_060_100_ratio_vs_anchor": float(partial / float(anchor)),
    }


def paired_ranking_delta_at_coverage(
    df: pd.DataFrame,
    score_a: np.ndarray,
    score_b: np.ndarray,
    coverage: float,
    label_a: str,
    label_b: str,
    policy: str = "static",
    scale: str = "err",
    n_boot: int = 2000,
    seed: int = 23330,
) -> Dict[str, Any]:
    """Paired block-bootstrap CI for ranking A minus ranking B at one coverage."""
    acc_a = _accept_at_coverage(np.asarray(score_a, dtype=np.float64), float(coverage))
    acc_b = _accept_at_coverage(np.asarray(score_b, dtype=np.float64), float(coverage))
    chosen_a = FB.apply_fallback(df, acc_a, policy)["a_chosen"]
    chosen_b = FB.apply_fallback(df, acc_b, policy)["a_chosen"]
    loss_a = FB.loss_of(df, chosen_a, scale)
    loss_b = FB.loss_of(df, chosen_b, scale)
    diff = loss_a - loss_b

    blocks = df["block_id"].to_numpy()
    _uniq, inv = np.unique(blocks, return_inverse=True)
    n_blk = int(inv.max() + 1)
    sum_d = np.bincount(inv, weights=diff, minlength=n_blk)
    cnt = np.bincount(inv, minlength=n_blk).astype(np.float64)
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=np.float64)
    for i in range(int(n_boot)):
        pick = rng.integers(0, n_blk, size=n_blk)
        draws[i] = sum_d[pick].sum() / cnt[pick].sum()
    ci = np.quantile(draws, [0.025, 0.975])

    cov_a = float(acc_a.mean())
    cov_b = float(acc_b.mean())
    risk_a = float(loss_a.mean())
    risk_b = float(loss_b.mean())
    accept_a = float(loss_a[acc_a].mean()) if acc_a.any() else float("nan")
    accept_b = float(loss_b[acc_b].mean()) if acc_b.any() else float("nan")
    reject_a = float(loss_a[~acc_a].mean()) if (~acc_a).any() else float("nan")
    reject_b = float(loss_b[~acc_b].mean()) if (~acc_b).any() else float("nan")
    cov_mean = 0.5 * (cov_a + cov_b)
    accept_delta = float(accept_a - accept_b)
    reject_delta = float(reject_a - reject_b)
    return {
        "coverage_target": float(coverage),
        "coverage_a": cov_a,
        "coverage_b": cov_b,
        "label_a": str(label_a),
        "label_b": str(label_b),
        "scale": str(scale),
        "policy": str(policy),
        "risk_a": risk_a,
        "risk_b": risk_b,
        "delta_a_minus_b": float(diff.mean()),
        "delta_ci95": [float(ci[0]), float(ci[1])],
        "delta_half_width_ci95": float((ci[1] - ci[0]) / 2.0),
        "ci_excludes_zero": bool(float(ci[1]) < 0.0 or float(ci[0]) > 0.0),
        "accept_risk_a": accept_a,
        "accept_risk_b": accept_b,
        "accept_delta_a_minus_b": accept_delta,
        "reject_risk_a": reject_a,
        "reject_risk_b": reject_b,
        "reject_delta_a_minus_b": reject_delta,
        "accept_contribution": float(cov_mean * accept_delta),
        "reject_contribution": float((1.0 - cov_mean) * reject_delta),
        "n_boot": int(n_boot),
        "seed": int(seed),
        "n_blocks": int(n_blk),
    }


def wasted_abstention_report(
    df: pd.DataFrame,
    accept: np.ndarray,
) -> Dict[str, Any]:
    """Rows with a_twin == static P1 cannot change action under F2 rejection."""
    p1 = FB.path_static_shortest()
    free = df["a_twin"].to_numpy(np.int64) == int(p1)
    reject = ~np.asarray(accept, dtype=bool)
    wasted = reject & free
    actionable_reject = reject & (~free)
    return {
        "static_path": int(p1),
        "p_a_twin_eq_p1": float(free.mean()),
        "coverage": float((~reject).mean()),
        "reject_share": float(reject.mean()),
        "wasted_reject_share_total_rows": float(wasted.mean()),
        "wasted_reject_given_reject": float(wasted.mean() / max(float(reject.mean()), 1e-12)),
        "actionable_reject_share_total_rows": float(actionable_reject.mean()),
        "actionable_reject_given_reject": float(actionable_reject.mean() / max(float(reject.mean()), 1e-12)),
    }


def _intervention_rate_check(
    df: pd.DataFrame,
    accept_a: np.ndarray,
    accept_b: np.ndarray,
    tol: float = 0.01,
) -> Dict[str, Any]:
    """L20: matched coverage is comparable only when actual intervention matches."""
    a = wasted_abstention_report(df, accept_a)
    b = wasted_abstention_report(df, accept_b)
    ir_a = float(a["actionable_reject_share_total_rows"])
    ir_b = float(b["actionable_reject_share_total_rows"])
    gap = float(ir_a - ir_b)
    return {
        "intervention_rate_a": ir_a,
        "intervention_rate_b": ir_b,
        "gap_a_minus_b": gap,
        "abs_gap": abs(gap),
        "tolerance": float(tol),
        "comparable_at_matched_coverage": bool(abs(gap) <= float(tol)),
        "note": (
            "PASS -> comparison at matched coverage is valid. "
            "FAIL -> compare at matched intervention rate instead of matched coverage."
        ),
    }


def _row_at_target(sweep: pd.DataFrame, target: float) -> Dict[str, Any]:
    delta = (sweep["coverage_target"].astype(float) - float(target)).abs()
    row = sweep.loc[delta.idxmin()].to_dict()
    return {str(k): _json_clean(v) for k, v in row.items()}


def _gate_report(df: pd.DataFrame) -> Dict[str, Any]:
    anchor = float(FB.loss_of(df, df["a_twin"].to_numpy(np.int64), "err").mean())
    random_sweep = sweep_ranking(df, score_B1_random(df), [0.30, 0.50, 0.78], label="B1_random")
    pc23_1 = {
        "pass": bool((random_sweep["err_accept"] - anchor).abs().max() < 0.01),
        "anchor_err": anchor,
        "max_abs_err_accept_minus_anchor": float((random_sweep["err_accept"] - anchor).abs().max()),
        "rows": random_sweep.to_dict(orient="records"),
    }

    s3 = score_B3_aoi(df)
    s4 = score_B4_variance_proxy(df)
    b4_rows = []
    for coverage in (0.20, 0.50, 0.78, 0.95):
        a3 = _accept_at_coverage(s3, coverage)
        a4 = _accept_at_coverage(s4, coverage)
        b4_rows.append(
            {
                "coverage": float(coverage),
                "bitwise_identical": bool(np.array_equal(a3, a4)),
                "n_disagree": int((a3 != a4).sum()),
            }
        )
    g23_10b = {
        "pass": bool(all(row["bitwise_identical"] for row in b4_rows)),
        "rows": b4_rows,
    }

    n = len(df)
    a_twin = df["a_twin"].to_numpy(np.int64)
    a_p1 = np.full(n, FB.path_static_shortest(), dtype=np.int64)
    loss_twin = FB.loss_of(df, a_twin, "err")
    loss_p1 = FB.loss_of(df, a_p1, "err")
    p1_wrong = float(loss_p1.mean())
    both_wrong = float(np.minimum(loss_twin, loss_p1).mean())
    closed = b6sys_closed_form(anchor, p1_wrong, both_wrong)
    score = score_B6sys_system_oracle(df, "static", "err")
    sweep = sweep_ranking(df, score, [c for c, _err in closed["knees"]], label="B6-sys")
    knee_rows = []
    max_abs_err = 0.0
    max_abs_coverage = 0.0
    for (coverage_expected, err_expected), (_, row) in zip(closed["knees"], sweep.iterrows()):
        cov_diff = abs(float(row["coverage"]) - float(coverage_expected))
        err_diff = abs(float(row["err_system"]) - float(err_expected))
        max_abs_coverage = max(max_abs_coverage, cov_diff)
        max_abs_err = max(max_abs_err, err_diff)
        knee_rows.append(
            {
                "coverage_expected": float(coverage_expected),
                "coverage_measured": float(row["coverage"]),
                "err_expected": float(err_expected),
                "err_measured": float(row["err_system"]),
                "abs_coverage_diff": float(cov_diff),
                "abs_err_diff": float(err_diff),
            }
        )
    g23_12c = {
        "pass": bool(max_abs_err < 1e-9 and max_abs_coverage < 1e-6),
        "anchor_always_trust": anchor,
        "static_fallback_err": p1_wrong,
        "both_wrong": both_wrong,
        "closed_form": closed,
        "max_abs_err_diff": float(max_abs_err),
        "max_abs_coverage_diff": float(max_abs_coverage),
        "knees": knee_rows,
    }
    return {"PC23_1": pc23_1, "G23_10b": g23_10b, "G23_12c": g23_12c}


def run_report(
    df: pd.DataFrame,
    config: str = "C3",
    policy: str = "static",
    coverages: Sequence[float] = BASELINE_COVERAGES,
    target_coverage: float = 0.78,
) -> Dict[str, Any]:
    """Run the Lesson 23.3 baseline sweep after the three prerequisite gates."""
    _calib, test, qhat_rows, fit, q_by_age, qbar = TF.fit_c3_inputs(df, config=config)
    anchor = {
        scale: float(FB.loss_of(test, test["a_twin"].to_numpy(np.int64), scale).mean())
        for scale in FB.SCALES
    }
    static_action = np.full(len(test), FB.path_static_shortest(), dtype=np.int64)
    static = {scale: float(FB.loss_of(test, static_action, scale).mean()) for scale in FB.SCALES}

    scores = {
        "B1_random": score_B1_random(test),
        "B2_constant_gap": score_B2_constant_gap(test),
        "B3_aoi": score_B3_aoi(test),
        "B4_variance_proxy": score_B4_variance_proxy(test),
        "B5_relative_margin": score_B5_relative_margin(test),
        "B6_prediction_oracle": score_B6_prediction_oracle(test),
        "C3_conformal": score_C3(test, qhat_rows),
        "B6_sys_oracle": score_B6sys_system_oracle(test, policy=policy, scale="err"),
    }
    sweeps = {
        label: sweep_ranking(test, score, coverages, policy=policy, label=label)
        for label, score in scores.items()
    }
    combined = pd.concat(sweeps.values(), ignore_index=True, sort=False)
    at_target = {label: _row_at_target(sweep, target_coverage) for label, sweep in sweeps.items()}
    beneficial = {
        label: beneficial_band(sweep, anchor["err"], "err")
        for label, sweep in sweeps.items()
    }
    overlap_c3_b3 = accept_overlap(scores["C3_conformal"], scores["B3_aoi"], target_coverage)

    return {
        "cell": "poisson@0.925",
        "config": config,
        "policy": policy,
        "coverage_grid": [float(x) for x in coverages],
        "target_coverage": float(target_coverage),
        "n_test": int(len(test)),
        "anchor_always_trust": anchor,
        "static_fallback": static,
        "qbar_slot1_age_bins": float(qbar),
        "qhat_slot1_by_age_bin": q_by_age,
        "fit_keys": list(fit["keys"]),
        "fit_score_cols": list(fit["score_cols"]),
        "baseline_status": {
            "B0_always_trust": "anchor, not swept as a ranking",
            "B4_variance_proxy": "degenerate with B3_aoi by monotone ranking invariance",
            "B6_prediction_oracle": "prediction oracle; not the system oracle",
            "B6_sys_oracle": "system oracle for static fallback and err scale",
        },
        "gates": _gate_report(test),
        "at_target_coverage": at_target,
        "accept_overlap_C3_B3": overlap_c3_b3,
        "beneficial_band_err": beneficial,
        "sweeps": {
            label: sweep.to_dict(orient="records")
            for label, sweep in sweeps.items()
        },
        "sweep_rows": int(len(combined)),
        "_combined_sweep_frame": combined,
    }


def run_c3_b2_audit(
    df: pd.DataFrame,
    config: str = "C3",
    policy: str = "static",
    coverages: Sequence[float] = (0.70, 0.78, 0.85),
    scales: Sequence[str] = FB.SCALES,
    n_boot: int = 2000,
    seed: int = 23330,
) -> Dict[str, Any]:
    """Audit the missing C3-vs-B2 comparison and wasted abstention."""
    _calib, test, qhat_rows, _fit, _q_by_age, _qbar = TF.fit_c3_inputs(df, config=config)
    score_c3 = score_C3(test, qhat_rows)
    score_b2 = score_B2_constant_gap(test)
    rows = []
    for coverage in coverages:
        for scale_idx, scale in enumerate(scales):
            rows.append(
                paired_ranking_delta_at_coverage(
                    test,
                    score_c3,
                    score_b2,
                    float(coverage),
                    label_a="C3_conformal",
                    label_b="B2_constant_gap",
                    policy=policy,
                    scale=scale,
                    n_boot=int(n_boot),
                    seed=int(seed) + int(1000 * float(coverage)) + scale_idx,
                )
            )
    accept_c3_078 = _accept_at_coverage(score_c3, 0.78)
    accept_b2_078 = _accept_at_coverage(score_b2, 0.78)
    anchor_err = float(FB.loss_of(test, test["a_twin"].to_numpy(np.int64), "err").mean())
    b6sys_078 = paired_ranking_delta_at_coverage(
        test,
        score_c3,
        score_B6sys_system_oracle(test, policy=policy, scale="err"),
        0.78,
        label_a="C3_conformal",
        label_b="B6_sys_oracle",
        policy=policy,
        scale="err",
        n_boot=1,
        seed=int(seed),
    )
    row_078_err = next(
        r for r in rows if abs(float(r["coverage_target"]) - 0.78) < 1e-12 and r["scale"] == "err"
    )
    gap_closed_by_c3 = (anchor_err - float(row_078_err["risk_a"])) / max(
        anchor_err - b6sys_078["risk_b"], 1e-12
    )
    return {
        "cell": "poisson@0.925",
        "config": config,
        "policy": policy,
        "n_test": int(len(test)),
        "coverages": [float(x) for x in coverages],
        "scales": [str(x) for x in scales],
        "c3_minus_b2_paired_block_bootstrap": rows,
        "wasted_abstention_C3_at_078": wasted_abstention_report(test, accept_c3_078),
        "wasted_abstention_B2_at_078": wasted_abstention_report(test, accept_b2_078),
        "L20_intervention_rate_check": _intervention_rate_check(test, accept_c3_078, accept_b2_078),
        "gap_closed_by_C3_vs_B6sys_at_078": float(gap_closed_by_c3),
        "n_boot": int(n_boot),
        "seed": int(seed),
    }


def write_json_report(report: Dict[str, Any], out_json: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    payload = dict(report)
    payload["provenance"] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty_before_write": bool(_git("git", "status", "--porcelain")),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(_json_clean(payload), f, indent=2, sort_keys=True)
        f.write("\n")


def write_report(report: Dict[str, Any], out_json: str, out_csv: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    combined = report["_combined_sweep_frame"]
    payload = {k: v for k, v in report.items() if k != "_combined_sweep_frame"}
    payload["provenance"] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty_before_write": bool(_git("git", "status", "--porcelain")),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(_json_clean(payload), f, indent=2, sort_keys=True)
        f.write("\n")
    combined.to_csv(out_csv, index=False)


def _print_summary(report: Dict[str, Any], out_json: str, out_csv: str) -> None:
    gates = report["gates"]
    print("=== Phase 23.3 baseline gates ===")
    print("PC23-1 random baseline:", "PASS" if gates["PC23_1"]["pass"] else "FAIL")
    print("G23-10b B4 == B3:", "PASS" if gates["G23_10b"]["pass"] else "FAIL")
    print("G23-12c B6-sys closed form:", "PASS" if gates["G23_12c"]["pass"] else "FAIL")
    g = gates["G23_12c"]
    print(
        "G23-12c masses: "
        "pos={mass_pos:.9f} zero={mass_zero:.9f} neg={mass_neg:.9f} aurc={aurc:.9f}".format(
            **g["closed_form"]
        )
    )
    for row in g["knees"]:
        print(
            "  knee target={coverage_expected:.9f} measured_cov={coverage_measured:.9f} "
            "closed_err={err_expected:.9f} measured_err={err_measured:.9f}".format(**row)
        )
    print()
    print("=== Mechanism check at coverage 0.78 ===")
    overlap = report["accept_overlap_C3_B3"]
    for key in (
        "coverage_a",
        "coverage_b",
        "intersection",
        "jaccard",
        "share_of_a",
        "independence_reference",
    ):
        print("%s=%.9f" % (key, overlap[key]))
    print()
    print("=== Beneficial band, err_system ===")
    for label in ("C3_conformal", "B3_aoi"):
        band = report["beneficial_band_err"][label]
        print(label + ":")
        for key, value in band.items():
            if isinstance(value, bool):
                print("  %s=%s" % (key, value))
            else:
                print("  %s=%.9f" % (key, value))
    print()
    print("wrote_json=%s" % out_json)
    print("wrote_csv=%s" % out_csv)


def _print_c3_b2_audit_summary(report: Dict[str, Any], out_json: str) -> None:
    print("=== Phase 23.3 C3-vs-B2 paired bootstrap audit ===")
    for row in report["c3_minus_b2_paired_block_bootstrap"]:
        if abs(float(row["coverage_target"]) - 0.78) >= 1e-12:
            continue
        print(
            "{scale}: C3-B2={delta_a_minus_b:+.9f} "
            "CI95=[{lo:+.9f}, {hi:+.9f}] excludes_zero={excludes}".format(
                scale=row["scale"],
                delta_a_minus_b=row["delta_a_minus_b"],
                lo=row["delta_ci95"][0],
                hi=row["delta_ci95"][1],
                excludes=row["ci_excludes_zero"],
            )
        )
    print()
    print("=== Wasted abstention, C3 at coverage 0.78 ===")
    for label, wasted in (
        ("C3", report["wasted_abstention_C3_at_078"]),
        ("B2", report["wasted_abstention_B2_at_078"]),
    ):
        print(label + ":")
        for key in (
            "p_a_twin_eq_p1",
            "coverage",
            "reject_share",
            "wasted_reject_share_total_rows",
            "wasted_reject_given_reject",
            "actionable_reject_share_total_rows",
            "actionable_reject_given_reject",
        ):
            print("  %s=%.9f" % (key, wasted[key]))
    print()
    print("=== L20 intervention-rate check, C3 vs B2 at coverage 0.78 ===")
    l20 = report["L20_intervention_rate_check"]
    for key in (
        "intervention_rate_a",
        "intervention_rate_b",
        "gap_a_minus_b",
        "abs_gap",
        "tolerance",
    ):
        print("%s=%.9f" % (key, l20[key]))
    print("comparable_at_matched_coverage=%s" % l20["comparable_at_matched_coverage"])
    print()
    print("gap_closed_by_C3_vs_B6sys_at_078=%.9f" % report["gap_closed_by_C3_vs_B6sys_at_078"])
    print("wrote_json=%s" % out_json)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    parser.add_argument("--config", default="C3")
    parser.add_argument("--policy", default="static")
    parser.add_argument("--target-coverage", type=float, default=0.78)
    parser.add_argument("--out-json", default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-csv", default=DEFAULT_OUT_CSV)
    parser.add_argument("--audit-c3-b2", action="store_true")
    parser.add_argument("--out-audit-json", default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=23330)
    args = parser.parse_args(argv)

    df = pd.read_parquet(args.artifact)
    if args.audit_c3_b2:
        report = run_c3_b2_audit(
            df,
            config=args.config,
            policy=args.policy,
            n_boot=int(args.n_boot),
            seed=int(args.seed),
        )
        report["input_artifact"] = {
            "path": args.artifact,
            "sha256": _sha256(args.artifact),
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "has_y_hat_a1": bool("y_hat_a1" in df.columns),
        }
        write_json_report(report, args.out_audit_json)
        _print_c3_b2_audit_summary(report, args.out_audit_json)
        return 0

    report = run_report(
        df,
        config=args.config,
        policy=args.policy,
        target_coverage=float(args.target_coverage),
    )
    report["input_artifact"] = {
        "path": args.artifact,
        "sha256": _sha256(args.artifact),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "has_y_hat_a1": bool("y_hat_a1" in df.columns),
    }
    write_report(report, args.out_json, args.out_csv)
    _print_summary(report, args.out_json, args.out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

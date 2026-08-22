#!/usr/bin/env python3
"""Phase 23 / Lesson 23.2 -- threshold families as rankings.

Each threshold family is a row score plus a moving cutoff:

    multiplicative: accept <=> min_j m_hat_j / q_hat_j >= kappa
    additive:       accept <=> min_j m_hat_j - q_hat_j >= -eps

The threshold chooses one operating point on a risk-coverage curve.  Comparing
families therefore means comparing them at matched coverage, not at matched raw
parameter values.
"""

from __future__ import annotations

import argparse
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


MHAT_COLS = ("m_hat_1", "m_hat_2", "m_hat_3")
QHAT_COLS = ("q_hat_1", "q_hat_2", "q_hat_3")
KAPPA_GRID = (
    0.0,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    2.0,
    3.0,
    4.0,
    6.0,
    8.0,
)
DELTA_GRID = (
    -4.0,
    -3.0,
    -2.0,
    -1.5,
    -1.0,
    -0.5,
    -0.25,
    0.0,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.85,
    0.90,
    1.0,
    1.25,
    1.5,
)
MATCHED_COVERAGE = (0.30, 0.50, 0.78)


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


def score_multiplicative(mhat: np.ndarray, qhat: np.ndarray) -> np.ndarray:
    """s = min_j(m_hat_j / q_hat_j); accept iff s >= kappa."""
    m = np.asarray(mhat, dtype=np.float64)
    q = np.asarray(qhat, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(q > 0.0, m / q, np.inf)
    return ratio.min(axis=1)


def score_additive(mhat: np.ndarray, qhat: np.ndarray) -> np.ndarray:
    """s = min_j(m_hat_j - q_hat_j); accept iff s >= -eps."""
    m = np.asarray(mhat, dtype=np.float64)
    q = np.asarray(qhat, dtype=np.float64)
    return (m - q).min(axis=1)


def accept_multiplicative(mhat: np.ndarray, qhat: np.ndarray, kappa: float) -> np.ndarray:
    return score_multiplicative(mhat, qhat) >= float(kappa)


def accept_additive(mhat: np.ndarray, qhat: np.ndarray, eps: float) -> np.ndarray:
    return score_additive(mhat, qhat) >= -float(eps)


def accept_regret(mhat: np.ndarray, qhat: np.ndarray, eps_regret: float) -> np.ndarray:
    """Algebraic regret family, kept only to lock G23-6b.

    max_j(q_j - m_j) <= eps  <=>  min_j(m_j - q_j) >= -eps.
    The bound is intentionally not clipped at zero, so the identity also holds
    for negative eps values in the additive sweep grid.
    """
    m = np.asarray(mhat, dtype=np.float64)
    q = np.asarray(qhat, dtype=np.float64)
    return (q - m).max(axis=1) <= float(eps_regret)


def qhat_by_age_bin(
    calib: pd.DataFrame,
    fit: Mapping[str, Any],
    slot: int = 0,
    weighted: bool = True,
) -> Dict[int, float]:
    """Aggregate C3 qhat cells into one qhat value per age bin."""
    keys = list(fit["keys"])
    if keys != ["z_bin", "m_hat_bin"]:
        raise ValueError("qhat_by_age_bin expects C3 Mondrian keys")
    q = fit["_q"]
    out: Dict[int, float] = {}
    for z in sorted(int(x) for x in calib["z_bin"].unique()):
        vals = []
        weights = []
        for key, vec in q.items():
            if int(key[0]) != z:
                continue
            vals.append(float(vec[int(slot)]))
            weights.append(int(((calib["z_bin"] == key[0]) & (calib["m_hat_bin"] == key[1])).sum()))
        if weighted:
            out[z] = float(np.average(vals, weights=weights))
        else:
            out[z] = float(np.mean(vals))
    return out


def age_conditioning_ratio(qhat_by_bin: Mapping[int, float], family: str, param: float) -> float:
    """r = threshold(oldest age bin) / threshold(youngest age bin)."""
    bins = sorted(qhat_by_bin)
    q0 = float(qhat_by_bin[bins[0]])
    q3 = float(qhat_by_bin[bins[-1]])
    if family == "multiplicative":
        return q3 / q0 if q0 > 0.0 else float("inf")
    if family == "additive":
        d0 = q0 - float(param)
        return (q3 - float(param)) / d0 if d0 > 0.0 else float("inf")
    raise ValueError("family must be 'multiplicative' or 'additive'")


def qbar_from_age_bins(qhat_by_bin: Mapping[int, float]) -> float:
    return float(np.mean([float(v) for v in qhat_by_bin.values()]))


def eps_grid_from_delta(qbar: float, deltas: Sequence[float] = DELTA_GRID) -> tuple[float, ...]:
    return tuple(float(d) * float(qbar) for d in deltas)


def sweep_family(
    df: pd.DataFrame,
    qhat_rows: np.ndarray,
    family: str,
    grid: Sequence[float],
    policy: str = "static",
    scales: Sequence[str] = FB.SCALES,
) -> pd.DataFrame:
    """Sweep one family and score whole-system risk with a fixed fallback."""
    mhat = df[list(MHAT_COLS)].to_numpy(np.float64)
    qhat = np.asarray(qhat_rows, dtype=np.float64)
    a_twin = df["a_twin"].to_numpy(np.int64)
    anchor = {s: float(FB.loss_of(df, a_twin, s).mean()) for s in scales}

    rows = []
    for p in grid:
        if family == "multiplicative":
            acc = accept_multiplicative(mhat, qhat, float(p))
            param_name = "kappa"
        elif family == "additive":
            acc = accept_additive(mhat, qhat, float(p))
            param_name = "eps"
        else:
            raise ValueError("family must be 'multiplicative' or 'additive'")

        result = FB.apply_fallback(df, acc, policy)
        a = result["a_chosen"]
        rec: Dict[str, Any] = {
            "family": family,
            "param": float(p),
            param_name: float(p),
            "policy": policy,
            "coverage": float(acc.mean()),
            "p_reject": float((~acc).mean()),
            "n_accept": int(acc.sum()),
            "n_reject": int((~acc).sum()),
        }
        for scale in scales:
            per_row = FB.loss_of(df, a, scale)
            rec["%s_system" % scale] = float(per_row.mean())
            rec["%s_accept" % scale] = float(per_row[acc].mean()) if acc.any() else float("nan")
            rec["%s_reject" % scale] = float(per_row[~acc].mean()) if (~acc).any() else float("nan")
            rec["%s_delta_vs_anchor" % scale] = float(per_row.mean() - anchor[scale])
        rows.append(rec)
    return pd.DataFrame(rows).sort_values(["coverage", "param"]).reset_index(drop=True)


def _collapse_by_coverage(sweep: pd.DataFrame, col: str) -> tuple[np.ndarray, np.ndarray]:
    s = sweep[["coverage", col]].dropna().sort_values("coverage")
    x_vals = []
    y_vals = []
    for cov, sub in s.groupby("coverage", sort=True):
        x_vals.append(float(cov))
        y_vals.append(float(sub[col].min()))
    return np.asarray(x_vals, dtype=np.float64), np.asarray(y_vals, dtype=np.float64)


def risk_at_matched_coverage(sweep: pd.DataFrame, target: float, col: str) -> float:
    """Linearly interpolate risk onto a shared coverage axis."""
    x, y = _collapse_by_coverage(sweep, col)
    if len(x) == 0 or float(target) < float(x.min()) or float(target) > float(x.max()):
        return float("nan")
    return float(np.interp(float(target), x, y))


def param_at_coverage(sweep: pd.DataFrame, target: float) -> float:
    """Interpolate the family parameter that reaches target coverage."""
    s = sweep[["coverage", "param"]].dropna().sort_values("coverage")
    x_vals = []
    p_vals = []
    for cov, sub in s.groupby("coverage", sort=True):
        x_vals.append(float(cov))
        p_vals.append(float(sub["param"].mean()))
    x = np.asarray(x_vals, dtype=np.float64)
    p = np.asarray(p_vals, dtype=np.float64)
    if len(x) == 0 or float(target) < float(x.min()) or float(target) > float(x.max()):
        return float("nan")
    return float(np.interp(float(target), x, p))


def compare_families_at_coverage(
    sweep_mul: pd.DataFrame,
    sweep_add: pd.DataFrame,
    targets: Sequence[float] = MATCHED_COVERAGE,
    scales: Sequence[str] = FB.SCALES,
) -> pd.DataFrame:
    """Compare multiplicative minus additive risk at matched coverage."""
    out = []
    for target in targets:
        rec: Dict[str, Any] = {"coverage": float(target)}
        for scale in scales:
            col = "%s_system" % scale
            mul = risk_at_matched_coverage(sweep_mul, target, col)
            add = risk_at_matched_coverage(sweep_add, target, col)
            rec["%s_mul" % scale] = mul
            rec["%s_add" % scale] = add
            rec["%s_diff_mul_minus_add" % scale] = float(mul - add)
        out.append(rec)
    return pd.DataFrame(out)


def _rank_average(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=np.float64)
    i = 0
    while i < len(x):
        j = i + 1
        while j < len(x) and x[order[j]] == x[order[i]]:
            j += 1
        ranks[order[i:j]] = 0.5 * (i + j - 1) + 1.0
        i = j
    return ranks


def _spearman_no_scipy(x: Sequence[float], y: Sequence[float]) -> float:
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < 2:
        return float("nan")
    ra = _rank_average(a[mask])
    rb = _rank_average(b[mask])
    da = ra - ra.mean()
    db = rb - rb.mean()
    denom = float(np.sqrt(np.dot(da, da) * np.dot(db, db)))
    return float(np.dot(da, db) / denom) if denom > 0.0 else float("nan")


def _spearman_pandas_check(x: Sequence[float], y: Sequence[float]) -> float:
    """Independent Spearman implementation for audit only."""
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < 2:
        return float("nan")
    ra = pd.Series(a[mask]).rank(method="average").to_numpy(np.float64)
    rb = pd.Series(b[mask]).rank(method="average").to_numpy(np.float64)
    da = ra - ra.mean()
    db = rb - rb.mean()
    denom = float(np.sqrt(np.dot(da, da) * np.dot(db, db)))
    return float(np.dot(da, db) / denom) if denom > 0.0 else float("nan")


def scale_agreement(sweep: pd.DataFrame, scales: Sequence[str] = FB.SCALES) -> Dict[str, Any]:
    """G23-9: agreement among risk scales over the whole coverage sweep."""
    out: Dict[str, Any] = {}
    vals = []
    for i, a in enumerate(scales):
        for b in scales[i + 1:]:
            rho = _spearman_no_scipy(sweep["%s_system" % a], sweep["%s_system" % b])
            out["spearman_%s_%s" % (a, b)] = rho
            vals.append(rho)
    out["min_spearman"] = float(np.nanmin(vals)) if vals else float("nan")
    return out


def scale_agreement_self_check(
    sweep: pd.DataFrame,
    scales: Sequence[str] = FB.SCALES,
    tol: float = 1e-12,
) -> Dict[str, Any]:
    """Internal consistency check for G23-9.

    Equal Spearman values are not by themselves bugs: they can arise from the
    same rank permutation.  The audit recomputes every pair through pandas ranks
    and checks the one hard implication: if rank(A) == rank(B), then Spearman
    with any third variable must also match.
    """
    pairs: Dict[str, Dict[str, Any]] = {}
    for i, a in enumerate(scales):
        for b in scales[i + 1:]:
            col_a = sweep["%s_system" % a]
            col_b = sweep["%s_system" % b]
            rho = _spearman_no_scipy(col_a, col_b)
            rho_check = _spearman_pandas_check(col_a, col_b)
            ranks_a = _rank_average(np.asarray(col_a, dtype=np.float64))
            ranks_b = _rank_average(np.asarray(col_b, dtype=np.float64))
            key = "%s_%s" % (a, b)
            pairs[key] = {
                "spearman": rho,
                "spearman_pandas_rank_check": rho_check,
                "abs_diff_vs_check": float(abs(rho - rho_check)),
                "rank_order_identical": bool(np.array_equal(np.argsort(ranks_a), np.argsort(ranks_b))),
            }
    if not pairs:
        return {
            "pairs": pairs,
            "max_abs_diff_vs_pandas_rank_check": 0.0,
            "rank_identity_implications": [],
            "pass": True,
            "note": "No scale pairs available for Spearman self-check.",
        }

    implication_ok = True
    implications = []
    scale_list = list(scales)
    for i, a in enumerate(scale_list):
        for b in scale_list[i + 1:]:
            ab = pairs["%s_%s" % (a, b)]["spearman"]
            if abs(float(ab) - 1.0) >= float(tol):
                continue
            for c in scale_list:
                if c in (a, b):
                    continue
                ac_key = "%s_%s" % tuple(sorted((a, c), key=scale_list.index))
                bc_key = "%s_%s" % tuple(sorted((b, c), key=scale_list.index))
                ac = pairs[ac_key]["spearman"]
                bc = pairs[bc_key]["spearman"]
                ok = bool(abs(float(ac) - float(bc)) < float(tol))
                implication_ok = implication_ok and ok
                implications.append(
                    {
                        "rank_identical_pair": "%s_%s" % (a, b),
                        "third_scale": c,
                        "rho_%s_%s" % (a, c): ac,
                        "rho_%s_%s" % (b, c): bc,
                        "pass": ok,
                    }
                )
    return {
        "pairs": pairs,
        "max_abs_diff_vs_pandas_rank_check": float(
            max(v["abs_diff_vs_check"] for v in pairs.values())
        ),
        "rank_identity_implications": implications,
        "pass": bool(
            max(v["abs_diff_vs_check"] for v in pairs.values()) < float(tol)
            and implication_ok
        ),
    }


def pareto_front(sweep: pd.DataFrame, scales: Sequence[str] = FB.SCALES) -> pd.DataFrame:
    """Non-dominated operating points across the requested risk scales."""
    cols = ["%s_system" % s for s in scales]
    vals = sweep[cols].to_numpy(np.float64)
    keep = np.ones(len(vals), dtype=bool)
    for i in range(len(vals)):
        dominated = np.all(vals <= vals[i], axis=1) & np.any(vals < vals[i], axis=1)
        keep[i] = not bool(dominated.any())
    return sweep[keep].copy().sort_values(["family", "coverage", "param"]).reset_index(drop=True)


def pareto_audit(candidates: pd.DataFrame, front: pd.DataFrame) -> Dict[str, Any]:
    """Record whether Pareto was computed on the combined candidate set."""
    candidate_counts = candidates["family"].value_counts().sort_index().to_dict()
    survivor_counts = front["family"].value_counts().sort_index().to_dict()
    families_considered = sorted(str(x) for x in candidate_counts)
    families_surviving = sorted(str(x) for x in survivor_counts)
    return {
        "n_candidates_considered": int(len(candidates)),
        "candidate_family_counts": {str(k): int(v) for k, v in candidate_counts.items()},
        "n_pareto_survivors": int(len(front)),
        "survivor_family_counts": {str(k): int(v) for k, v in survivor_counts.items()},
        "families_considered": families_considered,
        "families_surviving": families_surviving,
        "single_family_complete_dominance_on_grid": bool(
            len(families_considered) > 1 and len(families_surviving) == 1
        ),
    }


def aurc_system(sweep: pd.DataFrame, scale: str = "err") -> float:
    """Area under whole-system risk as a ranking-quality summary."""
    x, y = _collapse_by_coverage(sweep, "%s_system" % scale)
    if len(x) < 2:
        return float("nan")
    return float(np.trapezoid(y, x))


def aurc_system_by_scale(sweep: pd.DataFrame, scales: Sequence[str] = FB.SCALES) -> Dict[str, float]:
    return {scale: aurc_system(sweep, scale) for scale in scales}


def additive_local_degeneracy_report(
    mhat: np.ndarray,
    qhat_rows: np.ndarray,
    qhat_by_bin: Mapping[int, float],
    operating_eps: float,
) -> Dict[str, Any]:
    """G23-7b: the shift family loses age bins one by one before full coverage."""
    thresholds = [
        {"z_bin": int(z), "epsilon_star": float(q)}
        for z, q in sorted(qhat_by_bin.items(), key=lambda item: float(item[1]))
    ]
    for row in thresholds:
        eps = float(row["epsilon_star"])
        acc = accept_additive(mhat, qhat_rows, eps)
        row["coverage_at_epsilon_star"] = float(acc.mean())
        row["n_degenerate_age_bins"] = int(sum(eps >= float(q) for q in qhat_by_bin.values()))

    op_acc = accept_additive(mhat, qhat_rows, float(operating_eps))
    first = thresholds[0]
    return {
        "definition": "age bin is locally degenerate once q_hat_slot1(z) - epsilon <= 0",
        "thresholds_by_onset": thresholds,
        "first_local_degeneracy_epsilon": float(first["epsilon_star"]),
        "first_local_degeneracy_coverage": float(first["coverage_at_epsilon_star"]),
        "operating_epsilon": float(operating_eps),
        "operating_coverage": float(op_acc.mean()),
        "operating_minus_first_epsilon": float(float(operating_eps) - float(first["epsilon_star"])),
        "operating_minus_first_coverage": float(float(op_acc.mean()) - float(first["coverage_at_epsilon_star"])),
        "operating_degenerate_age_bins": int(
            sum(float(operating_eps) >= float(q) for q in qhat_by_bin.values())
        ),
        "degenerate_bin_count_monotone": bool(
            all(
                int(a["n_degenerate_age_bins"]) <= int(b["n_degenerate_age_bins"])
                for a, b in zip(thresholds, thresholds[1:])
            )
        ),
    }


def reject_risk_summary(
    sweep: pd.DataFrame,
    scale: str = "err",
    operational_param_range: tuple[float, float] = (0.05, 0.50),
) -> Dict[str, Any]:
    """Summarize risk on the reject branch and its local flatness."""
    col = "%s_reject" % scale
    finite = sweep[np.isfinite(sweep[col].to_numpy(np.float64))].copy()
    best = finite.loc[finite[col].idxmin()]
    lo, hi = operational_param_range
    band = finite[(finite["param"] >= float(lo)) & (finite["param"] <= float(hi))]
    band_best = band.loc[band[col].idxmin()] if len(band) else None
    return {
        "scale": scale,
        "global_min": {
            "family": str(best["family"]),
            "param": float(best["param"]),
            "coverage": float(best["coverage"]),
            col: float(best[col]),
            "%s_system" % scale: float(best["%s_system" % scale]),
        },
        "operational_param_range": [float(lo), float(hi)],
        "operational_range_min": (
            {
                "family": str(band_best["family"]),
                "param": float(band_best["param"]),
                "coverage": float(band_best["coverage"]),
                col: float(band_best[col]),
                "%s_system" % scale: float(band_best["%s_system" % scale]),
            }
            if band_best is not None
            else None
        ),
        "operational_range_reject_risk_min": float(band[col].min()) if len(band) else float("nan"),
        "operational_range_reject_risk_max": float(band[col].max()) if len(band) else float("nan"),
    }


def slot_reject_diagnostics(
    mhat: np.ndarray,
    qhat: np.ndarray,
    family: str,
    param: float,
) -> Dict[str, Any]:
    """Slot-level reject diagnostics, mirroring conformal_simultaneous."""
    m = np.asarray(mhat, dtype=np.float64)
    q = np.asarray(qhat, dtype=np.float64)
    if family == "multiplicative":
        reject = m < float(param) * q
    elif family == "additive":
        reject = m < q - float(param)
    else:
        raise ValueError("family must be 'multiplicative' or 'additive'")
    any_reject = reject.any(axis=1)
    return {
        "family": family,
        "param": float(param),
        "coverage": float((~any_reject).mean()),
        "slot_reject_rates": [float(x) for x in reject.mean(axis=0)],
        "slot1_decides_share": float((reject[:, 0] == any_reject).mean()),
        "slot1_rejects_given_reject": float(reject[any_reject, 0].mean()) if any_reject.any() else 0.0,
    }


def conditioning_ratios_at_targets(
    sweep_add: pd.DataFrame,
    qhat_by_bin: Mapping[int, float],
    targets: Sequence[float] = MATCHED_COVERAGE,
) -> list[Dict[str, Any]]:
    r_mul = age_conditioning_ratio(qhat_by_bin, "multiplicative", 1.0)
    out = []
    for target in targets:
        eps = param_at_coverage(sweep_add, float(target))
        out.append(
            {
                "coverage": float(target),
                "eps_interpolated": eps,
                "r_multiplicative": r_mul,
                "r_additive": age_conditioning_ratio(qhat_by_bin, "additive", eps),
            }
        )
    return out


def paired_family_delta_at_coverage(
    df: pd.DataFrame,
    qhat_rows: np.ndarray,
    sweep_mul: pd.DataFrame,
    sweep_add: pd.DataFrame,
    target: float = 0.78,
    policy: str = "static",
    scale: str = "err",
    n_boot: int = 1000,
    seed: int = 23202,
) -> Dict[str, Any]:
    """Paired block-bootstrap for multiplicative minus additive at one coverage."""
    mhat = df[list(MHAT_COLS)].to_numpy(np.float64)
    kappa = param_at_coverage(sweep_mul, target)
    eps = param_at_coverage(sweep_add, target)
    acc_mul = accept_multiplicative(mhat, qhat_rows, kappa)
    acc_add = accept_additive(mhat, qhat_rows, eps)
    a_mul = FB.apply_fallback(df, acc_mul, policy)["a_chosen"]
    a_add = FB.apply_fallback(df, acc_add, policy)["a_chosen"]
    diff = FB.loss_of(df, a_mul, scale) - FB.loss_of(df, a_add, scale)

    blocks = df["block_id"].to_numpy()
    uniq, inv = np.unique(blocks, return_inverse=True)
    n_blk = len(uniq)
    sum_d = np.bincount(inv, weights=diff, minlength=n_blk)
    cnt = np.bincount(inv, minlength=n_blk).astype(np.float64)
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=np.float64)
    for i in range(int(n_boot)):
        pick = rng.integers(0, n_blk, size=n_blk)
        draws[i] = sum_d[pick].sum() / cnt[pick].sum()
    ci = np.quantile(draws, [0.025, 0.975])
    overlap = acc_mul & acc_add
    union = acc_mul | acc_add
    return {
        "coverage_target": float(target),
        "scale": scale,
        "policy": policy,
        "kappa_interpolated": float(kappa),
        "eps_interpolated": float(eps),
        "coverage_mul": float(acc_mul.mean()),
        "coverage_add": float(acc_add.mean()),
        "accept_intersection": float(overlap.mean()),
        "accept_union": float(union.mean()),
        "accept_symmetric_difference": float((acc_mul ^ acc_add).mean()),
        "delta_mul_minus_add": float(diff.mean()),
        "delta_ci95": [float(ci[0]), float(ci[1])],
        "delta_half_width_ci95": float((ci[1] - ci[0]) / 2.0),
        "n_boot": int(n_boot),
        "seed": int(seed),
        "n_blocks": int(n_blk),
    }


def fit_c3_inputs(
    df: pd.DataFrame,
    config: str = "C3",
    multiplicity: str = "bonferroni",
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, Dict[str, Any], Dict[int, float], float]:
    from cert import config_matrix as CM
    from cert.simultaneous_score import ALPHA

    calib = df[df["is_calib"]]
    test = FB.sort_for_stateful(df[~df["is_calib"]])
    fit = CM.fit_config(calib, config, 1.0, alpha=ALPHA, multiplicity=multiplicity)
    qhat_rows = CM._q_rows(test, fit["keys"], fit["_q"], len(fit["score_cols"]))
    q_by_age = qhat_by_age_bin(calib, fit, slot=0, weighted=True)
    qbar = qbar_from_age_bins(q_by_age)
    return calib, test, qhat_rows, fit, q_by_age, qbar


def run_report(
    df: pd.DataFrame,
    config: str = "C3",
    policy: str = "static",
    cell_label: str = "poisson@0.925",
    input_path: str = "results/SUPERSEDED/phase-22/calib_set_v3.parquet",
    scales: Sequence[str] = FB.SCALES,
    targets: Sequence[float] = MATCHED_COVERAGE,
    n_boot: int = 1000,
) -> Dict[str, Any]:
    calib, test, qhat_rows, fit, q_by_age, qbar = fit_c3_inputs(df, config=config)
    eval_scales, skipped_scales = FB.available_scales(test, scales)
    eps_grid = eps_grid_from_delta(qbar)
    sweep_mul = sweep_family(
        test,
        qhat_rows,
        "multiplicative",
        KAPPA_GRID,
        policy=policy,
        scales=eval_scales,
    )
    sweep_add = sweep_family(
        test,
        qhat_rows,
        "additive",
        eps_grid,
        policy=policy,
        scales=eval_scales,
    )
    comparison = compare_families_at_coverage(sweep_mul, sweep_add, targets=targets)
    combined = pd.concat([sweep_mul, sweep_add], ignore_index=True, sort=False)
    mhat = test[list(MHAT_COLS)].to_numpy(np.float64)
    slot_targets = []
    for target in targets:
        slot_targets.append(
            {
                "coverage": float(target),
                "multiplicative": slot_reject_diagnostics(
                    mhat,
                    qhat_rows,
                    "multiplicative",
                    param_at_coverage(sweep_mul, target),
                ),
                "additive": slot_reject_diagnostics(
                    mhat,
                    qhat_rows,
                    "additive",
                    param_at_coverage(sweep_add, target),
                ),
            }
        )
    pareto = pareto_front(combined, scales=eval_scales)
    paired_078 = paired_family_delta_at_coverage(
        test,
        qhat_rows,
        sweep_mul,
        sweep_add,
        target=0.78,
        policy=policy,
        scale="err",
        n_boot=n_boot,
    )
    scale_check = {
        "multiplicative": scale_agreement_self_check(sweep_mul, scales=eval_scales),
        "additive": scale_agreement_self_check(sweep_add, scales=eval_scales),
        "combined": scale_agreement_self_check(combined, scales=eval_scales),
    }
    pareto_meta = pareto_audit(combined, pareto)
    local_degen = additive_local_degeneracy_report(
        mhat,
        qhat_rows,
        q_by_age,
        operating_eps=float(paired_078["eps_interpolated"]),
    )
    out: Dict[str, Any] = {
        "cell": str(cell_label),
        "config": config,
        "policy": policy,
        "requested_scales": [str(x) for x in scales],
        "scales": [str(x) for x in eval_scales],
        "skipped_scales": skipped_scales,
        "qbar_slot1_age_bins": qbar,
        "qhat_slot1_by_age_bin": q_by_age,
        "delta_grid": [float(x) for x in DELTA_GRID],
        "eps_grid": [float(x) for x in eps_grid],
        "kappa_grid": [float(x) for x in KAPPA_GRID],
        "sweep_multiplicative": sweep_mul.to_dict(orient="records"),
        "sweep_additive": sweep_add.to_dict(orient="records"),
        "compare_families_at_coverage": comparison.to_dict(orient="records"),
        "conditioning_ratios_at_coverage": conditioning_ratios_at_targets(sweep_add, q_by_age, targets),
        "slot_diagnostics_at_coverage": slot_targets,
        "scale_agreement": {
            "multiplicative": scale_agreement(sweep_mul, scales=eval_scales),
            "additive": scale_agreement(sweep_add, scales=eval_scales),
            "combined": scale_agreement(combined, scales=eval_scales),
        },
        "scale_agreement_self_check": scale_check,
        "aurc_system": {
            "multiplicative": aurc_system_by_scale(sweep_mul, scales=eval_scales),
            "additive": aurc_system_by_scale(sweep_add, scales=eval_scales),
            "diff_mul_minus_add": {
                scale: float(aurc_system(sweep_mul, scale) - aurc_system(sweep_add, scale))
                for scale in eval_scales
            },
        },
        "pareto_front": pareto.to_dict(orient="records"),
        "pareto_audit": pareto_meta,
        "paired_delta_at_coverage_0.78": paired_078,
        "local_degeneracy_additive": local_degen,
        "reject_risk_summary": {
            "multiplicative_err": reject_risk_summary(sweep_mul, "err"),
        },
        "gates": {
            "V23_4_additive_delta0_equals_multiplicative_kappa1": bool(
                np.array_equal(
                    accept_additive(mhat, qhat_rows, 0.0),
                    accept_multiplicative(mhat, qhat_rows, 1.0),
                )
            ),
            "G23_6b_regret_equals_additive": bool(
                all(
                    np.array_equal(
                        accept_additive(mhat, qhat_rows, eps),
                        accept_regret(mhat, qhat_rows, eps),
                    )
                    for eps in eps_grid
                )
            ),
            "G23_7_additive_degenerates_at_delta_1.5": bool(
                accept_additive(mhat, qhat_rows, eps_grid[-1]).all()
            ),
            "G23_8_full_coverage_is_anchor": bool(
                abs(sweep_mul.loc[sweep_mul["param"] == 0.0, "err_system"].iloc[0] - FB.loss_of(test, test["a_twin"].to_numpy(np.int64), "err").mean())
                < 1e-12
            ),
            "G23_7b_local_degeneracy_cascade_reported": bool(
                local_degen["first_local_degeneracy_epsilon"] < paired_078["eps_interpolated"]
                and local_degen["operating_degenerate_age_bins"] >= 1
                and local_degen["degenerate_bin_count_monotone"]
            ),
            "G23_9_scale_agreement_self_check": bool(
                all(v["pass"] for v in scale_check.values())
            ),
            "G23_9b_pareto_front_uses_combined_sweep": bool(
                pareto_meta["n_candidates_considered"] == len(sweep_mul) + len(sweep_add)
                and len(pareto_meta["families_considered"]) == 2
            ),
        },
        "fit_public": {k: v for k, v in fit.items() if k != "_q"},
        "provenance": {
            "script": "cert/threshold_families.py",
            "input": str(input_path),
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty_before_write": bool(_git("git", "status", "--short")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
    return _json_clean(out)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="results/SUPERSEDED/phase-22/calib_set_v3.parquet")
    ap.add_argument("--cell-label", default="poisson@0.925")
    ap.add_argument("--config", default="C3")
    ap.add_argument("--policy", default="static", choices=("static", "sticky", "wait"))
    ap.add_argument("--scales", nargs="+", choices=FB.SCALES, default=list(FB.SCALES))
    ap.add_argument("--out-json", default="results/SUPERSEDED/phase-23/threshold_families_poisson_0.925_C3_static.json")
    ap.add_argument("--out-csv", default="results/SUPERSEDED/phase-23/threshold_families_poisson_0.925_C3_static.csv")
    ap.add_argument("--n-boot", type=int, default=1000)
    args = ap.parse_args(argv)

    df = pd.read_parquet(args.input)
    report = run_report(
        df,
        config=args.config,
        policy=args.policy,
        cell_label=args.cell_label,
        input_path=args.input,
        scales=args.scales,
        n_boot=int(args.n_boot),
    )
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True)
        f.write("\n")

    rows = []
    rows.extend(report["sweep_multiplicative"])
    rows.extend(report["sweep_additive"])
    pd.DataFrame(rows).to_csv(args.out_csv, index=False)

    print("wrote", args.out_json)
    print("wrote", args.out_csv)
    if report.get("skipped_scales"):
        print("skipped_scales")
        print(json.dumps(report["skipped_scales"], indent=1, sort_keys=True))
    print("compare_families_at_coverage")
    print(pd.DataFrame(report["compare_families_at_coverage"]).to_string(index=False))
    print("scale_agreement")
    print(json.dumps(report["scale_agreement"], indent=1, sort_keys=True))
    print("scale_agreement_self_check")
    print(json.dumps(report["scale_agreement_self_check"], indent=1, sort_keys=True))
    print("pareto_audit")
    print(json.dumps(report["pareto_audit"], indent=1, sort_keys=True))
    print("local_degeneracy_additive")
    print(json.dumps(report["local_degeneracy_additive"], indent=1, sort_keys=True))
    print("aurc_system")
    print(json.dumps(report["aurc_system"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Lesson 23.7 [3b] -- conditioning, pruning, va do nhay cua ``a_star``.

Thu tu khoa cua phep do:

* [A] S4: conditioning va kha nang tach bien;
* [B] L21: gia cua hanh dong chet;
* [C] P23-D: bom residual vao CHAN LY, chay sau cung.

Module nay chi import xuong ``cert.cell_matrices``. No khong import ba script
hieu chuan cung cap bac ``cert.lesson23_7_*``.

Chay mot cell (cell chinh phai chay truoc)::

    python -m cert.conditioning_audit --cell poisson@0.925

Chay hai cell giu kin sau khi doi chung cell chinh da dat::

    python -m cert.conditioning_audit --cell poisson@0.850
    python -m cert.conditioning_audit --cell h2@0.700

Tong hop artifact, Figure 6 va tai lieu::

    python -m cert.conditioning_audit --summarize
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import baselines as BL
from cert import config_matrix as CM
from cert import fallback as FB
from cert import simultaneous_score as SS
from cert.cell_matrices import (
    ALPHA_EACH_NOMINAL,
    ALPHA_FAMILY,
    GAMMA_OP,
    HELD_OUT_CELLS,
    LADDER,
    MAIN_CALIB,
    MAIN_CELL,
    MAIN_QHAT,
    N_PATHS,
    RESIDUAL,
    TRUTH_TABLE,
    acceptance_for,
    cell_matrices,
    git,
    json_clean,
    pin,
    prepare,
)
from measurements import band_v2 as B
from measurements import residual_spec as RS
from measurements.decision_error_v2 import TruthTable
from twin import topology_v7 as T7


ENDPOINTS: Tuple[Tuple[str, float], ...] = (
    ("r_star", 0.008868196569470351),
    ("point", 0.009521786236599921),
    ("ci90_worst", 0.010135081793680400),
)
SIGN = -1.0

CELL_SPECS: Dict[str, Dict[str, Any]] = {
    MAIN_CELL: {
        "mode": "poisson",
        "rho_bar": 0.925,
        "parquet": MAIN_CALIB,
        "fallback": MAIN_QHAT,
        "slug": "poisson_0.925",
    },
    "poisson@0.850": {
        "mode": "poisson",
        "rho_bar": 0.850,
        "parquet": "results/phase-22/calib_set_v3_poisson_0.850.parquet",
        "fallback": "results/phase-23/fallback_poisson_0.850_C3_k0.50.json",
        "slug": "poisson_0.850",
    },
    "h2@0.700": {
        "mode": "h2",
        "rho_bar": 0.700,
        "parquet": "results/phase-22/calib_set_v3_h2_0.700.parquet",
        "fallback": "results/phase-23/fallback_h2_0.700_C3_k0.50.json",
        "slug": "h2_0.700",
    },
}

MAIN_BASELINE_EXPECTED = {
    "c_star_err": 0.453347031,
    "c_f2_err": 0.394852400,
    "delta": -0.01286885,
}
MAIN_BASELINE_TOL = 2e-8
MAIN_PFIX_PATH = "results/phase-23/lesson23_7_calibration_2b.json"
AMENDMENT = "docs/phase-23/00zf-amendment-30.md"
SUMMARY_PATH = "results/phase-23/conditioning_audit_summary.json"
FIGURE_PATH = "results/phase-23/fig6_conditioning_audit.png"
DOC_PATH = "docs/phase-23/12-mechanisms.md"


def artifact_path(cell: str) -> str:
    return "results/phase-23/conditioning_audit_%s.json" % CELL_SPECS[cell]["slug"]


def _fit_original(df: pd.DataFrame) -> Dict[str, Any]:
    calib = df[df["is_calib"]]
    return CM.fit_config(
        calib, "C3", 1.0, alpha=ALPHA_FAMILY, multiplicity="bonferroni"
    )


def _qhat_tensor(q: Mapping[tuple[Any, ...], np.ndarray]) -> np.ndarray:
    """Chuyen qhat Mondrian thanh tensor ``(z_bin, m_hat_bin, slot)``."""
    keys = list(q)
    n_z = 1 + max(int(k[0]) for k in keys)
    n_m = 1 + max(int(k[1]) for k in keys)
    n_s = len(next(iter(q.values())))
    arr = np.full((n_z, n_m, n_s), np.nan, dtype=np.float64)
    for key, value in q.items():
        arr[int(key[0]), int(key[1])] = np.asarray(value, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("qhat tensor co o thieu hoac khong huu han")
    return arr


def _spread_axis(arr: np.ndarray, axis: int) -> Dict[str, Any]:
    others = tuple(i for i in range(arr.ndim) if i != int(axis))
    profile = arr.mean(axis=others)
    return {
        "profile": [float(x) for x in profile],
        "spread": float(profile.max() / profile.min()),
        "argmax": int(profile.argmax()),
        "argmin": int(profile.argmin()),
    }


def spread_and_separability(q_tensor: np.ndarray) -> Dict[str, Any]:
    """M-1/M-2/M-3 (tat dinh) va M-9 (cham hai cell giu kin)."""
    arr = np.asarray(q_tensor, dtype=np.float64)
    axes = {
        "z": _spread_axis(arr, 0),
        "m_hat": _spread_axis(arr, 1),
        "slot": _spread_axis(arr, 2),
    }
    spread_total = float(arr.max() / arr.min())
    product = float(
        axes["z"]["spread"] * axes["m_hat"]["spread"] * axes["slot"]["spread"]
    )
    gap = float(abs(spread_total - product) / spread_total)
    return {
        "grid_shape": list(arr.shape),
        "M_1_spread_m": axes["m_hat"]["spread"],
        "M_2_spread_z": axes["z"]["spread"],
        "M_3_spread_total": spread_total,
        "spread_slot": axes["slot"]["spread"],
        "axes": axes,
        "product_of_marginal_spreads": product,
        "M_9_separability_gap_rel": gap,
        "M_9_in_band_le_0_05": bool(gap <= 0.05),
    }


def _global_qhat(calib: pd.DataFrame) -> np.ndarray:
    n_eff = int(calib["block_id"].nunique())
    level = SS.conformal_level(n_eff, ALPHA_EACH_NOMINAL)
    return np.asarray(
        [
            SS.empirical_qhat(calib["s_pair_%d" % slot].to_numpy(np.float64), level)
            for slot in (1, 2, 3)
        ],
        dtype=np.float64,
    )


def _overlap(score_a: np.ndarray, score_b: np.ndarray, gamma: float) -> Dict[str, Any]:
    a = BL._accept_at_coverage(score_a, gamma)
    b = BL._accept_at_coverage(score_b, gamma)
    inter = int((a & b).sum())
    union = int((a | b).sum())
    return {
        "jaccard": float(inter / union),
        "coverage_a": float(a.mean()),
        "coverage_b": float(b.mean()),
        "coverage_matched": bool(abs(a.mean() - b.mean()) < 1e-12),
        "n_different": int((a != b).sum()),
    }


def jaccard_vs_constant_qhat(df: pd.DataFrame, gamma: float = GAMMA_OP) -> Dict[str, Any]:
    """M-4: bao cao ca hai cach doc M-D2, cham theo ``post='none'``.

    (a) ``post_variant='none'`` van giu ``z_bin`` va chi bo ``m_hat_bin``.
    (b) qhat hang so toan cuc bo ca hai truc.

    Amendment 23-30 khoa cach (c): do ca hai, nhung M-4 chi cham (a).
    """
    calib = df[df["is_calib"]]
    test = FB.sort_for_stateful(df[~df["is_calib"]])
    fit_m = CM.fit_config(
        calib, "C3", 1.0, alpha=ALPHA_FAMILY, multiplicity="bonferroni"
    )
    fit_z = CM.fit_config(
        calib,
        "C3",
        1.0,
        alpha=ALPHA_FAMILY,
        multiplicity="bonferroni",
        post_variant="none",
    )
    score_m = BL.score_C3(test, CM._q_rows(test, fit_m["keys"], fit_m["_q"], 3))
    score_z = BL.score_C3(test, CM._q_rows(test, fit_z["keys"], fit_z["_q"], 3))
    q_global = _global_qhat(calib)
    score_global = BL.score_C3(test, np.broadcast_to(q_global, (len(test), 3)))
    scored = _overlap(score_m, score_z, gamma)
    global_diag = _overlap(score_m, score_global, gamma)
    return {
        "decision_locked_in_amendment": "(c) do ca hai; M-4 cham (a)",
        "gamma": float(gamma),
        "keys_mondrian": list(fit_m["keys"]),
        "keys_post_none": list(fit_z["keys"]),
        "M_4_scored_post_none_keeps_z": {
            **scored,
            "band": [0.94, 0.99],
            "in_band": bool(0.94 <= scored["jaccard"] <= 0.99),
        },
        "global_constant_diagnostic_not_scored": {
            **global_diag,
            "qhat": [float(x) for x in q_global],
        },
    }


def qhat_budget_ratio(calib: pd.DataFrame) -> Dict[str, Any]:
    """M-5: qhat(K'=3, alpha/2) / qhat(K=4, alpha/3), slot 1."""
    rows: List[Dict[str, Any]] = []
    for key, sub in calib.groupby(["z_bin", "m_hat_bin"], sort=True):
        n_eff = int(sub["block_id"].nunique())
        values = sub["s_pair_1"].to_numpy(np.float64)
        q_new = SS.empirical_qhat(
            values, SS.conformal_level(n_eff, ALPHA_FAMILY / 2.0)
        )
        q_old = SS.empirical_qhat(
            values, SS.conformal_level(n_eff, ALPHA_FAMILY / 3.0)
        )
        rows.append(
            {
                "z_bin": int(key[0]),
                "m_hat_bin": int(key[1]),
                "n_eff_blocks": n_eff,
                "qhat_K3": float(q_new),
                "qhat_K4": float(q_old),
                "ratio": float(q_new / q_old),
            }
        )
    ratios = np.asarray([r["ratio"] for r in rows], dtype=np.float64)
    return {
        "per_mondrian_cell": rows,
        "min": float(ratios.min()),
        "max": float(ratios.max()),
        "mean": float(ratios.mean()),
        "band": [0.905, 0.935],
        "all_cells_in_band": bool((ratios >= 0.905).all() and (ratios <= 0.935).all()),
    }


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = pd.Series(np.asarray(x, dtype=np.float64)).rank(method="average").to_numpy()
    ry = pd.Series(np.asarray(y, dtype=np.float64)).rank(method="average").to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def spearman_z_mhat(test: pd.DataFrame) -> Dict[str, Any]:
    rho = _spearman(
        test["z_s"].to_numpy(np.float64), test["m_hat_1"].to_numpy(np.float64)
    )
    return {
        "M_10_spearman": rho,
        "n_test": int(len(test)),
        "band": [-0.7, -0.3],
        "in_band": bool(-0.7 <= rho <= -0.3),
    }


def ladder_decomposed(
    base: Mapping[str, np.ndarray], prep: Mapping[str, Any]
) -> Dict[str, Any]:
    """M-6/M-6b/M-6c: tach rang buoc, ngan sach va tuong tac."""
    s0 = acceptance_for(base, prep, (), ALPHA_EACH_NOMINAL)
    base_accept = float(s0["acceptance_test"])
    rows: List[Dict[str, Any]] = []
    for label, pruned in LADDER[1:]:
        m_effective = N_PATHS - len(pruned) - 1
        alpha_effective = ALPHA_FAMILY / m_effective
        constraint = acceptance_for(base, prep, pruned, ALPHA_EACH_NOMINAL)
        budget = acceptance_for(base, prep, (), alpha_effective)
        both = acceptance_for(base, prep, pruned, alpha_effective)
        d_constraint = float(constraint["acceptance_test"] - base_accept)
        d_budget = float(budget["acceptance_test"] - base_accept)
        d_both = float(both["acceptance_test"] - base_accept)
        interaction = float(d_both - d_constraint - d_budget)
        rows.append(
            {
                "level": label,
                "pruned": ["P%d" % (p + 1) for p in pruned],
                "m_effective": int(m_effective),
                "alpha_each_effective": float(alpha_effective),
                "branch_i_constraint_only": {**constraint, "delta_vs_S0": d_constraint},
                "branch_ii_budget_only": {**budget, "delta_vs_S0": d_budget},
                "branch_iii_both": {**both, "delta_vs_S0": d_both},
                "M_6_delta_total": d_both,
                "M_6_in_band_0_08_0_18": bool(0.08 <= d_both <= 0.18),
                "interaction_abs": abs(interaction),
                "interaction_rel_to_total": abs(interaction) / abs(d_both) if d_both else None,
                "M_6b_budget_share": d_budget / d_both if d_both else None,
                "M_6b_in_band_0_75_1_00": bool(
                    d_both and 0.75 <= d_budget / d_both <= 1.00
                ),
            }
        )
    s1, s2 = rows
    margin = float(s1["M_6b_budget_share"] - s2["M_6b_budget_share"])
    return {
        "S0_acceptance": base_accept,
        "levels": rows,
        "M_6c_budget_share_S1_gt_S2": bool(margin > 0),
        "M_6c_margin": margin,
    }


def _main_pfix_threshold() -> float:
    with open(MAIN_PFIX_PATH, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    return float(report["M_D13_r_crit"]["M_13_threshold_r_cond_crit"])


def pruning_profitability(
    base: Mapping[str, np.ndarray], prep: Mapping[str, Any]
) -> Dict[str, Any]:
    """M-13/M-13b/M-13c tren P4, voi nguong P_fix tu cell chinh."""
    p = 3
    a_star = np.asarray(prep["a_star_full"], dtype=np.int64)
    y_hat = np.asarray(base["y_hat"], dtype=np.float64)
    a_twin = y_hat.argmin(axis=1)
    keep = [i for i in range(y_hat.shape[1]) if i != p]
    a_pruned = np.asarray(keep)[y_hat[:, keep].argmin(axis=1)]
    picked = a_twin == p
    star_is_p = a_star == p
    fixable = picked & ~star_is_p
    fixed = fixable & (a_pruned == a_star)
    broken = picked & star_is_p
    a = int(fixable.sum())
    b = int(broken.sum())
    p_fix = float(fixed.sum() / a) if a else None
    ratio_cond = float(a / b) if b else None
    ratio_is_infinite = bool(a > 0 and b == 0)
    p_star = float(star_is_p.mean())
    ratio_marginal = float(picked.mean() / p_star) if p_star else None
    threshold = _main_pfix_threshold()
    predicts_profit = bool(ratio_is_infinite or (ratio_cond is not None and ratio_cond > threshold))
    actual_profit = bool(int(fixed.sum()) > b)
    return {
        "path": "P4",
        "n_fixable_a": a,
        "n_broken_b": b,
        "n_fixed": int(fixed.sum()),
        "P_fix": p_fix,
        "M_13c_in_band_0_60_0_90": bool(p_fix is not None and 0.60 <= p_fix <= 0.90),
        "conditional_ratio_a_over_b": ratio_cond,
        "conditional_ratio_is_infinite": ratio_is_infinite,
        "threshold_1_over_Pfix_from_main_cell": threshold,
        "M_13_predicts_profitable": predicts_profit,
        "profitable_exact": actual_profit,
        "M_13_prediction_correct": bool(predicts_profit == actual_profit),
        "M_13b_marginal_overselection_ratio": ratio_marginal,
        "M_13b_in_band_1_0_2_5": bool(
            ratio_marginal is not None and 1.0 <= ratio_marginal <= 2.5
        ),
        "partition_check": bool(a + b == int(picked.sum())),
    }


def _score_and_accept_test(
    df: pd.DataFrame, fit: Mapping[str, Any], gamma: float = GAMMA_OP
) -> Tuple[np.ndarray, np.ndarray]:
    test = df[~df["is_calib"]]
    qrows = CM._q_rows(test, fit["keys"], fit["_q"], 3)
    score = BL.score_C3(test, qrows)
    return qrows, BL._accept_at_coverage(score, gamma)


def residual_vs_margin(test: pd.DataFrame, accept: np.ndarray) -> Dict[str, Any]:
    """M-11 mot phia tren all-test; M-14 so accept voi all-test."""
    m_hat = test[["m_hat_1", "m_hat_2", "m_hat_3"]].to_numpy(np.float64)
    m_true = test[["m_true_1", "m_true_2", "m_true_3"]].to_numpy(np.float64)
    harmful = np.maximum(m_hat[:, 0] - m_true[:, 0], 0.0)

    def ratio(mask: np.ndarray) -> Dict[str, Any]:
        q95 = float(np.quantile(harmful[mask], 0.95))
        mean_margin = float(m_hat[mask, 0].mean())
        return {
            "n": int(mask.sum()),
            "q95_harmful_residual": q95,
            "mean_m_hat_1": mean_margin,
            "ratio": float(q95 / mean_margin),
        }

    all_rows = ratio(np.ones(len(test), dtype=bool))
    accepted = ratio(np.asarray(accept, dtype=bool))
    m14 = float(accepted["ratio"] / all_rows["ratio"])
    one_sided_any = m_true.min(axis=1) < 0.0
    disagreement = test["a_twin"].to_numpy(np.int64) != test["a_star"].to_numpy(np.int64)
    return {
        "M_11_all_test": {
            **all_rows,
            "band": [1.45, 1.76],
            "in_band": bool(1.45 <= all_rows["ratio"] <= 1.76),
        },
        "accept_only_companion": accepted,
        "M_14_ratio_accept_over_all": m14,
        "M_14_lt_1": bool(m14 < 1.0),
        "one_sided_flip_identity": bool(np.array_equal(one_sided_any, disagreement)),
    }


def astar_sensitivity(
    base: Mapping[str, np.ndarray],
    prep: Mapping[str, Any],
    perturbed: Mapping[str, Mapping[str, np.ndarray]],
) -> Dict[str, Any]:
    """M-15: phan hang co ``a_star`` doi, headline o CI90 xau tren TEST."""
    a0 = np.asarray(base["y_true"]).argmin(axis=1)
    test = ~np.asarray(prep["is_calib"], dtype=bool)
    rows: List[Dict[str, Any]] = []
    for label, endpoint in ENDPOINTS:
        a1 = np.asarray(perturbed[label]["y_true"]).argmin(axis=1)
        flip = a0 != a1
        rows.append(
            {
                "endpoint_label": label,
                "endpoint": float(endpoint),
                "n_flip_all": int(flip.sum()),
                "flip_fraction_all": float(flip.mean()),
                "n_flip_test": int(flip[test].sum()),
                "n_test": int(test.sum()),
                "M_15_flip_fraction_test": float(flip[test].mean()),
                "M_15_in_band_0_10_0_40": bool(0.10 <= flip[test].mean() <= 0.40),
            }
        )
    return {
        "points": rows,
        "headline_endpoint": "ci90_worst",
        "headline": next(r for r in rows if r["endpoint_label"] == "ci90_worst"),
    }


def _pipeline(
    y_true: np.ndarray,
    y_hat: np.ndarray,
    prep: Mapping[str, Any],
    qhat_rows: np.ndarray,
    gamma_target: float = GAMMA_OP,
) -> Dict[str, Any]:
    """M-D14: tinh lai a*, wrong, c*, c_F2 va Delta tu mot bang chi phi."""
    a_star = np.asarray(y_true).argmin(axis=1)
    a_twin = np.asarray(y_hat).argmin(axis=1)
    p1 = FB.path_static_shortest()
    wrong_twin = a_twin != a_star
    wrong_p1 = np.full(len(a_star), p1, dtype=np.int64) != a_star
    m_hat = SS.pair_margins_hat(y_hat)
    score = np.min(m_hat / np.asarray(qhat_rows, dtype=np.float64), axis=1)
    test = ~np.asarray(prep["is_calib"], dtype=bool)
    accept_all = np.zeros(len(a_star), dtype=bool)
    accept_all[test] = BL._accept_at_coverage(score[test], gamma_target)
    accept = accept_all[test]
    w_t = wrong_twin[test]
    w_p = wrong_p1[test]
    c_star = float(w_t[~accept].mean())
    c_f2 = float(w_p[~accept].mean())
    gamma = float(accept.mean())
    return {
        "coverage": gamma,
        "r_neo": float(w_t.mean()),
        "r_accept": float(w_t[accept].mean()),
        "c_star_err": c_star,
        "c_f2_err": c_f2,
        "delta": float((1.0 - gamma) * (c_f2 - c_star)),
        "_accept": accept_all,
    }


def conclusion_flip(
    base: Mapping[str, np.ndarray],
    prep: Mapping[str, Any],
    qhat_rows: np.ndarray,
    perturbed: Mapping[str, Mapping[str, np.ndarray]],
    check_main_baseline: bool = False,
) -> Dict[str, Any]:
    """M-12a (dau) va M-12b (doi dau) tren ba diem."""
    baseline = _pipeline(base["y_true"], base["y_hat"], prep, qhat_rows)
    rows: List[Dict[str, Any]] = []
    yhat_ok = True
    accept_ok = True
    for label, endpoint in ENDPOINTS:
        pert = perturbed[label]
        same_yhat = bool(np.array_equal(base["y_hat"], pert["y_hat"]))
        yhat_ok = yhat_ok and same_yhat
        measured = _pipeline(pert["y_true"], pert["y_hat"], prep, qhat_rows)
        same_accept = bool(np.array_equal(baseline["_accept"], measured["_accept"]))
        accept_ok = accept_ok and same_accept
        gap0 = baseline["c_f2_err"] - baseline["c_star_err"]
        gap1 = measured["c_f2_err"] - measured["c_star_err"]
        rows.append(
            {
                "endpoint_label": label,
                "endpoint": float(endpoint),
                "baseline": {k: v for k, v in baseline.items() if not k.startswith("_")},
                "perturbed": {k: v for k, v in measured.items() if not k.startswith("_")},
                "d_gap_c_f2_minus_c_star": float(gap1 - gap0),
                "M_12a_sign_positive": bool(gap1 > gap0),
                "M_12b_flipped": bool(np.sign(measured["delta"]) != np.sign(baseline["delta"])),
                "y_hat_unchanged": same_yhat,
                "accept_set_unchanged": same_accept,
            }
        )
    baseline_clean = {k: v for k, v in baseline.items() if not k.startswith("_")}
    approval = None
    if check_main_baseline:
        gaps = {
            key: float(abs(baseline_clean[key] - expected))
            for key, expected in MAIN_BASELINE_EXPECTED.items()
        }
        approval = {
            "expected": MAIN_BASELINE_EXPECTED,
            "absolute_gaps": gaps,
            "tolerance": MAIN_BASELINE_TOL,
            "matches_lesson_23_6": bool(max(gaps.values()) <= MAIN_BASELINE_TOL),
        }
    return {
        "baseline": baseline_clean,
        "baseline_approval_23_6": approval,
        "points": rows,
        "control_y_hat_unchanged_all_three": bool(yhat_ok),
        "control_accept_set_unchanged_all_three": bool(accept_ok),
        "M_12a_positive_all_three": bool(all(r["M_12a_sign_positive"] for r in rows)),
        "M_12b_flipped_all_three": bool(all(r["M_12b_flipped"] for r in rows)),
    }


def _fit_q_scores(
    scores: np.ndarray, prep: Mapping[str, Any], m_bin: np.ndarray
) -> Dict[tuple[int, int], np.ndarray]:
    is_calib = np.asarray(prep["is_calib"], dtype=bool)
    z_bin = np.asarray(prep["z_bin"], dtype=np.int64)
    block_id = np.asarray(prep["block_id"])
    out: Dict[tuple[int, int], np.ndarray] = {}
    for z in np.unique(z_bin):
        for m in np.unique(m_bin):
            sel = is_calib & (z_bin == z) & (m_bin == m)
            if not sel.any():
                continue
            n_eff = int(pd.unique(block_id[sel]).size)
            level = SS.conformal_level(n_eff, ALPHA_EACH_NOMINAL)
            out[(int(z), int(m))] = np.asarray(
                [SS.empirical_qhat(scores[sel, j], level) for j in range(scores.shape[1])],
                dtype=np.float64,
            )
    return out


def _qrows_from_map(
    q: Mapping[tuple[int, int], np.ndarray],
    prep: Mapping[str, Any],
    m_bin: np.ndarray,
) -> np.ndarray:
    missing = np.full(3, np.inf, dtype=np.float64)
    return np.vstack(
        [
            q.get((int(z), int(m)), missing)
            for z, m in zip(np.asarray(prep["z_bin"]), np.asarray(m_bin))
        ]
    )


def coverage_under_misspec(
    base: Mapping[str, np.ndarray],
    prep: Mapping[str, Any],
    pert: Mapping[str, np.ndarray],
) -> Dict[str, Any]:
    """M-16 + doi chung NC23v2-8/PC23v2-3 tren CUNG mot endpoint."""
    s_orig = SS.pair_scores(base["y_true"], base["y_hat"])
    s_pert = SS.pair_scores(pert["y_true"], pert["y_hat"])
    m_hat = SS.pair_margins_hat(base["y_hat"])
    from cert.cell_matrices import mhat_bin

    m_bin = mhat_bin(m_hat[:, 0], np.asarray(prep["is_calib"], dtype=bool))
    q_orig = _fit_q_scores(s_orig, prep, m_bin)
    q_pert = _fit_q_scores(s_pert, prep, m_bin)
    qr_orig = _qrows_from_map(q_orig, prep, m_bin)
    qr_pert = _qrows_from_map(q_pert, prep, m_bin)
    test = ~np.asarray(prep["is_calib"], dtype=bool)

    def coverage(qrows: np.ndarray, scores: np.ndarray) -> float:
        return float((scores[test] <= qrows[test]).all(axis=1).mean())

    baseline = coverage(qr_orig, s_orig)
    negative = coverage(qr_pert, s_pert)
    positive = coverage(qr_orig, s_pert)
    # Bao dam conformal la MOT PHIA: coverage >= 1-alpha. Bao phu 0.923 khong
    # phai loi vi no cao hon 0.90; chi coverage TUT DUOI nominal moi kich hoat
    # canh bao dung duong ong. Dung cua so doi xung quanh 0.90 se bien tinh bao
    # thu hop le thanh mot loi gia.
    control_holds = bool(negative >= 1.0 - ALPHA_FAMILY)
    positive_drops = bool(positive < 1.0 - ALPHA_FAMILY)
    return {
        "endpoint_label": "ci90_worst",
        "alpha": ALPHA_FAMILY,
        "nominal_coverage": 1.0 - ALPHA_FAMILY,
        "baseline_orig_orig": baseline,
        "NC23v2_8_pert_pert": negative,
        "PC23v2_3_orig_pert": positive,
        "NC23v2_8_holds_at_or_above_nominal": control_holds,
        "M_16_PC23v2_3_below_0_90": positive_drops,
        "control_pair_discriminates": bool(control_holds and positive_drops),
    }


def _alignment_control(
    df: pd.DataFrame, base: Mapping[str, np.ndarray], prep: Mapping[str, Any]
) -> Dict[str, Any]:
    return {
        "same_length": bool(len(df) == len(base["y_true"])),
        "a_star_exact": bool(
            np.array_equal(df["a_star"].to_numpy(np.int64), base["y_true"].argmin(axis=1))
        ),
        "a_twin_exact": bool(
            np.array_equal(df["a_twin"].to_numpy(np.int64), base["y_hat"].argmin(axis=1))
        ),
        "split_exact": bool(
            np.array_equal(df["is_calib"].to_numpy(bool), prep["is_calib"])
        ),
    }


def _perturbed_matrices(
    cell: str,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, np.ndarray]], Dict[str, Any]]:
    spec = CELL_SPECS[cell]
    tt = TruthTable(TRUTH_TABLE)
    base = cell_matrices(tt, mode=spec["mode"], rho_bar=spec["rho_bar"])
    records = RS.load(RESIDUAL)
    rec = next(
        r
        for r in records
        if str(r.mode) == str(spec["mode"]) and str(r.channel) == "loss"
    )
    perturbed: Dict[str, Dict[str, np.ndarray]] = {}
    clip: Dict[str, Any] = {}
    for label, endpoint in ENDPOINTS:
        tt_pert = B.truth_table_for(rec, "common_mode", endpoint, sign=SIGN)
        perturbed[label] = cell_matrices(
            tt_pert, mode=spec["mode"], rho_bar=spec["rho_bar"]
        )
        n_eval = int(getattr(tt_pert, "eval_count", 0))
        n_clip = int(getattr(tt_pert, "clip_events", 0))
        clip[label] = {
            "clip_events": n_clip,
            "eval_count": n_eval,
            "clip_ratio": float(n_clip / max(n_eval, 1)),
        }
    return base, perturbed, clip


def run_cell(cell: str) -> Dict[str, Any]:
    """Chay [A] -> [B] -> [C] cho mot cell va tra artifact JSON-able."""
    if cell not in CELL_SPECS:
        raise ValueError("cell phai thuoc %s" % sorted(CELL_SPECS))
    spec = CELL_SPECS[cell]
    df = pd.read_parquet(spec["parquet"])
    fit = _fit_original(df)
    test = df[~df["is_calib"]]
    qrows_test, accept_test = _score_and_accept_test(df, fit)

    # [A] khong can tai sinh ma tran chi phi.
    section_a = {
        "spread_and_separability": spread_and_separability(_qhat_tensor(fit["_q"])),
        "jaccard_vs_constant_qhat": jaccard_vs_constant_qhat(df),
        "qhat_budget_ratio_M5": qhat_budget_ratio(df[df["is_calib"]]),
        "spearman_z_mhat_M10": spearman_z_mhat(test),
    }

    # [B] va [C] dung chung cac ma tran; moi endpoint chi duoc tai sinh mot lan.
    base, perturbed, clip = _perturbed_matrices(cell)
    prep = prepare(base)
    alignment = _alignment_control(df, base, prep)
    if not all(alignment.values()):
        raise AssertionError("parquet va cell_matrices khong thang hang: %s" % alignment)
    section_b = {
        "ladder_decomposed": ladder_decomposed(base, prep),
        "pruning_profitability": pruning_profitability(base, prep),
    }

    qrows_all = CM._q_rows(df, fit["keys"], fit["_q"], 3)
    conclusion = conclusion_flip(
        base,
        prep,
        qrows_all,
        perturbed,
        check_main_baseline=(cell == MAIN_CELL),
    )
    if cell == MAIN_CELL:
        approval = conclusion["baseline_approval_23_6"]
        if not approval or not approval["matches_lesson_23_6"]:
            raise AssertionError("doi chung 23.6 lech -- DUNG truoc cell giu kin: %s" % approval)
    section_c = {
        "residual_vs_margin": residual_vs_margin(test, accept_test),
        "astar_sensitivity": astar_sensitivity(base, prep, perturbed),
        "conclusion_flip": conclusion,
        "coverage_under_misspec": coverage_under_misspec(
            base, prep, perturbed["ci90_worst"]
        ),
        "clip_diagnostics": clip,
    }

    report: Dict[str, Any] = {
        "lesson": "23.7",
        "step": "[3b] conditioning audit",
        "cell": cell,
        "cell_role": (
            "PHONG HIEU CHUAN -- M-12b/M-16 cham tai day"
            if cell == MAIN_CELL
            else "PHONG THI GIU KIN -- 13 dong cham tai day"
        ),
        "order": ["[A] S4", "[B] L21", "[C] P23-D"],
        "controls": {"parquet_matrix_alignment": alignment},
        "A_conditioning": section_a,
        "B_dead_action": section_b,
        "C_astar_sensitivity": section_c,
        "provenance": {
            "script": "cert/conditioning_audit.py",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "inputs": [
                pin(spec["parquet"]),
                pin(spec["fallback"]),
                pin(RESIDUAL),
                pin(AMENDMENT),
                pin(MAIN_PFIX_PATH),
            ],
        },
    }
    return json_clean(report)


def _prediction_rows(reports: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for cell, report in reports.items():
        a = report["A_conditioning"]
        b = report["B_dead_action"]
        c = report["C_astar_sensitivity"]
        rows.extend(
            [
                {"cell": cell, "id": "M-4", "value": a["jaccard_vs_constant_qhat"]["M_4_scored_post_none_keeps_z"]["jaccard"], "hit": a["jaccard_vs_constant_qhat"]["M_4_scored_post_none_keeps_z"]["in_band"]},
                {"cell": cell, "id": "M-5", "value": a["qhat_budget_ratio_M5"]["mean"], "hit": a["qhat_budget_ratio_M5"]["all_cells_in_band"]},
                {"cell": cell, "id": "M-9", "value": a["spread_and_separability"]["M_9_separability_gap_rel"], "hit": a["spread_and_separability"]["M_9_in_band_le_0_05"]},
                {"cell": cell, "id": "M-10", "value": a["spearman_z_mhat_M10"]["M_10_spearman"], "hit": a["spearman_z_mhat_M10"]["in_band"]},
                {"cell": cell, "id": "M-11", "value": c["residual_vs_margin"]["M_11_all_test"]["ratio"], "hit": c["residual_vs_margin"]["M_11_all_test"]["in_band"]},
                {"cell": cell, "id": "M-12a", "value": c["conclusion_flip"]["points"][-1]["d_gap_c_f2_minus_c_star"], "hit": c["conclusion_flip"]["M_12a_positive_all_three"]},
                {"cell": cell, "id": "M-12b", "value": c["conclusion_flip"]["M_12b_flipped_all_three"], "hit": c["conclusion_flip"]["M_12b_flipped_all_three"]},
                {"cell": cell, "id": "M-13", "value": ("inf" if b["pruning_profitability"]["conditional_ratio_is_infinite"] else b["pruning_profitability"]["conditional_ratio_a_over_b"]), "hit": b["pruning_profitability"]["M_13_prediction_correct"]},
                {"cell": cell, "id": "M-13b", "value": b["pruning_profitability"]["M_13b_marginal_overselection_ratio"], "hit": b["pruning_profitability"]["M_13b_in_band_1_0_2_5"]},
                {"cell": cell, "id": "M-13c", "value": b["pruning_profitability"]["P_fix"], "hit": b["pruning_profitability"]["M_13c_in_band_0_60_0_90"]},
                {"cell": cell, "id": "M-14", "value": c["residual_vs_margin"]["M_14_ratio_accept_over_all"], "hit": c["residual_vs_margin"]["M_14_lt_1"]},
                {"cell": cell, "id": "M-15", "value": c["astar_sensitivity"]["headline"]["M_15_flip_fraction_test"], "hit": c["astar_sensitivity"]["headline"]["M_15_in_band_0_10_0_40"]},
                {"cell": cell, "id": "M-16", "value": c["coverage_under_misspec"]["PC23v2_3_orig_pert"], "hit": c["coverage_under_misspec"]["control_pair_discriminates"]},
            ]
        )
        for level in b["ladder_decomposed"]["levels"]:
            if level["level"] == "S2":
                rows.extend(
                    [
                        {"cell": cell, "id": "M-6", "value": level["M_6_delta_total"], "hit": level["M_6_in_band_0_08_0_18"]},
                        {"cell": cell, "id": "M-6b", "value": level["M_6b_budget_share"], "hit": level["M_6b_in_band_0_75_1_00"]},
                    ]
                )
        rows.append(
            {"cell": cell, "id": "M-6c", "value": b["ladder_decomposed"]["M_6c_margin"], "hit": b["ladder_decomposed"]["M_6c_budget_share_S1_gt_S2"]}
        )
    return rows


def summarize(reports: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    rows = _prediction_rows(reports)
    scored_cells = {
        "M-4": tuple(CELL_SPECS),
        "M-5": tuple(CELL_SPECS),
        "M-6": HELD_OUT_CELLS,
        "M-6b": HELD_OUT_CELLS,
        "M-6c": HELD_OUT_CELLS,
        "M-9": HELD_OUT_CELLS,
        "M-10": tuple(CELL_SPECS),
        "M-11": HELD_OUT_CELLS,
        "M-12a": tuple(CELL_SPECS),
        "M-12b": (MAIN_CELL,),
        "M-13": HELD_OUT_CELLS,
        "M-13b": HELD_OUT_CELLS,
        "M-13c": HELD_OUT_CELLS,
        "M-14": HELD_OUT_CELLS,
        "M-15": HELD_OUT_CELLS,
        "M-16": (MAIN_CELL,),
    }
    score: Dict[str, Any] = {}
    for prediction, cells in scored_cells.items():
        selected = [r for r in rows if r["id"] == prediction and r["cell"] in cells]
        score[prediction] = {
            "cells": list(cells),
            "hits": int(sum(bool(r["hit"]) for r in selected)),
            "n": int(len(selected)),
            "all_hit": bool(selected and all(bool(r["hit"]) for r in selected)),
            "values": {r["cell"]: r["value"] for r in selected},
        }
    return json_clean(
        {
            "lesson": "23.7",
            "cells": list(reports),
            "predictions": score,
            "rows": rows,
            "controls": {
                "main_baseline_23_6": reports[MAIN_CELL]["C_astar_sensitivity"]["conclusion_flip"]["baseline_approval_23_6"],
                "M16_pair": reports[MAIN_CELL]["C_astar_sensitivity"]["coverage_under_misspec"],
            },
            "provenance": {
                "script": "cert/conditioning_audit.py --summarize",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [pin(artifact_path(cell)) for cell in CELL_SPECS],
            },
        }
    )


def markdown_report(summary: Mapping[str, Any]) -> str:
    pred = summary["predictions"]
    main = summary["controls"]["main_baseline_23_6"]
    m16 = summary["controls"]["M16_pair"]
    lines = [
        "# 12 -- Lesson 23.7: conditioning va do nhay cua chan ly",
        "",
        "Code: `cert/conditioning_audit.py`  ",
        "Artifact: `results/phase-23/conditioning_audit_*.json`  ",
        "Hinh: `results/phase-23/fig6_conditioning_audit.png`",
        "",
        "## 1. Doi chung truoc khi doc cell giu kin",
        "",
        "Pipeline tai lap Lesson 23.6: `c* = %.9f`, `c_F2 = %.9f`, "
        "`Delta = %.9f`; sai lech lon nhat `%.2e` (PASS)."
        % (
            main["expected"]["c_star_err"],
            main["expected"]["c_f2_err"],
            main["expected"]["delta"],
            max(main["absolute_gaps"].values()),
        ),
        "",
        "M-16 duoc bao cao thanh CAP doi chung: NC23v2-8 = `%.6f`, "
        "PC23v2-3 = `%.6f`, nominal = `%.2f`; cap nay `%s`."
        % (
            m16["NC23v2_8_pert_pert"],
            m16["PC23v2_3_orig_pert"],
            m16["nominal_coverage"],
            "PHAN BIET DUOC" if m16["control_pair_discriminates"] else "KHONG phan biet duoc",
        ),
        "",
        "## 2. Bang cham 16 dong lop 3",
        "",
        "| ID | Cell cham | Gia tri | KQ |",
        "|---|---|---|:--:|",
    ]
    for prediction in pred:
        item = pred[prediction]
        values = "; ".join("%s=%s" % (c, _format_value(v)) for c, v in item["values"].items())
        lines.append(
            "| %s | %s | %s | %s %d/%d |"
            % (
                prediction,
                ", ".join(item["cells"]),
                values,
                "HIT" if item["all_hit"] else "MISS",
                item["hits"],
                item["n"],
            )
        )
    lines.extend(
        [
            "",
            "## 3. Co che",
            "",
            "M-4 dung doi chung `post_variant=none` van giu `z_bin`, nen no do "
            "dong gop rieng cua truc `m_hat_bin`. Doi chung qhat hang so toan cuc "
            "duoc bao cao rieng, khong dung de cham.",
            "",
            "Trong phep bom residual, `y_hat` va tap accept giu nguyen; chi `y_true`, "
            "`a_star`, wrong, `c*`, `c_F2` va `Delta` duoc tinh lai. Vi vay phep do "
            "khong dua chan ly vao quyet dinh (khong ro ri oracle).",
            "",
            "NC23v2-8 bom ca calib va test nen giu trao doi duoc. PC23v2-3 bom chi "
            "test trong khi qhat lay tu the gioi goc, nen co chu dich pha trao doi "
            "duoc. Day la sai lech he thong cua thuoc do, khong phai ket luan rang "
            "conformal prediction noi chung khong hoat dong.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "CO" if value else "KHONG"
    if value is None:
        return "n/a"
    if isinstance(value, str):
        return value
    return "%.6f" % float(value)


def plot_figure6(summary: Mapping[str, Any], out_path: str = FIGURE_PATH) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cells = list(CELL_SPECS)
    reports = {}
    for cell in cells:
        with open(artifact_path(cell), "r", encoding="utf-8") as handle:
            reports[cell] = json.load(handle)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    x = np.arange(len(ENDPOINTS))
    for cell in cells:
        points = reports[cell]["C_astar_sensitivity"]["conclusion_flip"]["points"]
        axes[0].plot(
            x,
            [p["d_gap_c_f2_minus_c_star"] for p in points],
            marker="o",
            linewidth=2,
            label=cell,
        )
    axes[0].axhline(0.0, color="black", linewidth=1)
    axes[0].set_xticks(x, [label for label, _ in ENDPOINTS])
    axes[0].set_ylabel("change in c_F2 - c_star")
    axes[0].set_title("M-12a: truth shift changes fallback gap")
    axes[0].legend(frameon=False, fontsize=8)

    m16 = summary["controls"]["M16_pair"]
    labels = ["original/original", "perturbed/perturbed", "original/perturbed"]
    values = [
        m16["baseline_orig_orig"],
        m16["NC23v2_8_pert_pert"],
        m16["PC23v2_3_orig_pert"],
    ]
    axes[1].bar(np.arange(3), values, color=["#4c78a8", "#59a14f", "#e15759"])
    axes[1].axhline(m16["nominal_coverage"], color="black", linestyle="--", linewidth=1)
    axes[1].set_xticks(np.arange(3), labels, rotation=18, ha="right")
    axes[1].set_ylim(0.0, 1.0)
    axes[1].set_ylabel("simultaneous score coverage")
    axes[1].set_title("M-16: exchangeability control pair")
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def _print_cell(report: Mapping[str, Any]) -> None:
    p = print
    cell = report["cell"]
    a = report["A_conditioning"]
    b = report["B_dead_action"]
    c = report["C_astar_sensitivity"]
    p("=" * 78)
    p("LESSON 23.7 [3b] -- %s" % cell)
    p("=" * 78)
    p("[A] M-4 Jaccard = %.6f; M-9 gap = %.6f; M-10 rho = %.6f" % (
        a["jaccard_vs_constant_qhat"]["M_4_scored_post_none_keeps_z"]["jaccard"],
        a["spread_and_separability"]["M_9_separability_gap_rel"],
        a["spearman_z_mhat_M10"]["M_10_spearman"],
    ))
    s2 = b["ladder_decomposed"]["levels"][-1]
    p("[B] M-6 Delta = %.6f; M-6b = %.6f; M-6c margin = %.6f" % (
        s2["M_6_delta_total"], s2["M_6b_budget_share"],
        b["ladder_decomposed"]["M_6c_margin"],
    ))
    pr = b["pruning_profitability"]
    if pr["conditional_ratio_is_infinite"]:
        ratio_text = "inf"
    elif pr["conditional_ratio_a_over_b"] is None:
        ratio_text = "n/a (neutral)"
    else:
        ratio_text = "%.6f" % pr["conditional_ratio_a_over_b"]
    p("[B] M-13 a/b = %s vs main crit %.6f; profitable = %s" % (
        ratio_text, pr["threshold_1_over_Pfix_from_main_cell"],
        pr["profitable_exact"],
    ))
    cf = c["conclusion_flip"]
    p("[C] baseline c*=%.9f c_F2=%.9f Delta=%+.9f" % (
        cf["baseline"]["c_star_err"], cf["baseline"]["c_f2_err"], cf["baseline"]["delta"],
    ))
    for row in cf["points"]:
        p("    %-10s d-gap=%+.6f M-12a=%s M-12b=%s" % (
            row["endpoint_label"], row["d_gap_c_f2_minus_c_star"],
            row["M_12a_sign_positive"], row["M_12b_flipped"],
        ))
    cov = c["coverage_under_misspec"]
    p("[C] M-16 baseline=%.6f NC=%.6f PC=%.6f discriminate=%s" % (
        cov["baseline_orig_orig"], cov["NC23v2_8_pert_pert"],
        cov["PC23v2_3_orig_pert"], cov["control_pair_discriminates"],
    ))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", choices=list(CELL_SPECS))
    parser.add_argument("--out")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    if args.summarize:
        reports = {}
        for cell in CELL_SPECS:
            with open(artifact_path(cell), "r", encoding="utf-8") as handle:
                reports[cell] = json.load(handle)
        summary = summarize(reports)
        os.makedirs(os.path.dirname(os.path.abspath(SUMMARY_PATH)), exist_ok=True)
        with open(SUMMARY_PATH, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=1, sort_keys=True)
            handle.write("\n")
        with open(DOC_PATH, "w", encoding="utf-8") as handle:
            handle.write(markdown_report(summary))
        plot_figure6(summary)
        print("summary -> %s" % SUMMARY_PATH)
        print("figure  -> %s" % FIGURE_PATH)
        print("doc     -> %s" % DOC_PATH)
        return
    if not args.cell:
        parser.error("can --cell hoac --summarize")
    output = args.out or artifact_path(args.cell)
    report = run_cell(args.cell)
    _print_cell(report)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("artifact -> %s" % output)


if __name__ == "__main__":
    main()

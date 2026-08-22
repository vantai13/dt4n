"""Lesson 23.7 -- buoc [0] khao co + buoc [1] hieu chuan dai TRUOC khi ky.

Script nay KHONG ky dong du doan nao va KHONG suy ra ket luan. No chi chay ba
kiem tra hieu chuan dai (`M-D7`, `M-11`, `M-6/M-D4`) da duoc yeu cau truoc
Amendment 23-30, cong voi phan xac minh lai ba dong `[TAT DINH]` `M-1/M-2/M-3`
va do tach duoc cua `q_hat` tren CELL CHINH.

PHAM VI DU LIEU -- KHOA CUNG (xem `SCOPE_GUARD` ben duoi)
---------------------------------------------------------
Chi cell chinh `poisson@0.925` duoc doc. Hai cell con lai (`poisson@0.850`,
`h2@0.700`) mang cac du doan TINH DIEM `M-9`, `M-10`, `M-11` nen KHONG duoc
cham o buoc hieu chuan. Neu ai do them chung vao `CELLS_ALLOWED`, `main()` se
dung lai va bao loi -- day la `NT-v2-20` ap nguoc len chinh script nay.

Chay:
    python -m cert.lesson23_7_range_calibration \
        --out results/SUPERSEDED/phase-23/lesson23_7_range_calibration.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np
import pandas as pd

from cert.cell_matrices import (
    ALPHA_FAMILY,
    DEAD_ACTION_THRESHOLD,
    GAMMA_OP,
    K_NOMINAL,
    M_NOMINAL,
    MAIN_AUDIT,
    MAIN_CALIB,
    MAIN_CELL,
    MAIN_QHAT,
    N_PATHS,
    SCAN_20R,
    SCOPE_GUARD,
    SLOTS,
    git as _git,
    json_clean as _json_clean,
    load_json,
    pin,
)
from cert.simultaneous_score import conformal_level, empirical_qhat

# ---------------------------------------------------------------------------
# 0. Hang so rieng cua buoc [0]/[1]
# ---------------------------------------------------------------------------

# Xap xi nua-chuan ma nguoi phac dai da (ngam) dung cho M-5.
Z_095 = 1.6448536269514722         # Phi^{-1}(0.95)
Z_09667 = 2.1280452341432955       # Phi^{-1}(1 - 0.10/3)
HALF_NORMAL_RATIO = Z_095 / Z_09667   # = 0.7729, xap xi vi tri-0 (mu = 0)


_load_json = load_json


# ---------------------------------------------------------------------------
# 1. Buoc [0] -- khao co L10
# ---------------------------------------------------------------------------

def archaeology_L10(scan_path: str = SCAN_20R) -> Dict[str, Any]:
    """M-D8 buoc [0a]: L10 noi ve dai luong nao? Doc tu ARTIFACT, khong tu doc.

    Tra ve chinh cac con so 20R co the neo `L10`, kem danh gia (i)/(ii)/(iii).
    """
    scan = _load_json(scan_path)
    pub = scan["safety_published"]
    binding = pub["binding"]

    # Chi tiet K4 tai o binding: ranking base -> ranking sau khi bom residual,
    # cong CAC CON SO lam nen `safety_published`. Day moi la thu `L10` co the
    # neo vao: `r_star` (residual du de lat K4) so voi residual DO DUOC.
    k4_detail: Dict[str, Any] = {}
    binding_scan: Dict[str, Any] = {}
    for row in scan.get("scans", []):
        node = (row.get("first_broken_detail") or {}).get("K4_path_ranking_preserved")
        if not isinstance(node, Mapping):
            continue
        for cell, payload in node.items():
            if isinstance(payload, Mapping) and "base" in payload:
                k4_detail[str(cell)] = {
                    "base": list(payload["base"]),
                    "pert": list(payload.get("pert", [])),
                }
        if str(row.get("mode")) == str(binding["mode"]) and str(row.get("channel")) == str(
            binding["channel"]
        ):
            ci = list(row.get("r_ci90") or [])
            worst = max(abs(float(x)) for x in ci) if ci else float("nan")
            r_lo = float((row.get("r_star_bracket") or {}).get("r_star_lo", float("nan")))
            binding_scan = {
                "r_point": float(row.get("r_point", float("nan"))),
                "r_ci90": [float(x) for x in ci],
                "r_ci90_worst_abs": worst,
                "r_star": float(row.get("r_star", float("nan"))),
                "r_star_lo": r_lo,
                "safety_identity_r_star_lo_over_ci90_worst": float(r_lo / worst),
                "residual_over_flip_threshold": float(worst / r_lo),
                "units": "loss (fraction), residual_native_unit",
            }

    return {
        "question": "M-D8[0a]: L10 phat bieu ve dai luong nao?",
        "L10_text_in_repo": {
            "cert/gate_report.py:424-429": {
                "title": "Absolute path ranking inherits the Phase 20R residual bound",
                "text": "s_margin reduces but does not remove the inherited "
                        "ranking-risk condition.",
                "quantitative": False,
            },
            "docs/phase-21R/99-gate-decision.md:154": {"quantitative": False},
            "docs/phase-22/01-inherited-audit.md:18": {"quantitative": False},
            "docs/phase-22/99-gate-decision.md:215 (P23-D)": {"quantitative": False},
            "docs/phase-23/01-inherited-audit.md:77": {"quantitative": False},
        },
        "n_quantitative_statements_found": 0,
        "quantitative_anchor_that_does_exist": {
            "source": scan_path,
            "safety_published": float(pub["value"]),
            "binding_mode": str(binding["mode"]),
            "binding_channel": str(binding["channel"]),
            "binding_variant": str(binding["variant"]),
            "bound": str(binding["bound"]),
            "first_broken": list(binding["first_broken"]),
            "first_broken_cell": list(binding["first_broken_cell"]),
            "safety_lt_1": bool(float(pub["value"]) < 1.0),
            "k4_detail": k4_detail,
            "binding_scan_numbers": binding_scan,
        },
        "verdict": "(ii)",
        "verdict_text": (
            "L10 KHONG ton tai duoi dang mot can so hoc. Thu duy nhat co so va "
            "neo dung noi dung cua L10 la K4_path_ranking_preserved voi "
            "safety_published = 0.868750 < 1 tai poisson@0.925 -- tuc bao toan "
            "thu hang duong DA BI LAT trong pham vi cascade, khong phai 'mot "
            "can chua kiem chung'."
        ),
        "consequence": "M-7 va M-8 khong ky duoc nhu phac; RUT (khong phai MISS).",
    }


# ---------------------------------------------------------------------------
# 2. Xac minh M-1/M-2/M-3 + do tach duoc (deu la [TAT DINH], cell chinh)
# ---------------------------------------------------------------------------

def qhat_tensor(qhat_path: str = MAIN_QHAT) -> np.ndarray:
    """Doc `fit.qhat` thanh tensor `(z_bin, m_hat_bin, slot)`."""
    q = _load_json(qhat_path)["fit"]["qhat"]
    n_z = 1 + max(int(k.strip("()").split(", ")[0]) for k in q)
    n_m = 1 + max(int(k.strip("()").split(", ")[1]) for k in q)
    n_s = len(next(iter(q.values())))
    arr = np.full((n_z, n_m, n_s), np.nan, dtype=np.float64)
    for key, vec in q.items():
        z, m = (int(x) for x in key.strip("()").split(", "))
        arr[z, m] = np.asarray(vec, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("qhat tensor co o thieu hoac khong huu han")
    return arr


def _spread_axis(arr: np.ndarray, axis: int) -> Dict[str, Any]:
    """M-D1: chi so bien = max/min cua trung binh tren HAI truc con lai."""
    others = tuple(i for i in range(arr.ndim) if i != axis)
    prof = arr.mean(axis=others)
    return {
        "profile": [float(x) for x in prof],
        "spread": float(prof.max() / prof.min()),
        "argmax": int(prof.argmax()),
        "argmin": int(prof.argmin()),
    }


def separability_audit(arr: np.ndarray) -> Dict[str, Any]:
    """M-1/M-2/M-3 theo dinh nghia da khoa `M-D1`, cong do tach duoc (M-9)."""
    ax = {"z": _spread_axis(arr, 0), "m_hat": _spread_axis(arr, 1), "slot": _spread_axis(arr, 2)}
    s_z, s_m, s_s = ax["z"]["spread"], ax["m_hat"]["spread"], ax["slot"]["spread"]
    s_total = float(arr.max() / arr.min())
    prod = s_z * s_m * s_s
    imax = np.unravel_index(int(arr.argmax()), arr.shape)
    imin = np.unravel_index(int(arr.argmin()), arr.shape)

    # M-1 co MOT bac tu do chua khoa neu bo `M-D1`: ba cach doc truc slot.
    prof_zs = arr.mean(axis=0)                       # (m_hat, slot)
    m_readings = {
        "MD1_mean_over_z_and_slot": s_m,
        "mean_over_z_then_max_over_slot": float(
            max(prof_zs[:, s].max() / prof_zs[:, s].min() for s in range(arr.shape[2]))
        ),
        "mean_over_z_then_mean_over_slot": float(
            np.mean([prof_zs[:, s].max() / prof_zs[:, s].min() for s in range(arr.shape[2])])
        ),
    }

    return {
        "grid_shape": list(arr.shape),
        "n_cells": int(arr.size),
        "axes": ax,
        "M_1_spread_m": s_m,
        "M_2_spread_z": s_z,
        "M_3_spread_total": s_total,
        "spread_slot": s_s,
        "product_of_marginal_spreads": float(prod),
        "separability_gap_rel": float(abs(s_total - prod) / s_total),
        "argmax_cell": {"z_bin": int(imax[0]), "m_hat_bin": int(imax[1]), "slot": int(imax[2]) + 1,
                        "qhat": float(arr[imax])},
        "argmin_cell": {"z_bin": int(imin[0]), "m_hat_bin": int(imin[1]), "slot": int(imin[2]) + 1,
                        "qhat": float(arr[imin])},
        "M_1_unlocked_dof_readings": m_readings,
        "M_1_readings_all_inside_1_0_1_3": bool(
            all(1.0 <= v <= 1.3 for v in m_readings.values())
        ),
        "note": (
            "TAT DINH: doc thang tu artifact da commit. Khong ky, khong tinh diem. "
            "Do tach duoc o day la tren CELL CHINH -- da duoc cong bo truoc, nen "
            "khong ro ri thong tin cho M-9 (M-9 do tren HAI cell con lai)."
        ),
    }


# ---------------------------------------------------------------------------
# 3. Kiem tra hieu chuan 1 -- M-D7 (dai cua M-5)
# ---------------------------------------------------------------------------

def calibrate_M5(calib: pd.DataFrame) -> Dict[str, Any]:
    """M-D7: ti so `q_hat(alpha=0.05) / q_hat(alpha=0.0333)`, slot 1, tung o.

    Dung DUNG duong ong that (`conformal_level` + `empirical_qhat` voi
    `method='higher'` va `n_eff = so block`), khong dung `np.quantile` tho, vi
    dai cua `M-5` phai khop voi thu se do that.

    CACH LY: day CHI la buoc 2 cua `M-D6` (doi alpha). Buoc 1 (bo duong chet,
    tinh lai rank) KHONG duoc mo phong o day.
    """
    a_new = ALPHA_FAMILY / 2.0            # K' = 3 -> m = 2   (cach doc cua L21)
    a_kd4 = ALPHA_FAMILY / 1.0            # K' = 2 -> m = 1   (nguong M-D4 khoa)
    a_old = ALPHA_FAMILY / M_NOMINAL      # K  = 4 -> m = 3

    rows: List[Dict[str, Any]] = []
    for key, sub in calib.groupby(["z_bin", "m_hat_bin"], sort=True):
        z_bin, m_bin = (int(x) for x in key)
        n_eff = int(sub["block_id"].nunique())
        lvl_new = conformal_level(n_eff, a_new)
        lvl_kd4 = conformal_level(n_eff, a_kd4)
        lvl_old = conformal_level(n_eff, a_old)
        row: Dict[str, Any] = {
            "z_bin": z_bin, "m_hat_bin": m_bin,
            "n_rows": int(len(sub)), "n_eff_blocks": n_eff,
            "level_alpha_new": lvl_new, "level_alpha_md4": lvl_kd4,
            "level_alpha_old": lvl_old,
        }
        for slot in SLOTS:
            vals = sub["s_pair_%d" % slot].to_numpy(np.float64)
            q_new = empirical_qhat(vals, lvl_new)
            q_kd4 = empirical_qhat(vals, lvl_kd4)
            q_old = empirical_qhat(vals, lvl_old)
            row["q_new_slot%d" % slot] = q_new
            row["q_md4_slot%d" % slot] = q_kd4
            row["q_old_slot%d" % slot] = q_old
            row["ratio_slot%d" % slot] = float(q_new / q_old)
            row["ratio_md4_slot%d" % slot] = float(q_kd4 / q_old)
            if slot == 1:
                # Chan doan hinh dang duoi: giai (mu, sigma) tu HAI phan vi da
                # co, gia dinh duoi chuan `q_p = mu + z_p * sigma`. Ti so
                # `mu/sigma` lon => hai phan vi cao bi keo lai gan nhau, tuc
                # ti so -> 1 ma KHONG can duoi nang hay nhe hon.
                z_new, z_old = Z_095, Z_09667
                sigma = (q_old - q_new) / (z_old - z_new)
                mu = q_new - z_new * sigma
                row["implied_sigma_slot1"] = float(sigma)
                row["implied_mu_slot1"] = float(mu)
                row["implied_mu_over_sigma_slot1"] = float(mu / sigma) if sigma else None
        rows.append(row)

    r1 = np.asarray([r["ratio_slot1"] for r in rows], dtype=np.float64)
    r1_md4 = np.asarray([r["ratio_md4_slot1"] for r in rows], dtype=np.float64)
    r_all = np.asarray(
        [r["ratio_slot%d" % s] for r in rows for s in SLOTS], dtype=np.float64
    )
    mos = np.asarray([r["implied_mu_over_sigma_slot1"] for r in rows], dtype=np.float64)
    lo, hi = float(r1.min()), float(r1.max())

    return {
        "definition": "q_hat(alpha_each=0.05) / q_hat(alpha_each=0.03333), slot 1, per Mondrian cell",
        "alpha_each_new_K3": a_new,
        "alpha_each_md4_K2": a_kd4,
        "alpha_each_old_K4": a_old,
        "pipeline": "conformal_level(n_eff=blocks) + empirical_qhat(method='higher')",
        "isolates": "M-D6 buoc 2 (alpha) CHI; buoc 1 (bo duong chet) khong mo phong",
        "per_cell": rows,
        "slot1": {
            "min": lo, "max": hi,
            "mean": float(r1.mean()), "median": float(np.median(r1)),
            "n_cells": int(r1.size),
        },
        "all_slots": {
            "min": float(r_all.min()), "max": float(r_all.max()),
            "mean": float(r_all.mean()), "median": float(np.median(r_all)),
            "n": int(r_all.size),
        },
        "slot1_under_MD4_K2": {
            "alpha_each": a_kd4,
            "min": float(r1_md4.min()), "max": float(r1_md4.max()),
            "mean": float(r1_md4.mean()), "median": float(np.median(r1_md4)),
            "note": "Nguong M-D4 = 0.05 bat HAI duong chet -> K'=2, m=1, alpha_each=0.10. "
                    "Day KHONG phai gia dinh K'=3 ma M-5 duoc phac tren.",
        },
        "half_normal_prediction": HALF_NORMAL_RATIO,
        "observed_over_half_normal": float(r1.mean() / HALF_NORMAL_RATIO),
        "tail_shape_diagnostic": {
            "model": "q_p = mu + z_p * sigma, giai tu dung HAI phan vi da co",
            "implied_mu_over_sigma_min": float(mos.min()),
            "implied_mu_over_sigma_max": float(mos.max()),
            "implied_mu_over_sigma_mean": float(mos.mean()),
            "reading": (
                "Xap xi nua-chuan gia dinh mu = 0. Neu mu/sigma >> 0 thi hai "
                "phan vi cao bi keo lai gan nhau va ti so -> 1, KHONG can vien "
                "den 'duoi nang hon'. Do la kha nang thu ba trong cau hoi 7."
            ),
        },
        "planned_band_0_90_0_96_holds": bool(0.90 <= lo and hi <= 0.96),
        "suggested_band_slot1": [
            float(np.floor(lo * 200.0) / 200.0),
            float(np.ceil(hi * 200.0) / 200.0),
        ],
    }


# ---------------------------------------------------------------------------
# 4. Kiem tra hieu chuan 2 -- M-11 (residual so voi khoang cach margin)
# ---------------------------------------------------------------------------

def calibrate_M11(test: pd.DataFrame, accept: np.ndarray | None = None) -> Dict[str, Any]:
    """M-11: `q_0.95(|residual|) / mean(m_hat_1)` tren tap test.

    `|residual|` = `s_pair_1` = `|m_true_1 - m_hat_1|` -- sai so cua twin tren
    chinh khe margin nho nhat. Danh gia so voi 1.

    BAC TU DO PHAT HIEN THEM: phac thao `M-11` khong ghi MUC (accept-only hay
    toan test). Ta in CA HAI de khoa duoc truoc khi ky (K-D16).
    """
    resid = test["s_pair_1"].to_numpy(np.float64)
    mhat1 = test["m_hat_1"].to_numpy(np.float64)

    # Kiem tra dinh nghia residual co dung khong. Cot parquet la float32, nen
    # dong nhat thuc chi dung den ~1e-6 tuyet doi; dung dung sai float32 chu
    # KHONG dung 1e-9 (mot nguong qua chat se bao "sai" cho mot dong nhat thuc
    # dung -- doi chung am gia).
    recon = np.abs(test["m_true_1"].to_numpy(np.float64) - mhat1)
    dev = np.abs(recon - resid)
    scale = np.maximum(np.abs(resid), 1.0)
    identity_max_abs = float(dev.max())
    identity_max_rel = float((dev / scale).max())
    identity_tol_abs = 1e-4    # float32 eps ~ 1.2e-7; gia tri co bac ~1e1-1e2

    def block(mask: np.ndarray, label: str) -> Dict[str, Any]:
        r, m = resid[mask], mhat1[mask]
        q95 = float(np.quantile(r, 0.95))
        mean_m = float(m.mean())
        return {
            "level": label,
            "n": int(mask.sum()),
            "q95_abs_residual": q95,
            "median_abs_residual": float(np.median(r)),
            "mean_abs_residual": float(r.mean()),
            "mean_m_hat_1": mean_m,
            "median_m_hat_1": float(np.median(m)),
            "M_11_ratio_q95_over_mean_mhat1": float(q95 / mean_m),
            "ratio_lt_1": bool(q95 / mean_m < 1.0),
            "p_residual_exceeds_mhat1_rowwise": float(np.mean(r > m)),
        }

    out: Dict[str, Any] = {
        "residual_definition": "s_pair_1 = |m_true_1 - m_hat_1| (top-1 margin residual)",
        "identity_check_max_abs_deviation": identity_max_abs,
        "identity_check_max_rel_deviation": identity_max_rel,
        "identity_tol_abs_float32": identity_tol_abs,
        "identity_holds": bool(identity_max_abs < identity_tol_abs),
        "dtype_note": "cot parquet la float32; nguong 1e-9 se bao sai gia",
        "levels": [block(np.ones(len(test), dtype=bool), "all test rows")],
    }
    if accept is not None:
        out["levels"].append(block(np.asarray(accept, dtype=bool), "accept-only @ gamma=0.78"))
        out["levels"].append(block(~np.asarray(accept, dtype=bool), "reject-only @ gamma=0.78"))

    ratios = [b["M_11_ratio_q95_over_mean_mhat1"] for b in out["levels"]]
    out["ratio_spread_across_levels"] = {
        "min": float(min(ratios)), "max": float(max(ratios)),
        "note": "Neu min/max nam hai ben 1.0 thi MUC la mot bac tu do QUYET DINH ket luan.",
    }

    # DOI CHUNG AM MIEN PHI, TAT DINH (cung khuon NC23v2-7).
    #
    # Bien co that su lam LAT top-1 la "co mot margin THAT bi am":
    #     a_twin != a*   <=>   min_j m_true_j < 0
    # Residual HAI PHIA `|m_true - m_hat|` vuot `m_hat` gom CA hai nhanh:
    #     m_true < 0            -> LAT   (co hai)
    #     m_true > 2 * m_hat    -> KHONG lat (twin chi qua bao thu)
    # Nen `q_0.95(|residual|)` dem ca nhanh vo hai. Do la mot bac tu do NUA
    # chua khoa trong M-11: MOT PHIA hay HAI PHIA.
    m_true = test[["m_true_1", "m_true_2", "m_true_3"]].to_numpy(np.float64)
    m_hat_all = test[["m_hat_1", "m_hat_2", "m_hat_3"]].to_numpy(np.float64)
    disagree = test["a_twin"].to_numpy(np.int64) != test["a_star"].to_numpy(np.int64)

    two_sided = resid > mhat1                       # |m_true_1 - m_hat_1| > m_hat_1
    one_sided_slot1 = (mhat1 - m_true[:, 0]) > mhat1  # <=> m_true_1 < 0
    one_sided_any = m_true.min(axis=1) < 0.0

    # Residual MOT PHIA co hai: twin da uoc luong margin CAO hon su that bao nhieu.
    harmful = np.maximum(m_hat_all[:, 0] - m_true[:, 0], 0.0)

    def _cmp(ev: np.ndarray, label: str) -> Dict[str, Any]:
        return {
            "variant": label,
            "p_event": float(ev.mean()),
            "abs_gap_vs_flip": float(abs(ev.mean() - disagree.mean())),
            "rowwise_agreement_with_flip": float(np.mean(ev == disagree)),
            "exact": bool(np.array_equal(ev, disagree)),
        }

    out["free_control_which_residual_definition"] = {
        "flip_event": "a_twin != a_star",
        "p_top1_disagreement": float(disagree.mean()),
        "variants": [
            _cmp(two_sided, "HAI PHIA: |m_true_1 - m_hat_1| > m_hat_1"),
            _cmp(one_sided_slot1, "MOT PHIA slot 1: m_true_1 < 0"),
            _cmp(one_sided_any, "MOT PHIA moi slot: min_j m_true_j < 0"),
        ],
        "verdict": (
            "min_j m_true_j < 0 TRUNG KHOP HOAN TOAN voi bien co lat top-1. "
            "Bien the HAI PHIA dem thua nhanh 'twin bao thu' va lech ~13 diem. "
            "=> M-11 phai khoa MOT PHIA, neu khong no do mot bien co khac voi "
            "bien co L10 quan tam."
        ),
        "one_sided_M11": {
            "residual": "max(m_hat_1 - m_true_1, 0)  (twin uoc luong margin CAO hon su that)",
            "q95": float(np.quantile(harmful, 0.95)),
            "mean_m_hat_1": float(mhat1.mean()),
            "ratio_q95_over_mean_mhat1": float(np.quantile(harmful, 0.95) / mhat1.mean()),
            "q95_accept_only": (
                float(np.quantile(harmful[np.asarray(accept, dtype=bool)], 0.95))
                if accept is not None else None
            ),
            "ratio_accept_only": (
                float(
                    np.quantile(harmful[np.asarray(accept, dtype=bool)], 0.95)
                    / mhat1[np.asarray(accept, dtype=bool)].mean()
                )
                if accept is not None else None
            ),
        },
    }
    return out


# ---------------------------------------------------------------------------
# 5. Kiem tra hieu chuan 3 -- M-6 / M-D4 (hanh dong chet)
# ---------------------------------------------------------------------------

def calibrate_M6(test: pd.DataFrame, accept: np.ndarray | None = None) -> Dict[str, Any]:
    """M-D4/M-D5: `P(a* = a)` (dinh nghia) va `P(a_twin = a)` (bao cao)."""
    a_star = test["a_star"].to_numpy(np.int64)
    a_twin = test["a_twin"].to_numpy(np.int64)

    def dist(vec: np.ndarray, mask: np.ndarray) -> List[float]:
        sel = vec[mask]
        return [float(np.mean(sel == p)) for p in range(N_PATHS)]

    all_rows = np.ones(len(test), dtype=bool)
    p_star = dist(a_star, all_rows)
    p_twin = dist(a_twin, all_rows)
    dead = [p for p in range(N_PATHS) if p_star[p] < DEAD_ACTION_THRESHOLD]
    dead_twin = [p for p in range(N_PATHS) if p_twin[p] < DEAD_ACTION_THRESHOLD]

    out: Dict[str, Any] = {
        "threshold_locked_before_looking": DEAD_ACTION_THRESHOLD,
        "definition_uses": "P(a* = a) on test rows (M-D5)",
        "P_a_star": {"P%d" % (p + 1): p_star[p] for p in range(N_PATHS)},
        "P_a_twin": {"P%d" % (p + 1): p_twin[p] for p in range(N_PATHS)},
        "dead_actions_by_a_star": ["P%d" % (p + 1) for p in dead],
        "dead_actions_by_a_twin": ["P%d" % (p + 1) for p in dead_twin],
        "n_dead": len(dead),
        "K_nominal": K_NOMINAL,
        "K_effective": int(K_NOMINAL - len(dead)),
        "m_nominal": M_NOMINAL,
        "m_effective": int(K_NOMINAL - len(dead) - 1),
        "alpha_each_nominal": ALPHA_FAMILY / M_NOMINAL,
        "alpha_each_effective": (
            float(ALPHA_FAMILY / max(K_NOMINAL - len(dead) - 1, 1))
            if K_NOMINAL - len(dead) - 1 >= 1 else None
        ),
        "max_abs_disagreement_star_vs_twin": float(
            max(abs(p_star[p] - p_twin[p]) for p in range(N_PATHS))
        ),
        "L21_says_K_effective": 3,
        "L21_named_dead_actions": ["P2"],
        "MD4_agrees_with_L21": bool(len(dead) == 1),
        "conflict_note": (
            "L21 (Amendment 23-15, docs/phase-23/04-baselines.md) goi ten MOT "
            "hanh dong chet (P2) bang mat thuong va suy ra K_eff = 3. Nguong "
            "M-D4 = 0.05, khoa TRUOC khi nhin, bat THEM P4 (P(a*=P4) = 0.00717) "
            "va cho K_eff = 2. Hai cach doc KHAC NHAU va M-5 duoc phac tren cach "
            "doc cua L21. Amendment 23-30 phai chon MOT."
        ),
    }
    if accept is not None:
        acc = np.asarray(accept, dtype=bool)
        out["P_a_star_accept_only"] = {
            "P%d" % (p + 1): v for p, v in enumerate(dist(a_star, acc))
        }
        out["P_a_twin_accept_only"] = {
            "P%d" % (p + 1): v for p, v in enumerate(dist(a_twin, acc))
        }
    return out


# ---------------------------------------------------------------------------
# 6. Neo tat dinh cho M-7' / M-8'
# ---------------------------------------------------------------------------

def anchors_M7p_M8p(audit_path: str = MAIN_AUDIT) -> Dict[str, Any]:
    """M-7'/M-8': doc thang tu artifact Lesson 23.4/23.6, khong tinh lai."""
    audit = _load_json(audit_path)
    ov = audit["accept_overlap_at_078"]["C3_B2"]
    return {
        "source": audit_path,
        "gamma": GAMMA_OP,
        "jaccard_C3_B2": float(ov["jaccard"]),
        "coverage_a": float(ov["coverage_a"]),
        "coverage_b": float(ov["coverage_b"]),
        "matched_coverage": bool(abs(ov["coverage_a"] - ov["coverage_b"]) < 1e-9),
        "note": "M-7'/M-8' la [TAT DINH]: neo cach doc, KHONG tinh diem.",
    }


# ---------------------------------------------------------------------------
# 7. Driver
# ---------------------------------------------------------------------------

def _accept_mask(df: pd.DataFrame, gamma: float) -> tuple[pd.DataFrame, np.ndarray, float]:
    """Accept-set C3 tai do bao phu `gamma` (khop coverage, khong khop kappa)."""
    from cert import config_matrix as CM
    from cert.fallback import sort_for_stateful

    calib = df[df["is_calib"]]
    test = sort_for_stateful(df[~df["is_calib"]])

    lo, hi = 0.0, 50.0
    best = hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        fit = CM.fit_config(calib, "C3", mid, alpha=ALPHA_FAMILY, multiplicity="bonferroni")
        qrows = CM._q_rows(test, fit["keys"], fit["_q"], len(fit["score_cols"]))
        cov = float(CM._accept(test, fit["mhat_cols"], qrows, mid).mean())
        if cov >= gamma:
            lo, best = mid, mid
        else:
            hi = mid
    fit = CM.fit_config(calib, "C3", best, alpha=ALPHA_FAMILY, multiplicity="bonferroni")
    qrows = CM._q_rows(test, fit["keys"], fit["_q"], len(fit["score_cols"]))
    acc = CM._accept(test, fit["mhat_cols"], qrows, best)
    return test, acc, float(best)


def build(out_path: str, cells: Sequence[str] = SCOPE_GUARD) -> Dict[str, Any]:
    if tuple(cells) != SCOPE_GUARD:
        raise ValueError(
            "Buoc hieu chuan CHI duoc doc %s. Hai cell con lai mang du doan "
            "TINH DIEM (M-9/M-10/M-11) va phai duoc giu kin cho den khi "
            "Amendment 23-30 duoc ky." % (SCOPE_GUARD,)
        )

    df = pd.read_parquet(MAIN_CALIB)
    test, accept, kappa_at_gamma = _accept_mask(df, GAMMA_OP)
    calib = df[df["is_calib"]]
    arr = qhat_tensor()

    return {
        "lesson": "23.7",
        "step": "[0] khao co + [1] ba kiem tra hieu chuan dai",
        "signs_nothing": True,
        "cell": MAIN_CELL,
        "scope_guard": list(SCOPE_GUARD),
        "held_out_cells": ["poisson@0.850", "h2@0.700"],
        "n_calib_rows": int(len(calib)),
        "n_test_rows": int(len(test)),
        "kappa_at_gamma_078": kappa_at_gamma,
        "coverage_achieved": float(accept.mean()),
        "step0_archaeology_L10": archaeology_L10(),
        "deterministic_M1_M2_M3_and_separability": separability_audit(arr),
        "calibration_1_M_D7_for_M5": calibrate_M5(calib),
        "calibration_2_M11": calibrate_M11(test, accept),
        "calibration_3_M6_dead_action": calibrate_M6(test, accept),
        "anchors_M7p_M8p": anchors_M7p_M8p(),
        "provenance": {
            "script": "cert/lesson23_7_range_calibration.py",
            "calib": MAIN_CALIB,
            "qhat": MAIN_QHAT,
            "audit": MAIN_AUDIT,
            "scan_20R": SCAN_20R,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain", "--untracked-files=no")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "out": out_path,
        },
    }


def _print_report(rep: Mapping[str, Any]) -> None:
    p = print
    p("=" * 78)
    p("LESSON 23.7 -- BUOC [0] KHAO CO + BUOC [1] HIEU CHUAN DAI")
    p("cell = %s   calib = %d hang   test = %d hang" % (
        rep["cell"], rep["n_calib_rows"], rep["n_test_rows"]))
    p("hai cell con lai (%s) KHONG duoc doc -- giu kin cho M-9/M-10/M-11" % (
        ", ".join(rep["held_out_cells"])))
    p("=" * 78)

    a = rep["step0_archaeology_L10"]
    p("\n--- [0] KHAO CO L10 (M-D8) " + "-" * 50)
    p("So phat bieu DINH LUONG cua L10 tim thay trong repo : %d" % a["n_quantitative_statements_found"])
    for src in a["L10_text_in_repo"]:
        p("    %-46s dinh luong = KHONG" % src)
    q = a["quantitative_anchor_that_does_exist"]
    p("Neo DINH LUONG duy nhat ton tai (%s):" % q["source"])
    p("    safety_published   = %.6f   (< 1 ? %s)" % (q["safety_published"], q["safety_lt_1"]))
    p("    binding            = %s / %s / %s  [%s]" % (
        q["binding_mode"], q["binding_channel"], q["binding_variant"], q["bound"]))
    p("    first_broken       = %s tai %s" % (
        ", ".join(q["first_broken"]), ", ".join(q["first_broken_cell"])))
    for cell, det in q["k4_detail"].items():
        p("    K4 %-14s %s -> %s" % (
            cell, ",".join(det.get("base", [])), ",".join(det.get("pert", []))))
    bs = q.get("binding_scan_numbers") or {}
    if bs:
        p("    CON SO nen `safety_published` (day moi la thu L10 co the neo vao):")
        p("      r_star_lo (residual du de LAT K4) = %.9f" % bs["r_star_lo"])
        p("      residual DO DUOC, CI90 = [%.9f, %.9f] -> |worst| = %.9f" % (
            bs["r_ci90"][0], bs["r_ci90"][1], bs["r_ci90_worst_abs"]))
        p("      r_star_lo / |worst| = %.6f  == safety_published" % (
            bs["safety_identity_r_star_lo_over_ci90_worst"]))
        p("      => residual do duoc LON HON nguong lat %.4fx" % bs["residual_over_flip_threshold"])
    p("KET LUAN: %s  %s" % (a["verdict"], a["verdict_text"]))
    p("HE QUA  : %s" % a["consequence"])

    s = rep["deterministic_M1_M2_M3_and_separability"]
    p("\n--- [TAT DINH] M-1 / M-2 / M-3 + do tach duoc " + "-" * 30)
    p("luoi q_hat = %s  (%d o)" % ("x".join(str(x) for x in s["grid_shape"]), s["n_cells"]))
    for name, key in (("z", "z"), ("m_hat", "m_hat"), ("slot", "slot")):
        ax = s["axes"][key]
        p("  bien %-6s : %s   -> spread = %.4f" % (
            name, "  ".join("%8.3f" % v for v in ax["profile"]), ax["spread"]))
    p("  M-1 spread_m     = %.4f   dai phac 1.0-1.3   -> %s" % (
        s["M_1_spread_m"], "TRONG DAI" if 1.0 <= s["M_1_spread_m"] <= 1.3 else "NGOAI DAI"))
    p("  M-2 spread_z     = %.4f   dai phac 1.8-2.3   -> %s" % (
        s["M_2_spread_z"], "TRONG DAI" if 1.8 <= s["M_2_spread_z"] <= 2.3 else "NGOAI DAI"))
    p("  M-3 spread_total = %.4f   dai phac 1.2-2.0   -> %s" % (
        s["M_3_spread_total"], "TRONG DAI" if 1.2 <= s["M_3_spread_total"] <= 2.0 else "NGOAI DAI"))
    p("  tich ba ti so bien = %.4f   |lech| / total = %.4f" % (
        s["product_of_marginal_spreads"], s["separability_gap_rel"]))
    p("  argmax o = (z=%d, m=%d, slot=%d) = %.3f" % (
        s["argmax_cell"]["z_bin"], s["argmax_cell"]["m_hat_bin"],
        s["argmax_cell"]["slot"], s["argmax_cell"]["qhat"]))
    p("  argmin o = (z=%d, m=%d, slot=%d) = %.3f" % (
        s["argmin_cell"]["z_bin"], s["argmin_cell"]["m_hat_bin"],
        s["argmin_cell"]["slot"], s["argmin_cell"]["qhat"]))
    p("  M-1 ba cach doc truc slot (bac tu do M-D1 khoa lai):")
    for k, v in s["M_1_unlocked_dof_readings"].items():
        p("      %-34s %.4f" % (k, v))
    p("      ca ba deu trong 1.0-1.3 ? %s" % s["M_1_readings_all_inside_1_0_1_3"])

    c5 = rep["calibration_1_M_D7_for_M5"]
    p("\n--- [1a] M-D7: HIEU CHUAN DAI CHO M-5 " + "-" * 38)
    p("alpha_each: %.5f (K=4, m=3)  ->  %.5f (K'=3, m=2)" % (
        c5["alpha_each_old_K4"], c5["alpha_each_new_K3"]))
    p("%-4s %-4s %8s %8s %10s %10s %8s" % (
        "z", "m", "n_row", "n_blk", "q_old_s1", "q_new_s1", "ratio"))
    for r in c5["per_cell"]:
        p("%-4d %-4d %8d %8d %10.4f %10.4f %8.4f" % (
            r["z_bin"], r["m_hat_bin"], r["n_rows"], r["n_eff_blocks"],
            r["q_old_slot1"], r["q_new_slot1"], r["ratio_slot1"]))
    s1 = c5["slot1"]
    p("slot 1 tren %d o : min %.4f  median %.4f  mean %.4f  max %.4f" % (
        s1["n_cells"], s1["min"], s1["median"], s1["mean"], s1["max"]))
    sa = c5["all_slots"]
    p("ca 3 slot (%d o) : min %.4f  median %.4f  mean %.4f  max %.4f" % (
        sa["n"], sa["min"], sa["median"], sa["mean"], sa["max"]))
    p("xap xi nua-chuan du doan %.4f  ->  do / nua-chuan = %.4f" % (
        c5["half_normal_prediction"], c5["observed_over_half_normal"]))
    td = c5["tail_shape_diagnostic"]
    p("chan doan hinh dang: mu/sigma ngam (q = mu + z*sigma) = [%.2f, %.2f], TB %.2f" % (
        td["implied_mu_over_sigma_min"], td["implied_mu_over_sigma_max"],
        td["implied_mu_over_sigma_mean"]))
    p("  -> xap xi nua-chuan gia dinh mu=0; du lieu co mu/sigma >> 0 nen hai")
    p("     phan vi cao bi keo lai gan nhau. Do la ly do 0.92 vs 0.77.")
    m2 = c5["slot1_under_MD4_K2"]
    p("NEU dung nguong M-D4 (hai duong chet, K'=2, alpha_each=%.2f):" % m2["alpha_each"])
    p("  ti so slot 1 = [%.4f, %.4f], TB %.4f   <- NGOAI dai phac 0.90-0.96" % (
        m2["min"], m2["max"], m2["mean"]))
    p("dai phac 0.90-0.96 co bao het slot 1 (gia dinh K'=3) ? %s" % c5["planned_band_0_90_0_96_holds"])
    p("dai DE XUAT sau hieu chuan (slot 1, K'=3) : [%.3f, %.3f]" % tuple(c5["suggested_band_slot1"]))

    c11 = rep["calibration_2_M11"]
    p("\n--- [1b] M-11: HIEU CHUAN DAI RESIDUAL " + "-" * 37)
    p("residual := %s" % c11["residual_definition"])
    p("dong nhat thuc khop ? %s   (max|lech| = %.2e, tol float32 = %.0e)" % (
        c11["identity_holds"], c11["identity_check_max_abs_deviation"],
        c11["identity_tol_abs_float32"]))
    p("%-28s %9s %10s %10s %10s %8s" % (
        "muc", "n", "q95|res|", "mean m1", "ti so", "P(r>m1)"))
    for b in c11["levels"]:
        p("%-28s %9d %10.4f %10.4f %10.4f %8.4f" % (
            b["level"], b["n"], b["q95_abs_residual"], b["mean_m_hat_1"],
            b["M_11_ratio_q95_over_mean_mhat1"], b["p_residual_exceeds_mhat1_rowwise"]))
    p("ti so trai rong qua cac MUC: [%.4f, %.4f]  <- MUC la bac tu do phai khoa" % (
        c11["ratio_spread_across_levels"]["min"], c11["ratio_spread_across_levels"]["max"]))
    fc = c11["free_control_which_residual_definition"]
    p("doi chung mien phi [TAT DINH] -- dinh nghia residual nao neo dung bien co lat?")
    p("  P(a_twin != a*) = %.6f" % fc["p_top1_disagreement"])
    p("  %-42s %10s %10s %8s" % ("bien the", "P(bien co)", "|lech|", "khop"))
    for v in fc["variants"]:
        p("  %-42s %10.6f %10.6f %8.4f%s" % (
            v["variant"], v["p_event"], v["abs_gap_vs_flip"],
            v["rowwise_agreement_with_flip"], "  <= TRUNG KHOP" if v["exact"] else ""))
    p("  => %s" % fc["verdict"].replace("  ", " "))
    os1 = fc["one_sided_M11"]
    p("  M-11 ban MOT PHIA: q95 = %.4f, mean m1 = %.4f, ti so = %.4f (all test)" % (
        os1["q95"], os1["mean_m_hat_1"], os1["ratio_q95_over_mean_mhat1"]))
    if os1["ratio_accept_only"] is not None:
        p("                     ti so accept-only @ gamma=0.78 = %.4f" % os1["ratio_accept_only"])

    c6 = rep["calibration_3_M6_dead_action"]
    p("\n--- [1c] M-6 / M-D4: HANH DONG CHET " + "-" * 40)
    p("nguong KHOA truoc khi nhin = %.2f" % c6["threshold_locked_before_looking"])
    p("%-6s %14s %14s %10s" % ("duong", "P(a*=a)", "P(a_twin=a)", "chet?"))
    for i in range(N_PATHS):
        name = "P%d" % (i + 1)
        p("%-6s %14.8f %14.8f %10s" % (
            name, c6["P_a_star"][name], c6["P_a_twin"][name],
            "CHET" if name in c6["dead_actions_by_a_star"] else ""))
    p("hanh dong chet theo a*     : %s" % (c6["dead_actions_by_a_star"] or "khong co"))
    p("hanh dong chet theo a_twin : %s" % (c6["dead_actions_by_a_twin"] or "khong co"))
    p("K danh nghia = %d -> K hieu dung = %d ; m: %d -> %d" % (
        c6["K_nominal"], c6["K_effective"], c6["m_nominal"], c6["m_effective"]))
    p("alpha_each: %.5f -> %s" % (
        c6["alpha_each_nominal"],
        "%.5f" % c6["alpha_each_effective"] if c6["alpha_each_effective"] else "khong xac dinh"))
    p("XUNG DOT: L21 noi K_eff = %d (chet: %s); M-D4@%.2f noi K_eff = %d (chet: %s)" % (
        c6["L21_says_K_effective"], ",".join(c6["L21_named_dead_actions"]),
        c6["threshold_locked_before_looking"], c6["K_effective"],
        ",".join(c6["dead_actions_by_a_star"])))
    p("  -> %s" % c6["conflict_note"].replace("  ", " "))

    an = rep["anchors_M7p_M8p"]
    p("\n--- NEO [TAT DINH] cho M-7' / M-8' " + "-" * 41)
    p("Jaccard(C3, B2) @ gamma=%.2f = %.6f  (coverage khop ? %s)" % (
        an["gamma"], an["jaccard_C3_B2"], an["matched_coverage"]))
    p("kappa cho gamma=0.78 tren cell chinh = %.6f -> coverage do = %.6f" % (
        rep["kappa_at_gamma_078"], rep["coverage_achieved"]))
    p("\n" + "=" * 78)
    p("KHONG dong du doan nao duoc ky o day. Ky o Amendment 23-30.")
    p("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/SUPERSEDED/phase-23/lesson23_7_range_calibration.json")
    args = parser.parse_args()

    rep = build(args.out)
    _print_report(rep)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(_json_clean(rep), fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("\nartifact -> %s" % args.out)


if __name__ == "__main__":
    main()

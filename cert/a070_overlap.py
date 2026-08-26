#!/usr/bin/env python3
"""A070b -- nhanh OVERLAP: go `L92` bang thiet ke, khong bang hoi quy.

Ky truoc o: docs/phase-23/A070b-amendment-70b.md   (M-222, M-223, M-224, NC-W-1)
Gate       : G23-285, G23-286, G23-287, G23-288

Vi sao module MOI thay vi sua `recalibrate_transfer.py`:
    `recalibrate_transfer.py` da sinh `recalibrate_transfer.json` -- mot
    artifact DA KY (G23-261..269). Sua no lam artifact cu khong tai tao
    duoc nguyen trang. Day la cung quy tac custody da dung o
    `cert/taxonomy_audit.py` (khong sua `conditioning_audit.py`) va o
    `cert/a070_extension.py`. Khi can phep do MOI tren du lieu CU, viet
    script moi doc cung du lieu.

Pham vi `N_GRID`:
    Chi (250, 500). Day la DUNG hai muc `A070b` ky (M-222 @250,
    M-223/224 @500), KHONG phai mot toi uu hoa. He qua: khong co duong
    `n*` cho cell moi -- ghi o `L116`.

    python -m cert.a070_overlap --cost-probe     # do chi phi TRUOC
    python -m cert.a070_overlap --run
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import a070_extension as EXT
from cert import recalibrate_transfer as RT
from cert import recalibration_cost as RC
from cert import transfer_matrix as TM
from cert.build_calib_set_v3 import AOI_V7, Z_EDGES_V7
from cert.cell_matrices import git, json_clean, pin
from measurements.validity import validity_block

AMENDMENT = "docs/phase-23/A070b-amendment-70b.md"
PREREG_TAG = "lesson-23-22d-a-prereg"
OUTPUT = "results/LIVE/phase-23/a070_overlap.json"
W_ALLOWLIST = "results/LIVE/phase-23/a070_window_allowlist.json"

# Manifest 32 cell cua `A070` la con tro DUY NHAT phu du CA 15 cell cua
# LIVE-15 (8 cu + 3 A069 + 4 W). Da doi chieu 2026-08-26: du ca 15.
SLA_MANIFEST = (
    "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_32cells_A070.json"
)

# --- Tap cell (A070b muc 2) ------------------------------------------------
OLD_LIVE_8 = ("h2@0.650", "h2@0.675", "h2@0.700",
              "poisson@0.850", "poisson@0.875", "poisson@0.900",
              "poisson@0.925", "poisson@0.960")
NEW_LIVE_3 = EXT.NEW_LIVE                       # h2@0.740, poisson@0.780, poisson@0.820
OVERLAP_4 = ("poisson@0.744", "h2@0.744", "poisson@0.750", "h2@0.750")
LIVE_15 = tuple(OLD_LIVE_8) + tuple(NEW_LIVE_3) + tuple(OVERLAP_4)
OVERLAP_RHOS = (0.744, 0.750)

# --- Tham so: KE THUA nguyen tu RT, khong dinh nghia lai -------------------
A_STAR = RT.A_STAR                # 0.42679
ALPHA = RT.ALPHA_FAMILY           # 0.10
ACCEPT_FLOOR = RT.ACCEPT_FLOOR    # 0.20
N_MAIN = RT.N_MAIN                # 250 -- M-222
N_FULL = RT.N_FULL                # 500 -- M-223, M-224
N_GRID = (N_MAIN, N_FULL)
SEED = RT.SEED                    # 232301
SEED_NCW = 232301                 # A070b muc 3, NC-W-1
NCW_DIAG_DRAWS = 200              # CHAN DOAN, khong cham diem

# --- Dai da ky (A070b muc 3). KHONG duoc doi -- test ghim bang so nguon ----
PRED = {
    "M-222": {"min_pairs": 2, "n": N_MAIN,
              "viol_max": 0.10, "acc_min": ACCEPT_FLOOR},
    "M-223": {"slope_lo": 0.40, "slope_hi": 0.62,
              "coef_max": 0.02, "dr2_max": 0.02, "spearman_min": 0.90,
              "n": N_FULL},
    "M-224": {"resid_gap_max": 0.02, "n": N_FULL},
}


# ---------------------------------------------------------------------------
# Nap cell -- BA ho duong dan
# ---------------------------------------------------------------------------

def _w_path(cell: str) -> str:
    mode, rho = cell.split("@")
    return ("results/LIVE/phase-21R/calib_set_%s_%.3f_U3_measured_v7_A070W.parquet"
            % (mode, float(rho)))


def load_any_cell(cell: str) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """8 cell cu -> TM.load_cell; 3 cell A069 -> EXT; 4 cell W -> A070W."""
    if cell in OVERLAP_4:
        path = _w_path(cell)
        if not os.path.exists(path):
            raise FileNotFoundError(
                "thieu parquet A070W: %s -- chay `python -m tools.a070_window "
                "--build` truoc" % path)
        frame = pd.read_parquet(path)
        return (frame[frame["is_calib"]].reset_index(drop=True),
                frame[~frame["is_calib"]].reset_index(drop=True), path)
    return EXT.load_any_cell(cell)


def _family(cell: str) -> str:
    return cell.split("@")[0]


def _rho(cell: str) -> float:
    return float(cell.split("@")[1])


# ---------------------------------------------------------------------------
# kappa_A -- 8 cu tu RT, 3 moi tu a069_pilot, 4 W GIAI TAI CHO
# ---------------------------------------------------------------------------

def build_kappa(cells: Sequence[str]) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """`kappa_A` cho ca 15 cell.

    Bon cell W chua tung co `kappa_A` -- no KHONG thuoc allowlist `A070`
    muc 2.2, nen no VAN MU (`A070b` muc 0.2). Giai bang `RT.solve_kappa`
    tai `a* = A_STAR`, dung DUNG duong ong da dung cho 11 cell kia.
    """
    kappa = dict(EXT.load_all_kappa(list(OLD_LIVE_8) + list(NEW_LIVE_3)))
    detail: Dict[str, Any] = {"solved_here": {}}
    for cell in OVERLAP_4:
        calib, _test, path = load_any_cell(cell)
        sol = RT.solve_kappa(calib, target=A_STAR)
        kappa[cell] = float(sol["kappa_A"])
        detail["solved_here"][cell] = {
            "kappa_A": float(sol["kappa_A"]),
            "acceptance_at_kappa_A": float(sol["acceptance_at_kappa_A"]),
            "bracketed": bool(sol["bracketed"]),
            "converged_on_acceptance": bool(sol["converged_on_acceptance"]),
            "qhat_source": sol["qhat_source"],
            "qhat_has_infinite": bool(sol["qhat_has_infinite"]),
            "qhat_at_sample_max": bool(sol["qhat_at_sample_max"]),
            "n_calib_blocks": int(calib["block_id"].nunique()),
            "parquet": pin(path),
            # `trace` CO Y KHONG GHI: `L113` do duoc rang in `trace` lam
            # mot du doan mat tinh mu vinh vien.
        }
        del calib, _test
    missing = [c for c in cells if c not in kappa]
    if missing:
        raise RuntimeError("thieu kappa_A: %s" % missing)
    return {c: float(kappa[c]) for c in cells}, detail


# ---------------------------------------------------------------------------
# Ma tran -- CRN, tap block chi phu thuoc (B, n, draw)
# ---------------------------------------------------------------------------

def run_matrix(cells: Sequence[str], kappa: Mapping[str, float]
               ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    paths: Dict[str, Any] = {}
    for b in cells:
        calib_B, test_B, path = load_any_cell(b)
        paths[b] = pin(path)
        tv = RT.prepare_test(test_B)
        rng = np.random.default_rng(SEED)
        n_all = int(calib_B["block_id"].nunique())
        for n in N_GRID:
            draws = 1 if int(n) >= n_all else RT.N_DRAWS
            for d in range(draws):
                sub = RC.subsample_blocks(calib_B, int(n), rng)
                for a in cells:
                    r = RT.run_one(sub, tv, kappa[a], matched=False)
                    r.update({"A": a, "B": b, "n": int(n), "draw": int(d),
                              "branch": "overlap",
                              "same_family": _family(a) == _family(b),
                              "same_rho": _rho(a) == _rho(b)})
                    rows.append(r)
                del sub
        del calib_B, test_B, tv
    return rows, paths


def cells_at_n(rows: Sequence[Mapping[str, Any]], n: int
               ) -> Dict[Tuple[str, str], Dict[str, float]]:
    return RT.cells_at_n(rows, int(n))


# ---------------------------------------------------------------------------
# Hoi quy toi thieu -- tu viet, khong keo statsmodels vao
# ---------------------------------------------------------------------------

def _ols(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
    """Tra (he so, R^2). X da co cot hang so."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return beta, r2


def _spearman(x: Sequence[float], y: Sequence[float]) -> float:
    a, b = np.asarray(x, np.float64), np.asarray(y, np.float64)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return float("nan")
    ra = pd.Series(a[ok]).rank().to_numpy()
    rb = pd.Series(b[ok]).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def _records(pairs: Sequence[Tuple[str, str]], kappa: Mapping[str, float],
             cells: Mapping[Tuple[str, str], Mapping[str, float]]
             ) -> List[Dict[str, Any]]:
    """Mot hang cho moi cap co huong CO acceptance huu han."""
    out: List[Dict[str, Any]] = []
    for a, b in pairs:
        cell = cells.get((a, b))
        if cell is None:
            continue
        acc = cell["C3_acceptance_test"]
        if not np.isfinite(acc):
            continue
        out.append({
            "A": a, "B": b,
            "lev": float(abs(np.log(kappa[a] / kappa[b]))),
            "dev": float(abs(acc - A_STAR)),
            "same": 1.0 if _family(a) == _family(b) else 0.0,
            "acceptance": float(acc),
            "rho_A": _rho(a), "rho_B": _rho(b),
            "same_rho": _rho(a) == _rho(b),
        })
    return out


def _cols(recs: Sequence[Mapping[str, Any]], key: str) -> np.ndarray:
    return np.asarray([r[key] for r in recs], np.float64)


# ---------------------------------------------------------------------------
# Cham diem
# ---------------------------------------------------------------------------

def score_m222(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Nang luc cap GIUA HO tai CUNG rho, tren OVERLAP-4, n = 250."""
    p = PRED["M-222"]
    cells = cells_at_n(rows, p["n"])
    ok, detail = [], []
    for a in OVERLAP_4:
        for b in OVERLAP_4:
            if a == b or _family(a) == _family(b) or _rho(a) != _rho(b):
                continue                       # chi cap GIUA HO, CUNG rho
            c = cells.get((a, b))
            if c is None:
                continue
            viol, acc = c["C3_viol_given_accept"], c["C3_acceptance_test"]
            hit = bool(np.isfinite(viol) and viol <= p["viol_max"]
                       and np.isfinite(acc) and acc >= p["acc_min"])
            detail.append({"A": a, "B": b, "rho": _rho(a),
                           "viol_given_accept": float(viol),
                           "acceptance": float(acc), "usable": hit})
            if hit:
                ok.append((a, b))
    return {
        "n_pairs_total": len(detail), "n_pairs_usable": len(ok),
        "threshold": p["min_pairs"],
        "hit": bool(len(ok) >= p["min_pairs"]),
        "pairs": detail,
        "note": ("MU: `kappa_A` cua 4 cell W chua tung duoc in "
                 "(`A070b` muc 0.2)"),
    }


def score_m223(rows: Sequence[Mapping[str, Any]], kappa: Mapping[str, float]
               ) -> Dict[str, Any]:
    """`M-210` nguyen van tren LIVE-15, n = 500, moi o ngoai duong cheo."""
    p = PRED["M-223"]
    cells = cells_at_n(rows, p["n"])
    pairs = [(a, b) for a in LIVE_15 for b in LIVE_15 if a != b]
    recs = _records(pairs, kappa, cells)
    lev, dev, same = _cols(recs, "lev"), _cols(recs, "dev"), _cols(recs, "same")
    n = len(dev)

    X1 = np.column_stack([np.ones(n), lev])
    b1, r2_1 = _ols(X1, dev)
    X2 = np.column_stack([np.ones(n), lev, same])
    b2, r2_2 = _ols(X2, dev)

    slope, coef_same, dr2 = float(b1[1]), float(b2[2]), float(r2_2 - r2_1)
    rho_s = _spearman(lev, dev)

    a_ok = bool(p["slope_lo"] <= slope <= p["slope_hi"])
    b_ok = bool(abs(coef_same) <= p["coef_max"] and abs(dr2) <= p["dr2_max"])
    c_ok = bool(rho_s >= p["spearman_min"])
    return {
        "n": p["n"],
        "n_cells": len(LIVE_15),
        "n_off_diagonal": int(n),
        "n_same_family": int(same.sum()),
        "intercept": float(b1[0]),
        "slope": slope,
        "slope_band": [p["slope_lo"], p["slope_hi"]],
        "coef_same_family": coef_same,
        "coef_band_abs": p["coef_max"],
        "delta_r2": dr2,
        "delta_r2_band_abs": p["dr2_max"],
        "r2_without_family": float(r2_1),
        "r2_with_family": float(r2_2),
        "spearman": rho_s,
        "spearman_min": p["spearman_min"],
        "hit_a_slope": a_ok,
        "hit_b_family_null": b_ok,
        "hit_c_spearman": c_ok,
        "hit": bool(a_ok and b_ok and c_ok),
        # mo hinh (a) -- `M-224` tru chinh mo hinh nay
        "model_a_intercept_slope": [float(b1[0]), float(b1[1])],
        "pairs": recs,
    }


def score_m224(rows: Sequence[Mapping[str, Any]], kappa: Mapping[str, float],
               model_a: Sequence[float]) -> Dict[str, Any]:
    """Doi chieu CUNG-RHO tren OVERLAP-4, tach theo tung rho.

    DOC SPEC -- `A070b` muc 3 viet "tach theo tung rho thuoc {0.744, 0.750}"
    roi "so giua cap CUNG HO va cap KHAC HO". Hai cach doc:

      R1 CHAT   rho_A == rho_B == rho.  OVERLAP-4 chi co MOT cell moi ho tai
                moi rho, nen so cap CUNG HO = 0 -> KHONG cham duoc.
      R2 PHAN TANG  tach theo `rho_B`; A chay khap OVERLAP-4.  Moi tang co
                6 cap (2 cung ho, 4 khac ho) -> cham duoc.

    Cham theo R2 vi do la cach doc DUY NHAT cho ra mot phep do; R1 duoc
    tinh va in KEM de nguoi doc thay chinh xac vi sao no rong. Viec chon
    cach doc nay duoc ghi o `L115`.
    """
    p = PRED["M-224"]
    cells = cells_at_n(rows, p["n"])
    pairs = [(a, b) for a in OVERLAP_4 for b in OVERLAP_4 if a != b]
    recs = _records(pairs, kappa, cells)
    b0, b1 = float(model_a[0]), float(model_a[1])
    for r in recs:
        r["residual"] = float(r["dev"] - (b0 + b1 * r["lev"]))

    by_rho: Dict[str, Any] = {}
    gaps = []
    for rho in OVERLAP_RHOS:
        grp = [r for r in recs if r["rho_B"] == rho]
        cross = [r["residual"] for r in grp if r["same"] == 0.0]
        sameh = [r["residual"] for r in grp if r["same"] == 1.0]
        med_c = float(np.median(cross)) if cross else float("nan")
        med_s = float(np.median(sameh)) if sameh else float("nan")
        gap = float(abs(med_c - med_s))
        gaps.append(gap)
        by_rho["%.3f" % rho] = {
            "n_pairs": len(grp),
            "n_cross_family": len(cross), "n_same_family": len(sameh),
            "median_residual_cross_family": med_c,
            "median_residual_same_family": med_s,
            "abs_gap": gap,
            "within_band": bool(np.isfinite(gap) and gap <= p["resid_gap_max"]),
        }

    # R1 CHAT -- in ra de chung minh no rong, khong de cham diem
    strict = [r for r in recs if r["same_rho"]]
    strict_note = {
        "n_pairs": len(strict),
        "n_same_family": int(sum(1 for r in strict if r["same"] == 1.0)),
        "n_cross_family": int(sum(1 for r in strict if r["same"] == 0.0)),
        "scoreable": False,
        "why": ("OVERLAP-4 co dung MOT cell moi ho tai moi rho, nen khi ep "
                "rho_A == rho_B thi so cap CUNG HO bang 0 va phep so khong "
                "co ve thu hai. Xem `L115`."),
    }

    scoreable = all(np.isfinite(g) for g in gaps) and len(gaps) == len(OVERLAP_RHOS)
    return {
        "n": p["n"],
        "reading": "R2_phan_tang_theo_rho_B",
        "reading_alternatives_considered": ["R1_chat_rho_A_eq_rho_B", "R2_phan_tang_theo_rho_B"],
        "band_abs": p["resid_gap_max"],
        "model_a_intercept_slope": [b0, b1],
        "by_rho": by_rho,
        "scoreable": bool(scoreable),
        "hit": bool(scoreable and all(v["within_band"] for v in by_rho.values())),
        "strict_same_rho_reading": strict_note,
        "pairs": recs,
    }


def score_nc_w_1(m223: Mapping[str, Any]) -> Dict[str, Any]:
    """Doi chung AM: thay bien ho tai bang NHAN NGAU NHIEN cung ti le.

    `M-223`(b) la mot kiem dinh gia thuyet KHONG -- muon he so GAN 0. Nhung
    "gan 0" la ket qua mac dinh cua MOI bien vo dung. Neu mot nhan ngau
    nhien CUNG roi vao dai da ky thi ve (b) khong phan biet duoc gi va
    KHONG duoc trich dan. Cung hinh dang `L99`/`NC-B3-1`.
    """
    p = PRED["M-223"]
    recs = m223["pairs"]
    lev, dev, same = _cols(recs, "lev"), _cols(recs, "dev"), _cols(recs, "same")
    n = len(dev)
    X1 = np.column_stack([np.ones(n), lev])
    _b1, r2_1 = _ols(X1, dev)

    def _fit(labels: np.ndarray) -> Tuple[float, float]:
        X2 = np.column_stack([np.ones(n), lev, labels])
        b2, r2_2 = _ols(X2, dev)
        return float(b2[2]), float(r2_2 - r2_1)

    # -- ve DA KY: mot rut tham, seed 232301
    rng = np.random.default_rng(SEED_NCW)
    shuffled = same.copy()
    rng.shuffle(shuffled)
    coef, dr2 = _fit(shuffled)
    in_band = bool(abs(coef) <= p["coef_max"] and abs(dr2) <= p["dr2_max"])

    # -- CHAN DOAN (khong cham diem): phan bo tren nhieu rut tham
    rng2 = np.random.default_rng(SEED_NCW)
    coefs, dr2s = [], []
    for _ in range(NCW_DIAG_DRAWS):
        lab = same.copy()
        rng2.shuffle(lab)
        c, d = _fit(lab)
        coefs.append(c)
        dr2s.append(d)
    coefs_a, dr2s_a = np.asarray(coefs), np.asarray(dr2s)
    share_in_band = float(np.mean((np.abs(coefs_a) <= p["coef_max"])
                                  & (np.abs(dr2s_a) <= p["dr2_max"])))

    return {
        "n": p["n"],
        "seed": SEED_NCW,
        "n_labels_true": int(same.sum()),
        "n_pairs": int(n),
        "random_label_coef": coef,
        "random_label_delta_r2": dr2,
        "coef_band_abs": p["coef_max"],
        "delta_r2_band_abs": p["dr2_max"],
        "random_label_in_signed_band": in_band,
        # FIRE = doi chung KEU = nhan ngau nhien cung "khong co suc giai
        # thich" => ve (b) khong phan biet duoc gi.
        "fires": in_band,
        "m223_b_citable": bool(not in_band),
        "diagnostic_not_scored": {
            "draws": NCW_DIAG_DRAWS,
            "share_in_signed_band": share_in_band,
            "coef_abs_median": float(np.median(np.abs(coefs_a))),
            "coef_abs_p95": float(np.percentile(np.abs(coefs_a), 95)),
            "delta_r2_abs_median": float(np.median(np.abs(dr2s_a))),
            "delta_r2_abs_p95": float(np.percentile(np.abs(dr2s_a), 95)),
            "note": ("phan bo nay KHONG thuoc dai da ky; no chi cho biet mot "
                     "rut tham don le co dai dien khong"),
        },
        "true_label_coef": float(m223["coef_same_family"]),
        "true_label_delta_r2": float(m223["delta_r2"]),
    }


# ---------------------------------------------------------------------------
# Chay
# ---------------------------------------------------------------------------

def cost_probe() -> Dict[str, Any]:
    """Do chi phi TRUOC khi chay -- `L110`: gia dinh 1800s/cell da sai 204 lan."""
    cell = OVERLAP_4[0]
    t0 = time.time()
    calib, test, path = load_any_cell(cell)
    t_load = time.time() - t0
    t0 = time.time()
    tv = RT.prepare_test(test)
    t_prep = time.time() - t0
    rng = np.random.default_rng(SEED)
    sub = RC.subsample_blocks(calib, N_MAIN, rng)
    t0 = time.time()
    RT.run_one(sub, tv, 1.0, matched=False)
    t_250 = time.time() - t0
    t0 = time.time()
    RT.run_one(calib, tv, 1.0, matched=False)
    t_500 = time.time() - t0
    t0 = time.time()
    RT.solve_kappa(calib, target=A_STAR)
    t_kappa = time.time() - t0

    n_250 = len(LIVE_15) * RT.N_DRAWS * len(LIVE_15)
    n_500 = len(LIVE_15) * 1 * len(LIVE_15)
    total = (n_250 * t_250 + n_500 * t_500
             + len(OVERLAP_4) * t_kappa + len(LIVE_15) * (t_load + t_prep))
    return {
        "probe_cell": cell, "parquet": path,
        "seconds_load": t_load, "seconds_prepare_test": t_prep,
        "seconds_run_one_n250": t_250, "seconds_run_one_n500": t_500,
        "seconds_solve_kappa": t_kappa,
        "n_run_one_n250": n_250, "n_run_one_n500": n_500,
        "n_solve_kappa": len(OVERLAP_4),
        "projected_total_seconds": float(total),
        "projected_total_hours": float(total / 3600.0),
    }


def run() -> Dict[str, Any]:
    with open(W_ALLOWLIST, "r", encoding="utf-8") as fh:
        allow = json.load(fh)
    common = [float(x) for x in allow["scores"]["M_215"]["common_alive_rho"]]
    if sorted(common) != sorted(OVERLAP_RHOS):
        raise RuntimeError(
            "cua so chong lan da doi: allowlist ghi %s, OVERLAP_RHOS = %s"
            % (common, list(OVERLAP_RHOS)))

    kappa, kappa_detail = build_kappa(LIVE_15)
    rows, paths = run_matrix(LIVE_15, kappa)

    m222 = score_m222(rows)
    m223 = score_m223(rows, kappa)
    # STOP-RULE A070b: `M-222` MISS -> `M-224` NOT_RUN co ly do. `M-223` VAN
    # chay vi no dung LIVE-15 chu khong chi OVERLAP-4. Stop-rule gan TUNG
    # du doan, theo `L109`.
    if m222["hit"]:
        m224 = score_m224(rows, kappa, m223["model_a_intercept_slope"])
        m224["not_run"] = False
    else:
        m224 = {
            "not_run": True,
            "hit": False,
            "reason": ("STOP-RULE A070b: `M-222` MISS (%d/%d cap giua ho dung "
                       "duoc, can >= %d) -- khong du cap giua ho de doi chieu"
                       % (m222["n_pairs_usable"], m222["n_pairs_total"],
                          PRED["M-222"]["min_pairs"])),
        }
    ncw1 = score_nc_w_1(m223)

    return {
        "schema": "dt4n.a070_overlap.v1",
        "lesson": "23.22d",
        "branch": "A070b-overlap",
        "amendment": AMENDMENT,
        "prereg_tag": PREREG_TAG,
        "cells_overlap_4": list(OVERLAP_4),
        "cells_live_15": list(LIVE_15),
        "overlap_rhos": list(OVERLAP_RHOS),
        "kappa_A": {k: float(v) for k, v in kappa.items()},
        "kappa_detail": kappa_detail,
        "config": {
            "a_star": A_STAR, "alpha_family": ALPHA,
            "acceptance_floor": ACCEPT_FLOOR,
            "n_grid": list(N_GRID), "n_draws": RT.N_DRAWS, "seed": SEED,
            "n_grid_note": ("chi (250, 500) -- DUNG hai muc A070b ky. He qua: "
                            "khong co duong `n*` cho cell moi; xem `L116`"),
        },
        "predictions": {"M_222": m222, "M_223": m223, "M_224": m224},
        "controls": {"NC_W_1": ncw1},
        "gates": {"G23-285": "M_222", "G23-286": "M_223",
                  "G23-287": "M_224", "G23-288": "NC_W_1"},
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=RT.W_LOSS,
        ),
        "provenance": {
            "script": "cert/a070_overlap.py::run",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
            "window_allowlist": pin(W_ALLOWLIST),
            "sla_manifest": pin(SLA_MANIFEST),
            "cell_parquet": paths,
        },
    }


def _write(path: str, out: Mapping[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(json_clean(out), fh, indent=1, sort_keys=True)


def print_run(out: Mapping[str, Any]) -> None:
    p, c = out["predictions"], out["controls"]
    m222, m223, m224, nc = p["M_222"], p["M_223"], p["M_224"], c["NC_W_1"]
    print("M-222 [G23-285]: %s  %d/%d cap giua ho dung duoc (can >= %d)" % (
        m222["hit"], m222["n_pairs_usable"], m222["n_pairs_total"],
        m222["threshold"]))
    for pr in m222["pairs"]:
        print("        %-14s -> %-14s rho=%.3f  viol=%.4f  acc=%.4f  %s" % (
            pr["A"], pr["B"], pr["rho"], pr["viol_given_accept"],
            pr["acceptance"], "OK" if pr["usable"] else "--"))
    print("M-223 [G23-286]: %s  slope=%.4f %s | coef_ho=%+.5f dR2=%+.5f %s | "
          "Spearman=%+.4f %s  (n_off=%d)" % (
              m223["hit"], m223["slope"], "OK" if m223["hit_a_slope"] else "--",
              m223["coef_same_family"], m223["delta_r2"],
              "OK" if m223["hit_b_family_null"] else "--",
              m223["spearman"], "OK" if m223["hit_c_spearman"] else "--",
              m223["n_off_diagonal"]))
    if m224.get("not_run"):
        print("M-224 [G23-287]: NOT_RUN  %s" % m224["reason"])
    else:
        print("M-224 [G23-287]: %s  (doc theo %s)" % (m224["hit"], m224["reading"]))
        for rho, v in sorted(m224["by_rho"].items()):
            print("        rho=%s  khac_ho=%+.5f (n=%d)  cung_ho=%+.5f (n=%d)"
                  "  |chenh|=%.5f  %s" % (
                      rho, v["median_residual_cross_family"], v["n_cross_family"],
                      v["median_residual_same_family"], v["n_same_family"],
                      v["abs_gap"], "OK" if v["within_band"] else "VUOT"))
    print("NC-W-1 [G23-288]: FIRE=%s  nhan ngau nhien coef=%+.5f dR2=%+.5f "
          "-> M-223(b) %s" % (
              nc["fires"], nc["random_label_coef"], nc["random_label_delta_r2"],
              "TRICH DAN DUOC" if nc["m223_b_citable"] else "KHONG duoc trich dan"))
    print("        chan doan (%d rut tham): %.1f%% roi trong dai da ky" % (
        nc["diagnostic_not_scored"]["draws"],
        100.0 * nc["diagnostic_not_scored"]["share_in_signed_band"]))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--cost-probe", action="store_true")
    group.add_argument("--run", action="store_true")
    ap.add_argument("--out", default=OUTPUT)
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.cost_probe:
        probe = cost_probe()
        for k, v in probe.items():
            print("   %-28s %s" % (k, v))
        return 0
    if not args.run:
        raise AssertionError("phai chon --cost-probe hoac --run")
    out = run()
    _write(args.out, out)
    print_run(out)
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

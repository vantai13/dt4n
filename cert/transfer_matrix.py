#!/usr/bin/env python3
"""Lesson 23.22 / Task B -- ma tran chuyen giao C3 vs B2.

Cau hoi: khi CHE DO VAN HANH doi, dieu gi xay ra voi mot luat da hieu chuan o
che do cu?

    C3 :  chap nhan <=> m_hat_j / qhat_j >= kappa   -- TI SO
    B2 :  chap nhan <=> m_hat_1 >= c                -- NGUONG TUYET DOI

CA HAI deu can NHAN de hieu chuan. `s_pair_j` la ham cua `y_true` qua
`pair_scores` (`cert/simultaneous_score.py:82`), nen `qhat` cung can nhan --
xem `A066` muc 1.1, noi mot cau sai bi rut lai. Khac biet nam o BAN CHAT tham
so: `qhat` la mot PHAN VI (uoc luong, co yeu cau co mau da biet, co chung chi
mau-huu-han); `c` la mot tham so TU DO do bang tim kiem (khong co ca hai).

Va o THAM SO DUOC CHUYEN GIAO (`A066b`): C3 chuyen `kappa`, khong thu nguyen;
`qhat` la mot THONG KE cua phan phoi trien khai. B2 chuyen `c`, co thu nguyen
`cost_ms`. Thang that su doi rat lon giua cac cell: `qhat` cua ho poisson di
tu 1.05 (`rho=0.700`) den 62.34 (`rho=0.960`), tuc 59.6x.

KHONG dung `qhat` muon cho B2 de "so cho cong bang". B2 khong co phat bieu bao
phu; o TRONG trong bang `T3` CHINH LA ket qua (`A066` muc 3).

Chay:
    python -m cert.transfer_matrix --run
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
from cert.cell_matrices import ALPHA_FAMILY, git, json_clean, pin
from cert.taxonomy_audit import calib_path, live_region_flags

AMENDMENT = "docs/phase-23/A066-amendment-66.md"
AMENDMENT_B = "docs/phase-23/A066b-amendment-66b.md"
OUTPUT = "results/LIVE/phase-23/transfer_matrix.json"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Diem van hanh. KHONG chon theo du lieu Task B -- day la he qua cua `M-192`
# (`A065c`, ky truoc khi Task B ton tai): `kappa=0.5` la diem DUY NHAT trong
# luoi ma V-S co `min_blocks` trong [421, 490] >> san on dinh 59 tren CA 8 cell
# song. Tai `kappa=1`, 4/8 cell roi duoi san (`M-191`). Tai `kappa=2`, V-S
# khong chay -- no tra ve `qhat` cua V-N (`L95`).
KAPPA_OP = 0.50
POST_VARIANT = "selective"
MULTIPLICITY = "bonferroni"
MATCHED_ACCEPTANCE = CM.MATCHED_ACCEPTANCE      # (0.70, 0.50, 0.30, 0.15)
COVERAGE_TOL = 0.05
SCALE_NC3 = 2.0                                 # luy thua cua 2 -> nhan chinh xac
SEED_B1 = 23301                                 # `score_B1_random` mac dinh

# Chi doc nhung cot thuc su dung: parquet la 69 MB / cell x 12 cell.
NEEDED_COLS = (
    ["block_id", "z_bin", "m_hat_bin", "is_calib", "wrong"]
    + list(CM.SIM_COLS) + list(CM.MHAT_COLS)
    + ["m_true_1", "m_true_2", "m_true_3"]
)


# ---------------------------------------------------------------------------
# Tap cell va cac khoi cua ma tran
# ---------------------------------------------------------------------------

def cells_by_role() -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """8 cell SONG va 4 cell CHET, sinh TU artifact -- khong hard-code.

    Tieu chi A (`err_neo >= 0.05`) DA KY o amendment 23-62. Ghi tay danh sach
    nay la mo cua cho no lech khoi tieu chi ma khong ai biet.
    """
    f = live_region_flags()
    live = tuple(sorted(k for k, v in f.items() if v["A_err_neo_ge_0_05"]))
    dead = tuple(sorted(k for k, v in f.items() if not v["A_err_neo_ge_0_05"]))
    assert len(live) == 8 and len(dead) == 4, (live, dead)
    return live, dead


def _family(cell: str) -> str:
    return cell.split("@")[0]


def classify_pairs(cells: Sequence[str]) -> Dict[str, List[Tuple[str, str]]]:
    """Ba khoi cua ma tran, phan hoach hoan toan `len(cells)**2` o.

    Voi 8 cell song: 8 duong cheo + 26 trong ho + 30 giua ho = 64.
    `L92` van rang buoc: khoi GIUA HO NHAT THIET cung la "rho thap <-> rho
    cao", nen phat bieu duoc phep la "chuyen giao qua CHE DO VAN HANH", KHONG
    phai "qua HO TAI".
    """
    out: Dict[str, List[Tuple[str, str]]] = {
        "diagonal": [], "within_family": [], "cross_family": []}
    for a in cells:
        for b in cells:
            if a == b:
                out["diagonal"].append((a, b))
            elif _family(a) == _family(b):
                out["within_family"].append((a, b))
            else:
                out["cross_family"].append((a, b))
    return out


def load_cell(name: str) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    mode, rho = name.split("@")[0], float(name.split("@")[1])
    path = calib_path(mode, rho)
    if not os.path.exists(path):
        raise FileNotFoundError("thieu calib_set LIVE: %s" % path)
    df = pd.read_parquet(path, columns=NEEDED_COLS)
    return (df[df["is_calib"]].reset_index(drop=True),
            df[~df["is_calib"]].reset_index(drop=True), path)


def rescale(df: pd.DataFrame, scale: float) -> pd.DataFrame:
    """Nhan MOI dai luong thang chi phi voi `scale`.

    `m_hat` va `s` phai gian CUNG nhau -- do la dinh nghia cua "doi che do
    lam thang gian", va la dieu kien de `NC-3a` co nghia.
    """
    if float(scale) == 1.0:
        return df
    out = df.copy()
    for col in list(CM.MHAT_COLS) + list(CM.SIM_COLS):
        out[col] = out[col].to_numpy(np.float64) * float(scale)
    return out


# ---------------------------------------------------------------------------
# Hieu chuan tren cell A
# ---------------------------------------------------------------------------

def fit_on_A(calib_A: pd.DataFrame) -> Dict[str, Any]:
    """C3 hoc `qhat`; B2 do `c` de dat CUNG acceptance tren A.

    B2 duoc cho dieu kien TOT NHAT co the (`A066` muc 2.4): `c` duoc do de
    khop acceptance cua C3 tren chinh cell A. Neu B2 van troi khi chuyen sang
    B, do khong phai vi ta dat no o mot diem bat loi.
    """
    fit = CM.fit_config(calib_A, "C3", KAPPA_OP, alpha=ALPHA_FAMILY,
                        post_variant=POST_VARIANT, multiplicity=MULTIPLICITY)

    # `A066` muc 2.1: neu vong lap suy bien o vong 0 thi `qhat` chinh la cua
    # `none`, thu tuc DA DO LA VO (`M-187`). Khong duoc dan nhan `selective`
    # len no, va `M-192` noi dieu nay KHONG duoc xay ra tai `kappa=0.5`.
    if fit.get("qhat_source") == "degenerate_fallback_to_none":
        raise RuntimeError(
            "V-S suy bien o vong 0 tren cell hieu chuan -- `qhat` la cua "
            "`none` (`L95`). `M-192` noi dieu nay KHONG duoc xay ra tai "
            "kappa=%.2f. Kiem lai truoc khi chay tiep." % KAPPA_OP)

    keys = CM._keys(POST_VARIANT)
    n_cols = len(CM.SIM_COLS)
    q_rows_A = CM._q_rows(calib_A, keys, fit["_q"], n_cols)
    acc_A = float(CM._accept(calib_A, CM.MHAT_COLS, q_rows_A, KAPPA_OP).mean())

    # `c` = phan vi cua `m_hat_1` sao cho B2 chap nhan dung `acc_A`.
    m1 = calib_A["m_hat_1"].to_numpy(np.float64)
    c = float(np.quantile(m1, 1.0 - acc_A, method="higher"))
    # `c_B1` -- CUNG mot phep dat nguong, tren score ngau nhien (`NC-2`).
    b1 = BL.score_B1_random(calib_A, seed=SEED_B1)
    c_b1 = float(np.quantile(b1, 1.0 - acc_A, method="higher"))

    return {
        "qhat": fit["_q"],
        "qhat_source": fit.get("qhat_source"),
        "min_blocks_at_final_qhat": fit.get("min_blocks_at_final_qhat"),
        "min_blocks_floor": fit.get("min_blocks_floor"),
        "min_blocks_stable": fit.get("min_blocks_stable"),
        "qhat_at_sample_max": bool(fit.get("qhat_at_sample_max", False)),
        "kappa": KAPPA_OP,
        "c_B2": c,
        "c_B1": c_b1,
        "acceptance_on_A": acc_A,
        "degenerate": bool(fit.get("degenerate", False)),
        "converged": bool(fit.get("converged", False)),
    }


# ---------------------------------------------------------------------------
# Trien khai tren cell B -- ba thang
# ---------------------------------------------------------------------------

def deploy_on_B(fit_A: Mapping[str, Any], test_B: pd.DataFrame,
                scale: float = 1.0) -> Dict[str, Any]:
    """`scale != 1` chi dung cho `NC-3b` (mang nguyen `qhat_A`, khong hieu
    chuan lai). Nhanh bat bien that su la `NC-3a` -- xem `nc3_rescale_report`.
    """
    B = rescale(test_B, scale)
    keys = CM._keys(POST_VARIANT)
    n_cols = len(CM.SIM_COLS)

    q_rows = CM._q_rows(B, keys, fit_A["qhat"], n_cols)
    acc_c3 = CM._accept(B, CM.MHAT_COLS, q_rows, float(fit_A["kappa"]))
    acc_b2 = B["m_hat_1"].to_numpy(np.float64) >= float(fit_A["c_B2"])

    s = B[list(CM.SIM_COLS)].to_numpy(np.float64)
    viol_rows = (s > q_rows).any(axis=1)
    wrong = B["wrong"].to_numpy(bool)

    def _risk(mask: np.ndarray) -> float:
        return float(wrong[mask].mean()) if mask.any() else float("nan")

    # `T2` -- acceptance KHOP: ep ca hai cung ti le chap nhan roi so risk.
    sc3 = BL.score_C3(B, q_rows)
    sb2 = BL.score_B2_constant_gap(B)
    sb1 = BL.score_B1_random(B, seed=SEED_B1)
    matched: Dict[str, Dict[str, float]] = {}
    for t in MATCHED_ACCEPTANCE:
        matched["%.2f" % t] = {
            "err_C3": _risk(BL._accept_at_coverage(sc3, t)),
            "err_B2": _risk(BL._accept_at_coverage(sb2, t)),
        }

    # `NC-2`: doi chung DUONG. B1 phai duoc doi xu Y HET B2 -- mang mot NGUONG
    # do tren A sang B. Dung `_accept_at_coverage` o day se EP dung ti le chap
    # nhan cua A, khien drift = 0 DO DUNG chu khong do tinh chat cua B1, va
    # doi chung se noi mot dieu no khong duoc phep noi.
    acc_b1 = sb1 >= float(fit_A["c_B1"])

    return {
        # `T1` -- thang CHINH, ca hai deu co
        "T1_acceptance_C3": float(acc_c3.mean()),
        "T1_acceptance_B2": float(acc_b2.mean()),
        "T1_drift_C3": float(abs(acc_c3.mean() - fit_A["acceptance_on_A"])),
        "T1_drift_B2": float(abs(acc_b2.mean() - fit_A["acceptance_on_A"])),
        "T1_drift_B1": float(abs(acc_b1.mean() - fit_A["acceptance_on_A"])),
        # `T2` -- risk tai acceptance khop
        "T2_matched": matched,
        # `T3` -- CHI C3. B2 khong co `qhat` -> khong co phat bieu bao phu.
        #        O TRONG nay CHINH LA ket qua; khong nguy tao mot `qhat` cho B2.
        "T3_viol_given_accept_C3": (float(viol_rows[acc_c3].mean())
                                    if acc_c3.any() else float("nan")),
        "T3_viol_given_accept_B2": None,
        "T3_B2_has_no_coverage_claim": True,
        "n_accept_C3": int(acc_c3.sum()),
        "n_accept_B2": int(acc_b2.sum()),
        "n_rows_B": int(len(B)),
        "anchor_err_B": float(wrong.mean()),
        "err_given_accept_C3": _risk(acc_c3),
        "err_given_accept_B2": _risk(acc_b2),
        "scale": float(scale),
    }


# ---------------------------------------------------------------------------
# `NC-3` -- hai nhanh (amendment 23-66b)
# ---------------------------------------------------------------------------

def nc3_rescale_report(base: pd.DataFrame, big: pd.DataFrame) -> Dict[str, Any]:
    """Kiem CO CHE bat bien thang, tach lam hai nhanh.

    `NC-3a`  nhan CA calib va test roi HIEU CHUAN LAI. Tham so chuyen giao la
             `kappa`, khong thu nguyen -> `qhat -> lambda*qhat` tu dong ->
             acceptance TRUNG BIT. B2 mang nguyen `c` (co thu nguyen) -> doi.

    `NC-3b`  mang nguyen `qhat_A` va `c` sang che do da gian. CA HAI troi.
             Nhanh nay chan cach doc "C3 mien nhiem voi doi che do".

    `big` phai la `base` da nhan `SCALE_NC3` tren CA `m_hat_*` lan `s_pair_*`.
    """
    cal_0 = base[base["is_calib"]].reset_index(drop=True)
    tst_0 = base[~base["is_calib"]].reset_index(drop=True)
    cal_1 = big[big["is_calib"]].reset_index(drop=True)
    tst_1 = big[~big["is_calib"]].reset_index(drop=True)

    fit_0 = fit_on_A(cal_0)
    out_0 = deploy_on_B(fit_0, tst_0)

    # (a) hieu chuan LAI tren che do moi, chuyen giao `kappa`
    fit_1 = fit_on_A(cal_1)
    out_a = deploy_on_B(fit_1, tst_1)
    # B2 o nhanh (a) mang nguyen `c` do tren che do CU -- day moi la phep so
    # sanh ve THAM SO DUOC CHUYEN GIAO.
    acc_b2_a = float((tst_1["m_hat_1"].to_numpy(np.float64)
                      >= float(fit_0["c_B2"])).mean())

    # (b) mang nguyen `qhat_A` va `c`, KHONG hieu chuan lai
    out_b = deploy_on_B(fit_0, tst_1)

    return {
        "scale": float(SCALE_NC3),
        "acceptance_C3_original": out_0["T1_acceptance_C3"],
        "acceptance_B2_original": out_0["T1_acceptance_B2"],
        "NC3a_acceptance_C3_base": out_0["T1_acceptance_C3"],
        "NC3a_acceptance_C3_rescaled": out_a["T1_acceptance_C3"],
        "NC3a_acceptance_B2_rescaled": acc_b2_a,
        "NC3a_delta_acceptance_C3": float(
            abs(out_a["T1_acceptance_C3"] - out_0["T1_acceptance_C3"])),
        "NC3a_delta_acceptance_B2": float(
            abs(acc_b2_a - out_0["T1_acceptance_B2"])),
        "NC3b_acceptance_C3_rescaled": out_b["T1_acceptance_C3"],
        "NC3b_acceptance_B2_rescaled": out_b["T1_acceptance_B2"],
        "NC3b_delta_acceptance_C3": float(
            abs(out_b["T1_acceptance_C3"] - out_0["T1_acceptance_C3"])),
        "NC3b_delta_acceptance_B2": float(
            abs(out_b["T1_acceptance_B2"] - out_0["T1_acceptance_B2"])),
        "qhat_ratio_slot1": float(
            np.mean([float(fit_1["qhat"][k][0]) / float(fit_0["qhat"][k][0])
                     for k in fit_0["qhat"]])),
    }


# ---------------------------------------------------------------------------
# Cham du doan
# ---------------------------------------------------------------------------

def _median(xs: Sequence[float]) -> float:
    v = np.asarray([x for x in xs if np.isfinite(x)], dtype=np.float64)
    return float(np.median(v)) if v.size else float("nan")


def score_predictions(cellwise: Mapping[str, Mapping[str, Any]],
                      blocks: Mapping[str, Sequence[Tuple[str, str]]],
                      diag_reference: Mapping[str, Mapping[str, float]],
                      ) -> Dict[str, Any]:
    """`M-193` .. `M-196` va `M-190`, dung nguong da ky o `A066` muc 4/6."""
    def _rows(block: str) -> List[Dict[str, Any]]:
        return [cellwise["%s->%s" % ab] for ab in blocks[block]]

    # -- M-193: KIEM WIRING. Dap an da biet (`A066` muc 0.1): duong cheo phai
    #    TAI TAO hang `variant_sweep` @ kappa=0.5 cua `taxonomy_audit.json`.
    d_viol, d_acc, b2_off = [], [], []
    for a, _b in blocks["diagonal"]:
        r = cellwise["%s->%s" % (a, a)]
        ref = diag_reference.get(a)
        if ref is not None:
            d_viol.append(abs(r["T3_viol_given_accept_C3"] - ref["violation_given_accept"]))
            d_acc.append(abs(r["T1_acceptance_C3"] - ref["acceptance"]))
        b2_off.append(r["T1_drift_B2"])
    m193 = {
        "n_cells_checked": int(len(d_viol)),
        "max_abs_delta_violation_C3": float(max(d_viol)) if d_viol else float("nan"),
        "max_abs_delta_acceptance_C3": float(max(d_acc)) if d_acc else float("nan"),
        "max_B2_acceptance_offset": float(max(b2_off)) if b2_off else float("nan"),
        "hit": bool(d_viol and max(d_viol) <= 1e-9 and max(d_acc) <= 1e-9
                    and max(b2_off) <= 0.02),
        "label": "KIEM WIRING -- dap an da biet (A066 muc 0.1)",
    }

    # -- M-194: T1 giua ho, trung vi drift cua B2 >= 3x cua C3
    cross = _rows("cross_family")
    med_c3 = _median([r["T1_drift_C3"] for r in cross])
    med_b2 = _median([r["T1_drift_B2"] for r in cross])
    m194 = {
        "median_drift_C3": med_c3, "median_drift_B2": med_b2,
        "ratio_B2_over_C3": float(med_b2 / med_c3) if med_c3 > 0 else float("inf"),
        "n_cells": int(len(cross)),
        "hit": bool(med_c3 > 0 and med_b2 >= 3.0 * med_c3),
    }

    # -- M-195: T3 giua ho, C3 giu |viol - alpha| <= 0.05 o >= 20/30 o
    ok = [r for r in cross
          if np.isfinite(r["T3_viol_given_accept_C3"])
          and abs(r["T3_viol_given_accept_C3"] - ALPHA_FAMILY) <= COVERAGE_TOL]
    m195 = {
        "n_within_tol": int(len(ok)), "n_cells": int(len(cross)),
        "tol": COVERAGE_TOL, "alpha": ALPHA_FAMILY,
        "hit": bool(len(ok) >= 20),
        "label": "NGOAI SUY -- C3 KHONG co bao dam khi calib != test",
    }

    # -- M-196: T2 giua ho, trung vi |err_C3 - err_B2| tai acceptance khop
    gaps = [abs(v["err_C3"] - v["err_B2"])
            for r in cross for v in r["T2_matched"].values()
            if np.isfinite(v["err_C3"]) and np.isfinite(v["err_B2"])]
    m196 = {
        "median_abs_gap": _median(gaps), "n_points": int(len(gaps)),
        "hit": bool(np.isfinite(_median(gaps)) and _median(gaps) <= 0.02),
        "label": "KET QUA AM -- bao cao ngang hang voi M-194",
    }

    # -- M-190: bat doi xung. `L92`: chieu nay CUNG LA (rho cao -> rho thap),
    #    nen neu TRUNG thi KHONG duoc quy cho ho tai.
    p2h = _median([cellwise["%s->%s" % (a, b)]["T1_drift_C3"]
                   for a, b in blocks["cross_family"]
                   if _family(a) == "poisson" and _family(b) == "h2"])
    h2p = _median([cellwise["%s->%s" % (a, b)]["T1_drift_C3"]
                   for a, b in blocks["cross_family"]
                   if _family(a) == "h2" and _family(b) == "poisson"])
    m190 = {
        "median_drift_poisson_to_h2": p2h,
        "median_drift_h2_to_poisson": h2p,
        "hit": bool(np.isfinite(p2h) and np.isfinite(h2p) and p2h > h2p),
        "L92_warning": ("chieu poisson->h2 CUNG LA rho cao->rho thap; "
                        "trung KHONG duoc quy cho ho tai"),
    }

    # -- NC-2: doi chung DUONG (B1 ngau nhien)
    med_b1 = _median([r["T1_drift_B1"] for r in cross])
    nc2 = {
        "median_drift_B1": med_b1, "median_drift_B2": med_b2,
        "hit": bool(np.isfinite(med_b1) and med_b1 >= med_b2),
        "label": "neu B1 ~ C3 thi thang T1 khong phan biet duoc gi",
    }

    return {"M_193": m193, "M_194": m194, "M_195": m195, "M_196": m196,
            "M_190": m190, "NC_2": nc2}


def _diag_reference() -> Dict[str, Dict[str, float]]:
    """Hang V-S @ `kappa=0.5` cua `taxonomy_audit.json` -- dap an cua `M-193`.

    Duong cheo cua ma tran chuyen giao la DUNG BANG hang do: cung `fit_config`,
    cung `evaluate_config`, cung tach `is_calib`. Khai o `A066` muc 0.1.
    """
    path = os.path.join(REPO, "results/LIVE/phase-23/taxonomy_audit.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        art = json.load(fh)
    out: Dict[str, Dict[str, float]] = {}
    for c in art["cells"]:
        for r in c["variant_sweep"]:
            if r["post"] == POST_VARIANT and float(r["kappa"]) == KAPPA_OP:
                out[c["cell"]] = {
                    "acceptance": float(r["acceptance"]),
                    "violation_given_accept": float(r["violation_given_accept"]),
                }
    return out


# ---------------------------------------------------------------------------
# Chay
# ---------------------------------------------------------------------------

def _run_matrix(cells: Sequence[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Hai luot de khong giu 12 parquet 69 MB trong bo nho cung luc."""
    fits: Dict[str, Dict[str, Any]] = {}
    paths: Dict[str, Dict[str, Any]] = {}
    for name in cells:
        calib, _test, path = load_cell(name)
        fits[name] = fit_on_A(calib)
        paths[name] = pin(path)
        del calib

    cellwise: Dict[str, Any] = {}
    for b in cells:
        _calib, test, _path = load_cell(b)
        for a in cells:
            cellwise["%s->%s" % (a, b)] = deploy_on_B(fits[a], test)
        del test
    return cellwise, {"fits": fits, "parquet": paths}


def run() -> Dict[str, Any]:
    live, dead = cells_by_role()
    blocks = classify_pairs(live)

    cellwise, meta = _run_matrix(live)
    scored = score_predictions(cellwise, blocks, _diag_reference())

    # `NC-1` -- doi chung AM tren 4 cell chet. Neu thiet hai o day KHONG nho
    # thi cai do duoc o cell song la HIEN VAT cua duong ong. DUNG.
    dead_cellwise, _ = _run_matrix(dead)
    dead_off_diag = [v for k, v in dead_cellwise.items()
                     if k.split("->")[0] != k.split("->")[1]]
    nc1 = {
        "n_cells": int(len(dead_off_diag)),
        "median_drift_C3": _median([r["T1_drift_C3"] for r in dead_off_diag]),
        "median_drift_B2": _median([r["T1_drift_B2"] for r in dead_off_diag]),
    }
    nc1["hit"] = bool(nc1["median_drift_C3"] <= 0.05
                      and nc1["median_drift_B2"] <= 0.05)
    nc1["label"] = ("neu KHONG nho -> thiet hai o cell song la HIEN VAT cua "
                    "duong ong, khong phai hieu ung chuyen giao. DUNG.")

    # `NC-3a` / `NC-3b` tren cell duong cheo dau tien cua `live`.
    nc3_cell = sorted(live)[0]
    calib, test, _p = load_cell(nc3_cell)
    base = pd.concat([calib, test], ignore_index=True)
    nc3 = nc3_rescale_report(base, rescale(base, SCALE_NC3))
    nc3["cell"] = nc3_cell

    return {
        "schema": "dt4n.transfer_matrix.v1",
        "lesson": "23.22",
        "task": "B",
        "amendment": [AMENDMENT, AMENDMENT_B],
        "config": {
            "kappa_op": KAPPA_OP, "post_variant": POST_VARIANT,
            "multiplicity": MULTIPLICITY, "alpha_family": ALPHA_FAMILY,
            "matched_acceptance": list(MATCHED_ACCEPTANCE),
            "coverage_tol": COVERAGE_TOL, "scale_nc3": SCALE_NC3,
            "kappa_justification": (
                "M-192 (A065c): kappa=0.5 la diem duy nhat trong luoi ma V-S "
                "hop le VA on dinh tren ca 8 cell song. KHONG chon theo du "
                "lieu Task B."),
        },
        "cells_live": list(live),
        "cells_dead": list(dead),
        "blocks": {k: ["%s->%s" % ab for ab in v] for k, v in blocks.items()},
        "cellwise": cellwise,
        "predictions": scored,
        "NC_1_dead_cell_control": nc1,
        "NC_3_scale_invariance": nc3,
        "fits": {k: {kk: vv for kk, vv in v.items() if kk != "qhat"}
                 for k, v in meta["fits"].items()},
        "provenance": {
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
            "parquet": meta["parquet"],
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true", help="chay ca ma tran")
    ap.add_argument("--out", default=OUTPUT,
                    help="KHONG duoc mac dinh vao results/RAW hay "
                         "results/SUPERSEDED -- hai tang do da `chmod a-w` "
                         "(amendment 23-61, `L96`)")
    args = ap.parse_args(list(argv) if argv is not None else None)
    if not args.run:
        ap.error("can --run")
    out = run()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(json_clean(out), fh, indent=1, sort_keys=True)
    p = out["predictions"]
    print("M-193 wiring   : %s (max|dviol| = %.3e)"
          % (p["M_193"]["hit"], p["M_193"]["max_abs_delta_violation_C3"]))
    print("M-194 T1 cross : %s (B2/C3 = %.2fx)"
          % (p["M_194"]["hit"], p["M_194"]["ratio_B2_over_C3"]))
    print("M-195 T3 cross : %s (%d/%d trong dung sai)"
          % (p["M_195"]["hit"], p["M_195"]["n_within_tol"], p["M_195"]["n_cells"]))
    print("M-196 T2 cross : %s (trung vi |derr| = %.4f)"
          % (p["M_196"]["hit"], p["M_196"]["median_abs_gap"]))
    print("M-190 bat doi xung: %s" % p["M_190"]["hit"])
    print("NC-1 cell chet : %s | NC-2 B1: %s"
          % (out["NC_1_dead_cell_control"]["hit"], p["NC_2"]["hit"]))
    print("NC-3a dC3 = %.3e | NC-3b dC3 = %.4f"
          % (out["NC_3_scale_invariance"]["NC3a_delta_acceptance_C3"],
             out["NC_3_scale_invariance"]["NC3b_delta_acceptance_C3"]))
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

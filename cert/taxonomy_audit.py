#!/usr/bin/env python3
"""Lesson 23.22 / Task A0 -- do lai co so cua truc `m_hat` tren truc AoI da duyet.

Ban ke hoach `PHASE_23_v3.md` chi dinh bo truc `m_hat` khoi taxonomy Mondrian,
va trich `spread_z=2.1232 / spread_m=1.1188` lam co so. Hai so do do tren
`Z_EDGES_LEGACY`, truc DA BI THAY THE o amendment 23-49c (`L89`).

Module nay do lai co so tren truc `measured_v7_uniform`, va do them ba dai
luong ma `conditioning_audit` (Lesson 23.7) khong co:

  * tong dieu tra taxonomy song song HANG va BLOCK          -> M-181, M-182
  * chan doan tap trung cua hieu ung `m_hat` o o cao nhat    -> M-185
  * CI cua qhat bang paired block bootstrap                  -> M-186

Module KHONG sua `cert/conditioning_audit.py` (1400 dong): script do sinh
artifact cua mot lesson DA DONG, va sua no lam artifact cu khong tai tao duoc
nguyen trang -- vi pham quy tac custody dung o 23.21j. Khi can mot phep do MOI
tren du lieu CU, viet script moi doc cung du lieu; dung sua script da sinh ra
bang chung da ky.

Ba bien the chi khac nhau MOT tham so, vi `cert/config_matrix.py:111` da co:

    _keys(post) -> ["z_bin","m_hat_bin"] neu post=="mondrian", nguoc lai ["z_bin"]

Chay ba cell chinh:
    python -m cert.taxonomy_audit --run

Them chin cell robustness:
    python -m cert.taxonomy_audit --run --robustness

Ky truoc o: docs/phase-23/A064-amendment-64.md
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import config_matrix as CM
from cert.build_calib_set_v3 import AOI_V7, Z_EDGES_V7
from cert.cell_matrices import ALPHA_FAMILY, git, json_clean, pin
from measurements.validity import validity_block


AMENDMENT = "docs/phase-23/A064-amendment-64.md"
SLA_MANIFEST = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
CALIB_TEMPLATE = (
    "results/LIVE/phase-21R/calib_set_{mode}_{rho:.3f}_U3_measured_v7.parquet"
)
OUTPUT = "results/LIVE/phase-23/taxonomy_audit.json"

# Ba cell CHINH -- tien dang ky tu Lesson 23.7, khong doi.
MAIN_CELLS: Tuple[Tuple[str, float], ...] = (
    ("poisson", 0.925),
    ("poisson", 0.850),
    ("h2", 0.700),
)
# Chin cell ROBUSTNESS -- bao cao, khong dung de chon ket luan.
ROBUSTNESS_CELLS: Tuple[Tuple[str, float], ...] = (
    ("poisson", 0.700), ("poisson", 0.875), ("poisson", 0.900), ("poisson", 0.960),
    ("h2", 0.650), ("h2", 0.675), ("h2", 0.850), ("h2", 0.925), ("h2", 0.960),
)

VARIANTS: Tuple[str, ...] = ("mondrian", "none", "selective")
KAPPA_GRID: Tuple[float, ...] = (0.0, 0.25, 0.50, 1.00, 2.00)
KAPPA_OP = 1.00                 # diem van hanh chinh, ky truoc
N_BOOT = 2000
SEED_BOOT = 232200              # 23.22 -> 2322 -> 232200
W_LOSS = 5000.0

# Bang du doan da ky o amendment 23-64 muc 4. KHONG duoc doi trong code --
# `test_prediction_bands_match_signed_amendment` ghim chung.
PREDICTIONS: Dict[str, Dict[str, Any]] = {
    "M-181": {"lo": 440.0, "hi": 500.0, "what": "n_blocks tb moi o Mondrian"},
    "M-182": {"lo": 1.00,  "hi": 1.15,  "what": "ti so n_blocks (4 o)/(16 o)"},
    "M-183": {"lo": 1.45,  "hi": 1.70,  "what": "spread_z tren truc v7", "scored": False},
    "M-184": {"lo": 1.05,  "hi": 1.30,  "what": "spread_m tren truc v7"},
    "M-185": {"lo": 1.10,  "hi": 1.30,  "what": "qhat[m3]/mean(qhat[m0..m2])"},
    "M-186": {"lo": 0.50,  "hi": 1.00,  "what": "ti so do rong CI95 qhat (4 o)/(16 o)"},
}


def cell_name(mode: str, rho: float) -> str:
    return "%s@%.3f" % (str(mode), float(rho))


def calib_path(mode: str, rho: float) -> str:
    return CALIB_TEMPLATE.format(mode=str(mode), rho=float(rho))


# ---------------------------------------------------------------------------
# (1) Tong dieu tra taxonomy -- M-181, M-182
# ---------------------------------------------------------------------------

def taxonomy_census(calib: pd.DataFrame, keys: Sequence[str]) -> Dict[str, Any]:
    """Dem SONG SONG so hang va so BLOCK cho tung o cua mot taxonomy.

    Day la phep do truc tiep gia thuyet H-B. Duoi chia block, don vi
    exchangeability la BLOCK -- `cert/config_matrix.py::_qhat` dung
    `n_eff = sub["block_id"].nunique()`. Neu mot block trai qua nhieu gia tri
    z va m_hat (dieu ma AoI rang cua bao dam, vi T = 500 ms << block 5 s),
    thi gan nhu moi block cham moi o, va so BLOCK moi o gan bang TONG so
    block du so HANG moi o chi con 1/|o|.
    """
    keys = list(keys)
    grouped = calib.groupby(keys, sort=True)
    rows = grouped.size()
    blocks = grouped["block_id"].nunique()
    n_block_total = int(calib["block_id"].nunique())

    labels = ["|".join(str(int(x)) for x in (k if isinstance(k, tuple) else (k,)))
              for k in rows.index]
    n_rows = [int(v) for v in rows.to_numpy()]
    n_blocks = [int(v) for v in blocks.to_numpy()]

    return {
        "keys": keys,
        "n_cells": int(len(labels)),
        "n_block_total_calib": n_block_total,
        "n_rows_by_cell": dict(zip(labels, n_rows)),
        "n_blocks_by_cell": dict(zip(labels, n_blocks)),
        "n_rows_mean": float(np.mean(n_rows)),
        "n_blocks_mean": float(np.mean(n_blocks)),
        "n_blocks_min": int(np.min(n_blocks)),
        # Ti le block da cham: 1.0 nghia la moi o cham MOI block.
        "block_touch_ratio": float(np.mean(n_blocks) / max(n_block_total, 1)),
    }


# ---------------------------------------------------------------------------
# (2) Chan doan tap trung cua truc m_hat -- M-185
# ---------------------------------------------------------------------------

def mhat_concentration(q: Mapping[Any, np.ndarray]) -> Dict[str, Any]:
    """Hieu ung cua `m_hat` co deu tren bon o khong?

    `spread_m` cua `conditioning_audit` la max/min cua PROFILE BIEN -- trung
    binh qhat theo (z, slot) cho tung o m_hat. Mot hieu ung don tap trung o
    MOT dau bi trung binh lam nhoe di.

    Do o day: trong tung z_bin, ti so giua o m_hat cao nhat va trung binh ba
    o thap. Neu H-A dung, ti so nay > 1.10 trong khi `spread_m` ~ 1.12.
    """
    z_bins = sorted({int(k[0]) for k in q})
    m_bins = sorted({int(k[1]) for k in q if len(k) > 1})
    if len(m_bins) < 2:
        return {"applicable": False, "reason": "taxonomy khong co truc m_hat"}

    top, low = m_bins[-1], m_bins[:-1]
    per_z: Dict[str, float] = {}
    for z in z_bins:
        q_top = float(np.mean(q[(z, top)]))
        q_low = float(np.mean([np.mean(q[(z, m)]) for m in low]))
        per_z[str(z)] = float(q_top / max(q_low, 1e-12))

    values = np.asarray(list(per_z.values()), dtype=np.float64)
    low_profile = [float(np.mean([np.mean(q[(z, m)]) for z in z_bins])) for m in low]
    return {
        "applicable": True,
        "top_bin": int(top),
        "ratio_by_z_bin": per_z,
        "M_185_ratio_mean": float(values.mean()),
        "M_185_ratio_min": float(values.min()),
        "M_185_ratio_max": float(values.max()),
        # Doi chieu: bien thien GIUA ba o thap. Neu ~1.0 thi hieu ung
        # THUC SU chi nam o o cao nhat.
        "spread_among_low_bins": float(max(low_profile) / max(min(low_profile), 1e-12)),
    }


# ---------------------------------------------------------------------------
# (3) Do trai cua qhat theo truc z va m_hat -- M-183, M-184
# ---------------------------------------------------------------------------

def spread_profiles(q: Mapping[Any, np.ndarray]) -> Dict[str, Any]:
    """Tai lap `spread_and_separability` cua Lesson 23.7 tren truc MOI.

    Cong thuc giu NGUYEN de so sanh duoc voi `00zf-amendment-30.md`:
    profile bien = trung binh qhat tren cac truc CON LAI.
    """
    keys = list(q)
    n_z = 1 + max(int(k[0]) for k in keys)
    n_m = 1 + max(int(k[1]) for k in keys) if len(keys[0]) > 1 else 1
    n_s = len(next(iter(q.values())))

    arr = np.full((n_z, n_m, n_s), np.nan, dtype=np.float64)
    for k, v in q.items():
        z = int(k[0])
        m = int(k[1]) if len(k) > 1 else 0
        arr[z, m] = np.asarray(v, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("qhat tensor co o thieu hoac khong huu han")

    def _axis(axis: int) -> Dict[str, Any]:
        others = tuple(i for i in range(arr.ndim) if i != int(axis))
        prof = arr.mean(axis=others)
        return {
            "profile": [float(x) for x in prof],
            "spread": float(prof.max() / prof.min()),
        }

    return {
        "grid_shape": [int(x) for x in arr.shape],
        "M_183_spread_z": _axis(0)["spread"],
        "M_184_spread_m": _axis(1)["spread"] if n_m > 1 else None,
        "spread_slot": _axis(2)["spread"],
        "spread_total": float(arr.max() / arr.min()),
        "axes": {"z": _axis(0), "m_hat": _axis(1) if n_m > 1 else None, "slot": _axis(2)},
    }


# ---------------------------------------------------------------------------
# (4) CI cua qhat bang PAIRED block bootstrap -- M-186
# ---------------------------------------------------------------------------

def _resample_blocks(
    by_block: Mapping[Any, pd.DataFrame], pick: Sequence[Any]
) -> pd.DataFrame:
    """Ghep cac block da lay mau va GAN NHAN block MOI cho tung ban sao.

    Vi sao phai gan nhan lai -- day la mot loi that, do duoc:
    lay 500 block CO HOAN LAI tu 500 block cho ~311 block DUY NHAT
    (ky vong `n*(1-1/e)` = 316). `_qhat` dung `block_id.nunique()` lam
    `n_eff`, nen neu giu nguyen nhan cu thi `n_eff = 311` thay vi 500 ->
    muc conformal bi bao thu gia tao o MOI vong bootstrap.

    Gan nhan moi giu dung so don vi exchangeability = 500.
    """
    parts = []
    for i, b in enumerate(pick):
        sub = by_block[b].copy()
        sub["block_id"] = i          # nhan MOI, duy nhat cho tung ban sao
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


def paired_block_bootstrap_qhat(
    calib: pd.DataFrame,
    n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
    alpha: float = ALPHA_FAMILY,
) -> Dict[str, Any]:
    """CI95 cua qhat slot-1 duoi HAI taxonomy, dung CUNG mau block.

    PAIRED (Common Random Numbers): moi vong bootstrap lay MOT danh sach block
    va dung no cho ca hai taxonomy. Vay hieu so CI phan anh khac biet cua THU
    TUC, khong phai nhieu lay mau.

    Lay mau BLOCK co hoan lai -- KHONG lay mau HANG. Lay mau hang gia dinh
    hang doc lap; hang trong cung block khong doc lap (cung cua so thoi gian,
    cung trang thai hang doi), nen lay mau hang cho CI HEP GIA TAO o CA HAI
    taxonomy va lam ti so M-186 vo nghia. Do chinh la loi ma phep do nay sinh
    ra de tra loi.
    """
    rng = np.random.default_rng(int(seed))
    blocks = np.sort(calib["block_id"].unique())
    n_blk = len(blocks)
    by_block = {b: sub for b, sub in calib.groupby("block_id", sort=True)}

    a_each = float(alpha) / len(CM.SIM_COLS)          # alpha/3, Bonferroni
    out: Dict[str, List[float]] = {"mondrian": [], "flat": []}

    for _ in range(int(n_boot)):
        pick = rng.choice(blocks, size=n_blk, replace=True)
        boot = _resample_blocks(by_block, pick)
        for name, keys in (("mondrian", ["z_bin", "m_hat_bin"]), ("flat", ["z_bin"])):
            cells = [CM._norm(k) for k, _s in boot.groupby(keys, sort=True)]
            q = CM._qhat(boot, CM.SIM_COLS, keys, {k: a_each for k in cells})
            vals = [float(v[0]) for v in q.values() if np.isfinite(v[0])]
            out[name].append(float(np.mean(vals)) if vals else float("nan"))

    def _ci(x: List[float]) -> Dict[str, float]:
        arr = np.asarray([v for v in x if np.isfinite(v)], dtype=np.float64)
        if arr.size == 0:
            return {"mean": float("nan"), "lo95": float("nan"), "hi95": float("nan"),
                    "width95": float("nan"), "n_finite": 0}
        lo, hi = np.percentile(arr, [2.5, 97.5])
        return {
            "mean": float(arr.mean()), "lo95": float(lo), "hi95": float(hi),
            "width95": float(hi - lo), "n_finite": int(arr.size),
        }

    ci_m, ci_f = _ci(out["mondrian"]), _ci(out["flat"])
    return {
        "n_boot": int(n_boot), "seed": int(seed), "resample_unit": "block",
        "paired": True,
        "block_relabelled": True,
        "n_blocks_resampled": int(n_blk),
        "mondrian_16cells": ci_m,
        "flat_4cells": ci_f,
        "M_186_width_ratio_flat_over_mondrian": float(
            ci_f["width95"] / max(ci_m["width95"], 1e-12)
        ),
    }


# ---------------------------------------------------------------------------
# (5) So sanh ba bien the tren luoi kappa -- M-187
# ---------------------------------------------------------------------------

def variant_sweep(calib: pd.DataFrame, test: pd.DataFrame, anchor_err: float) -> Dict[str, Any]:
    """Ba bien the x luoi kappa. `evaluate_config` da tra `pass_coverage`."""
    rows: List[Dict[str, Any]] = []
    fits: Dict[str, Dict[str, Any]] = {}
    for post in VARIANTS:
        for kappa in KAPPA_GRID:
            fit = CM.fit_config(
                calib, "C3", float(kappa),
                alpha=ALPHA_FAMILY, post_variant=post, multiplicity="bonferroni",
            )
            ev = CM.evaluate_config(test, fit, anchor_err, alpha=ALPHA_FAMILY)
            ev = dict(ev)
            ev["variant"] = {"mondrian": "V-M", "none": "V-N", "selective": "V-S"}[post]
            ev["n_taxonomy_cells"] = int(len(fit["_q"]))
            rows.append(ev)
            if float(kappa) == float(KAPPA_OP):
                fits[post] = fit
    return {"rows": rows, "_fits": fits}


def score_M187(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """V-N PHAI vo bao phu; V-S PHAI khong vo. Ca hai tai kappa van hanh."""
    def _at(post: str) -> Mapping[str, Any]:
        return next(r for r in rows if r["post"] == post and float(r["kappa"]) == KAPPA_OP)

    n, s, m = _at("none"), _at("selective"), _at("mondrian")
    v_n, v_s, v_m = (float(r["violation_given_accept"]) for r in (n, s, m))
    return {
        "kappa": KAPPA_OP, "alpha": float(ALPHA_FAMILY),
        "V_N_viol_given_accept": v_n,
        "V_S_viol_given_accept": v_s,
        "V_M_viol_given_accept": v_m,
        "V_N_breaks": bool(v_n > ALPHA_FAMILY),
        "V_S_holds": bool(v_s <= ALPHA_FAMILY),
        "M_187_hit": bool(v_n > ALPHA_FAMILY and v_s <= ALPHA_FAMILY),
        # G23-237: cai gia cua V-S, bao cao khong lam tron
        "acceptance_V_M": float(m["acceptance"]),
        "acceptance_V_S": float(s["acceptance"]),
        "G23_237_acceptance_cost_ratio": float(
            float(s["acceptance"]) / max(float(m["acceptance"]), 1e-12)
        ),
    }


# ---------------------------------------------------------------------------
# (6) Doi chung
# ---------------------------------------------------------------------------

def control_negative_kappa0(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """G23-235 (DA SUA TRUOC KHI CHAY THAT -- xem amendment 23-64 muc 5.1).

    Dang KY BAN DAU doi CA BA bien the cho `viol|acc` bang nhau den 1e-12 tai
    kappa=0. Dieu do SAI VE THIET KE, va da bi bac bo bang chay nhap:

        `_accept` = (m_hat >= kappa*qhat); tai kappa=0 thanh (m_hat >= 0),
        DOC LAP taxonomy -> tap accept TRUNG NHAU, `acceptance` = 1.0. DUNG.
        Nhung `viol|acc` = P(score > qhat | accept), va `qhat` PHU THUOC
        taxonomy. V-M dung 16 o, V-N/V-S dung 4 o -> qhat khac -> viol khac.
        Bat chung bang nhau la bat mot dieu SAI.

    Hai khang dinh DUNG va sac hon, thay the:

      (a) `acceptance == 1.0` o ca ba -- vi quy tac accept doc lap taxonomy.
      (b) V-N va V-S TRUNG BIT o kappa=0 -- ca hai dung keys=[z_bin], va vong
          diem bat dong cua `selective` bat dau tu TOAN BO tap calib roi
          `_accept` nhan het, nen no dung yen ngay vong dau. Neu hai cai nay
          LECH thi co thu khac ngoai taxonomy dang doi.

    V-M KHAC chung la KY VONG, khong phai vi pham -- va do chinh la dieu ca
    lesson dang do.
    """
    at0 = {r["variant"]: r for r in rows if float(r["kappa"]) == 0.0}
    acc_ok = all(abs(float(r["acceptance"]) - 1.0) < 1e-12 for r in at0.values())
    d_viol = abs(float(at0["V-N"]["violation_given_accept"])
                 - float(at0["V-S"]["violation_given_accept"]))
    d_qhat = abs(float(at0["V-N"]["qhat_slot1_mean"])
                 - float(at0["V-S"]["qhat_slot1_mean"]))
    return {
        "acceptance_all_one": bool(acc_ok),
        "VN_VS_viol_gap": float(d_viol),
        "VN_VS_qhat_gap": float(d_qhat),
        "VM_differs_as_expected": bool(
            abs(float(at0["V-M"]["violation_given_accept"])
                - float(at0["V-N"]["violation_given_accept"])) > 0.0
        ),
        "G23_235_hit": bool(acc_ok and d_viol < 1e-12 and d_qhat < 1e-12),
        "detail": {v: {"acceptance": float(r["acceptance"]),
                       "viol": float(r["violation_given_accept"]),
                       "qhat_slot1_mean": float(r["qhat_slot1_mean"])}
                   for v, r in at0.items()},
    }


def control_positive_kappa2(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """G23-236: V-M PHAI vo o kappa=2 -- tai lap Lesson 22.4 tren truc moi.

    Neu no KHONG vo, ket qua Phase 22 khong chuyen sang truc moi va lesson
    phai dung. Do la mot doi chung DUONG: ta MUON thay hong.
    """
    r = next(x for x in rows if x["post"] == "mondrian" and float(x["kappa"]) == 2.0)
    v = float(r["violation_given_accept"])
    return {
        "V_M_viol_at_kappa2": v,
        "G23_236_hit": bool(v > ALPHA_FAMILY),
        "phase22_reference_kappa2": 0.1199,
        "note": "Lesson 22.4 do 0.1199 tren truc CU. Day la truc MOI; ky vong "
                "cung DAU, khong cung GIA TRI.",
    }


# ---------------------------------------------------------------------------
# (7) Chay mot cell
# ---------------------------------------------------------------------------

def run_cell(mode: str, rho: float, role: str, n_boot: int = N_BOOT) -> Dict[str, Any]:
    path = calib_path(mode, rho)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "thieu calib_set LIVE: %s\n  -> chay tools/run_23_20_matrix.py cho cell %s"
            % (path, cell_name(mode, rho))
        )
    df = pd.read_parquet(path)
    calib = df[df["is_calib"]].reset_index(drop=True)
    test = df[~df["is_calib"]].reset_index(drop=True)
    anchor_err = float(test["wrong"].mean())        # neo = luon tin twin

    fit_m = CM.fit_config(
        calib, "C3", KAPPA_OP, alpha=ALPHA_FAMILY,
        post_variant="mondrian", multiplicity="bonferroni",
    )
    q_m = fit_m["_q"]

    sweep = variant_sweep(calib, test, anchor_err)
    census_16 = taxonomy_census(calib, ["z_bin", "m_hat_bin"])
    census_4 = taxonomy_census(calib, ["z_bin"])

    return {
        "cell": cell_name(mode, rho),
        "role": role,                                # "MAIN" hoac "ROBUSTNESS"
        "parquet": pin(path),
        "n_rows": int(len(df)),
        "n_calib_blocks": int(calib["block_id"].nunique()),
        "n_test_blocks": int(test["block_id"].nunique()),
        "anchor_err": anchor_err,
        "census": {
            "mondrian_16cells": census_16,
            "flat_4cells": census_4,
            "M_181_n_blocks_mean_16cells": census_16["n_blocks_mean"],
            "M_182_block_ratio_4_over_16": float(
                census_4["n_blocks_mean"] / max(census_16["n_blocks_mean"], 1e-12)
            ),
            "row_ratio_4_over_16": float(
                census_4["n_rows_mean"] / max(census_16["n_rows_mean"], 1e-12)
            ),
        },
        "spread": spread_profiles(q_m),
        "mhat_concentration": mhat_concentration(q_m),
        "bootstrap": paired_block_bootstrap_qhat(calib, n_boot=n_boot),
        "variant_sweep": sweep["rows"],
        "M_187": score_M187(sweep["rows"]),
        "controls": {
            "G23_235_negative_kappa0": control_negative_kappa0(sweep["rows"]),
            "G23_236_positive_kappa2": control_positive_kappa2(sweep["rows"]),
        },
    }


# ---------------------------------------------------------------------------
# (8) Cham du doan + provenance
# ---------------------------------------------------------------------------

def score_predictions(cells: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Cham theo dai DA KY. Khong doi dai sau khi xem so."""
    getters = {
        "M-181": lambda c: c["census"]["M_181_n_blocks_mean_16cells"],
        "M-182": lambda c: c["census"]["M_182_block_ratio_4_over_16"],
        "M-183": lambda c: c["spread"]["M_183_spread_z"],
        "M-184": lambda c: c["spread"]["M_184_spread_m"],
        "M-185": lambda c: c["mhat_concentration"]["M_185_ratio_mean"],
        "M-186": lambda c: c["bootstrap"]["M_186_width_ratio_flat_over_mondrian"],
    }
    main = [c for c in cells if c["role"] == "MAIN"]
    out: Dict[str, Any] = {}
    for mid, spec in PREDICTIONS.items():
        vals = [float(getters[mid](c)) for c in main]
        hits = [bool(spec["lo"] <= v <= spec["hi"]) for v in vals]
        out[mid] = {
            "what": spec["what"],
            "band": [spec["lo"], spec["hi"]],
            "values_by_main_cell": {c["cell"]: v for c, v in zip(main, vals)},
            "n_hit": int(sum(hits)),
            "n_cells": int(len(vals)),
            "scored": bool(spec.get("scored", True)),
        }
    out["M-187"] = {
        "what": "V-N vo VA V-S khong vo tai kappa=1",
        "band": None,
        "values_by_main_cell": {c["cell"]: c["M_187"]["M_187_hit"] for c in main},
        "n_hit": int(sum(c["M_187"]["M_187_hit"] for c in main)),
        "n_cells": int(len(main)),
        "scored": True,
    }
    return out


def build_report(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "lesson": "23.22",
        "task": "A0 + A",
        "amendment": AMENDMENT,
        "superseded_basis": {
            "L89": "PHASE_23_v3.md trich spread_z=2.1232/spread_m=1.1188 tu "
                   "00zf-amendment-30.md dong 176-177, do tren Z_EDGES_LEGACY "
                   "(da thay the o amendment 23-49c). So do lai nam o "
                   "cells[].spread.",
            "legacy_spread_z": 2.1232,
            "legacy_spread_m": 1.1188,
            "legacy_axis": "assumed_sawtooth_51ms (DEPRECATED)",
            "legacy_z_edges": [0.055, 0.10, 0.20, 0.30, 0.5501],
            "current_z_edges": [float(x) for x in Z_EDGES_V7],
        },
        "config": {
            "alpha_family": float(ALPHA_FAMILY),
            "alpha_each": float(ALPHA_FAMILY / len(CM.SIM_COLS)),
            "multiplicity": "bonferroni",
            "variants": list(VARIANTS),
            "kappa_grid": list(KAPPA_GRID),
            "kappa_operating": float(KAPPA_OP),
            "n_boot": int(N_BOOT),
            "seed_boot": int(SEED_BOOT),
        },
        "cells": cells,
        "predictions": score_predictions(cells),
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=W_LOSS,
        ),
        "provenance": {
            "script": "cert/taxonomy_audit.py::build_report",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lesson 23.22 Task A0 -- taxonomy audit")
    ap.add_argument("--run", action="store_true", help="chay va ghi artifact")
    ap.add_argument("--robustness", action="store_true", help="them 9 cell robustness")
    ap.add_argument("--n-boot", type=int, default=N_BOOT, help="so vong block bootstrap")
    ap.add_argument("--out", default=OUTPUT, help="duong dan artifact")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="CHI de chay nhap. Artifact sinh ra co git_dirty=true "
                         "va KHONG duoc dung lam bang chung (G23-228).")
    args = ap.parse_args(argv)

    if not args.run:
        ap.print_help()
        return 0

    if git("git", "status", "--porcelain") and not args.allow_dirty:
        raise SystemExit(
            "worktree BAN. Commit amendment 23-64 va code truoc khi chay "
            "(protocol G23-228). Artifact voi git_dirty=true khong duoc dung "
            "lam bang chung. Chay nhap: them --allow-dirty."
        )

    cells: List[Dict[str, Any]] = []
    for mode, rho in MAIN_CELLS:
        print("[MAIN]      %s" % cell_name(mode, rho), flush=True)
        cells.append(run_cell(mode, rho, "MAIN", n_boot=int(args.n_boot)))
    if args.robustness:
        for mode, rho in ROBUSTNESS_CELLS:
            print("[ROBUST]    %s" % cell_name(mode, rho), flush=True)
            cells.append(run_cell(mode, rho, "ROBUSTNESS", n_boot=int(args.n_boot)))

    report = build_report(cells)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(json_clean(report), fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("\nartifact: %s" % args.out)

    for mid, res in report["predictions"].items():
        print("  %-7s %d/%d %s" % (mid, res["n_hit"], res["n_cells"],
                                   "" if res.get("scored", True) else "(khong cham)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

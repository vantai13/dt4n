#!/usr/bin/env python3
"""Lesson 23.25b -- phan xu H1 (confound chung diem cuoi) vs H2 (chuoi ngan).

Tien dang ky: docs/phase-23/A078-amendment-78.md muc 4.

VAN DE: `r(uA,uB) = +0.599` va `r(vC,vD) = +0.638` trong khi ca hai la cap
NULL (khong chung duong nao). Hai cap nay giai thich 85-111% cua ket qua
`Var(m)_do/don_vi = 0.54-0.71` cua Lesson 23.25.

TEST A -- do tan cua `r` qua 15 run DOC LAP.
    H1 dung -> 15 gia tri bam quanh +0.6, `sd` nho, khong co gia tri am.
    H2 dung -> vang loan, `sd` lon, co ca gia tri am.
    So lieu DA NAM trong duong `pooled_corr` -- chi chua bao gio duoc in ra.

TEST B -- doi chieu `rho_offered_*.csv` (Y DINH cua bo sinh tai, KHONG chiu
    nghen host) voi `rho_measured_*.csv` (thuc te qua kernel counter).
        `r_offered ~ 0` nhung `r_measured ~ +0.6`  -> H1: nghen host THAT
        ca hai ~ +0.6                              -> thiet ke BO SINH
        ca hai vang loan                           -> H2

Chay:
    python -m measurements.link_pair_stability \\
        --campaign results/RAW/phase-23/aoi_v7_campaign \\
        --out results/LIVE/phase-23/link_pair_stability.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

from measurements import validity as V
from measurements.link_corr_matrix import (
    IDX, _provenance, cell_of, fisher_z, load_run, tau_from_meta)

# Cap can phan xu + cap DOI CHIEU nhanh.
# `ac`/`ad` cung chung host `hA`; `bc`/`bd` cung chung `hB` -- neu H1 dung o
# muc "chung endpoint" thi hai cap nay CUNG PHAI cao. Do duoc: chung ~ +0.03.
FOCUS_PAIRS = (("uA", "uB"), ("vC", "vD"), ("ac", "ad"), ("bc", "bd"))

# --- HANG SO KHOA o `A078` muc 4. KHONG phai co dong lenh. ---------------
SD_H1_MAX = 0.30          # `M-252`
SD_H2_MIN = 0.45
N_NEG_H2_MIN = 3          # `M-253`
R_OFFERED_H1_MAX = 0.15   # `M-254`
R_OFFERED_DESIGN_MIN = 0.40


def per_run_pair_corr(mats, pairs) -> dict:
    """`r` cua tung cap, tinh RIENG trong tung run (khong gop)."""
    out = {}
    for a, b in pairs:
        rs = []
        for X in mats:
            if X.shape[0] < 10:
                continue
            r = np.corrcoef(X[:, IDX[a]], X[:, IDX[b]])[0, 1]
            rs.append(0.0 if not np.isfinite(r) else float(r))
        arr = np.asarray(rs, dtype=float)
        if arr.size == 0:
            continue
        z = fisher_z(arr)
        se = float(z.std(ddof=1) / np.sqrt(z.size)) if z.size > 1 else None
        out["%s-%s" % (a, b)] = {
            "n_runs": int(arr.size),
            "r_per_run": [round(float(x), 4) for x in arr],
            "r_pooled_fisher": float(np.tanh(z.mean())),
            "sd_r_across_runs": float(arr.std(ddof=1)) if arr.size > 1 else None,
            "min_r": float(arr.min()), "max_r": float(arr.max()),
            "n_runs_negative": int((arr < 0).sum()),
            "se_of_pooled": se,
            "t_like": (float(abs(z.mean()) / se) if se else None),
        }
    return out


def adjudicate(measured: dict, offered: dict | None) -> dict:
    """Ap tieu chi da ky o `A078` muc 4/5. Khong dien giai lai."""
    verdicts = {}
    for key in ("uA-uB", "vC-vD"):
        m = measured.get(key)
        if m is None:
            continue
        sd, neg = m["sd_r_across_runs"], m["n_runs_negative"]
        if (sd is not None and sd > SD_H2_MIN) or neg >= N_NEG_H2_MIN:
            v_a = "H2"
        elif sd is not None and sd < SD_H1_MAX and neg <= 1:
            v_a = "H1"
        else:
            v_a = "UNCLEAR"

        v_b, r_off = "NO_OFFERED_DATA", None
        if offered and key in offered:
            r_off = abs(offered[key]["r_pooled_fisher"])
            if r_off < R_OFFERED_H1_MAX:
                v_b = "H1"
            elif r_off > R_OFFERED_DESIGN_MIN:
                v_b = "GENERATOR_DESIGN"
            else:
                v_b = "UNCLEAR"
        verdicts[key] = {"test_A": v_a, "test_B": v_b,
                         "sd_across_runs": sd, "n_runs_negative": neg,
                         "r_measured": m["r_pooled_fisher"],
                         "r_offered_abs": r_off}

    # Ap DUNG TUNG CHU tieu chi `A078` muc 5. KHONG duoc noi long.
    #   K1 = (M-252 < 0.30) VA (M-254 |r| < 0.15)          -- LIEN KET VA
    #   K2 = (M-252 > 0.45) HOAC (M-253 >= 3)
    #   K3 = M-252 trong [0.30, 0.45]
    sds = [v["sd_across_runs"] for v in verdicts.values()
           if v["sd_across_runs"] is not None]
    negs = [v["n_runs_negative"] for v in verdicts.values()]
    roffs = [v["r_offered_abs"] for v in verdicts.values()
             if v["r_offered_abs"] is not None]

    k1 = (bool(sds) and all(x < SD_H1_MAX for x in sds)
          and bool(roffs) and all(x < R_OFFERED_H1_MAX for x in roffs))
    k2 = ((bool(sds) and any(x > SD_H2_MIN for x in sds))
          or (bool(negs) and any(x >= N_NEG_H2_MIN for x in negs)))
    k3 = bool(sds) and all(SD_H1_MAX <= x <= SD_H2_MIN for x in sds)

    if k2:
        overall, scenario = "H2_SHORT_SERIES_ARTEFACT", "A078 muc 5 K2"
    elif k1:
        overall, scenario = "H1_ENDPOINT_CONFOUND", "A078 muc 5 K1"
    elif k3:
        overall, scenario = "UNCLEAR_REPORT_BOTH", "A078 muc 5 K3"
    else:
        # ★ Ba kich ban da ky KHONG PHU KIN khong gian ket qua. Vi du do
        # duoc: `sd < 0.30` (thoa ve dau cua K1) nhung `|r_offered| >= 0.15`
        # (hong ve sau), va `sd` khong nam trong [0.30, 0.45] nen K3 cung
        # khong ap duoc. KHONG duoc chon dai gan nhat -- do la dien giai lai
        # sau khi nhin so. Roi ve xu ly BAO THU cua K3. Ghi `L145`.
        overall, scenario = "GAP_IN_SIGNED_SCENARIOS", "A078 muc 5 -- KHE HO"

    return {"per_pair": verdicts, "overall": overall, "scenario": scenario,
            "K1_met": k1, "K2_met": k2, "K3_met": k3,
            "scenarios_partition_outcome_space": bool(k1 or k2 or k3),
            "fallback_if_gap": ("xu ly nhu K3: bao cao CA HAI kich ban, va "
                                "Lesson 23.26 phai keo dai run"),
            "thresholds": {"SD_H1_MAX": SD_H1_MAX, "SD_H2_MIN": SD_H2_MIN,
                           "N_NEG_H2_MIN": N_NEG_H2_MIN,
                           "R_OFFERED_H1_MAX": R_OFFERED_H1_MAX}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    def collect(pattern):
        ps = sorted(glob.glob(os.path.join(a.campaign, "**", pattern),
                              recursive=True))
        return ps, [X for X in (load_run(p) for p in ps) if X.shape[0] >= 10]

    p_meas, m_meas = collect("rho_measured_clean_*.csv")
    if not m_meas:
        raise SystemExit("khong tim thay rho_measured_clean_*.csv")
    p_off, m_off = collect("rho_offered_clean_*.csv")

    measured = per_run_pair_corr(m_meas, FOCUS_PAIRS)
    offered = per_run_pair_corr(m_off, FOCUS_PAIRS) if m_off else None

    import measurements.link_pair_stability as _self

    report = {
        "schema": "dt4n.link.pair_stability.v1",
        "lesson": "23.25b",
        "prereg": "docs/phase-23/A078-amendment-78.md",
        "status": "MEASUREMENT_ESTIMATE" if m_off else "INCOMPLETE_NO_OFFERED",
        "locked_constants": {"SD_H1_MAX": SD_H1_MAX, "SD_H2_MIN": SD_H2_MIN,
                             "N_NEG_H2_MIN": N_NEG_H2_MIN,
                             "R_OFFERED_H1_MAX": R_OFFERED_H1_MAX,
                             "R_OFFERED_DESIGN_MIN": R_OFFERED_DESIGN_MIN},
        "tau_by_link_from_meta": tau_from_meta(a.campaign),
        "n_files_measured": len(p_meas), "n_files_offered": len(p_off),
        "cells_measured": sorted({cell_of(p) for p in p_meas}),
        "testA_measured_per_run": measured,
        "testB_offered_per_run": offered,
        "adjudication": adjudicate(measured, offered),
        "provenance": _provenance("measurements/link_pair_stability.py",
                                  {"campaign": a.campaign, "out": a.out}),
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=(p_meas[:1] + p_off[:1]),
            note=("Artifact DO do on dinh cua tuong quan theo cap (vai tro "
                  "MEASURES). Khong tieu thu truc AoI va khong tieu thu truc "
                  "SLA -- no chi doc `rho` tho. Xem `A078` muc 8."),
        ),
    }

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    for key in ("uA-uB", "vC-vD", "ac-ad", "bc-bd"):
        m = measured.get(key)
        if m:
            o = offered.get(key, {}).get("r_pooled_fisher") if offered else None
            print("[stab] %-6s r_do=%+.4f  sd_qua_run=%.4f  am=%d/%d  "
                  "[%+.3f,%+.3f]  r_offered=%s"
                  % (key, m["r_pooled_fisher"], m["sd_r_across_runs"] or 0.0,
                     m["n_runs_negative"], m["n_runs"], m["min_r"], m["max_r"],
                     "%+.4f" % o if o is not None else "-"))
    adj = report["adjudication"]
    print("[stab] ★ PHAN XU: %s  (%s)" % (adj["overall"], adj["scenario"]))


if __name__ == "__main__":
    main()

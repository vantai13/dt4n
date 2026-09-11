#!/usr/bin/env python3
"""20R2.6b -- PHU LUC THAM DO: phan quyet gop nhin tu TUNG O.

KHONG doi phan quyet 20R2.6 (8 o, DA KY, 5/8). File nay chi TACH lop gop ra:
  (1) err_total/Sheppard va err_stale/Sheppard cho TUNG o gate
  (2) do nhay quan the: trung vi o; bo 2 o EXTRAPOLATION_CONTAMINATED theo luat
      T2-R7 (ky 2026-09-08, TRUOC 20R2, ly do DOC LAP ket qua)
  (3) bien chuan hoa m va so duong "song" -- tinh tu BANG CHI PHI SU THAT,
      KHONG tu err, de doi chieu duoc voi he so Rice exp(-m^2/2).

VI SAO m PHAI TINH TU BANG CHI PHI, KHONG TU err
================================================
Neu suy m tu err thi m va err khong con doc lap: ta se "giai thich" err bang
mot dai luong duoc dan ra TU err, va moi quan he se dung theo dinh nghia. Chi
khi m den tu bang chi phi su that thi "Rice du doan err" moi la mot phep kiem
CO THE SAI.

⚠️ MOI SO O DAY LA THAM DO, sinh SAU khi mo hop. Muon thanh KHANG DINH: dang
ky du doan tu m TRUOC, roi kiem tren seed MOI (xem prereg §19).

    python -m tools.20r2_6b_per_cell --out docs/phase-20R2/06b-per-cell.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = "docs/phase-20R2/03-run-plan.json"
ADJ = "docs/phase-20R2/06-adjudication.json"
EXO = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
Z, Z_SIGNED, A = 0.366, 0.365, 0.9
M_SEEDS, M_TAU, M_N = (101, 102, 103), 3.0, 200_000
ACTIVE_SHARE = 0.05
# T2-R7 (docs/phase-T2/00-preregistration.md, A-T2-1 muc (c)): rho_bar = 0.96
# danh dau EXTRAPOLATION_CONTAMINATED, "khong dung lam headline", KHONG loai
# khoi luoi chay. Ly do DOC LAP ket qua: link `ad` co mu = 1.0225, cach tran
# mien bang su that (1.04) chi 1.82 sigma, va np.interp kep phang IM LANG.
R7_RHO_BAR = 0.96


def sheppard(z, tau):
    return math.acos(math.exp(-float(z) / float(tau))) / math.pi


def per_cell_ratios() -> pd.DataFrame:
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    fr = [pd.read_parquet(ROOT / r["out"]) for r in plan["runs"]
          if not r["is_canary"] and r["branch"] == "main" and r["a"] == A]
    d = pd.concat(fr, ignore_index=True)
    s = d[np.isclose(d["z_s"].to_numpy(float), Z) & (d["mode"] != "cbr")]
    g = (s.groupby(["mode", "rho_bar", "tau_rho"])
         [["err_total", "err_stale", "err_model", "tt_domain_clip_max"]]
         .mean().reset_index())
    sh = g["tau_rho"].map(lambda t: sheppard(Z_SIGNED, t))
    g["sheppard"] = sh
    g["total_over_sh"] = g["err_total"] / sh
    g["stale_over_sh"] = g["err_stale"] / sh
    g["contaminated_T2_R7"] = np.isclose(g["rho_bar"], R7_RHO_BAR)
    return g


def margin_structure() -> dict:
    """m = mean/sd cua BIEN giua hai duong thang nhieu nhat, tu BANG SU THAT."""
    import measurements.decision_error_v2 as DE
    tt = DE.TruthTable(DE.TRUTH_TABLE)
    out = {}
    for c in DE.feasible_cells(EXO, include_pc1=True):
        if c["mode"] == "cbr":
            continue
        sig, _ = DE.resolve_sigma(c, a_override=A)
        ms, shares = [], None
        for seed in M_SEEDS:
            rho = DE.rho_matrix_from_cell(c["mode"], float(c["rho_bar"]), sig, seed,
                                          tau=M_TAU, n=M_N, dt=DE.DT,
                                          source=DE.RHO_SOURCE)
            _, _, ct = tt.path_tables(c["mode"], rho, float(c["w_loss"]))
            v, cnt = np.unique(ct.argmin(axis=1), return_counts=True)
            o = np.argsort(-cnt)
            shares = (cnt[o] / cnt.sum()).tolist()
            if len(o) < 2:
                ms.append(float("inf"))
                continue
            M = ct[:, v[o[1]]] - ct[:, v[o[0]]]   # bien CO DAU: nhi > nhat
            ms.append(float(M.mean() / M.std()))
        finite = [x for x in ms if math.isfinite(x)]
        m = float(np.mean(finite)) if finite else float("inf")
        out["%s@%.3f" % (c["mode"], float(c["rho_bar"]))] = {
            "m_mean": m,
            "m_sd_over_seeds": float(np.std(finite)) if finite else 0.0,
            "rice_factor": math.exp(-m * m / 2) if math.isfinite(m) else 0.0,
            "argmin_shares": shares,
            "n_active": int(sum(x >= ACTIVE_SHARE for x in shares)),
            "n_seeds_m": len(finite),
        }
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    g = per_cell_ratios()
    taus = sorted(g["tau_rho"].unique().tolist())
    agg = {
        "pooled_8_signed": g.groupby("tau_rho")["total_over_sh"].mean().tolist(),
        "median_8": g.groupby("tau_rho")["total_over_sh"].median().tolist(),
        "pooled_6_without_T2_R7":
            g[~g["contaminated_T2_R7"]].groupby("tau_rho")["total_over_sh"].mean().tolist(),
        "pooled_7_without_h2_0960":
            g[~((g["mode"] == "h2") & np.isclose(g["rho_bar"], R7_RHO_BAR))]
            .groupby("tau_rho")["total_over_sh"].mean().tolist(),
    }
    # DOI CHUNG CHO CHINH TOOL NAY: cot gop phai TAI LAP artifact da ky.
    adj = json.loads((ROOT / ADJ).read_text(encoding="utf-8"))
    signed = [r["err_hat"] / r["sheppard_signed"] for r in adj["primary_directional"]["rows"]]
    worst = max(abs(x - y) for x, y in zip(agg["pooled_8_signed"], signed))
    if worst > 1e-9:
        raise AssertionError("KHONG tai lap cot gop da ky: lech max %.3g" % worst)

    stale = {
        "pooled_8": g.groupby("tau_rho")["stale_over_sh"].mean().tolist(),
        "n_cells_stale_above_sheppard_all_tau": int(
            sum(1 for _, c in g.groupby(["mode", "rho_bar"])
                if (c["stale_over_sh"] > 1.0).all())),
        "n_cells_stale_below_sheppard_all_tau": int(
            sum(1 for _, c in g.groupby(["mode", "rho_bar"])
                if (c["stale_over_sh"] < 1.0).all())),
    }
    doc = {"schema": "dt4n.per_cell_20r2_6b.v1",
           "generated_by": "tools/20r2_6b_per_cell.py",
           "STATUS": "THAM DO -- sinh SAU khi mo hop. KHONG doi phan quyet 20R2.6 (8 o, 5/8).",
           "self_control": "cot pooled_8_signed TAI LAP artifact da ky, lech max < 1e-9",
           "T2_R7": ("rho_bar = 0.96 danh dau EXTRAPOLATION_CONTAMINATED, "
                     "'khong dung lam headline' (docs/phase-T2/00-preregistration.md "
                     "A-T2-1 muc (c), ky 2026-09-08 TRUOC 20R2). prereg 20R2 KHONG nhac."),
           "taus": taus, "aggregates": agg, "stale": stale,
           "cells": g.to_dict(orient="records"),
           "margin_structure": margin_structure()}
    (ROOT / a.out).write_text(json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n",
                              encoding="utf-8")
    print("tau:", [("%g" % t) for t in taus])
    for k, v in agg.items():
        print("%-26s %s" % (k, [round(x, 3) for x in v]))
    print()
    ms = doc["margin_structure"]
    print("%-15s %6s %8s %7s  %s" % ("o", "m", "rice", "active", "shares"))
    for k in sorted(ms, key=lambda k: -ms[k]["rice_factor"]):
        v = ms[k]
        print("%-15s %6.2f %8.3f %7d  %s" % (
            k, v["m_mean"], v["rice_factor"], v["n_active"],
            [round(x, 3) for x in v["argmin_shares"][:4]]))
    print()
    print("o co err_stale > Sheppard o MOI tau: %d/8" % stale["n_cells_stale_above_sheppard_all_tau"])
    print("o co err_stale < Sheppard o MOI tau: %d/8" % stale["n_cells_stale_below_sheppard_all_tau"])
    print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

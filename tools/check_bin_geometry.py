#!/usr/bin/env python3
"""Tach 'thay doi TRUC' khoi 'thay doi HINH HOC BIN'.  (Lesson 23.20)

Phan du 2.6% cua M-125b DOI DAU giua cac bin (B0 +0.83% -> B3 -0.66%), ma
mot luat luy thua thi KHONG the doi dau khi moi ty so z deu > 1. Nen chan
doan "so mu thuc te < 0.431" SAI DAU va da bi rut (amendment 23-49d).

Gia thuyet thay the: HINH HOC BIN. Bin cu rong khong deu (45/100/100/250 ms),
bin moi deu (~125-150 ms). `q_hat` cua mot bin la phan vi tren mot HON HOP z
trong bin do; bin rong hon tron nhieu z hon -> duoi tren cua score bi day len.

    B0  45 -> 141 ms  (rong RA 3.1x)  -> q_hat moi bi day len -> lech DUONG
    B3 250 -> 150 ms  (HEP di 1.7x)   -> q_hat moi it bi day  -> lech AM

VAN DE: ty so BE RONG cong tuyen voi ty so z (corr 0.88) tren 4 diem, nen
khong tach duoc bang tuong quan. Phep kiem NAY tach duoc: bin lai CA HAI
truc bang TU PHAN VI CUA CHINH NO -> hai ben cung hinh hoc (deu 25%), ty so
be rong ~1 o moi bin, trong khi ty so z VAN bien thien. Neu do lech sup ve
~0 thi hinh hoc bin la nguyen nhan.

KHONG build lai: chi doc z_s/s_margin tu parquet da co roi bin lai.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from cert.build_calib_set_v2 import ALPHA
from cert.conformal_v2 import conformal_level, empirical_qhat

CELLS = ["h2@0.700", "poisson@0.850", "poisson@0.925", "poisson@0.960"]
BETA = 0.431
COLS = ["z_s", "z_bin", "s_margin", "is_calib", "block_id"]


def load(cell, axis):
    m, r = cell.split("@")
    # truc ke thua -> SUPERSEDED (da bi thay the); truc do duoc -> PENDING
    # (hien hanh, cho truc SLA duoc duyet). Amendment 23-49d muc 4.
    tier = "SUPERSEDED" if axis == "legacy_sawtooth_51ms" else "PENDING"
    return pd.read_parquet(
        "results/%s/phase-21R/calib_set_%s_%.3f_U0_%s.parquet"
        % (tier, m, float(r), axis), columns=COLS)


def qhat_bins(df, bins, alpha=ALPHA):
    """q_hat theo bin, DUNG ham cua pipeline (empirical_qhat + mondrian_level)."""
    cal = df[df.is_calib.astype(bool)]
    out, zbar, width = {}, {}, {}
    for b in range(len(bins) - 1):
        lo, hi = bins[b], bins[b + 1]
        m = (cal.z_s >= lo) & (cal.z_s < hi if b < len(bins) - 2 else cal.z_s <= hi)
        sub = cal[m]
        n_blk = sub.block_id.nunique()
        lvl = conformal_level(n_blk, alpha)
        out[b] = (empirical_qhat(sub.s_margin.to_numpy(float), lvl)
                  if lvl is not None else float("inf"))
        zbar[b] = float(sub.z_s.mean() * 1000.0)
        width[b] = float((hi - lo) * 1000.0)
    return out, zbar, width


def own_quartiles(df):
    e = np.quantile(df.z_s.to_numpy(float), [0.0, .25, .50, .75, 1.0])
    e[0] -= 1e-9
    e[-1] += 1e-9
    return e


def main() -> None:
    LEG = np.array([0.055, 0.10, 0.20, 0.30, 0.5501])
    NEW = np.array([0.100, 0.241, 0.366, 0.491, 0.641])

    rows_mis, rows_match = [], []
    print("## Hinh hoc LECH (canh da khoa: cu 45/100/100/250 vs moi ~125-150)\n")
    print("| cell | bin | z_tb CU | z_tb MOI | rong CU | rong MOI | ty so rong | lech |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")
    for c in CELLS:
        lo, ln = load(c, "legacy_sawtooth_51ms"), load(c, "measured_v7")
        qo, zo, wo = qhat_bins(lo, LEG)
        qn, zn, wn = qhat_bins(ln, NEW)
        for b in range(4):
            d = (qn[b] / qo[b]) / ((zn[b] / zo[b]) ** BETA) - 1
            rows_mis.append(d)
            print(f"| {c} | B{b} | {zo[b]:.1f} | {zn[b]:.1f} | {wo[b]:.0f} | "
                  f"{wn[b]:.0f} | {wn[b]/wo[b]:.2f} | {d*100:+.2f}% |")

    print("\n## Hinh hoc KHOP (bin lai CA HAI truc bang tu phan vi cua chinh no)\n")
    print("| cell | bin | z_tb CU | z_tb MOI | ty so z | rong CU | rong MOI | ty so rong | lech |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for c in CELLS:
        lo, ln = load(c, "legacy_sawtooth_51ms"), load(c, "measured_v7")
        qo, zo, wo = qhat_bins(lo, own_quartiles(lo))
        qn, zn, wn = qhat_bins(ln, own_quartiles(ln))
        for b in range(4):
            d = (qn[b] / qo[b]) / ((zn[b] / zo[b]) ** BETA) - 1
            rows_match.append(d)
            print(f"| {c} | B{b} | {zo[b]:.1f} | {zn[b]:.1f} | {zn[b]/zo[b]:.3f} | "
                  f"{wo[b]:.0f} | {wn[b]:.0f} | {wn[b]/wo[b]:.2f} | {d*100:+.2f}% |")

    a, m = np.abs(np.array(rows_mis)), np.abs(np.array(rows_match))
    print(f"\n**Hinh hoc LECH : |lech| max {a.max()*100:.2f}%, trung binh "
          f"{a.mean()*100:.2f}%**")
    print(f"**Hinh hoc KHOP : |lech| max {m.max()*100:.2f}%, trung binh "
          f"{m.mean()*100:.2f}%**")
    verdict = ("BIN_GEOMETRY_EXPLAINS" if m.max() < 0.01 else
               "PARTIAL" if m.max() < a.max() else "NOT_EXPLAINED")
    print(f"\n**PHAN XU: {verdict}**")
    import sys as _sys
    _sys.path.insert(0, ".")
    from measurements import validity as _V
    import tools.check_bin_geometry as _self
    json.dump({"schema": "dt4n.bin_geometry.v1", "beta": BETA, "cells": CELLS,
               "validity": _V.measurement_validity_block(
                   instrument_module=_self,
                   inputs=["results/LIVE/phase-23/axis_remeasure_impact_wave1.json"],
                   note=("So sanh GHEP CAP hai luoi bin tren CUNG du lieu -> "
                         "nguong SLA triet tieu trong ty so, nen ket luan mien "
                         "nhiem voi Lesson 23.21 (amendment 23-49d muc 5).")),
               "mismatched_geometry": {"max_abs": float(a.max()),
                                       "mean_abs": float(a.mean())},
               "matched_geometry": {"max_abs": float(m.max()),
                                    "mean_abs": float(m.mean())},
               "verdict": verdict},
              open("results/LIVE/phase-23/bin_geometry_check.json", "w"),
              indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

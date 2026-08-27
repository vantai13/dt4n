#!/usr/bin/env python3
"""Lesson 23.25c -- truy nguon tuong quan endpoint bang shortfall.

So sanh ba ma tran, luon tinh TRONG tung run roi gop Fisher-z:

* `offered`: tai ma generator dinh phat;
* `measured`: tai that tren interface;
* `shortfall = measured / offered`: phan truyen dat/hao hut cua dung cu.

Chay:
    python -m measurements.host_confound_probe \
        --campaign results/RAW/phase-23/aoi_v7_campaign \
        --out results/LIVE/phase-23/host_confound_probe.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

from measurements import validity as V
from measurements.link_corr_matrix import (
    IDX, LINKS, LOAD_CHANNELS, _provenance, load_run, pooled_corr, shares_host)


def load_offered(flowdir: str, n_target: int) -> np.ndarray:
    """Gop CSV 10 ms cua tung link ve dung `n_target` cua so do 200 ms.

    Cot 2 la `rho_offered`; cot 1 la timestamp. Ghim chi so cot tai day de
    tranh vo tinh tinh tuong quan cua timestamp chung giua cac link.
    """
    columns = []
    for link in LINKS:
        path = os.path.join(flowdir, "rho_offered_%s.csv" % link)
        values = np.loadtxt(path, delimiter=",", skiprows=1, usecols=2)
        group = len(values) // n_target
        if group < 1:
            raise ValueError("%s co %d mau, khong du cho %d cua so"
                             % (path, len(values), n_target))
        values = values[:group * n_target].reshape(n_target, group).mean(axis=1)
        columns.append(values)
    return np.asarray(columns, dtype=float).T


def collect_triplets(campaign: str):
    measured, offered, shortfall, run_names = [], [], [], []
    paths = sorted(glob.glob(os.path.join(
        campaign, "**", "rho_measured_clean_*.csv"), recursive=True))
    for path in paths:
        tag = os.path.basename(path).replace("rho_measured_", "").replace(".csv", "")
        flowdir = os.path.join(os.path.dirname(path), "flows_%s" % tag)
        if not os.path.isdir(flowdir):
            continue
        M = load_run(path)
        if M.shape[0] < 10:
            continue
        O = load_offered(flowdir, M.shape[0])
        S = M / np.clip(O, 1e-9, None)
        measured.append(M)
        offered.append(O)
        shortfall.append(S)
        run_names.append(tag)
    return measured, offered, shortfall, run_names, paths


def _pair_rows(Rm: np.ndarray, Ro: np.ndarray, Rs: np.ndarray) -> dict:
    out = {}
    for ia, a in enumerate(LINKS):
        for b in LINKS[ia + 1:]:
            hosts = sorted(set(LOAD_CHANNELS[a]) & set(LOAD_CHANNELS[b]))
            out["%s-%s" % (a, b)] = {
                "shared_host": bool(hosts), "hosts": hosts,
                "r_offered": float(Ro[IDX[a], IDX[b]]),
                "r_measured": float(Rm[IDX[a], IDX[b]]),
                "r_shortfall": float(Rs[IDX[a], IDX[b]]),
            }
    return out


def adjudicate(pairs: dict) -> dict:
    """Ba nhanh A079 phu kin; probe nay chi phan xu VI TRI cua hien vat."""
    focus = pairs["uA-uB"]
    ro = focus["r_offered"]
    rm = focus["r_measured"]
    rs = focus["r_shortfall"]
    if abs(ro) >= 0.40:
        verdict = "GENERATOR_DESIGN_OR_SHARED_RNG"
    elif rs >= 0.30:
        verdict = "HOST_SHORTFALL_SUPPORTED"
    elif rm >= 0.40:
        verdict = "SWITCH_OR_MEASUREMENT_INSTRUMENT"
    else:
        verdict = "NO_LARGE_SHARED_ENDPOINT_ARTIFACT"
    return {
        "focus_pair": "uA-uB", "verdict": verdict,
        "r_offered": ro, "r_measured": rm, "r_shortfall": rs,
        "thresholds": {"generator_abs_r_offered_min": 0.40,
                       "host_r_shortfall_min": 0.30,
                       "large_r_measured_min": 0.40},
        "note": ("Phan xu K1/K2/K3 cuoi cung con can chi2/dof M3 trong "
                 "link_corr_matrix.json::T8_identifiability."),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    mats_m, mats_o, mats_s, run_names, paths = collect_triplets(a.campaign)
    if not mats_m:
        raise SystemExit("khong tim thay cap measured/flows CLEAN hoan chinh")
    Rm, nr_m = pooled_corr(mats_m)
    Ro, nr_o = pooled_corr(mats_o)
    Rs, nr_s = pooled_corr(mats_s)
    pairs = _pair_rows(Rm, Ro, Rs)

    import measurements.host_confound_probe as _self

    report = {
        "schema": "dt4n.host_confound_probe.v1",
        "lesson": "23.25c",
        "prereg": "docs/phase-23/A079-amendment-79.md",
        "status": "MEASUREMENT_ESTIMATE",
        "n_runs": min(nr_m, nr_o, nr_s),
        "run_names": run_names,
        "offered_column_index": 2,
        "pairs": pairs,
        "adjudication": adjudicate(pairs),
        "provenance": _provenance(
            "measurements/host_confound_probe.py",
            {"campaign": a.campaign, "out": a.out}),
        "validity": V.measurement_validity_block(
            instrument_module=_self, inputs=paths[:1],
            note=("Do offered/measured/shortfall tren cung 15 run CLEAN; "
                  "khong do Mininet moi, khong dung AoI/SLA.")),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("%-10s %12s %11s %12s %13s"
          % ("cap", "chung host", "r_offered", "r_measured", "r_shortfall"))
    for name, row in pairs.items():
        print("%-10s %12s %+11.4f %+12.4f %+13.4f"
              % (name, ",".join(row["hosts"]) or "-", row["r_offered"],
                 row["r_measured"], row["r_shortfall"]))
    j = report["adjudication"]
    print("[host_probe] %s: offered=%+.4f measured=%+.4f shortfall=%+.4f"
          % (j["verdict"], j["r_offered"], j["r_measured"],
             j["r_shortfall"]))


if __name__ == "__main__":
    main()

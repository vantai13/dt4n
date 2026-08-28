#!/usr/bin/env python3
"""Lesson 23.25f -- SNR o cell bao hoa la that hay artifact censoring?

Tien dang ky: docs/phase-23/A082-amendment-82.md
KHONG do moi. Doc `rho_measured_clean_*.csv` va `flows_*/rho_offered_*.csv`
cua chinh chien dich 23.8.

Chay:
    .venv/bin/python -m measurements.snr_censoring_artifact \
        --campaign results/RAW/phase-23/aoi_v7_campaign \
        --out results/LIVE/phase-23/snr_censoring_artifact.json
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr

from measurements import validity as V
from measurements.host_confound_probe import load_offered
from measurements.link_corr_matrix import (
    MODE, PATH_PAIRS, W_LOSS, _provenance, cell_of, load_run)
from twin import cost_v2 as C
from twin import topology_v7 as T7

# Hang so khoa o A082. KHONG phai co dong lenh.
HARD_CEILING_PROBE_MIN = 1.0
CEILING_SAFETY = 0.995
R_HIT_LO, R_HIT_HI = 0.85, 1.30
NC_LO, NC_HI = 0.95, 1.05
CLEAN_CELL_MAX_P_CENSORED = 0.20

T0_T11_SOURCES = (
    "results/LIVE/phase-23/link_corr_matrix.json",
    "results/LIVE/phase-23/lesson_23_25_final_audit.json",
)
T0_T11_CANONICAL_SHA256_BEFORE = (
    "9b82306376688f275a9e31a5a926c56a7d14f3b9a23704723c441a160339e3fb")
SOURCE_FILE_SHA256_BEFORE = {
    T0_T11_SOURCES[0]:
        "6a753c1a6e7791682b74ebd8e0eef5a4ab8f451614f5c05a02f5b55835e8e291",
    T0_T11_SOURCES[1]:
        "64cdf9f579dd9ac5719c07e7059aaddeb138c0211e1d9fd4df0183ae1e44ce78",
}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_hash(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def t0_t11_canonical(sources=T0_T11_SOURCES) -> dict:
    block = {}
    for path in sources:
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
        for key, value in report.items():
            if re.match(r"^T(?:[0-9]|1[01])(?:\D|$)", key):
                block[key] = value
    return block


def snr_by_pair(X: np.ndarray) -> dict:
    """Tinh `|E[m]|/sd(m)` cho 6 cap; bao cao clip cua mien CostV2."""
    clip_share = float(np.mean((X < C.RHO_MIN) | (X > C.RHO_MAX)))
    Xc = np.clip(X, C.RHO_MIN, C.RHO_MAX)
    cv = C.CostV2(strict_reliable=False)
    _delay, _loss, cost = cv.tables_batch(Xc, MODE, W_LOSS)
    out = {"_clip_share": clip_share}
    for pi, pj in PATH_PAIRS:
        m = (cost[:, T7.PATH_NAMES.index(pi)]
             - cost[:, T7.PATH_NAMES.index(pj)])
        sd = float(m.std(ddof=1))
        mean = float(m.mean())
        out["m(%s,%s)" % (pi, pj)] = {
            "E_m": mean, "sd_m": sd,
            "snr": (abs(mean) / sd) if sd > 0 else None,
        }
    return out


def measure_hard_ceiling(mats_measured: list) -> dict:
    """Do tran TX bang median p99 cua cac link-run co p99 > 1.0."""
    tops = []
    for X in mats_measured:
        for j in range(X.shape[1]):
            p99 = float(np.percentile(X[:, j], 99))
            if p99 > HARD_CEILING_PROBE_MIN:
                tops.append(p99)
    if not tops:
        return {"hard_ceiling_measured": 1.0, "n_saturated_link_runs": 0,
                "framing_overhead_percent": 0.0,
                "censoring_threshold": CEILING_SAFETY,
                "note": "Khong link-run nao bao hoa; dung tran dinh nghia 1.0."}
    ceiling = float(np.median(tops))
    return {
        "hard_ceiling_measured": ceiling,
        "n_saturated_link_runs": len(tops),
        "framing_overhead_percent": (ceiling - 1.0) * 100.0,
        "censoring_threshold": ceiling * CEILING_SAFETY,
        "p99_candidates": tops,
        "note": ("Tran DO DUOC. Moi gate censoring dung ceiling*0.995, "
                 "khong dung 0.99 mac dinh."),
    }


def collect(campaign: str):
    """Ghep measured/offered cung run; bo run thieu du lieu offered."""
    rows = []
    paths = sorted(glob.glob(os.path.join(
        campaign, "**", "rho_measured_clean_*.csv"), recursive=True))
    for path in paths:
        tag = (os.path.basename(path)
               .replace("rho_measured_", "").replace(".csv", ""))
        flowdir = os.path.join(os.path.dirname(path), "flows_%s" % tag)
        if not os.path.isdir(flowdir):
            continue
        measured = load_run(path)
        if measured.shape[0] < 10:
            continue
        offered = load_offered(flowdir, measured.shape[0])
        rows.append({"tag": tag, "cell": cell_of(path), "M": measured,
                     "O": offered, "path": path})
    return rows


def adjudicate(R_hi, R_nc) -> tuple[str, str, bool, bool]:
    m276 = R_nc is not None and NC_LO <= R_nc <= NC_HI
    m275 = R_hi is not None and R_HIT_LO <= R_hi <= R_HIT_HI
    if not m276:
        return ("NEGATIVE_CONTROL_FAILED_STOP",
                "DOI CHUNG AM HONG: DUNG; khong doc M-275.", m275, m276)
    if m275:
        return ("SNR_IS_REAL_D3_MAY_PROCEED",
                "D3 thi hanh tren clean@0.960.", m275, m276)
    if R_hi is not None and R_hi > R_HIT_HI:
        return ("SNR_IS_CENSORING_ARTIFACT",
                "Khong chay 23.26 tren 0.960; dung cell da khoa.", m275, m276)
    return ("CENSORING_HIDES_SIGNAL",
            "23.26 phai doi dau vao; khong dung rho_measured.", m275, m276)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    source_hash_before_run = {path: _sha256(path) for path in T0_T11_SOURCES}
    canonical_before_run = _canonical_hash(t0_t11_canonical())
    if canonical_before_run != T0_T11_CANONICAL_SHA256_BEFORE:
        raise RuntimeError("T0..T11 khong khop hash da khoa truoc T12")

    rows = collect(args.campaign)
    if not rows:
        raise SystemExit("khong tim thay cap measured/flows CLEAN hoan chinh")

    ceiling = measure_hard_ceiling([row["M"] for row in rows])
    threshold = ceiling["censoring_threshold"]
    per_run, by_cell_acc = {}, defaultdict(lambda: defaultdict(list))
    for row in rows:
        sm, so = snr_by_pair(row["M"]), snr_by_pair(row["O"])
        p_cens = float(np.mean(row["M"] > threshold))
        ratios = []
        for pair in ["m(%s,%s)" % p for p in PATH_PAIRS]:
            measured_snr, offered_snr = sm[pair]["snr"], so[pair]["snr"]
            if measured_snr is None or offered_snr is None or offered_snr <= 0:
                continue
            ratio = measured_snr / offered_snr
            ratios.append(ratio)
            by_cell_acc[row["cell"]]["ratio"].append(ratio)
            by_cell_acc[row["cell"]]["snr_measured"].append(measured_snr)
            by_cell_acc[row["cell"]]["snr_offered"].append(offered_snr)
        by_cell_acc[row["cell"]]["p_censored"].append(p_cens)
        by_cell_acc[row["cell"]]["clip_share_offered"].append(so["_clip_share"])
        by_cell_acc[row["cell"]]["clip_share_measured"].append(sm["_clip_share"])
        per_run[row["tag"]] = {
            "cell": row["cell"], "p_censored": p_cens,
            "clip_share_measured": sm["_clip_share"],
            "clip_share_offered": so["_clip_share"],
            "median_ratio": float(np.median(ratios)) if ratios else None,
            "snr_measured": {k: v["snr"] for k, v in sm.items()
                             if k.startswith("m(")},
            "snr_offered": {k: v["snr"] for k, v in so.items()
                            if k.startswith("m(")},
        }

    by_cell = {}
    for cell, acc in sorted(by_cell_acc.items()):
        by_cell[cell] = {
            "R_median_snr_measured_over_offered": float(np.median(acc["ratio"])),
            "snr_measured_median": float(np.median(acc["snr_measured"])),
            "snr_offered_median": float(np.median(acc["snr_offered"])),
            "p_censored_median": float(np.median(acc["p_censored"])),
            "clip_share_offered_median": float(
                np.median(acc["clip_share_offered"])),
            "clip_share_measured_median": float(
                np.median(acc["clip_share_measured"])),
            "n_runs": len(acc["p_censored"]),
        }

    cells = sorted(by_cell)
    p_vec = [by_cell[cell]["p_censored_median"] for cell in cells]
    r_vec = [by_cell[cell]["R_median_snr_measured_over_offered"]
             for cell in cells]
    rho, pvalue = spearmanr(p_vec, r_vec) if len(cells) > 2 else (None, None)
    R_hi = by_cell.get("clean@0.960", {}).get(
        "R_median_snr_measured_over_offered")
    R_nc = by_cell.get("clean@0.700", {}).get(
        "R_median_snr_measured_over_offered")
    verdict, action, m275, m276 = adjudicate(R_hi, R_nc)

    eligible = [cell for cell in cells
                if by_cell[cell]["p_censored_median"]
                <= CLEAN_CELL_MAX_P_CENSORED]
    chosen = (max(eligible, key=lambda cell:
                  by_cell[cell]["snr_offered_median"])
              if eligible else "clean@0.850")

    source_hash_after_run = {path: _sha256(path) for path in T0_T11_SOURCES}
    canonical_after_run = _canonical_hash(t0_t11_canonical())
    nc_passed = bool(
        source_hash_before_run == source_hash_after_run
        and source_hash_before_run == SOURCE_FILE_SHA256_BEFORE
        and canonical_before_run == canonical_after_run
        == T0_T11_CANONICAL_SHA256_BEFORE)
    if not nc_passed:
        raise RuntimeError("G23-336 FAIL: T0..T11 da doi")

    import measurements.snr_censoring_artifact as _self
    report = {
        "schema": "dt4n.snr_censoring_artifact.v1",
        "lesson": "23.25f", "prereg": "docs/phase-23/A082-amendment-82.md",
        "status": "MEASUREMENT_ESTIMATE",
        "locked_constants": {
            "MODE": MODE, "W_LOSS": W_LOSS,
            "HARD_CEILING_PROBE_MIN": HARD_CEILING_PROBE_MIN,
            "CEILING_SAFETY": CEILING_SAFETY,
            "R_HIT_LO": R_HIT_LO, "R_HIT_HI": R_HIT_HI,
            "NC_LO": NC_LO, "NC_HI": NC_HI,
            "CLEAN_CELL_MAX_P_CENSORED": CLEAN_CELL_MAX_P_CENSORED,
        },
        "G23_335_hard_ceiling": ceiling,
        "by_cell": by_cell, "per_run": per_run,
        "M_275_R_at_0_960": R_hi, "M_275_hit": bool(m275),
        "M_276_R_at_0_700_negative_control": R_nc,
        "M_276_hit": bool(m276),
        "M_278_spearman_p_censored_vs_R": {
            "rho": None if rho is None else float(rho),
            "pvalue": None if pvalue is None else float(pvalue),
            "n_cells": len(cells)},
        "G23_334_verdict": verdict, "action_required": action,
        "cell_choice_for_23_26": {
            "rule": ("SNR_offered cao nhat trong cell p_censored<=%.2f; "
                     "neu rong dung clean@0.850" % CLEAN_CELL_MAX_P_CENSORED),
            "eligible_cells": eligible, "chosen": chosen,
            "actionable_only_if_M276_hit": bool(m276)},
        "G23_336_T0_T11_unchanged": {
            "canonical_sha256_before": canonical_before_run,
            "canonical_sha256_after": canonical_after_run,
            "source_file_sha256_before": source_hash_before_run,
            "source_file_sha256_after": source_hash_after_run,
            "passed": nc_passed},
        "provenance": _provenance(
            "measurements/snr_censoring_artifact.py",
            {"campaign": args.campaign, "out": args.out}),
        "validity": V.measurement_validity_block(
            instrument_module=_self, inputs=[row["path"] for row in rows][:1],
            note=("Do SNR tren measured/offered de tach artifact censoring; "
                  "co dung truc SLA qua W_LOSS=K06.")),
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("[T12] tran cung do duoc = %.4f  (overhead %.2f%%)  nguong = %.4f"
          % (ceiling["hard_ceiling_measured"],
             ceiling["framing_overhead_percent"],
             ceiling["censoring_threshold"]))
    print("%-14s %9s %11s %11s %8s %10s"
          % ("cell", "p_cens", "SNR_meas", "SNR_off", "R", "clip_off"))
    for cell in cells:
        value = by_cell[cell]
        print("%-14s %9.4f %11.4f %11.4f %8.3f %10.4f"
              % (cell, value["p_censored_median"],
                 value["snr_measured_median"],
                 value["snr_offered_median"],
                 value["R_median_snr_measured_over_offered"],
                 value["clip_share_offered_median"]))
    print("[T12] M-276 doi chung am R(0.700)=%s hit=%s"
          % (None if R_nc is None else round(R_nc, 3), m276))
    print("[T12] M-275 R(0.960)=%s hit=%s"
          % (None if R_hi is None else round(R_hi, 3), m275))
    print("[T12] verdict=%s" % verdict)
    print("[T12] cell cho 23.26 = %s  (eligible=%s, actionable=%s)"
          % (chosen, eligible, m276))


if __name__ == "__main__":
    main()

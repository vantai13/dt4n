#!/usr/bin/env python3
"""Lesson 23.25g -- phan ra R=R_num/R_den va truy lech thoi gian.

Tien dang ky: docs/phase-23/A083-amendment-83.md. KHONG do moi.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict

import numpy as np

from measurements import validity as V
from measurements.link_corr_matrix import (
    IDX, LINKS, MODE, PATH_PAIRS, W_LOSS, _provenance)
from measurements.snr_censoring_artifact import collect
from twin import cost_v2 as C
from twin import topology_v7 as T7

MAX_LAG_SAMPLES = 50
DT_S = 0.2
NOISY_PAIRS = (("uA", "uB"), ("vC", "vD"))
SOURCE_SHA256_BEFORE = {
    "results/LIVE/phase-23/link_corr_matrix.json":
        "6a753c1a6e7791682b74ebd8e0eef5a4ab8f451614f5c05a02f5b55835e8e291",
    "results/LIVE/phase-23/lesson_23_25_final_audit.json":
        "64cdf9f579dd9ac5719c07e7059aaddeb138c0211e1d9fd4df0183ae1e44ce78",
    "results/LIVE/phase-23/snr_censoring_artifact.json":
        "db513321903413d8b0bc194ab2ea9c68341b9ad0ce330d9a3596026faf9f3ffe",
}


def _sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def margin_stats(X: np.ndarray) -> dict:
    """Tra `abs(E[m])` va `sd(m)` cho 6 cap, chua tao ti so."""
    Xc = np.clip(X, C.RHO_MIN, C.RHO_MAX)
    cv = C.CostV2(strict_reliable=False)
    _delay, _loss, cost = cv.tables_batch(Xc, MODE, W_LOSS)
    out = {}
    for pi, pj in PATH_PAIRS:
        margin = (cost[:, T7.PATH_NAMES.index(pi)]
                  - cost[:, T7.PATH_NAMES.index(pj)])
        out["m(%s,%s)" % (pi, pj)] = {
            "abs_E_m": abs(float(margin.mean())),
            "sd_m": float(margin.std(ddof=1)),
        }
    return out


def noisy_pairs_in_margin(pi: str, pj: str) -> int:
    """Dem cap residual T9 vao margin voi dau nguoc nhau."""
    coef = defaultdict(int)
    for link in T7.PATHS[pi]:
        coef[link] += 1
    for link in T7.PATHS[pj]:
        coef[link] -= 1
    return sum(1 for a, b in NOISY_PAIRS
               if coef[a] != 0 and coef[b] != 0 and coef[a] * coef[b] < 0)


def best_lag(measured: np.ndarray, offered: np.ndarray) -> dict:
    """Quet correlation tai lag [-50,50]; lag duong = measured tre."""
    a = np.asarray(measured, dtype=float)
    b = np.asarray(offered, dtype=float)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    best, best_r = 0, -2.0
    for lag in range(-MAX_LAG_SAMPLES, MAX_LAG_SAMPLES + 1):
        if lag >= 0:
            x, y = a[lag:], b[:n - lag]
        else:
            x, y = a[:n + lag], b[-lag:]
        if len(x) < 50 or x.std() <= 0 or y.std() <= 0:
            continue
        r = float(np.corrcoef(x, y)[0, 1])
        if r > best_r:
            best, best_r = lag, r
    return {"best_lag_samples": int(best),
            "best_lag_s": float(best * DT_S),
            "r_at_best_lag": float(best_r),
            "at_scan_boundary": bool(abs(best) == MAX_LAG_SAMPLES)}


def summarize(values) -> dict | None:
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)],
                   dtype=float)
    if not v.size:
        return None
    return {"n": int(v.size), "min": float(v.min()),
            "median": float(np.median(v)),
            "p25": float(np.percentile(v, 25)),
            "p75": float(np.percentile(v, 75)),
            "max": float(v.max())}


def ratio_sensitivity(acc: dict) -> dict:
    """Bao cao median-of-ratio va ratio-of-medians, khong loai mau."""
    num = summarize(acc["R_num"])
    den = summarize(acc["R_den"])
    em = summarize(acc["abs_E_measured"])
    eo = summarize(acc["abs_E_offered"])
    sm = summarize(acc["sd_measured"])
    so = summarize(acc["sd_offered"])
    return {
        "R_num_median_of_ratio": num,
        "R_den_median_of_ratio": den,
        "R_num_ratio_of_medians": em["median"] / eo["median"],
        "R_den_ratio_of_medians": sm["median"] / so["median"],
        "abs_E_measured": em, "abs_E_offered_denominator": eo,
        "sd_measured": sm, "sd_offered_denominator": so,
        "R_num_relative_difference_between_summaries": abs(
            num["median"] - em["median"] / eo["median"])
            / max(num["median"], 1e-15),
    }


def adjudicate(all_summary: dict, max_abs_lag: int) -> str:
    if max_abs_lag > 1:
        return "TIME_MISALIGNMENT_SUSPECTED"
    r_den = all_summary["R_den_median_of_ratio"]["median"]
    r_num = all_summary["R_num_median_of_ratio"]["median"]
    if r_den < 0.95:
        return "SD_COMPRESSION_CORRELATED_RESIDUAL"
    if r_num > 1.10:
        return "MEAN_SHIFT_SHORTFALL"
    return "NO_DOMINANT_MECHANISM"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    before = {path: _sha256(path) for path in SOURCE_SHA256_BEFORE}
    if before != SOURCE_SHA256_BEFORE:
        raise RuntimeError("T0..T12 source khong khop hash da khoa truoc T13")
    rows = collect(args.campaign)
    if not rows:
        raise SystemExit("khong tim thay cap measured/flows CLEAN")

    acc = defaultdict(lambda: defaultdict(list))
    per_run, lag_rows, mean_shift = {}, [], defaultdict(list)
    for row in rows:
        sm, so = margin_stats(row["M"]), margin_stats(row["O"])
        rec = {}
        for pi, pj in PATH_PAIRS:
            key = "m(%s,%s)" % (pi, pj)
            nnz = noisy_pairs_in_margin(pi, pj)
            em, eo = sm[key]["abs_E_m"], so[key]["abs_E_m"]
            sdm, sdo = sm[key]["sd_m"], so[key]["sd_m"]
            num = em / eo if eo > 0 else None
            den = sdm / sdo if sdo > 0 else None
            rec[key] = {
                "abs_E_m_measured": em, "abs_E_m_offered": eo,
                "sd_m_measured": sdm, "sd_m_offered": sdo,
                "R_num": num, "R_den": den,
                "n_noisy_pairs_in_margin": nnz,
            }
            for group in (row["cell"], "_all", "_bynoisy_%d" % nnz):
                acc[group]["R_num"].append(num)
                acc[group]["R_den"].append(den)
                acc[group]["abs_E_measured"].append(em)
                acc[group]["abs_E_offered"].append(eo)
                acc[group]["sd_measured"].append(sdm)
                acc[group]["sd_offered"].append(sdo)

        for link in LINKS:
            lag = best_lag(row["M"][:, IDX[link]], row["O"][:, IDX[link]])
            lag.update({"run": row["tag"], "cell": row["cell"], "link": link})
            lag_rows.append(lag)
            mean_shift[link].append(float(
                row["M"][:, IDX[link]].mean() - row["O"][:, IDX[link]].mean()))
        per_run[row["tag"]] = {"cell": row["cell"], "by_pair": rec}

    by_cell = {cell: ratio_sensitivity(acc[cell])
               for cell in sorted(acc) if not cell.startswith("_")}
    by_noisy = {key.replace("_bynoisy_", "n_noisy="):
                ratio_sensitivity(acc[key]) for key in sorted(acc)
                if key.startswith("_bynoisy_")}
    all_summary = ratio_sensitivity(acc["_all"])

    abs_lags = np.asarray([abs(row["best_lag_samples"]) for row in lag_rows])
    max_abs_lag = int(abs_lags.max())
    alignment = {
        "max_abs_lag_samples": max_abs_lag,
        "max_abs_lag_s": float(max_abs_lag * DT_S),
        "median_abs_lag_samples": float(np.median(abs_lags)),
        "p90_abs_lag_samples": float(np.percentile(abs_lags, 90)),
        "n_over_1_sample": int(np.sum(abs_lags > 1)),
        "n_at_scan_boundary": int(sum(row["at_scan_boundary"] for row in lag_rows)),
        "n_link_runs": len(lag_rows), "scan_range_s": MAX_LAG_SAMPLES * DT_S,
        "per_run_and_link": lag_rows,
    }
    verdict = adjudicate(all_summary, max_abs_lag)
    after = {path: _sha256(path) for path in SOURCE_SHA256_BEFORE}
    if after != before:
        raise RuntimeError("T0..T12 source da doi trong luc T13")

    import measurements.snr_decomposition as _self
    report = {
        "schema": "dt4n.snr_decomposition.v1", "lesson": "23.25g",
        "prereg": "docs/phase-23/A083-amendment-83.md",
        "status": "MEASUREMENT_ESTIMATE",
        "locked_constants": {"MODE": MODE, "W_LOSS": W_LOSS,
                             "MAX_LAG_SAMPLES": MAX_LAG_SAMPLES,
                             "DT_S": DT_S,
                             "NOISY_PAIRS": [list(pair) for pair in NOISY_PAIRS]},
        "R_decomposition_all": all_summary,
        "by_cell": by_cell, "by_n_noisy_pairs": by_noisy,
        "time_alignment": alignment,
        "mean_shift_measured_minus_offered_by_link": {
            link: summarize(values) for link, values in sorted(mean_shift.items())},
        "per_run": per_run, "verdict": verdict,
        "NC_T0_T12_unchanged": {"source_sha256_before": before,
                                "source_sha256_after": after,
                                "passed": before == after},
        "provenance": _provenance(
            "measurements/snr_decomposition.py",
            {"campaign": args.campaign, "out": args.out}),
        "validity": V.measurement_validity_block(
            instrument_module=_self, inputs=[row["path"] for row in rows][:1],
            note="Phan ra R; co dung truc SLA qua W_LOSS=K06."),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    rn = all_summary["R_num_median_of_ratio"]
    rd = all_summary["R_den_median_of_ratio"]
    print("[T13] R_num median-of-ratio=%.4f [%.3f, %.3f]; ratio-of-medians=%.4f"
          % (rn["median"], rn["p25"], rn["p75"],
             all_summary["R_num_ratio_of_medians"]))
    print("[T13] R_den median-of-ratio=%.4f [%.3f, %.3f]; ratio-of-medians=%.4f"
          % (rd["median"], rd["p25"], rd["p75"],
             all_summary["R_den_ratio_of_medians"]))
    print("[T13] min |E[m]| offered=%.6g; R_num summary gap=%.1f%%"
          % (all_summary["abs_E_offered_denominator"]["min"],
             100 * all_summary["R_num_relative_difference_between_summaries"]))
    print("%-14s %10s %10s" % ("cell", "R_num", "R_den"))
    for cell, value in by_cell.items():
        print("%-14s %10.4f %10.4f" % (
            cell, value["R_num_median_of_ratio"]["median"],
            value["R_den_median_of_ratio"]["median"]))
    print("%-14s %10s %10s" % ("lop nhieu", "R_num", "R_den"))
    for key, value in by_noisy.items():
        print("%-14s %10.4f %10.4f" % (
            key, value["R_num_median_of_ratio"]["median"],
            value["R_den_median_of_ratio"]["median"]))
    print("[T13] lag max=%d (%.1fs), median=%.1f, p90=%.1f, >1=%d/%d, boundary=%d"
          % (max_abs_lag, max_abs_lag * DT_S,
             alignment["median_abs_lag_samples"],
             alignment["p90_abs_lag_samples"], alignment["n_over_1_sample"],
             alignment["n_link_runs"], alignment["n_at_scan_boundary"]))
    print("[T13] verdict=%s" % verdict)


if __name__ == "__main__":
    main()

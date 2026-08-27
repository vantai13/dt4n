#!/usr/bin/env python3
"""A081 -- T5b/T9/T10/T11 de dong Lesson 23.25 nhu doi chung am."""
from __future__ import annotations

import argparse
import glob
import hashlib
import itertools
import json
import os
import re
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr

from measurements import validity as V
from measurements.host_confound_probe import load_offered
from measurements.link_corr_matrix import (
    IDX, K_PAIR, LINKS, LOAD_CHANNELS, PATH_PAIRS, _provenance, load_run,
    margin_vector, shares_host, structured_matrix)
from twin import topology_v7 as T7

CORE_LINKS = ("ac", "ad", "bc", "bd")
EDGE_LINKS = ("uA", "uB", "vC", "vD")


def _canonical_hash(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_separate_output(out: str, *sources: str) -> None:
    if os.path.abspath(out) in {os.path.abspath(path) for path in sources}:
        raise ValueError("--out phai la artifact rieng, khong duoc ghi de nguon")


def t0_t8_block(report: dict) -> dict:
    return {k: v for k, v in report.items()
            if re.match(r"^T[0-8](?:\D|$)", k)}


def profile_median(campaign: str, field: str) -> dict:
    per = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(campaign, "**", "meta_*.json"),
                                 recursive=True)):
        with open(path, encoding="utf-8") as fh:
            profile = json.load(fh).get("profile", {})
        for link, row in profile.items():
            if field in row:
                per[link].append(float(row[field]))
    return {link: float(np.median(per[link])) for link in LINKS if per[link]}


def var_margin_cov(R: np.ndarray, omega: float, sd: dict) -> dict:
    """T5b: covariance design-target `D R D`; T5 cu correlation giu nguyen."""
    D = np.diag([float(sd[l]) for l in LINKS])
    Rw, R1 = structured_matrix(omega), structured_matrix(1.0)
    out = {"sd_by_link_used": {l: float(sd[l]) for l in LINKS},
           "sd_source": "median meta::profile::sigma_target"}
    for pi, pj in PATH_PAIRS:
        v = margin_vector(pi, pj)
        vd = D @ v
        base = float(vd @ vd)
        name = "m(%s,%s)" % (pi, pj)
        out[name] = {
            "var_identity_scaled": base,
            "var_measured_cov": float(vd @ R @ vd),
            "var_structured_at_omega_hat": float(vd @ Rw @ vd),
            "ratio_measured_over_identity": float(vd @ R @ vd) / base,
            "ratio_at_omega_1_analytic": float(vd @ R1 @ vd) / base,
            "shared_link": bool(set(T7.PATHS[pi]) & set(T7.PATHS[pj])),
        }
    out["_note"] = ("Design-target covariance, khong phai empirical covariance. "
                    "Moi phat bieu dung sigma target phai trich T5b; T5 giu lich su.")
    return out


def empirical_margin_covariance(mats) -> dict:
    """T5c mo ta: ratio covariance empirical trong tung run, khong dung target sd."""
    acc = defaultdict(list)
    for X in mats:
        cov = np.cov(X, rowvar=False, ddof=1)
        diag = np.diag(np.diag(cov))
        for pi, pj in PATH_PAIRS:
            v = margin_vector(pi, pj)
            base = float(v @ diag @ v)
            if base > 0.0:
                acc["m(%s,%s)" % (pi, pj)].append(float(v @ cov @ v) / base)
    return {name: {"median_ratio": float(np.median(vals)),
                   "mean_ratio": float(np.mean(vals)),
                   "min_ratio": float(np.min(vals)),
                   "max_ratio": float(np.max(vals)),
                   "n_runs": len(vals)}
            for name, vals in sorted(acc.items())}


def contrast_2x2(R: np.ndarray) -> dict:
    groups = defaultdict(list)
    rows = []
    for a, b in itertools.combinations(LINKS, 2):
        k = round(float(K_PAIR[(a, b)]), 4)
        shared = shares_host(a, b)
        r = float(R[IDX[a], IDX[b]])
        groups[(k, shared)].append(r)
        rows.append({"pair": "%s-%s" % (a, b), "k": k,
                     "shared_host": shared, "r": r})
    table = {}
    for k in (0.0, 0.5, 0.7071):
        for shared in (False, True):
            vals = groups.get((k, shared), [])
            table["k=%s|shared_host=%s" % (k, shared)] = {
                "n": len(vals), "mean_r": (float(np.mean(vals)) if vals else None),
                "values": [float(x) for x in vals],
            }
    r05 = table["k=0.5|shared_host=False"]["mean_r"]
    r00 = table["k=0.0|shared_host=False"]["mean_r"]
    return {"table": table, "all_28_pairs": rows,
            "omega_descriptive_no_shared_host_contrast": float((r05 - r00) / 0.5),
            "warning": ("Descriptive contrast; k=0.5 va k=0 co the khac loai "
                        "link/thang thoi gian. Khong la causal clean estimate.")}


def attenuation_ceiling_check(R: np.ndarray, nugget: dict) -> dict:
    signal, projected = {}, []
    for link in LINKS:
        value = nugget["per_link"][link].get("signal_fraction")
        if value is None:
            value = 1.0
            projected.append(link)
        signal[link] = float(value)
    rows, violations = {}, []
    for a, b in itertools.combinations(LINKS, 2):
        r = float(R[IDX[a], IDX[b]])
        ceiling = float(np.sqrt(signal[a] * signal[b]))
        exceeds = abs(r) > ceiling
        name = "%s-%s" % (a, b)
        rows[name] = {"r_measured": r,
                      "ceiling_if_lag0_residual_independent": ceiling,
                      "excess_ratio": float(abs(r) / ceiling),
                      "exceeds": bool(exceeds),
                      "signal_fraction_projected_to_1":
                          bool(a in projected or b in projected)}
        if exceeds:
            violations.append(name)
    return {"signal_fraction_used": signal,
            "projected_to_1_links": projected, "per_pair": rows,
            "pairs_violating_independent_residual_ceiling": violations,
            "n_violations": len(violations),
            "verdict": ("LAG0_RESIDUAL_IS_CROSS_CORRELATED_PROVEN"
                        if violations else "INDEPENDENT_RESIDUAL_NOT_REFUTED"),
            "note": ("Model-free voi signal fraction da chap nhan. Vuot tran "
                     "chung minh residual lag-0 cross-correlated; host probe "
                     "moi quy no cho execution/measurement shortfall.")}


def host_dose_response(R: np.ndarray, nconc: dict) -> dict:
    total = defaultdict(float)
    for link, value in nconc.items():
        for host in LOAD_CHANNELS[link]:
            total[host] += value
    rows = []
    for a, b in itertools.combinations(LINKS, 2):
        shared = sorted(set(LOAD_CHANNELS[a]) & set(LOAD_CHANNELS[b]))
        if not shared or K_PAIR[(a, b)] != 0.0:
            continue
        host = shared[0]
        rows.append({"pair": "%s-%s" % (a, b), "shared_host": host,
                     "pair_process_dose": float(nconc[a] + nconc[b]),
                     "total_endpoint_dose": float(total[host]),
                     "r_measured": float(R[IDX[a], IDX[b]])})
    pair_dose = np.asarray([x["pair_process_dose"] for x in rows])
    total_dose = np.asarray([x["total_endpoint_dose"] for x in rows])
    rvals = np.asarray([x["r_measured"] for x in rows])
    rho_pair, p_pair = spearmanr(np.log(pair_dose), rvals)
    rho_total, p_total = spearmanr(np.log(total_dose), rvals)
    return {"n_concurrent_by_link": nconc,
            "total_endpoint_dose_by_host": dict(sorted(total.items())),
            "null_shared_host_pairs": rows,
            "spearman_log_pair_process_dose_vs_r": float(rho_pair),
            "spearman_pair_pvalue": float(p_pair),
            "spearman_log_total_endpoint_dose_vs_r": float(rho_total),
            "spearman_total_pvalue": float(p_total),
            "n_pairs": len(rows),
            "note": ("Hai dose duoc khoa truoc. Neu ket luan doi theo dinh "
                     "nghia dose, khong phat bieu nhan qua tong host load.")}


def censoring_audit(campaign: str) -> dict:
    per_run, grouped = {}, defaultdict(list)
    paths = sorted(glob.glob(os.path.join(
        campaign, "**", "rho_measured_clean_*.csv"), recursive=True))
    for path in paths:
        tag = os.path.basename(path).replace("rho_measured_", "").replace(".csv", "")
        flowdir = os.path.join(os.path.dirname(path), "flows_%s" % tag)
        if not os.path.isdir(flowdir):
            continue
        M = load_run(path)
        O = load_offered(flowdir, M.shape[0])
        cell = tag.rsplit("_rep", 1)[0].replace("clean_rho", "clean@")
        for i, link in enumerate(LINKS):
            so, sm = float(O[:, i].std(ddof=1)), float(M[:, i].std(ddof=1))
            row = {"mean_offered": float(O[:, i].mean()),
                   "mean_measured": float(M[:, i].mean()),
                   "sd_offered": so, "sd_measured": sm,
                   "sd_ratio_measured_over_offered": sm / so if so > 0 else None,
                   "p_measured_gt_0_99": float(np.mean(M[:, i] > 0.99)),
                   "p_measured_ge_offered_p99": float(
                       np.mean(M[:, i] >= np.percentile(O[:, i], 99))),
                   "measured_p99": float(np.percentile(M[:, i], 99)),
                   "offered_p99": float(np.percentile(O[:, i], 99))}
            per_run["%s|%s" % (tag, link)] = row
            grouped[(cell, link)].append(row)
    by_cell = {}
    for (cell, link), rows in sorted(grouped.items()):
        by_cell["%s|%s" % (cell, link)] = {
            key + "_median": float(np.median([r[key] for r in rows]))
            for key in ("sd_ratio_measured_over_offered", "p_measured_gt_0_99",
                        "p_measured_ge_offered_p99", "measured_p99", "offered_p99")}
    focus = [by_cell["clean@0.960|%s" % link]
             ["sd_ratio_measured_over_offered_median"] for link in CORE_LINKS]
    p99_focus = [by_cell["clean@0.960|%s" % link]["p_measured_gt_0_99_median"]
                 for link in CORE_LINKS]
    m274_hit = bool(np.median(focus) <= 0.60)
    hard_ceiling = bool(max(p99_focus) > 0.10)
    return {"per_run_and_link": per_run, "by_cell_and_link": by_cell,
            "M274_core_clean_0_960_median_sd_ratio": float(np.median(focus)),
            "M274_prediction_hit": m274_hit,
            "core_clean_0_960_sd_ratio_by_link": dict(zip(CORE_LINKS, focus)),
            "core_clean_0_960_p_gt_0_99_by_link": dict(zip(CORE_LINKS, p99_focus)),
            "hard_ceiling_monitor_threshold": 0.10,
            "hard_ceiling_monitor_fired": hard_ceiling,
            "saturation_evidence_present": bool(m274_hit or hard_ceiling),
            "note": ("M-274 chi cham median sd_ratio<=0.60. Monitor tran cung "
                     "p(measured>0.99)>0.10 duoc bao cao rieng; no la dau hieu "
                     "saturation/censoring, khong tu no chung minh co che queue. "
                     "Offered la demand generator; measured la TX service.")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--corr-artifact", required=True)
    ap.add_argument("--nugget-artifact", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(a.corr_artifact, encoding="utf-8") as fh:
        corr_art = json.load(fh)
    with open(a.nugget_artifact, encoding="utf-8") as fh:
        nugget = json.load(fh)
    R = np.asarray(corr_art["T1_corr_matrix_within_run"]["R"], dtype=float)
    paths = sorted(glob.glob(os.path.join(
        a.campaign, "**", "rho_measured_clean_*.csv"), recursive=True))
    mats = [load_run(path) for path in paths]
    mats = [X for X in mats if X.shape[0] >= 10]
    sigma = profile_median(a.campaign, "sigma_target")
    nconc = profile_median(a.campaign, "n_concurrent")
    omega = corr_art["T2_omega"]["omega_hat_corrected"]
    source_block = t0_t8_block(corr_art)
    source_hash_before = _canonical_hash(source_block)

    validate_separate_output(a.out, a.corr_artifact, a.nugget_artifact)

    import measurements.lesson_23_25_final_audit as _self
    report = {
        "schema": "dt4n.lesson_23_25_final_audit.v1", "lesson": "23.25e",
        "prereg": "docs/phase-23/A081-amendment-81.md",
        "status": "MEASUREMENT_ESTIMATE",
        "contrast_2x2": contrast_2x2(R),
        "T5b_var_margin_target_covariance": var_margin_cov(R, omega, sigma),
        "T5c_var_margin_empirical_covariance": empirical_margin_covariance(mats),
        "T9_attenuation_ceiling": attenuation_ceiling_check(R, nugget),
        "T10_host_dose_response": host_dose_response(R, nconc),
        "T11_censoring_audit": censoring_audit(a.campaign),
        "NC_T0_T8_external_append_only": {
            "source_t0_t8_sha256_before": source_hash_before,
            "source_keys": sorted(source_block),
            "output_is_separate_file": True,
            "note": "Audit ghi artifact rieng; doi chieu hash truoc/sau tinh toan."},
        "provenance": _provenance(
            "measurements/lesson_23_25_final_audit.py",
            {"campaign": a.campaign, "corr_artifact": a.corr_artifact,
             "nugget_artifact": a.nugget_artifact, "out": a.out}),
        "validity": V.measurement_validity_block(
            instrument_module=_self, inputs=paths[:1] + [a.corr_artifact,
                                                        a.nugget_artifact],
            note="Offline final audit T5b/T9/T10/T11; khong do Mininet moi."),
    }
    with open(a.corr_artifact, encoding="utf-8") as fh:
        source_after = t0_t8_block(json.load(fh))
    source_hash_after = _canonical_hash(source_after)
    nc = report["NC_T0_T8_external_append_only"]
    nc["source_t0_t8_sha256_after"] = source_hash_after
    nc["passed"] = bool(source_hash_after == source_hash_before)
    if not nc["passed"]:
        raise RuntimeError("corr artifact T0..T8 da doi trong luc audit")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    c = report["contrast_2x2"]
    print("[final] omega contrast no-shared-host=%+.4f" %
          c["omega_descriptive_no_shared_host_contrast"])
    t5 = report["T5b_var_margin_target_covariance"]
    vals = [t5["m(%s,%s)" % p]["ratio_measured_over_identity"] for p in PATH_PAIRS]
    adj = [t5["m(%s,%s)" % p]["ratio_at_omega_1_analytic"] for p in PATH_PAIRS
           if set(T7.PATHS[p[0]]) & set(T7.PATHS[p[1]])]
    print("[final:T5b] measured ratio %.4f..%.4f adjacent omega1=%.4f" %
          (min(vals), max(vals), float(np.mean(adj))))
    t9 = report["T9_attenuation_ceiling"]
    print("[final:T9] violations=%s verdict=%s" %
          (t9["pairs_violating_independent_residual_ceiling"], t9["verdict"]))
    t10 = report["T10_host_dose_response"]
    print("[final:T10] Spearman pair-dose=%+.4f total-dose=%+.4f n=%d" %
          (t10["spearman_log_pair_process_dose_vs_r"],
           t10["spearman_log_total_endpoint_dose_vs_r"], t10["n_pairs"]))
    t11 = report["T11_censoring_audit"]
    print("[final:T11] core@0.960 median sd_ratio=%.4f M274_hit=%s "
          "hard_ceiling=%s saturation_evidence=%s" %
          (t11["M274_core_clean_0_960_median_sd_ratio"],
           t11["M274_prediction_hit"], t11["hard_ceiling_monitor_fired"],
           t11["saturation_evidence_present"]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""A084 -- T14/T15/T16/T17 append-only closeout cua Lesson 23.25."""
from __future__ import annotations

import argparse
import glob
import hashlib
import itertools
import json
import os

import numpy as np

from measurements import validity as V
from measurements.link_corr_matrix import (
    IDX, K_PAIR, LINKS, NULL_PAIRS, PATH_PAIRS, S_PAIRS, _provenance,
    err_bivariate, load_run, pooled_corr, shares_host, structured_matrix)
from twin import topology_v7 as T7

K_SIGNAL = 0.5
JACKKNIFE_SPREAD_WARN = 0.075
N_SLICES = 3
WARMUP_DELTA_WARN = 0.10
OMEGA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
LEGACY_V1 = {"adjacent": 1.70711, "crossed": 1.94281}
ADJACENT_PAIRS = ("m(P1,P2)", "m(P1,P3)", "m(P2,P4)", "m(P3,P4)")
CORR_SHA256_LOCKED = (
    "6a753c1a6e7791682b74ebd8e0eef5a4ab8f451614f5c05a02f5b55835e8e291")


def _sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if (a, b) in K_PAIR else (b, a)


def clean_pairs(drop_link: str | None = None):
    """Signal k=.5 va baseline k=0; ca hai loai moi shared-host."""
    signal, baseline = [], []
    for a, b in itertools.combinations(LINKS, 2):
        if drop_link is not None and drop_link in (a, b):
            continue
        if shares_host(a, b):
            continue
        k = float(K_PAIR[(a, b)])
        if np.isclose(k, K_SIGNAL):
            signal.append((a, b))
        elif np.isclose(k, 0.0):
            baseline.append((a, b))
    return signal, baseline


def omega_contrast(R: np.ndarray, drop_link: str | None = None):
    signal, baseline = clean_pairs(drop_link)
    if not signal or not baseline:
        return None
    s = np.asarray([R[IDX[a], IDX[b]] for a, b in signal])
    n = np.asarray([R[IDX[a], IDX[b]] for a, b in baseline])
    return {"omega": float((s.mean() - n.mean()) / K_SIGNAL),
            "mean_signal": float(s.mean()), "n_signal": int(s.size),
            "mean_baseline": float(n.mean()), "n_baseline": int(n.size)}


def jackknife_by_link(R: np.ndarray) -> dict:
    full = omega_contrast(R)
    loo_full = {link: omega_contrast(R, drop_link=link) for link in LINKS}
    if full is None or any(value is None for value in loo_full.values()):
        raise ValueError("drop-link lam rong tap signal/baseline")
    vals = np.asarray([loo_full[link]["omega"] for link in LINKS])
    n = len(vals)
    sd_desc = float(np.sqrt((n - 1) / n * np.sum((vals - vals.mean()) ** 2)))
    sign_flip = bool(vals.min() < 0.0 < vals.max())
    spread = float(vals.max() - vals.min())
    return {
        "label": "PRIMARY_DESCRIPTIVE_UNCERTAINTY_FOR_OMEGA",
        "omega_full": full["omega"], "full_contrast": full,
        "leave_one_out": {link: float(loo_full[link]["omega"])
                          for link in LINKS},
        "leave_one_out_details": loo_full,
        "loo_min": float(vals.min()), "loo_max": float(vals.max()),
        "loo_range": spread, "sd_jackknife_descriptive": sd_desc,
        "sign_flips_under_loo": sign_flip,
        "noise_floor_abs_omega": float(max(abs(vals.min()), abs(vals.max()))),
        "verdict": ("NOT_IDENTIFIABLE_SIGN_UNDETERMINED"
                    if sign_flip or spread > 2 * JACKKNIFE_SPREAD_WARN
                    else "IDENTIFIABLE_DESCRIPTIVELY_STABLE"),
        "note": ("Leave-one-link values share pairs; sd is descriptive, "
                 "not an asymptotic SE. Cite range/noise floor."),
    }


def _robust_null_level(R: np.ndarray) -> float:
    return float(np.median([R[IDX[a], IDX[b]] for a, b in NULL_PAIRS]))


def time_slice_audit(mats: list[np.ndarray]) -> dict:
    out = {}
    for slice_idx in range(N_SLICES):
        sub = []
        lengths = []
        for X in mats:
            n = X.shape[0]
            lo, hi = n * slice_idx // N_SLICES, n * (slice_idx + 1) // N_SLICES
            if hi - lo >= 10:
                sub.append(X[lo:hi])
                lengths.append(hi - lo)
        if not sub:
            continue
        R_slice, n_runs = pooled_corr(sub)
        contrast = omega_contrast(R_slice)
        null_vals = [R_slice[IDX[a], IDX[b]] for a, b in NULL_PAIRS]
        out["slice_%d" % (slice_idx + 1)] = {
            "n_runs": n_runs,
            "n_samples_per_run_median": int(np.median(lengths)),
            "b_hat_median_null": _robust_null_level(R_slice),
            "b_hat_mean_null": float(np.mean(null_vals)),
            "omega_contrast": None if contrast is None else contrast["omega"],
        }
    b = [out[key]["b_hat_median_null"] for key in sorted(out)]
    later = float(np.mean(b[1:])) if len(b) > 1 else float("nan")
    delta = float(b[0] - later) if np.isfinite(later) else None
    detected = bool(delta is not None and delta > WARMUP_DELTA_WARN)
    out["_summary"] = {
        "b_hat_by_slice": [float(value) for value in b],
        "b_hat_first_minus_later": delta,
        "b_hat_spread": float(max(b) - min(b)),
        "warmup_detected": detected,
        "verdict": ("WARMUP_TRANSIENT_SUSPECTED_MUST_TRIM" if detected
                    else "STATIONARY_NO_TRIM_NEEDED"),
        "note": "Difference, not ratio; later null level may cross zero.",
    }
    return out


def null_partners(a: str, b: str) -> dict:
    def side(keep: str, other: str):
        pairs = []
        for candidate in LINKS:
            if candidate in (keep, other):
                continue
            pair = _pair_key(keep, candidate)
            if np.isclose(K_PAIR[pair], 0.0) and not shares_host(*pair):
                pairs.append(pair)
        return pairs
    return {"hold_a": side(a, b), "hold_b": side(b, a)}


def paired_null_table(R: np.ndarray) -> dict:
    rows = []
    for a, b in S_PAIRS:
        partners = null_partners(a, b)
        null_pairs = list(dict.fromkeys(partners["hold_a"] + partners["hold_b"]))
        null_values = {"%s-%s" % pair: float(R[IDX[pair[0]], IDX[pair[1]]])
                       for pair in null_pairs}
        max_null = max(null_values.values()) if null_values else None
        mean_null = float(np.mean(list(null_values.values()))) if null_values else None
        r_struct = float(R[IDX[a], IDX[b]])
        survives = bool(max_null is not None and r_struct > max_null)
        k = float(K_PAIR[(a, b)])
        rows.append({
            "structured_pair": "%s-%s" % (a, b), "k": k,
            "shared_host": shares_host(a, b), "r_structured": r_struct,
            "null_partners_hold_a": ["%s-%s" % pair
                                     for pair in partners["hold_a"]],
            "null_partners_hold_b": ["%s-%s" % pair
                                     for pair in partners["hold_b"]],
            "null_values": null_values, "r_null_mean": mean_null,
            "r_null_max": max_null, "survives_strict_null": survives,
            "excess_over_mean_per_k": ((r_struct - mean_null) / k
                                       if mean_null is not None and k > 0 else None),
            "excess_over_max_per_k": ((r_struct - max_null) / k
                                      if max_null is not None and k > 0 else None),
        })
    survived = sum(row["survives_strict_null"] for row in rows)
    group = {}
    for shared in (False, True):
        values = [row["excess_over_mean_per_k"] for row in rows
                  if row["shared_host"] is shared]
        group["shared_host=%s" % shared] = {
            "n": len(values), "mean_excess_over_k": float(np.mean(values)),
            "median_excess_over_k": float(np.median(values))}
    nohost = group["shared_host=False"]["mean_excess_over_k"]
    verdict = ("NULLS_CANCEL_STRUCTURE"
               if survived <= 6 and -0.10 <= nohost <= 0.10
               else "STRUCTURE_SURVIVES_NULLS")
    return {"rows": rows, "n_structured_pairs": len(rows),
            "n_survives_strict_null": survived,
            "by_shared_host": group, "verdict": verdict}


def err_grid(snr: float, r: float, v1: float) -> dict:
    e0 = err_bivariate(float(snr), float(r))
    row = {}
    for omega in OMEGA_GRID:
        inflation = 1.0 + omega * (float(v1) - 1.0)
        adjusted_snr = float(snr) / np.sqrt(inflation)
        err = err_bivariate(adjusted_snr, float(r))
        row["omega_%.2f" % omega] = {
            "var_inflation": float(inflation), "snr": adjusted_snr,
            "err": float(err),
            "ratio_to_omega0": float(err / e0) if e0 > 0 else None}
    return row


def err_sensitivity(corr_artifact: dict, final_audit: dict) -> dict:
    t6 = corr_artifact["T6_snr_and_decision"]
    r_by_pair = corr_artifact["T8_identifiability"]["margin_acf_measured"][
        "by_path_pair"]
    t5b = final_audit["T5b_var_margin_target_covariance"]
    rows = {}
    effects = []
    effects_legacy = []
    for key, snr in sorted(t6["snr_by_cell_and_pair"].items()):
        cell, pair = [part.strip() for part in key.split("|")]
        cls = "adjacent" if pair in ADJACENT_PAIRS else "crossed"
        r = float(r_by_pair[pair]["r_margin_at_requested_z"])
        v1 = float(t5b[pair]["ratio_at_omega_1_analytic"])
        grid = err_grid(float(snr), r, v1)
        legacy_grid = err_grid(float(snr), r, LEGACY_V1[cls])
        effect = 100.0 * (grid["omega_1.00"]["ratio_to_omega0"] - 1.0)
        effect_legacy = 100.0 * (
            legacy_grid["omega_1.00"]["ratio_to_omega0"] - 1.0)
        effects.append(effect)
        effects_legacy.append(effect_legacy)
        rows[key] = {"cell": cell, "pair": pair, "class": cls,
                     "snr_pilot_measured": float(snr), "r_measured": r,
                     "v1_target_covariance": v1, "grid": grid,
                     "effect_pct_omega1": effect,
                     "legacy_unit_variance_effect_pct": effect_legacy}

    snr_nc = 0.375
    r_measured = min(float(value["r_margin_at_requested_z"])
                     for value in r_by_pair.values())
    r_legacy = float(t6["r_at_z_median"])
    v_nc = float(t5b["m(P1,P4)"]["ratio_at_omega_1_analytic"])
    measured_grid = err_grid(snr_nc, r_measured, v_nc)
    legacy_r_grid = err_grid(snr_nc, r_legacy, v_nc)
    ratio_measured = measured_grid["omega_1.00"]["ratio_to_omega0"]
    ratio_legacy = legacy_r_grid["omega_1.00"]["ratio_to_omega0"]
    level_ratio = (measured_grid["omega_0.00"]["err"]
                   / legacy_r_grid["omega_0.00"]["err"])
    nc = {"snr": snr_nc, "r_measured": r_measured, "r_legacy": r_legacy,
          "err_level_ratio": float(level_ratio),
          "ratio_with_r_measured": float(ratio_measured),
          "ratio_with_r_legacy": float(ratio_legacy),
          "absolute_difference": float(abs(ratio_measured - ratio_legacy)),
          "passed": bool(level_ratio > 3.0
                         and abs(ratio_measured - ratio_legacy) < 0.01)}
    return {
        "headline_parameterization": "T5b_TARGET_COVARIANCE_L154",
        "conditional_on": "pilot measured SNR T6; magnitude remains undecided",
        "rows": rows, "n_rows": len(rows),
        "bound_pct_at_median": float(np.median(effects)),
        "bound_pct_worst_case": float(np.max(effects)),
        "bound_pct_min": float(np.min(effects)),
        "worst_case_key": max(rows, key=lambda key: rows[key]["effect_pct_omega1"]),
        "legacy_unit_variance": {
            "median_effect_pct": float(np.median(effects_legacy)),
            "worst_effect_pct": float(np.max(effects_legacy)),
            "note": "Historical only; superseded by T5b/L154."},
        "NC_ratio_invariant_to_r_correction": nc,
    }


def collect_clean(campaign: str):
    paths = sorted(glob.glob(os.path.join(
        campaign, "**", "rho_measured_clean_*.csv"), recursive=True))
    mats = [load_run(path) for path in paths]
    keep = [(path, X) for path, X in zip(paths, mats) if X.shape[0] >= 10]
    return [item[1] for item in keep], [item[0] for item in keep]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--corr-artifact", required=True)
    ap.add_argument("--final-audit",
                    default="results/LIVE/phase-23/lesson_23_25_final_audit.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    before = _sha256(args.corr_artifact)
    if before != CORR_SHA256_LOCKED:
        raise RuntimeError("corr artifact khong khop hash A084")
    with open(args.corr_artifact, encoding="utf-8") as fh:
        corr = json.load(fh)
    with open(args.final_audit, encoding="utf-8") as fh:
        final = json.load(fh)
    R = np.asarray(corr["T1_corr_matrix_within_run"]["R"], dtype=float)
    mats, paths = collect_clean(args.campaign)
    if not mats:
        raise SystemExit("khong co run CLEAN hop le")

    t14 = jackknife_by_link(R)
    t15 = time_slice_audit(mats)
    t16 = paired_null_table(R)
    t17 = err_sensitivity(corr, final)
    after = _sha256(args.corr_artifact)
    if after != before:
        raise RuntimeError("NC-84-5 FAIL: corr artifact da doi")

    import measurements.lesson_23_25_closeout as _self
    report = {
        "schema": "dt4n.lesson_23_25_closeout.v1", "lesson": "23.25-closeout",
        "prereg": "docs/phase-23/A084-amendment-84.md",
        "status": "MEASUREMENT_ESTIMATE", "n_runs": len(mats),
        "instrument_history": ("First pre-final run used max(NULL) for both "
                               "strict survival and M-288 mean excess. Before "
                               "commit, split into max for survival and mean "
                               "for M-288; source data and thresholds unchanged."),
        "T14_jackknife_by_link": t14, "T15_time_slice_audit": t15,
        "T16_paired_null_table": t16, "T17_err_omega_sensitivity": t17,
        "NC_84_5_append_only": {"corr_sha256_before": before,
                                "corr_sha256_after": after,
                                "passed": before == after},
        "provenance": _provenance(
            "measurements/lesson_23_25_closeout.py",
            {"campaign": args.campaign, "corr_artifact": args.corr_artifact,
             "final_audit": args.final_audit, "out": args.out}),
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=paths[:1] + [args.corr_artifact, args.final_audit],
            note="Offline append-only closeout T14--T17; no new Mininet data."),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("[T14] omega_full=%+.4f LOO [%+.4f,%+.4f] floor=%.3f verdict=%s"
          % (t14["omega_full"], t14["loo_min"], t14["loo_max"],
             t14["noise_floor_abs_omega"], t14["verdict"]))
    summary = t15["_summary"]
    print("[T15] b_hat slices=%s delta=%+.4f verdict=%s"
          % ([round(value, 4) for value in summary["b_hat_by_slice"]],
             summary["b_hat_first_minus_later"], summary["verdict"]))
    print("[T16] survives=%d/%d nohost excess/k=%+.4f verdict=%s"
          % (t16["n_survives_strict_null"], t16["n_structured_pairs"],
             t16["by_shared_host"]["shared_host=False"]["mean_excess_over_k"],
             t16["verdict"]))
    print("[T17] target-cov effect median=%+.2f%% worst=%+.2f%% at %s"
          % (t17["bound_pct_at_median"], t17["bound_pct_worst_case"],
             t17["worst_case_key"]))
    nc = t17["NC_ratio_invariant_to_r_correction"]
    print("[T17:NC] err level x%.2f ratio delta=%.6f passed=%s"
          % (nc["err_level_ratio"], nc["absolute_difference"], nc["passed"]))


if __name__ == "__main__":
    main()

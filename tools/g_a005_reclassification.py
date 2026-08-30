#!/usr/bin/env python3
"""Post-hoc G-A005 reclassification of the locked G-A004 FAIL.

This diagnostic does not change any G-A004 threshold or verdict.  It asks a
narrower question: can the failed physical result identify which component of
the deployed calibration-plus-two-band pipeline caused the failure?
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from mininet.run_sync_v7 import LINK_ENDPOINTS
from tools.g_a003_split_sample import (
    DT_TARGET_S,
    MEASURED_INPUT,
    OFFERED_INPUT,
    aggregate_offered,
    load_by_link,
    sha256,
)
from tools.measurement_path_calib import estimate_two_band


CALIBRATION = Path("results/SMOKE/phase-G/g_a003_split_calibration.json")
POWER = Path("results/SMOKE/phase-G/g_a004_paired_power.json")
HELD_OUT = Path("results/SMOKE/phase-G/g_a004_split_sample.json")
FULL_RUN = Path("results/SMOKE/phase-G/g1_4_physical_reanalysis.json")
COHERENCE = Path("results/SMOKE/phase-G/g_measurement_coherence.json")
POWER_TOOL = Path("tools/g_a004_paired_power.py")
OUT = Path("results/SMOKE/phase-G/g_a005_reclassification.json")

EDGE_LINKS = ("uA", "uB", "vC", "vD")
PAIR = ("uA", "uB")
DERIVATIVE_STEP = 1e-4


def git_hash() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fit_pair(
    measured: dict[str, np.ndarray],
    test_slice: slice,
    sf: dict[str, float],
    phi: dict[str, float],
    truth: float,
) -> dict[str, object]:
    left, right = PAIR
    fit = estimate_two_band(
        measured[left][test_slice],
        measured[right][test_slice],
        sf[left],
        sf[right],
        phi[left],
        phi[right],
    )
    return {
        "sf": {left: sf[left], right: sf[right]},
        "r_true_hat": float(fit["r_true_hat"]),
        "rho_eps_hat": float(fit["rho_eps_hat"]),
        "cond_A": float(fit["cond_A"]),
        "absolute_error": abs(float(fit["r_true_hat"]) - truth),
        "pair_gate_pass": abs(float(fit["r_true_hat"]) - truth) <= 0.10,
    }


def build() -> dict[str, object]:
    calibration = _read(CALIBRATION)
    power = _read(POWER)
    held_out = _read(HELD_OUT)
    full = _read(FULL_RUN)["cellA_long"]
    coherence = _read(COHERENCE)

    measured = load_by_link(MEASURED_INPUT, "rho")
    offered = aggregate_offered(
        load_by_link(OFFERED_INPUT, "rho_offered"), len(measured["uA"])
    )
    split_index = int(calibration["split"]["split_index"])
    test_slice = slice(split_index, len(measured["uA"]))
    truth = float(np.corrcoef(offered["uA"][test_slice], offered["uB"][test_slice])[0, 1])

    half1 = {
        link: calibration["per_link"][link]["measured_calibration"]
        for link in EDGE_LINKS
    }
    phi = {
        link: float(np.exp(-DT_TARGET_S / float(half1[link]["tau_from_fit_s"])))
        for link in EDGE_LINKS
    }
    sf_half1 = {link: float(half1[link]["sf"]) for link in EDGE_LINKS}
    sf_full = {link: float(full["per_link"][link]["sf"]) for link in EDGE_LINKS}

    v2 = {
        link: 2.0 * float(full["per_link"][link]["v"]) - float(half1[link]["v"])
        for link in EDGE_LINKS
    }
    # Sensitivity only: this conversion assumes the full-run signal variance
    # transfers unchanged to the second half.
    sf_second_inferred = {
        link: float(full["per_link"][link]["sigma_true"]) ** 2
        / (float(full["per_link"][link]["sigma_true"]) ** 2 + v2[link])
        for link in EDGE_LINKS
    }

    solves = {
        "first_half_G_A004": _fit_pair(
            measured, test_slice, sf_half1, phi, truth
        ),
        "full_run_posthoc": _fit_pair(measured, test_slice, sf_full, phi, truth),
        "second_half_inferred_posthoc": _fit_pair(
            measured, test_slice, sf_second_inferred, phi, truth
        ),
    }
    solves["second_half_inferred_posthoc"]["assumption"] = (
        "v2=2*v_full-v1 and full-run signal variance is unchanged"
    )

    def estimate_with_shift(du_a: float, du_b: float) -> float:
        changed = dict(sf_half1)
        changed["uA"] += du_a
        changed["uB"] += du_b
        return float(
            _fit_pair(measured, test_slice, changed, phi, truth)["r_true_hat"]
        )

    h = DERIVATIVE_STEP
    derivatives = {
        "step": h,
        "dr_dsf_uA": (estimate_with_shift(h, 0.0) - estimate_with_shift(-h, 0.0)) / (2.0 * h),
        "dr_dsf_uB": (estimate_with_shift(0.0, h) - estimate_with_shift(0.0, -h)) / (2.0 * h),
        "dr_dcommon_sf_shift": (estimate_with_shift(h, h) - estimate_with_shift(-h, -h)) / (2.0 * h),
    }

    model_class_violations = {
        link: {
            "sf": float(row["sf"]),
            "v": float(row["v"]),
            "estimator_ok": bool(row["ok"]),
            "classification": "OUTSIDE_PHYSICAL_DOMAIN_MODEL_CLASS_WARNING",
        }
        for link, row in full["per_link"].items()
        if float(row["sf"]) > 1.0 and float(row["v"]) < 0.0
    }

    pair_grouping = {}
    for name, row in held_out["pairs"].items():
        left, right = name.split("-")
        same_tx_node = LINK_ENDPOINTS[left][0] == LINK_ENDPOINTS[right][0]
        pair_grouping[name] = {
            "tx_nodes": [LINK_ENDPOINTS[left][0], LINK_ENDPOINTS[right][0]],
            "same_tx_node": same_tx_node,
            "rho_eps_hat": float(row["rho_eps_hat"]),
            "rho_eps_ge_0p50": float(row["rho_eps_hat"]) >= 0.50,
        }

    paths = (CALIBRATION, POWER, HELD_OUT, FULL_RUN, COHERENCE, POWER_TOOL)
    return {
        "schema": "dt4n.phase_g.g_a005_reclassification.v1",
        "status": "POST_HOC_RECLASSIFICATION_COMPLETE",
        "scope": {
            "changes_G_A004_numeric_verdict": False,
            "G_A004_verdict": held_out["summary"]["verdict"],
            "G1_closed": False,
            "pipeline_certified": False,
            "component_cause_identified_by_G_A004": False,
            "cause_classification": "NON_IDENTIFYING_AMONG_NUISANCE_ERROR_MODEL_MISSPECIFICATION_AND_TWO_BAND_DEFECT",
        },
        "pipeline_mismatch": {
            "power_stage": "simulates with locked sf/phi and gives the same values directly to estimate_two_band",
            "physical_stage": "estimates sf/phi on first half and transfers them to second-half estimate_two_band",
            "full_pipeline_refit_in_power": False,
            "power_all_six_probability": float(power["gates"]["all_pairs_success_probability"]),
            "conclusion": "the power calculation calibrated a conditional solver, not the deployed nuisance-estimation-plus-solver pipeline",
        },
        "uA_uB_sensitivity": {
            "r_offered_held_out": truth,
            "r_measured_held_out": float(held_out["pairs"]["uA-uB"]["r_measured"]),
            "phi_fixed_from_first_half": {link: phi[link] for link in PAIR},
            "solves": solves,
            "local_derivatives_at_first_half_sf": derivatives,
        },
        "coherence": {
            "W_star_s": coherence["summary"]["W_star_s_largest_all_link_pass"],
            "all_link_pass_by_window": coherence["summary"]["all_link_pass_by_window"],
            "interpretation": "fixed-configuration nuisance transfer is rejected on every identifiable signed window",
        },
        "model_class_warnings": model_class_violations,
        "H6_grouping_posthoc": {
            "old_H6b_same_telemetry_side_retained_as_confirmatory": False,
            "candidate_H6c": "high rho_eps iff both link counters are on interfaces transmitted by the same switch node",
            "pairs": pair_grouping,
            "warning": "formed after outcomes; descriptive only until tested on fresh/direct static-control data",
        },
        "custody": {
            "raw_outcomes_already_burned": True,
            "data_manifest_doi": _read(Path("results/DATA_MANIFEST.json")).get("doi"),
            "input_sha256": {str(path): sha256(path) for path in paths},
        },
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_a005_reclassification.py",
        },
    }


def main() -> None:
    artifact = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print("G-A004 numeric verdict:", artifact["scope"]["G_A004_verdict"], "(unchanged)")
    print("component-cause classification:", artifact["scope"]["cause_classification"])
    print("uA-uB sf sensitivity")
    for source, row in artifact["uA_uB_sensitivity"]["solves"].items():
        print("  %-34s r_hat=%.6f error=%.6f cond=%.3f" % (
            source, row["r_true_hat"], row["absolute_error"], row["cond_A"]
        ))
    print("artifact:", OUT)


if __name__ == "__main__":
    main()

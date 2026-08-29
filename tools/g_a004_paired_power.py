#!/usr/bin/env python3
"""G-A004 direct paired-power gate and held-out split test.

``power`` uses only the frozen first-half calibration artifact and synthetic
data.  ``test`` can read the held-out half only after the preregistration tag
exists and the paired-power artifact passes its locked gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.g_a003_split_sample import (
    DT_TARGET_S,
    EDGE_LINKS,
    EDGE_PAIRS,
    MEASURED_INPUT,
    OFFERED_INPUT,
    aggregate_offered,
    load_by_link,
    sha256,
)
from tools.measurement_path_calib import estimate_two_band


CALIBRATION = Path("results/SMOKE/phase-G/g_a003_split_calibration.json")
POWER_OUT = Path("results/SMOKE/phase-G/g_a004_paired_power.json")
TEST_OUT = Path("results/SMOKE/phase-G/g_a004_split_sample.json")

CALIBRATION_SHA256 = "46a8cc8d49b9d1d6f182eaf10ba5ecea0a717931ef4f9d3daa68d9051fa80fd1"
PREREG_TAG = "phase-G-g-a004-prereg"
POWER_SEED = 20260830
POWER_REPETITIONS = 2_000
POWER_BATCH = 100
SYNTHETIC_R_TRUE = 0.0
RHO_EPS_SAME_SIDE = 0.65
RHO_EPS_CROSS_SIDE = 0.10
PAIR_ERROR_MAX = 0.10
MEDIAN_ERROR_MAX = 0.02
ALL_PAIRS_SUCCESS_PROB_MIN = 0.95
MEDIAN_SUCCESS_PROB_MIN = 0.90
WILSON_Z = 1.959963984540054
DYNAMIC_RANGE_MIN = 0.20


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_hash() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def prereg_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{PREREG_TAG}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(
            f"G-A004 remains sealed: missing preregistration tag {PREREG_TAG}"
        )
    return result.stdout.strip()


def load_calibration() -> dict[str, object]:
    actual = file_sha256(CALIBRATION)
    if actual != CALIBRATION_SHA256:
        raise RuntimeError(
            f"calibration artifact drift: expected {CALIBRATION_SHA256}, got {actual}"
        )
    artifact = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if artifact.get("held_out_correlations_read") is not False:
        raise RuntimeError("G-A004 requires the held-out correlations to remain unread")
    return artifact


def wilson_lower(successes: int, total: int) -> float:
    """Two-sided 95% Wilson interval lower endpoint for a binomial rate."""
    if total <= 0 or not 0 <= successes <= total:
        raise ValueError("invalid binomial counts")
    probability = successes / total
    z2 = WILSON_Z * WILSON_Z
    denominator = 1.0 + z2 / total
    center = probability + z2 / (2.0 * total)
    radius = WILSON_Z * math.sqrt(
        probability * (1.0 - probability) / total + z2 / (4.0 * total * total)
    )
    return (center - radius) / denominator


def noise_covariance() -> np.ndarray:
    side = {"uA": "source", "uB": "source", "vC": "dest", "vD": "dest"}
    covariance = np.eye(len(EDGE_LINKS))
    for i, left in enumerate(EDGE_LINKS):
        for j, right in enumerate(EDGE_LINKS):
            if i == j:
                continue
            covariance[i, j] = (
                RHO_EPS_SAME_SIDE
                if side[left] == side[right]
                else RHO_EPS_CROSS_SIDE
            )
    eigen_min = float(np.linalg.eigvalsh(covariance).min())
    if eigen_min <= 0.0:
        raise RuntimeError(f"locked nugget covariance is not positive definite: {eigen_min}")
    return covariance


def simulate_ar1_batch(
    rng: np.random.Generator,
    batch_size: int,
    n: int,
    phis: np.ndarray,
) -> np.ndarray:
    """Generate stationary, unit-variance independent AR(1) link signals."""
    series = np.empty((batch_size, len(phis), n), dtype=float)
    series[:, :, 0] = rng.standard_normal((batch_size, len(phis)))
    innovation_scale = np.sqrt(1.0 - phis * phis)
    innovations = rng.standard_normal((batch_size, len(phis), n - 1))
    for index in range(1, n):
        series[:, :, index] = (
            phis * series[:, :, index - 1]
            + innovation_scale * innovations[:, :, index - 1]
        )
    return series


def run_power() -> dict[str, object]:
    prereg = prereg_commit()
    calibration = load_calibration()
    n_test = int(calibration["split"]["n_test"])
    fits = {
        link: calibration["per_link"][link]["measured_calibration"]
        for link in EDGE_LINKS
    }
    sf = np.asarray([float(fits[link]["sf"]) for link in EDGE_LINKS])
    tau = np.asarray([float(fits[link]["tau_from_fit_s"]) for link in EDGE_LINKS])
    phi = np.exp(-DT_TARGET_S / tau)
    covariance = noise_covariance()
    cholesky = np.linalg.cholesky(covariance)
    rng = np.random.default_rng(POWER_SEED)

    errors = {f"{left}-{right}": [] for left, right in EDGE_PAIRS}
    all_success: list[bool] = []
    median_success: list[bool] = []
    medians: list[float] = []

    for start in range(0, POWER_REPETITIONS, POWER_BATCH):
        batch = min(POWER_BATCH, POWER_REPETITIONS - start)
        signal = simulate_ar1_batch(rng, batch, n_test, phi)
        independent_noise = rng.standard_normal((batch, len(EDGE_LINKS), n_test))
        nugget = np.einsum("ij,bjt->bit", cholesky, independent_noise)
        measured = (
            np.sqrt(sf)[None, :, None] * signal
            + np.sqrt(1.0 - sf)[None, :, None] * nugget
        )

        for replicate in range(batch):
            replicate_errors = []
            for left, right in EDGE_PAIRS:
                left_index = EDGE_LINKS.index(left)
                right_index = EDGE_LINKS.index(right)
                estimate = estimate_two_band(
                    measured[replicate, left_index],
                    measured[replicate, right_index],
                    float(sf[left_index]),
                    float(sf[right_index]),
                    float(phi[left_index]),
                    float(phi[right_index]),
                )
                if not estimate.get("valid"):
                    error = float("inf")
                else:
                    r_offered = float(np.corrcoef(
                        signal[replicate, left_index],
                        signal[replicate, right_index],
                    )[0, 1])
                    error = abs(float(estimate["r_true_hat"]) - r_offered)
                errors[f"{left}-{right}"].append(error)
                replicate_errors.append(error)
            median = float(np.median(replicate_errors))
            medians.append(median)
            all_success.append(max(replicate_errors) <= PAIR_ERROR_MAX)
            median_success.append(median < MEDIAN_ERROR_MAX)

    all_count = int(sum(all_success))
    median_count = int(sum(median_success))
    all_probability = all_count / POWER_REPETITIONS
    median_probability = median_count / POWER_REPETITIONS
    all_lower = wilson_lower(all_count, POWER_REPETITIONS)
    median_lower = wilson_lower(median_count, POWER_REPETITIONS)
    all_gate = all_lower >= ALL_PAIRS_SUCCESS_PROB_MIN
    median_gate = median_lower >= MEDIAN_SUCCESS_PROB_MIN

    per_pair = {}
    for name, values in errors.items():
        array = np.asarray(values)
        per_pair[name] = {
            "median_absolute_error": float(np.median(array)),
            "p95_absolute_error": float(np.percentile(array, 95)),
            "max_absolute_error": float(array.max()),
            "probability_error_at_most_pair_gate": float(np.mean(array <= PAIR_ERROR_MAX)),
        }

    artifact = {
        "schema": "dt4n.phase_g.g_a004_paired_power.v1",
        "status": "PREREGISTERED_SYNTHETIC_POWER_GATE",
        "held_out_correlations_read": False,
        "preregistration_tag": PREREG_TAG,
        "preregistration_commit": prereg,
        "calibration_artifact": str(CALIBRATION),
        "calibration_sha256": CALIBRATION_SHA256,
        "locked_design": {
            "seed": POWER_SEED,
            "repetitions": POWER_REPETITIONS,
            "batch_size": POWER_BATCH,
            "n_test": n_test,
            "dt_s": DT_TARGET_S,
            "r_true": SYNTHETIC_R_TRUE,
            "rho_eps_same_side": RHO_EPS_SAME_SIDE,
            "rho_eps_cross_side": RHO_EPS_CROSS_SIDE,
            "pair_error_max": PAIR_ERROR_MAX,
            "median_error_max_strict": MEDIAN_ERROR_MAX,
            "all_pairs_success_probability_min": ALL_PAIRS_SUCCESS_PROB_MIN,
            "median_success_probability_min": MEDIAN_SUCCESS_PROB_MIN,
            "decision_uses_wilson_95pct_lower_bound": True,
            "sf_by_link": {link: float(sf[i]) for i, link in enumerate(EDGE_LINKS)},
            "tau_s_by_link": {link: float(tau[i]) for i, link in enumerate(EDGE_LINKS)},
            "phi_by_link": {link: float(phi[i]) for i, link in enumerate(EDGE_LINKS)},
            "nugget_covariance": covariance.tolist(),
        },
        "per_pair": per_pair,
        "six_pair_median_error": {
            "median": float(np.median(medians)),
            "p90": float(np.percentile(medians, 90)),
            "p95": float(np.percentile(medians, 95)),
            "max": float(np.max(medians)),
        },
        "gates": {
            "all_pairs_success_count": all_count,
            "all_pairs_success_probability": all_probability,
            "all_pairs_success_probability_wilson_lower": all_lower,
            "all_pairs_power_gate_pass": all_gate,
            "median_success_count": median_count,
            "median_success_probability": median_probability,
            "median_success_probability_wilson_lower": median_lower,
            "median_power_gate_pass": median_gate,
            "overall_pass": bool(all_gate and median_gate),
        },
        "limitations": (
            "This proves feasibility under the locked additive-white-nugget and "
            "exponential-ACF model only. It does not promise physical-data PASS; "
            "a physical FAIL is evidence against the estimator/model combination."
        ),
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_a004_paired_power.py --stage power",
        },
    }
    POWER_OUT.parent.mkdir(parents=True, exist_ok=True)
    POWER_OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def run_test() -> dict[str, object]:
    prereg = prereg_commit()
    calibration = load_calibration()
    power = json.loads(POWER_OUT.read_text(encoding="utf-8"))
    if power.get("preregistration_commit") != prereg:
        raise RuntimeError("power artifact does not belong to the G-A004 preregistration")
    if power.get("held_out_correlations_read") is not False:
        raise RuntimeError("power stage unexpectedly read held-out correlations")
    if power.get("gates", {}).get("overall_pass") is not True:
        raise RuntimeError("paired-power gate did not pass; held-out test remains sealed")

    raw_hashes = {
        "measured": sha256(MEASURED_INPUT),
        "offered": sha256(OFFERED_INPUT),
    }
    if raw_hashes != calibration["input"]["sha256"]:
        raise RuntimeError("raw input digest changed after calibration")
    measured = load_by_link(MEASURED_INPUT, "rho")
    n_total = int(calibration["split"]["n_total"])
    offered = aggregate_offered(load_by_link(OFFERED_INPUT, "rho_offered"), n_total)
    test_slice = slice(int(calibration["split"]["split_index"]), n_total)

    pairs = {}
    for left, right in EDGE_PAIRS:
        name = f"{left}-{right}"
        if not (
            calibration["per_link"][left]["censoring_gate_pass"]
            and calibration["per_link"][right]["censoring_gate_pass"]
        ):
            raise RuntimeError(f"locked edge pair unexpectedly failed censoring: {name}")
        left_fit = calibration["per_link"][left]["measured_calibration"]
        right_fit = calibration["per_link"][right]["measured_calibration"]
        left_tau = float(left_fit["tau_from_fit_s"])
        right_tau = float(right_fit["tau_from_fit_s"])
        estimate = estimate_two_band(
            measured[left][test_slice],
            measured[right][test_slice],
            float(left_fit["sf"]),
            float(right_fit["sf"]),
            float(np.exp(-DT_TARGET_S / left_tau)),
            float(np.exp(-DT_TARGET_S / right_tau)),
        )
        r_offered = float(np.corrcoef(
            offered[left][test_slice], offered[right][test_slice]
        )[0, 1])
        r_measured = float(np.corrcoef(
            measured[left][test_slice], measured[right][test_slice]
        )[0, 1])
        absolute_error = (
            abs(float(estimate["r_true_hat"]) - r_offered)
            if estimate.get("valid") else float("nan")
        )
        pairs[name] = {
            "first": left,
            "second": right,
            "r_measured": r_measured,
            "r_offered": r_offered,
            **estimate,
            "absolute_error": absolute_error,
            "pair_error_gate_pass": bool(
                estimate.get("valid") and absolute_error <= PAIR_ERROR_MAX
            ),
        }

    max_abs_offered = max(abs(row["r_offered"]) for row in pairs.values())
    dynamic_pass = max_abs_offered >= DYNAMIC_RANGE_MIN
    median_error = float(np.median([row["absolute_error"] for row in pairs.values()]))
    pair_gates_pass = all(row["pair_error_gate_pass"] for row in pairs.values())
    median_gate_pass = median_error < MEDIAN_ERROR_MAX
    if not dynamic_pass:
        verdict = "INSUFFICIENT_DYNAMIC_RANGE"
    elif pair_gates_pass and median_gate_pass:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    artifact = {
        "schema": "dt4n.phase_g.g_a004_split_sample.v1",
        "status": "PREREGISTERED_HELD_OUT_SPLIT_SAMPLE",
        "preregistration_tag": PREREG_TAG,
        "preregistration_commit": prereg,
        "held_out_correlations_read": True,
        "calibration_sha256": CALIBRATION_SHA256,
        "power_artifact": str(POWER_OUT),
        "power_artifact_sha256": file_sha256(POWER_OUT),
        "split": calibration["split"],
        "locked_gates": {
            "pair_error_max": PAIR_ERROR_MAX,
            "median_error_max_strict": MEDIAN_ERROR_MAX,
            "dynamic_range_min": DYNAMIC_RANGE_MIN,
        },
        "pairs": pairs,
        "summary": {
            "edge_pairs_total": len(pairs),
            "edge_pairs_error_pass": sum(
                bool(row["pair_error_gate_pass"]) for row in pairs.values()
            ),
            "median_absolute_error": median_error,
            "max_absolute_error": max(row["absolute_error"] for row in pairs.values()),
            "max_abs_r_offered": max_abs_offered,
            "dynamic_range_gate_pass": dynamic_pass,
            "all_pair_error_gates_pass": pair_gates_pass,
            "median_error_gate_pass": median_gate_pass,
            "verdict": verdict,
            "G1_closed": verdict == "PASS",
        },
        "interpretation_scope": (
            "This held-out split validates paired reconstruction on historical "
            "cellA data. H6b remains post-hoc and reserved for fresh G1-B data."
        ),
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_a004_paired_power.py --stage test",
        },
    }
    TEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEST_OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def print_power(artifact: dict[str, object]) -> None:
    print("G-A004 paired-statistic synthetic power")
    print("held-out correlations read:", artifact["held_out_correlations_read"])
    print("%-9s %10s %10s %10s" % ("pair", "median", "p95", "max"))
    for name, row in artifact["per_pair"].items():
        print("%-9s %10.4f %10.4f %10.4f" % (
            name, row["median_absolute_error"], row["p95_absolute_error"],
            row["max_absolute_error"]
        ))
    gates = artifact["gates"]
    print("P(all six <= 0.10): %.4f; Wilson lower: %.4f" % (
        gates["all_pairs_success_probability"],
        gates["all_pairs_success_probability_wilson_lower"],
    ))
    print("P(median six < 0.02): %.4f; Wilson lower: %.4f" % (
        gates["median_success_probability"],
        gates["median_success_probability_wilson_lower"],
    ))
    print("verdict:", "PASS" if gates["overall_pass"] else "FAIL")
    print("artifact:", POWER_OUT)


def print_test(artifact: dict[str, object]) -> None:
    print("G-A004 held-out six-pair result")
    print("%-9s %9s %9s %9s %9s %9s" % (
        "pair", "r_meas", "r_offer", "r_hat", "rho_eps", "abs_err"))
    for name, row in artifact["pairs"].items():
        print("%-9s %9.4f %9.4f %9.4f %9.4f %9.4f" % (
            name, row["r_measured"], row["r_offered"], row["r_true_hat"],
            row["rho_eps_hat"], row["absolute_error"]
        ))
    summary = artifact["summary"]
    print("median absolute error: %.5f" % summary["median_absolute_error"])
    print("max absolute error: %.5f" % summary["max_absolute_error"])
    print("max abs r_offered: %.5f" % summary["max_abs_r_offered"])
    print("verdict:", summary["verdict"])
    print("G1 closed:", summary["G1_closed"])
    print("artifact:", TEST_OUT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("power", "test"), required=True)
    args = parser.parse_args()
    if args.stage == "power":
        print_power(run_power())
    else:
        print_test(run_test())


if __name__ == "__main__":
    main()

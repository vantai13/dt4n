#!/usr/bin/env python3
"""G-A003 split-sample power audit and held-out edge-pair validation.

The calibration stage reads only the first half of ``cellA_long``.  It locks
per-link censoring, nugget, and time-scale estimates.  The test stage refuses
to inspect held-out correlations until the preregistration tag exists, and it
short-circuits before outcome estimation when the temporal-power gate leaves
no eligible pair.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.measurement_path_calib import estimate_nugget, estimate_two_band


MEASURED_INPUT = Path("results/RAW/phase-D/cellA_long/rho_measured_rep1.csv")
OFFERED_INPUT = Path("results/RAW/phase-D/cellA_long/rho_offered_rep1.csv")
CALIBRATION_OUT = Path("results/SMOKE/phase-G/g_a003_split_calibration.json")
TEST_OUT = Path("results/SMOKE/phase-G/g_a003_split_sample.json")

ALL_LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
EDGE_LINKS = ("uA", "uB", "vC", "vD")
EDGE_PAIRS = tuple(
    (left, right)
    for index, left in enumerate(EDGE_LINKS)
    for right in EDGE_LINKS[index + 1 :]
)

DT_TARGET_S = 0.20
OFFERED_SAMPLES_PER_BIN = 20
N_FIT_LAGS = 8
K09 = 1.0094102536
CENSORING_FRACTION_MAX = 0.05
T_OVER_TAU_MIN = 50.0
PAIR_ERROR_MAX = 0.10
MEDIAN_ERROR_MAX = 0.02
DYNAMIC_RANGE_MULTIPLIER = 2.0
PREREG_TAG = "phase-G-g-a003-prereg"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_by_link(path: Path, value_column: str) -> dict[str, np.ndarray]:
    values: dict[str, list[float]] = {link: [] for link in ALL_LINKS}
    indices: dict[str, list[int]] = {link: [] for link in ALL_LINKS}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            link = row["link"]
            if link not in values:
                continue
            indices[link].append(int(row["sample_index"]))
            values[link].append(float(row[value_column]))

    output = {}
    for link in ALL_LINKS:
        if not values[link]:
            raise ValueError(f"{path}: missing link {link}")
        index = np.asarray(indices[link], dtype=int)
        if not np.array_equal(index, np.arange(len(index))):
            raise ValueError(f"{path}: non-contiguous sample_index for {link}")
        output[link] = np.asarray(values[link], dtype=float)
    return output


def aggregate_offered(
    raw: dict[str, np.ndarray], target_length: int
) -> dict[str, np.ndarray]:
    output = {}
    for link, values in raw.items():
        usable = len(values) - len(values) % OFFERED_SAMPLES_PER_BIN
        aggregated = values[:usable].reshape(-1, OFFERED_SAMPLES_PER_BIN).mean(axis=1)
        if len(aggregated) < target_length:
            raise ValueError(
                f"{link}: offered aggregation has {len(aggregated)} bins; "
                f"need {target_length}"
            )
        output[link] = aggregated[:target_length]
    return output


def git_hash() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def finite_positive(value: object) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(number) and number > 0.0)


def make_calibration() -> dict[str, object]:
    measured = load_by_link(MEASURED_INPUT, "rho")
    lengths = {len(values) for values in measured.values()}
    if len(lengths) != 1:
        raise ValueError(f"measured link lengths differ: {sorted(lengths)}")
    n_total = lengths.pop()
    split_index = n_total // 2
    if split_index * 2 != n_total:
        raise ValueError("G-A003 requires an exactly even 50/50 split")

    offered = aggregate_offered(
        load_by_link(OFFERED_INPUT, "rho_offered"), n_total
    )
    calibration_slice = slice(0, split_index)
    test_n = n_total - split_index
    test_duration_s = test_n * DT_TARGET_S

    per_link = {}
    for link in ALL_LINKS:
        measured_estimate = estimate_nugget(
            measured[link][calibration_slice], DT_TARGET_S, N_FIT_LAGS
        )
        offered_estimate = estimate_nugget(
            offered[link][calibration_slice], DT_TARGET_S, N_FIT_LAGS
        )
        measured_tau = float(measured_estimate.get("tau_from_fit_s", float("nan")))
        offered_tau = float(offered_estimate.get("tau_from_fit_s", float("nan")))
        censor_fraction = float(
            np.mean(offered[link][calibration_slice] > K09)
        )
        measured_power = (
            test_duration_s / measured_tau if finite_positive(measured_tau) else float("nan")
        )
        offered_power = (
            test_duration_s / offered_tau if finite_positive(offered_tau) else float("nan")
        )
        per_link[link] = {
            "class": "edge" if link in EDGE_LINKS else "core",
            "offered_censor_fraction": censor_fraction,
            "censoring_gate_pass": censor_fraction < CENSORING_FRACTION_MAX,
            "measured_calibration": measured_estimate,
            "offered_calibration": offered_estimate,
            "test_T_over_tau_measured": measured_power,
            "test_T_over_tau_offered": offered_power,
            "temporal_power_gate_pass": bool(
                measured_power >= T_OVER_TAU_MIN
                and offered_power >= T_OVER_TAU_MIN
            ),
        }

    pairs = {}
    for left, right in EDGE_PAIRS:
        name = f"{left}-{right}"
        links = (per_link[left], per_link[right])
        censor_pass = all(bool(row["censoring_gate_pass"]) for row in links)
        estimator_fit_pass = all(
            bool(row["measured_calibration"].get("ok"))
            and 0.0 < float(row["measured_calibration"].get("sf", float("nan"))) < 1.0
            and finite_positive(row["measured_calibration"].get("tau_from_fit_s"))
            and finite_positive(row["offered_calibration"].get("tau_from_fit_s"))
            for row in links
        )
        temporal_power_pass = all(
            bool(row["temporal_power_gate_pass"]) for row in links
        )
        pairs[name] = {
            "first": left,
            "second": right,
            "censoring_gate_pass": censor_pass,
            "calibration_estimator_gate_pass": estimator_fit_pass,
            "temporal_power_gate_pass": temporal_power_pass,
            "minimum_test_T_over_tau": float(
                min(
                    row[key]
                    for row in links
                    for key in (
                        "test_T_over_tau_measured",
                        "test_T_over_tau_offered",
                    )
                )
            ),
            "eligible_before_dynamic_range": bool(
                censor_pass and estimator_fit_pass and temporal_power_pass
            ),
        }

    artifact = {
        "schema": "dt4n.phase_g.g_a003_split_calibration.v1",
        "status": "CALIBRATION_HALF_ONLY_PRE_PREREG",
        "held_out_correlations_read": False,
        "input": {
            "measured_path": str(MEASURED_INPUT),
            "offered_path": str(OFFERED_INPUT),
            "sha256": {
                "measured": sha256(MEASURED_INPUT),
                "offered": sha256(OFFERED_INPUT),
            },
        },
        "split": {
            "rule": "first contiguous half calibration; second contiguous half test",
            "n_total": n_total,
            "split_index": split_index,
            "n_calibration": split_index,
            "n_test": test_n,
            "calibration_duration_s": split_index * DT_TARGET_S,
            "test_duration_s": test_duration_s,
        },
        "locked_constants": {
            "dt_target_s": DT_TARGET_S,
            "offered_samples_per_bin": OFFERED_SAMPLES_PER_BIN,
            "n_fit_lags": N_FIT_LAGS,
            "K09": K09,
            "censoring_fraction_max_strict": CENSORING_FRACTION_MAX,
            "T_over_tau_min": T_OVER_TAU_MIN,
            "pair_error_max": PAIR_ERROR_MAX,
            "median_error_max_strict": MEDIAN_ERROR_MAX,
            "dynamic_range_multiplier": DYNAMIC_RANGE_MULTIPLIER,
            "dynamic_range_min": DYNAMIC_RANGE_MULTIPLIER * PAIR_ERROR_MAX,
        },
        "per_link": per_link,
        "pairs": pairs,
        "summary": {
            "edge_pairs_total": len(EDGE_PAIRS),
            "edge_pairs_censoring_pass": sum(
                bool(row["censoring_gate_pass"]) for row in pairs.values()
            ),
            "edge_pairs_temporal_power_pass": sum(
                bool(row["temporal_power_gate_pass"]) for row in pairs.values()
            ),
            "edge_pairs_eligible_before_dynamic_range": sum(
                bool(row["eligible_before_dynamic_range"]) for row in pairs.values()
            ),
        },
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_a003_split_sample.py --stage calibrate",
        },
    }
    CALIBRATION_OUT.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_OUT.write_text(
        json.dumps(artifact, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    return artifact


def prereg_tag_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{PREREG_TAG}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"held-out data remain sealed: missing preregistration tag {PREREG_TAG}"
        )
    return result.stdout.strip()


def run_test() -> dict[str, object]:
    prereg_commit = prereg_tag_hash()
    calibration = json.loads(CALIBRATION_OUT.read_text(encoding="utf-8"))
    current_hashes = {
        "measured": sha256(MEASURED_INPUT),
        "offered": sha256(OFFERED_INPUT),
    }
    if current_hashes != calibration["input"]["sha256"]:
        raise RuntimeError("raw input digest changed after calibration")

    pairs = {
        name: {
            **row,
            "held_out_outcome_status": "NOT_EVALUATED_TEMPORAL_POWER_GATE",
        }
        for name, row in calibration["pairs"].items()
    }
    eligible = [
        name for name, row in pairs.items()
        if row["eligible_before_dynamic_range"]
    ]

    # The temporal gate is ordered before the dynamic-range and accuracy
    # gates.  If it rejects every pair, do not load either held-out ledger:
    # this preserves a genuinely sealed test half for a future valid design.
    if len(eligible) != len(EDGE_PAIRS):
        verdict = "INSUFFICIENT_POWER_PRE_OUTCOME"
        dynamic_range = {
            "status": "NOT_EVALUATED_TEMPORAL_POWER_GATE",
            "max_abs_r_offered": None,
            "gate_pass": None,
        }
        held_out_read = False
    else:
        measured = load_by_link(MEASURED_INPUT, "rho")
        n_total = int(calibration["split"]["n_total"])
        offered = aggregate_offered(
            load_by_link(OFFERED_INPUT, "rho_offered"), n_total
        )
        test_slice = slice(int(calibration["split"]["split_index"]), n_total)
        for name in eligible:
            row = pairs[name]
            left, right = row["first"], row["second"]
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
            r_offered = float(
                np.corrcoef(offered[left][test_slice], offered[right][test_slice])[0, 1]
            )
            r_measured = float(
                np.corrcoef(measured[left][test_slice], measured[right][test_slice])[0, 1]
            )
            error = (
                abs(float(estimate["r_true_hat"]) - r_offered)
                if estimate.get("valid") else float("nan")
            )
            row.update({
                "held_out_outcome_status": "EVALUATED",
                "r_offered": r_offered,
                "r_measured": r_measured,
                **estimate,
                "absolute_error": error,
            })

        max_abs_r = max(abs(float(pairs[name]["r_offered"])) for name in eligible)
        dynamic_pass = max_abs_r >= DYNAMIC_RANGE_MULTIPLIER * PAIR_ERROR_MAX
        dynamic_range = {
            "status": "EVALUATED",
            "max_abs_r_offered": max_abs_r,
            "gate_pass": dynamic_pass,
        }
        for name in eligible:
            pairs[name]["accuracy_gate_interpretable"] = dynamic_pass
            pairs[name]["accuracy_gate_pass"] = bool(
                dynamic_pass
                and pairs[name].get("valid")
                and float(pairs[name]["absolute_error"]) <= PAIR_ERROR_MAX
            )
        median_error = float(np.median([
            float(pairs[name]["absolute_error"]) for name in eligible
        ]))
        verdict = (
            "PASS"
            if (
                dynamic_pass
                and all(pairs[name]["accuracy_gate_pass"] for name in eligible)
                and median_error < MEDIAN_ERROR_MAX
            )
            else "FAIL" if dynamic_pass
            else "INSUFFICIENT_DYNAMIC_RANGE"
        )
        held_out_read = True

    artifact = {
        "schema": "dt4n.phase_g.g_a003_split_sample.v1",
        "status": "PREREGISTERED_HELD_OUT_SPLIT_SAMPLE",
        "preregistration_tag": PREREG_TAG,
        "preregistration_commit": prereg_commit,
        "held_out_correlations_read": held_out_read,
        "calibration_artifact": str(CALIBRATION_OUT),
        "split": calibration["split"],
        "locked_constants": calibration["locked_constants"],
        "pairs": pairs,
        "dynamic_range_gate": dynamic_range,
        "summary": {
            "edge_pairs_total": len(EDGE_PAIRS),
            "edge_pairs_eligible_before_dynamic_range": len(eligible),
            "edge_pairs_accuracy_pass": (
                sum(bool(pairs[name].get("accuracy_gate_pass")) for name in eligible)
                if held_out_read else 0
            ),
            "median_absolute_error": (
                median_error if held_out_read else None
            ),
            "verdict": verdict,
            "G1_closed": verdict == "PASS",
        },
        "interpretation_scope": (
            "H6b thresholds were formed from the full historical cellA run. "
            "They are not tested confirmatorily here; they remain locked for fresh G1-B data."
        ),
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_a003_split_sample.py --stage test",
        },
    }
    TEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEST_OUT.write_text(
        json.dumps(artifact, indent=2, allow_nan=True) + "\n", encoding="utf-8"
    )
    return artifact


def print_calibration(artifact: dict[str, object]) -> None:
    print("G-A003 calibration half (held-out correlations NOT read)")
    print("%-7s %10s %11s %11s %10s" % (
        "link", "p_censor", "T/tau_meas", "T/tau_offer", "power"))
    for link in ALL_LINKS:
        row = artifact["per_link"][link]
        print("%-7s %10.4f %11.2f %11.2f %10s" % (
            link,
            row["offered_censor_fraction"],
            row["test_T_over_tau_measured"],
            row["test_T_over_tau_offered"],
            "PASS" if row["temporal_power_gate_pass"] else "FAIL",
        ))
    print("\n%-9s %12s %10s %10s" % ("pair", "min T/tau", "censor", "eligible"))
    for name, row in artifact["pairs"].items():
        print("%-9s %12.2f %10s %10s" % (
            name,
            row["minimum_test_T_over_tau"],
            "PASS" if row["censoring_gate_pass"] else "FAIL",
            "YES" if row["eligible_before_dynamic_range"] else "NO",
        ))
    print("artifact:", CALIBRATION_OUT)


def print_test(artifact: dict[str, object]) -> None:
    print("G-A003 held-out split-sample")
    print("held-out correlations read:", artifact["held_out_correlations_read"])
    print("%-9s %12s %38s" % ("pair", "min T/tau", "status"))
    for name, row in artifact["pairs"].items():
        print("%-9s %12.2f %38s" % (
            name, row["minimum_test_T_over_tau"], row["held_out_outcome_status"]
        ))
    print("verdict:", artifact["summary"]["verdict"])
    print("G1 closed:", artifact["summary"]["G1_closed"])
    print("artifact:", TEST_OUT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("calibrate", "test"), required=True)
    args = parser.parse_args()
    if args.stage == "calibrate":
        print_calibration(make_calibration())
    else:
        print_test(run_test())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Calibrate and measure the local-stationarity window of nugget variance."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.g_a003_split_sample import (
    DT_TARGET_S,
    EDGE_LINKS,
    MEASURED_INPUT,
    load_by_link,
    sha256,
)


REFERENCE = Path("results/SMOKE/phase-G/g1_4_physical_reanalysis.json")
THRESHOLD_OUT = Path("results/SMOKE/phase-G/g_coherence_thresholds.json")
MEASURE_OUT = Path("results/SMOKE/phase-G/g_measurement_coherence.json")
PREREG_TAG = "phase-G-coherence-threshold-prereg"
THRESHOLD_TAG = "phase-G-coherence-threshold-locked"

WINDOWS_S = (50, 100, 200, 400, 750, 1505)
STRIDE_FRACTION = 0.50
N_FIT_LAGS = 8
NULL_REPETITIONS = 400
NULL_SEED = 20260831
NULL_PERCENTILE = 95.0


def git_hash() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def tag_commit(tag: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(f"missing required tag {tag}")
    return result.stdout.strip()


def require_paths_match_tag(tag: str, paths: tuple[Path, ...]) -> None:
    result = subprocess.run(
        ["git", "diff", "--quiet", tag, "--", *(str(path) for path in paths)]
    )
    if result.returncode != 0:
        rendered = ", ".join(str(path) for path in paths)
        raise RuntimeError(f"locked content differs from {tag}: {rendered}")


def window_slices(n: int, requested_s: int) -> tuple[list[slice], int, int]:
    requested_n = int(round(requested_s / DT_TARGET_S))
    window_n = min(requested_n, n)
    stride_n = max(1, int(round(window_n * STRIDE_FRACTION)))
    starts = list(range(0, n - window_n + 1, stride_n))
    if starts and starts[-1] != n - window_n:
        starts.append(n - window_n)
    return [slice(start, start + window_n) for start in starts], window_n, stride_n


def estimate_local_v(values: np.ndarray) -> dict[str, float | bool | int]:
    """Match ``estimate_nugget`` while retaining boundary-projected v."""
    x = np.asarray(values, dtype=float)
    centered = x - x.mean()
    denominator = float(centered @ centered)
    if denominator <= 0.0:
        return {"fit_available": False, "v_raw": float("nan"), "v_projected": float("nan")}
    acf = np.asarray([
        float(centered[:-lag] @ centered[lag:] / denominator)
        for lag in range(1, N_FIT_LAGS + 1)
    ])
    lags = np.arange(1, N_FIT_LAGS + 1, dtype=float)
    noise_floor = 2.0 / np.sqrt(len(x))
    keep = acf > noise_floor
    if int(keep.sum()) < 4:
        return {
            "fit_available": False,
            "v_raw": float("nan"),
            "v_projected": float("nan"),
            "n_lags_used": int(keep.sum()),
        }
    design = np.vstack([np.ones(int(keep.sum())), lags[keep]]).T
    coefficients, *_ = np.linalg.lstsq(design, np.log(acf[keep]), rcond=None)
    sf = float(np.exp(coefficients[0]))
    phi = float(np.exp(coefficients[1]))
    total_variance = float(x.var(ddof=1))
    v_raw = total_variance * (1.0 - sf)
    return {
        "fit_available": True,
        "sf": sf,
        "phi": phi,
        "tau_s": float(-DT_TARGET_S / np.log(phi)) if 0.0 < phi < 1.0 else float("nan"),
        "v_raw": v_raw,
        "v_projected": max(v_raw, 0.0),
        "at_boundary": v_raw <= 0.0,
        "n_lags_used": int(keep.sum()),
    }


def curve_for_trace(values: np.ndarray) -> dict[str, dict[str, object]]:
    output = {}
    n = len(values)
    for requested_s in WINDOWS_S:
        slices, window_n, stride_n = window_slices(n, requested_s)
        estimates = [estimate_local_v(values[part]) for part in slices]
        available = [row for row in estimates if row["fit_available"]]
        projected = np.asarray([row["v_projected"] for row in available], dtype=float)
        if len(projected) >= 2 and float(projected.mean()) > 0.0:
            cv = float(projected.std(ddof=1) / projected.mean())
        else:
            cv = None
        output[str(requested_s)] = {
            "requested_window_s": requested_s,
            "effective_window_s": window_n * DT_TARGET_S,
            "stride_s": stride_n * DT_TARGET_S,
            "n_windows": len(slices),
            "n_fits_available": len(available),
            "cv_v_projected": cv,
            "v_projected_mean": float(projected.mean()) if len(projected) else None,
            "v_projected_min": float(projected.min()) if len(projected) else None,
            "v_projected_max": float(projected.max()) if len(projected) else None,
            "boundary_fraction": (
                float(np.mean([bool(row["at_boundary"]) for row in available]))
                if available else None
            ),
        }
    return output


def ar1_measurement(
    rng: np.random.Generator, n: int, sf: float, tau_s: float
) -> np.ndarray:
    phi = float(np.exp(-DT_TARGET_S / tau_s))
    signal = np.empty(n)
    signal[0] = rng.standard_normal()
    innovations = rng.standard_normal(n - 1)
    scale = np.sqrt(1.0 - phi * phi)
    for index in range(1, n):
        signal[index] = phi * signal[index - 1] + scale * innovations[index - 1]
    noise = rng.standard_normal(n)
    return np.sqrt(sf) * signal + np.sqrt(1.0 - sf) * noise


def reference_parameters() -> tuple[int, dict[str, dict[str, float]]]:
    artifact = json.loads(REFERENCE.read_text(encoding="utf-8"))
    run = artifact["cellA_long"]
    parameters = {
        link: {
            "sf": float(run["per_link"][link]["sf"]),
            "tau_s": float(run["per_link"][link]["tau_from_fit_s"]),
        }
        for link in EDGE_LINKS
    }
    return int(run["n_measured"]), parameters


def run_threshold() -> dict[str, object]:
    prereg = tag_commit(PREREG_TAG)
    n, parameters = reference_parameters()
    rng = np.random.default_rng(NULL_SEED)
    distributions = {
        link: {str(window): [] for window in WINDOWS_S} for link in EDGE_LINKS
    }
    boundary_distributions = {
        link: {str(window): [] for window in WINDOWS_S} for link in EDGE_LINKS
    }
    for _ in range(NULL_REPETITIONS):
        for link in EDGE_LINKS:
            trace = ar1_measurement(rng, n, **parameters[link])
            curve = curve_for_trace(trace)
            for window in WINDOWS_S:
                row = curve[str(window)]
                if row["cv_v_projected"] is not None:
                    distributions[link][str(window)].append(row["cv_v_projected"])
                if row["boundary_fraction"] is not None:
                    boundary_distributions[link][str(window)].append(
                        row["boundary_fraction"]
                    )

    thresholds = {}
    for link in EDGE_LINKS:
        thresholds[link] = {}
        for window in WINDOWS_S:
            values = np.asarray(distributions[link][str(window)], dtype=float)
            boundary = np.asarray(
                boundary_distributions[link][str(window)], dtype=float
            )
            slices, effective_n, stride_n = window_slices(n, window)
            available = len(values) >= int(np.ceil(0.95 * NULL_REPETITIONS))
            thresholds[link][str(window)] = {
                "n_windows": len(slices),
                "effective_window_s": effective_n * DT_TARGET_S,
                "stride_s": stride_n * DT_TARGET_S,
                "finite_cv_repetitions": len(values),
                "threshold_available": bool(available and len(slices) >= 2),
                "cv_null_median": float(np.median(values)) if len(values) else None,
                "cv_null_p95": (
                    float(np.percentile(values, NULL_PERCENTILE))
                    if available and len(slices) >= 2 else None
                ),
                "boundary_fraction_null_p95": (
                    float(np.percentile(boundary, NULL_PERCENTILE))
                    if len(boundary) else None
                ),
            }

    artifact = {
        "schema": "dt4n.phase_g.measurement_coherence_thresholds.v1",
        "status": "PREREGISTERED_STATIONARY_NULL_CALIBRATION",
        "physical_curve_read": False,
        "preregistration_tag": PREREG_TAG,
        "preregistration_commit": prereg,
        "reference_artifact": str(REFERENCE),
        "locked_design": {
            "windows_s": list(WINDOWS_S),
            "stride_fraction": STRIDE_FRACTION,
            "n_fit_lags": N_FIT_LAGS,
            "null_repetitions": NULL_REPETITIONS,
            "null_seed": NULL_SEED,
            "null_percentile": NULL_PERCENTILE,
            "v_boundary_projection": "max(v_raw,0)",
            "parameters": parameters,
        },
        "thresholds": thresholds,
        "limitations": (
            "Thresholds are pointwise p95 by link and W, not a simultaneous "
            "familywise band. W=1505 s has one window and is not identifiable."
        ),
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_measurement_coherence.py --stage threshold",
        },
    }
    THRESHOLD_OUT.parent.mkdir(parents=True, exist_ok=True)
    THRESHOLD_OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def run_measure() -> dict[str, object]:
    threshold_commit = tag_commit(THRESHOLD_TAG)
    require_paths_match_tag(
        THRESHOLD_TAG, (Path("tools/g_measurement_coherence.py"), THRESHOLD_OUT)
    )
    thresholds = json.loads(THRESHOLD_OUT.read_text(encoding="utf-8"))
    if thresholds.get("physical_curve_read") is not False:
        raise RuntimeError("threshold calibration has physical outcome leakage")
    if thresholds.get("preregistration_commit") != tag_commit(PREREG_TAG):
        raise RuntimeError("threshold artifact does not match preregistration tag")
    measured = load_by_link(MEASURED_INPUT, "rho")
    curves = {link: curve_for_trace(measured[link]) for link in EDGE_LINKS}

    for link in EDGE_LINKS:
        for window in WINDOWS_S:
            key = str(window)
            row = curves[link][key]
            null = thresholds["thresholds"][link][key]
            threshold = null["cv_null_p95"]
            row["cv_null_p95"] = threshold
            row["coherence_gate_pass"] = (
                bool(row["cv_v_projected"] <= threshold)
                if row["cv_v_projected"] is not None and threshold is not None
                else None
            )

    identifiable = [
        window for window in WINDOWS_S
        if all(curves[link][str(window)]["coherence_gate_pass"] is not None
               for link in EDGE_LINKS)
    ]
    all_link_pass = {
        str(window): all(
            bool(curves[link][str(window)]["coherence_gate_pass"])
            for link in EDGE_LINKS
        )
        for window in identifiable
    }
    passing = [window for window in identifiable if all_link_pass[str(window)]]
    w_star = max(passing) if passing else None

    artifact = {
        "schema": "dt4n.phase_g.measurement_coherence.v1",
        "status": "POST_HOC_COHERENCE_DIAGNOSTIC",
        "threshold_tag": THRESHOLD_TAG,
        "threshold_commit": threshold_commit,
        "threshold_artifact": str(THRESHOLD_OUT),
        "threshold_sha256": sha256(THRESHOLD_OUT),
        "input": {
            "path": str(MEASURED_INPUT),
            "sha256": sha256(MEASURED_INPUT),
        },
        "curves": curves,
        "summary": {
            "identifiable_windows_s": identifiable,
            "all_link_pass_by_window": all_link_pass,
            "W_star_s_largest_all_link_pass": w_star,
            "window_1505_status": "NOT_IDENTIFIABLE_ONE_WINDOW",
        },
        "interpretation_scope": (
            "Post-hoc diagnostic after G-A004 FAIL. It does not reverse that "
            "verdict and is used only to design G-A005/fresh measurement windows."
        ),
        "provenance": {
            "git_hash": git_hash(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g_measurement_coherence.py --stage measure",
        },
    }
    MEASURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    MEASURE_OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def print_threshold(artifact: dict[str, object]) -> None:
    print("Stationary-null p95 thresholds (physical curve NOT read)")
    print("%-5s" % "link", *("%9ss" % w for w in WINDOWS_S))
    for link in EDGE_LINKS:
        values = []
        for window in WINDOWS_S:
            value = artifact["thresholds"][link][str(window)]["cv_null_p95"]
            values.append("%9.3f" % value if value is not None else "%9s" % "N/A")
        print("%-5s" % link, *values)
    print("artifact:", THRESHOLD_OUT)


def print_measure(artifact: dict[str, object]) -> None:
    print("Measurement-path coherence curve: CV(v_projected)")
    print("%-5s" % "link", *("%9ss" % w for w in WINDOWS_S))
    for link in EDGE_LINKS:
        values = []
        for window in WINDOWS_S:
            row = artifact["curves"][link][str(window)]
            value = row["cv_v_projected"]
            gate = row["coherence_gate_pass"]
            if value is None:
                values.append("%9s" % "N/A")
            else:
                values.append("%7.3f%s" % (value, "+" if gate else "-"))
        print("%-5s" % link, *values)
    print("W* largest all-link PASS:", artifact["summary"]["W_star_s_largest_all_link_pass"])
    print("artifact:", MEASURE_OUT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("threshold", "measure"), required=True)
    args = parser.parse_args()
    if args.stage == "threshold":
        print_threshold(run_threshold())
    else:
        print_measure(run_measure())


if __name__ == "__main__":
    main()

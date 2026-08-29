#!/usr/bin/env python3
"""G-A002: validate the two-band measurement estimator on synthetic truth."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.measurement_path_calib import estimate_two_band

PRIOR = Path("results/SMOKE/phase-G/g1a_estimator_validation.json")
OUT = Path("results/SMOKE/phase-G/g1a_two_band_validation.json")

SEED = 20260903
DT_S = 0.20
TAU_S = 3.0
SIGMA = 0.03
N_SAMPLES = 30_000
N_SEED = 16
SF_GRID = (0.30, 0.50, 0.70, 0.85, 0.95)
SCENARIOS = ((0.0, 1.0), (0.4, 0.9))
ERROR_TOLERANCE = 0.05
COND_MAX = 10.0
DEGENERACY_GAP_MIN = 0.05


def correlated_ar1_pair(
    n: int, phi: float, correlation: float, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a stationary AR(1) pair with locked cross-correlation."""
    independent = np.sqrt(1.0 - correlation**2)
    initial_l = rng.standard_normal()
    initial_m = correlation * initial_l + independent * rng.standard_normal()
    innovation_l = rng.standard_normal(n)
    innovation_m = correlation * innovation_l + independent * rng.standard_normal(n)
    innovation_scale = np.sqrt(1.0 - phi**2)

    left = np.empty(n)
    right = np.empty(n)
    left[0] = initial_l
    right[0] = initial_m
    for index in range(1, n):
        left[index] = phi * left[index - 1] + innovation_scale * innovation_l[index]
        right[index] = phi * right[index - 1] + innovation_scale * innovation_m[index]
    return left, right


def correlated_white_pair(
    n: int, correlation: float, scale: float, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    left = rng.standard_normal(n)
    right = correlation * left + np.sqrt(1.0 - correlation**2) * rng.standard_normal(n)
    return scale * left, scale * right


def aggregate(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "median": float(np.median(array)),
        "p05": float(np.percentile(array, 5)),
        "p95": float(np.percentile(array, 95)),
    }


def main() -> None:
    if not PRIOR.exists():
        raise SystemExit(f"missing prior G1-0a/b receipt: {PRIOR}")
    prior_bytes = PRIOR.read_bytes()
    prior = json.loads(prior_bytes)
    prior_sf_pass = bool(prior["gates"]["sf_all_pass"])
    prior_model_max_error = max(
        abs(row["rho_eps_hat_median"] - row["raw_diff_corr_theory"])
        for row in prior["rows"]
    )
    prior_model_pass = prior_model_max_error <= 0.01

    rng = np.random.default_rng(SEED)
    phi = float(np.exp(-DT_S / TAU_S))
    rows = []
    for sf_true in SF_GRID:
        nugget_variance = SIGMA**2 * (1.0 / sf_true - 1.0)
        for r_true, rho_eps_true in SCENARIOS:
            r_estimates = []
            rho_estimates = []
            conditions = []
            gaps = []
            physical = []
            valid = []
            for _ in range(N_SEED):
                signal_l, signal_m = correlated_ar1_pair(
                    N_SAMPLES, phi, r_true, rng
                )
                nugget_l, nugget_m = correlated_white_pair(
                    N_SAMPLES, rho_eps_true, np.sqrt(nugget_variance), rng
                )
                x_l = 0.857 + SIGMA * signal_l + nugget_l
                x_m = 0.857 + SIGMA * signal_m + nugget_m
                estimate = estimate_two_band(x_l, x_m, sf_true, sf_true, phi)
                valid.append(bool(estimate["valid"]))
                if not estimate["valid"]:
                    continue
                r_estimates.append(float(estimate["r_true_hat"]))
                rho_estimates.append(float(estimate["rho_eps_hat"]))
                conditions.append(float(estimate["cond_A"]))
                gaps.append(abs(float(estimate["w_l"]) - sf_true))
                physical.append(bool(estimate["in_physical_range"]))

            r_summary = aggregate(r_estimates)
            rho_summary = aggregate(rho_estimates)
            condition_summary = aggregate(conditions)
            gap_summary = aggregate(gaps)
            gates = {
                "G1-0c_r_true": abs(r_summary["median"] - r_true) <= ERROR_TOLERANCE,
                "G1-0c_rho_eps": (
                    abs(rho_summary["median"] - rho_eps_true) <= ERROR_TOLERANCE
                ),
                "G1-0c_condition": condition_summary["p95"] <= COND_MAX,
                "G1-0d_degeneracy": gap_summary["p05"] >= DEGENERACY_GAP_MIN,
            }
            rows.append(
                {
                    "sf_true": sf_true,
                    "r_true": r_true,
                    "rho_eps_true": rho_eps_true,
                    "r_true_hat": r_summary,
                    "rho_eps_hat": rho_summary,
                    "cond_A": condition_summary,
                    "w_minus_sf_abs": gap_summary,
                    "valid_fraction": float(np.mean(valid)),
                    "physical_range_fraction": float(np.mean(physical)),
                    "gates": gates,
                }
            )

    new_gates_pass = all(all(row["gates"].values()) for row in rows)
    artifact = {
        "schema": "dt4n.phase_g.g1a_two_band_validation.v1",
        "amendment": "G-A002",
        "status": "SYNTHETIC_DIAGNOSTIC_NO_EXPERIMENTAL_DATA",
        "constants": {
            "seed": SEED,
            "dt_s": DT_S,
            "tau_s": TAU_S,
            "tau_over_dt": TAU_S / DT_S,
            "phi": phi,
            "sigma": SIGMA,
            "n_samples": N_SAMPLES,
            "n_seed": N_SEED,
            "sf_grid": SF_GRID,
            "scenarios": [
                {"r_true": r_true, "rho_eps_true": rho_eps}
                for r_true, rho_eps in SCENARIOS
            ],
        },
        "prior_receipt": {
            "path": str(PRIOR),
            "sha256": hashlib.sha256(prior_bytes).hexdigest(),
            "G1-0a_sf_pass": prior_sf_pass,
            "G1-0b_model_max_abs_error": prior_model_max_error,
            "G1-0b_model_pass": prior_model_pass,
        },
        "gate_thresholds": {
            "absolute_estimation_error_max": ERROR_TOLERANCE,
            "condition_number_max": COND_MAX,
            "w_minus_sf_abs_min": DEGENERACY_GAP_MIN,
        },
        "gate_summary": {
            "G1-0a_pass": prior_sf_pass,
            "G1-0b_pass": prior_model_pass,
            "G1-0c_and_d_pass": new_gates_pass,
            "G1-0_overall_pass": bool(
                prior_sf_pass and prior_model_pass and new_gates_pass
            ),
        },
        "rows": rows,
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "prereg_tag": "phase-G-g1a-g-a002-prereg",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g1a_two_band_validation.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        "%6s %7s %7s | %8s %8s | %8s %8s | %7s %7s | %s"
        % (
            "sf",
            "r_true",
            "rho_e",
            "r_hat",
            "err_r",
            "rho_hat",
            "err_rho",
            "cond95",
            "gap05",
            "gates",
        )
    )
    for row in rows:
        print(
            "%6.2f %7.2f %7.2f | %8.4f %8.4f | %8.4f %8.4f | %7.2f %7.3f | %s"
            % (
                row["sf_true"],
                row["r_true"],
                row["rho_eps_true"],
                row["r_true_hat"]["median"],
                row["r_true_hat"]["median"] - row["r_true"],
                row["rho_eps_hat"]["median"],
                row["rho_eps_hat"]["median"] - row["rho_eps_true"],
                row["cond_A"]["p95"],
                row["w_minus_sf_abs"]["p05"],
                "PASS" if all(row["gates"].values()) else "FAIL",
            )
        )
    print(
        "\nG1-0a=%s G1-0b=%s G1-0c/d=%s OVERALL=%s"
        % tuple(
            "PASS" if artifact["gate_summary"][key] else "FAIL"
            for key in (
                "G1-0a_pass",
                "G1-0b_pass",
                "G1-0c_and_d_pass",
                "G1-0_overall_pass",
            )
        )
    )
    print("artifact: %s" % OUT)


if __name__ == "__main__":
    main()

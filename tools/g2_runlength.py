#!/usr/bin/env python3
"""Synthetic run-length budget for the G.2 omega estimator."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from tools.g2_topology import (
    K_VEC,
    PAIRS,
    SUM_K2,
    a0_from_sigma_at,
    simulate_correlations,
)


DT_S = 0.2
SD_TARGET = 0.05
OMEGA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
TAU_GRID = (3.0, 10.0, 30.0)
MULTIPLIER_GRID = (25, 50, 100, 200)
SEEDS = 120
SIGMA_REF = 0.030348837209302317
NULL_REPLICATES = 4000
BUDGET_T_OVER_TAU = 200.0


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


def _omega_batch(correlations: np.ndarray) -> np.ndarray:
    r_values = np.stack(
        [correlations[:, i, j] for i, j in PAIRS], axis=1
    )
    return (r_values @ K_VEC) / SUM_K2


def _null_spread_gate() -> tuple[float, float]:
    """Calibrate spread with the same 12 rows x 5 within-row SD estimates."""
    rng = np.random.default_rng(4242)
    spreads = np.empty(NULL_REPLICATES, dtype=float)
    for index in range(NULL_REPLICATES):
        estimated_sds = np.std(
            rng.standard_normal(
                (len(TAU_GRID) * len(MULTIPLIER_GRID), len(OMEGA_GRID), SEEDS)
            ),
            axis=2,
        )
        row_maxima = estimated_sds.max(axis=1)
        spreads[index] = row_maxima.max() / row_maxima.min()
    return float(np.median(spreads)), float(np.percentile(spreads, 95.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rng = np.random.default_rng(20260903)
    a0 = a0_from_sigma_at("uA", SIGMA_REF)
    rows = []
    for tau_s in TAU_GRID:
        for multiplier in MULTIPLIER_GRID:
            duration = multiplier * tau_s
            n = int(round(duration / DT_S))
            sds = []
            biases = []
            per_omega = []
            for omega in OMEGA_GRID:
                correlations, _ = simulate_correlations(
                    a0, omega, tau_s, DT_S, n, SEEDS, rng
                )
                estimates = _omega_batch(correlations)
                sd = float(np.std(estimates))
                bias = float(abs(np.median(estimates) - omega))
                sds.append(sd)
                biases.append(bias)
                per_omega.append(
                    {
                        "omega_true": omega,
                        "omega_hat_median": float(np.median(estimates)),
                        "omega_hat_sd": sd,
                        "abs_bias": bias,
                    }
                )
            sd_max = max(sds)
            rows.append(
                {
                    "tau_s": tau_s,
                    "T_over_tau": multiplier,
                    "T_run_s": duration,
                    "n": n,
                    "sd_max": sd_max,
                    "bias_max": max(biases),
                    "c_scaled": sd_max * np.sqrt(duration / tau_s),
                    "meets_target": bool(sd_max <= SD_TARGET),
                    "per_omega": per_omega,
                }
            )

    c_values = np.asarray([row["c_scaled"] for row in rows])
    c_central = float(np.median(c_values))
    c_conservative = float(np.max(c_values))
    spread = float(c_values.max() / c_values.min())
    null_median, spread_gate = _null_spread_gate()
    central_required = (c_central / SD_TARGET) ** 2
    conservative_required = (c_conservative / SD_TARGET) ** 2
    direct_budget_pass = all(
        row["meets_target"]
        for row in rows
        if row["T_over_tau"] == BUDGET_T_OVER_TAU
    )
    scaling_pass = spread <= spread_gate
    budget_pass = (
        conservative_required <= BUDGET_T_OVER_TAU and direct_budget_pass
    )
    overall = scaling_pass and budget_pass
    artifact = {
        "schema": "dt4n.phase_g.g2_runlength.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "dt_s": DT_S,
        "sd_target": SD_TARGET,
        "seeds": SEEDS,
        "scaling_constant_c_central": c_central,
        "scaling_constant_c_conservative_observed": c_conservative,
        "scaling_constant_spread": spread,
        "scaling_law_spread_null_median": null_median,
        "scaling_law_spread_gate_p95_null": spread_gate,
        "scaling_law_holds": bool(scaling_pass),
        "T_over_tau_required_central": central_required,
        "T_over_tau_required_conservative_observed": conservative_required,
        "T_over_tau_budgeted_G_A001": BUDGET_T_OVER_TAU,
        "safety_factor_central": BUDGET_T_OVER_TAU / central_required,
        "safety_factor_conservative_observed": (
            BUDGET_T_OVER_TAU / conservative_required
        ),
        "direct_budget_cells_pass": bool(direct_budget_pass),
        "budget_sufficient": bool(budget_pass),
        "overall": "PASS" if overall else "FAIL",
        "rows": rows,
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        "%5s %7s %10s %8s %9s %10s %18s  %s"
        % ("tau", "T/tau", "T_run(s)", "n", "sd max", "bias max", "c scaled", "sd<=.05")
    )
    for row in rows:
        print(
            "%5.0f %7d %10.0f %8d %9.4f %10.4f %18.3f  %s"
            % (
                row["tau_s"], row["T_over_tau"], row["T_run_s"], row["n"],
                row["sd_max"], row["bias_max"], row["c_scaled"],
                "YES" if row["meets_target"] else "no",
            )
        )
    print(
        "\nc central=%.3f  c conservative=%.3f  spread=%.3fx  null p95=%.3fx"
        % (c_central, c_conservative, spread, spread_gate)
    )
    print(
        "T/tau required: central=%.1f, conservative=%.1f; budget=%.0f"
        % (central_required, conservative_required, BUDGET_T_OVER_TAU)
    )
    print(
        "safety: central=%.2fx, conservative=%.2fx; direct budget=%s"
        % (
            artifact["safety_factor_central"],
            artifact["safety_factor_conservative_observed"],
            "PASS" if direct_budget_pass else "FAIL",
        )
    )
    print("G.2 RUN-LENGTH: %s" % artifact["overall"])
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()


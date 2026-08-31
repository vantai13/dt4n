#!/usr/bin/env python3
"""G.2 closed-form, negative/positive-control, and MC omega checks."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from tools.g2_topology import (
    CAP_BPS,
    DEGREE,
    K_TOPO,
    K_VEC,
    LINKS,
    NULL_PAIRS,
    PAIRS,
    SHARED,
    SUM_K2,
    a0_from_sigma_at,
    design_correlation,
    design_covariance,
    estimate_omega,
    sigma_per_link,
    simulate_correlations,
)


OMEGA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
TAU_GRID = (3.0, 10.0, 30.0)
DT_S = 0.2
T_OVER_TAU = 200.0
MC_SEEDS = 120
SIGMA_REF_LINK = "uA"
SIGMA_REF = 0.030348837209302317

GATE_ALGEBRA = 1e-12
GATE_VAR_INVARIANCE = 1e-12
GATE_OMEGA_MC = 0.05
GATE_TAU_INVARIANCE_REL = 0.05


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


def _tau_batch(traces: np.ndarray, dt_s: float) -> np.ndarray:
    centered = traces - traces.mean(axis=1, keepdims=True)
    denominator = np.sum(centered * centered, axis=1)
    acf2 = np.sum(centered[:, :-2] * centered[:, 2:], axis=1) / denominator
    acf3 = np.sum(centered[:, :-3] * centered[:, 3:], axis=1) / denominator
    phi = np.divide(acf3, acf2, out=np.full_like(acf2, np.nan), where=acf2 > 0.0)
    valid = (acf3 > 0.0) & (phi > 0.0) & (phi < 1.0)
    out = np.full_like(phi, np.nan)
    out[valid] = -dt_s / np.log(phi[valid])
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rng = np.random.default_rng(20260902)
    a0 = a0_from_sigma_at(SIGMA_REF_LINK, SIGMA_REF)
    checks: list[dict[str, object]] = []

    def record(check_id, description, value, gate, passed, **extra):
        checks.append(
            {
                "id": check_id,
                "description": description,
                "value": value,
                "gate": gate,
                "verdict": "PASS" if passed else "FAIL",
                **extra,
            }
        )

    record(
        "ALG-G2-1", "sum(k_topo^2) over 28 pairs equals 5",
        SUM_K2, GATE_ALGEBRA, abs(SUM_K2 - 5.0) <= GATE_ALGEBRA,
    )
    correlation_one = design_correlation(a0, 1.0)
    error_one = max(
        abs(correlation_one[i, j] - K_TOPO[i, j]) for i, j in PAIRS
    )
    record(
        "ALG-G2-2", "omega=1 gives r_lm=k_topo",
        error_one, GATE_ALGEBRA, error_one <= GATE_ALGEBRA,
    )
    linear_error = max(
        abs(design_correlation(a0, omega)[i, j] - omega * K_TOPO[i, j])
        for omega in OMEGA_GRID for i, j in PAIRS
    )
    record(
        "ALG-G2-3", "r_lm=omega*k_topo for every grid point and pair",
        linear_error, GATE_ALGEBRA, linear_error <= GATE_ALGEBRA,
    )

    target_variance = sigma_per_link(a0) ** 2
    variance_error = max(
        float(np.max(np.abs(np.diag(design_covariance(a0, omega)) - target_variance)))
        for omega in OMEGA_GRID
    )
    record(
        "INV-G2-1", "per-link variance is invariant in omega",
        variance_error, GATE_VAR_INVARIANCE,
        variance_error <= GATE_VAR_INVARIANCE,
    )

    def old_covariance(a_fixed: float, omega: float) -> np.ndarray:
        shared = a_fixed**2 * SHARED / np.outer(CAP_BPS, CAP_BPS)
        independent = (
            (1.0 / omega - 1.0) * a_fixed**2 * DEGREE / CAP_BPS**2
        )
        return shared + np.diag(independent)

    old_sigma_quarter = np.sqrt(np.diag(old_covariance(a0, 0.25))).max()
    old_sigma_one = np.sqrt(np.diag(old_covariance(a0, 1.0))).max()
    positive_ratio = float(old_sigma_quarter / old_sigma_one)
    record(
        "PC-G2-1", "fixed-a legacy parameterisation must break invariance",
        positive_ratio, ">=1.5 (analytic expectation 2)", positive_ratio >= 1.5,
    )

    no_coupling = estimate_omega(np.eye(len(LINKS)))
    record(
        "NC-G2-1", "identity correlation recovers omega=0",
        no_coupling, GATE_ALGEBRA, abs(no_coupling) <= GATE_ALGEBRA,
    )
    null_error = max(
        abs(design_correlation(a0, omega)[LINKS.index(left), LINKS.index(right)])
        for omega in OMEGA_GRID for left, right in NULL_PAIRS
    )
    record(
        "NC-G2-2", "%d k=0 pairs remain zero" % len(NULL_PAIRS),
        null_error, GATE_ALGEBRA, null_error <= GATE_ALGEBRA,
        null_pairs=["%s-%s" % pair for pair in NULL_PAIRS],
    )

    monte_carlo = []
    for tau_s in TAU_GRID:
        n = int(round(T_OVER_TAU * tau_s / DT_S))
        for omega in OMEGA_GRID:
            correlations, traces = simulate_correlations(
                a0, omega, tau_s, DT_S, n, MC_SEEDS, rng, keep_link=0
            )
            estimates = _omega_batch(correlations)
            tau_estimates = _tau_batch(traces, DT_S)
            omega_median = float(np.median(estimates))
            tau_median = float(np.nanmedian(tau_estimates))
            bias = omega_median - omega
            sd = float(np.std(estimates))
            monte_carlo.append(
                {
                    "tau_s": tau_s,
                    "n": n,
                    "omega_true": omega,
                    "omega_hat_median": omega_median,
                    "omega_hat_sd": sd,
                    "bias": bias,
                    "tau_hat_median": tau_median,
                    "tau_rel_error": abs(tau_median - tau_s) / tau_s,
                    "valid_tau_replicates": int(np.isfinite(tau_estimates).sum()),
                    "verdict": (
                        "PASS"
                        if abs(bias) <= GATE_OMEGA_MC and sd <= GATE_OMEGA_MC
                        else "FAIL"
                    ),
                }
            )

    worst_bias = max(abs(row["bias"]) for row in monte_carlo)
    worst_sd = max(row["omega_hat_sd"] for row in monte_carlo)
    record(
        "PC-G2-2", "round-trip omega at T=200*tau",
        {"max_abs_bias": worst_bias, "max_sd": worst_sd},
        GATE_OMEGA_MC,
        worst_bias <= GATE_OMEGA_MC and worst_sd <= GATE_OMEGA_MC,
    )
    tau_spreads = []
    for tau_s in TAU_GRID:
        row = [
            item["tau_hat_median"] for item in monte_carlo
            if item["tau_s"] == tau_s
        ]
        tau_spreads.append((max(row) - min(row)) / float(np.mean(row)))
    worst_tau_spread = float(max(tau_spreads))
    record(
        "INV-G2-2", "tau_hat spread across omega at fixed tau",
        worst_tau_spread, GATE_TAU_INVARIANCE_REL,
        worst_tau_spread <= GATE_TAU_INVARIANCE_REL,
    )
    absolute_tau_bias = max(row["tau_rel_error"] for row in monte_carlo)
    record(
        "OBS-G2-1", "absolute finite-sample tau_hat bias (reported only)",
        absolute_tau_bias, "reported only", True,
    )

    overall = all(check["verdict"] == "PASS" for check in checks)
    artifact = {
        "schema": "dt4n.phase_g.g2_omega_algebra.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "sigma_ref_link": SIGMA_REF_LINK,
        "sigma_ref": SIGMA_REF,
        "a0": a0,
        "sigma_per_link": dict(zip(LINKS, sigma_per_link(a0).tolist())),
        "dt_s": DT_S,
        "T_over_tau": T_OVER_TAU,
        "mc_seeds": MC_SEEDS,
        "checks": checks,
        "monte_carlo": monte_carlo,
        "overall": "PASS" if overall else "FAIL",
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        f"a0 = {a0:,.0f}  "
        f"(sigma_ref={SIGMA_REF:.8f} at {SIGMA_REF_LINK})"
    )
    print("sigma_l = " + "  ".join(
        "%s:%.4f" % (link, sigma)
        for link, sigma in zip(LINKS, sigma_per_link(a0))
    ))
    print("\n%-11s %26s  %-8s %s" % ("id", "value", "verdict", "description"))
    for check in checks:
        value = check["value"]
        if isinstance(value, dict):
            rendered = "bias%+.4f/sd%.4f" % (
                value["max_abs_bias"], value["max_sd"]
            )
        elif isinstance(value, float):
            rendered = "%.3e" % value
        else:
            rendered = str(value)
        print("%-11s %26s  %-8s %s" % (
            check["id"], rendered, check["verdict"], check["description"]
        ))
    print("\n%5s %8s | %s" % (
        "tau", "n", "".join("w=%-11s" % omega for omega in OMEGA_GRID)
    ))
    for tau_s in TAU_GRID:
        rows = [row for row in monte_carlo if row["tau_s"] == tau_s]
        print("%5.0f %8d | %s" % (
            tau_s,
            rows[0]["n"],
            "".join("%.3f+/-%.3f  " % (
                row["omega_hat_median"], row["omega_hat_sd"]
            ) for row in rows),
        ))
    print("\nG.2 ALGEBRA: %s" % artifact["overall"])
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()

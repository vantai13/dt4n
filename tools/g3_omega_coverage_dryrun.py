#!/usr/bin/env python3
"""Dry-run for relocating omega from a DECISION axis to a COVERAGE axis.

STATUS: SYNTHETIC_NO_NETWORK.  This tool adjudicates no physical outcome and
amends no signed preregistration.  It tests one proposition:

    G-A010 proved that omega cancels exactly from the stale pairwise decision
    when the path and link-private processes share one time scale.  The
    proposition is that omega nevertheless changes SIMULTANEOUS coverage
    across K links at that same single time scale, while MARGINAL coverage
    stays flat.

The marginal curve is a negative control built into the estimand itself: a
result in which both curves move would mean omega had merely rescaled the
variance, and would not support the proposition.

If the gates pass, a separate amendment may propose dropping the kappa axis.
This tool does not make that change.  ``docs/phase-G/42-...md`` and its
``kappa = 5`` selection remain in force.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np

from tools.g2_topology import CAP_BPS, DEGREE, INCIDENCE, LINKS
from tools.g3_dryrun import A0, DT_S, OMEGA_GRID, ar1

TAU_S = 3.0                       # ONE time scale; no kappa
ALPHA = 0.10
Z = NormalDist().inv_cdf(1.0 - ALPHA / 2.0)
SF_GRID = (1.00, 0.85, 0.70)      # 0.85 is the G.1 certificate floor
SF_PRIMARY = 0.85
K_GRID = (2, 4, 8)
K_PRIMARY = len(LINKS)
T_GRID_S = (600.0, 1800.0, 3000.0)
TAU_GRID_S = (1.0, 3.0, 10.0, 30.0)
T_PRIMARY_S = 600.0
REPLICATES = 60
SEED = 20260903

GATE_COV0_ANALYTIC = 0.005
GATE_COV1_MARGINAL = 0.010
GATE_COV2_AMPLITUDE = 0.050
GATE_COV3_MONOTONE = -0.002
GATE_COV4_SNR = 3.0


def git_hash() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=False)
    return out.stdout.strip() or "unknown"


def amplification_factor(k: int = K_PRIMARY, alpha: float = ALPHA) -> float:
    """d(m^K)/dm at m = 1-alpha: how a marginal deficit reaches K links."""
    if k < 1:
        raise ValueError("k must be positive")
    return float(k * (1.0 - alpha) ** (k - 1))


def trace(omega: float, sf: float, n: int, rng, tau_s: float = TAU_S) -> np.ndarray:
    """Measured link loads: signed G.2 generator plus an independent nugget."""
    if not 0.0 <= omega <= 1.0:
        raise ValueError("omega outside [0,1]")
    if not 0.0 < sf <= 1.0:
        raise ValueError("signal fraction outside (0,1]")
    if n < 2:
        raise ValueError("n must be at least 2")
    if tau_s <= 0.0:
        raise ValueError("tau_s must be positive")
    path = ar1(INCIDENCE.shape[1], tau_s, n, rng)
    private = ar1(len(LINKS), tau_s, n, rng)
    signal = (
        (A0 * np.sqrt(omega) / CAP_BPS)[:, None] * (INCIDENCE @ path)
        + (A0 * np.sqrt((1.0 - omega) * DEGREE) / CAP_BPS)[:, None] * private
    )
    if sf >= 1.0:
        return signal
    scale = signal.std(axis=1, keepdims=True) * np.sqrt((1.0 - sf) / sf)
    return signal + scale * rng.standard_normal(signal.shape)


def coverage(matrix: np.ndarray, k_values: tuple[int, ...]) -> dict[int, float]:
    """Return marginal coverage under key 0 and simultaneous coverage per k."""
    sd = matrix.std(axis=1, keepdims=True)
    if np.any(sd <= 0.0):
        raise ValueError("a link has zero spread; coverage is undefined")
    inside = np.abs(matrix) <= Z * sd
    out = {0: float(inside.mean())}
    for k in k_values:
        if not 1 <= k <= matrix.shape[0]:
            raise ValueError("k outside the link index")
        out[k] = float(inside[:k].all(axis=0).mean())
    return out


def sweep(sf: float, k_values: tuple[int, ...], duration_s: float,
          replicates: int) -> list[dict[str, object]]:
    """One omega sweep; every requested k reuses the SAME simulated traces."""
    n = int(round(duration_s / DT_S))
    rows = []
    for omega in OMEGA_GRID:
        samples: dict[int, list[float]] = {0: []}
        for k in k_values:
            samples[k] = []
        for offset in range(replicates):
            rng = np.random.default_rng(SEED + 1000 * offset)
            values = coverage(trace(omega, sf, n, rng), k_values)
            for key, value in values.items():
                samples[key].append(value)
        row: dict[str, object] = {"omega": float(omega)}
        row["marginal_mean"] = float(np.mean(samples[0]))
        row["marginal_sd"] = float(np.std(samples[0], ddof=1))
        for k in k_values:
            row[f"simultaneous_mean_k{k}"] = float(np.mean(samples[k]))
            row[f"simultaneous_sd_k{k}"] = float(np.std(samples[k], ddof=1))
        rows.append(row)
    return rows


def tau_amplification_sweep(
    tau_grid: tuple[float, ...] = TAU_GRID_S,
    sf: float = SF_PRIMARY,
    k: int = K_PRIMARY,
    duration_s: float = T_PRIMARY_S,
    replicates: int = REPLICATES,
) -> list[dict[str, object]]:
    """COV-7, REPORTED: the second, coupling-independent regime channel.

    An interval built from the trace's own sd undercovers because coverage is
    concave in the estimated sd, so Jensen's inequality bites; a larger tau
    lowers the effective sample size, widens the sd estimate's spread, and
    deepens the deficit.  That marginal deficit then reaches simultaneous
    coverage amplified by ``amplification_factor``.  Evaluated at omega=0, so
    no cross-link coupling contributes and the two channels are separated.
    """
    n = int(round(duration_s / DT_S))
    nominal_marginal = 1.0 - ALPHA
    nominal_simultaneous = nominal_marginal ** k
    predicted = amplification_factor(k)
    rows = []
    for tau_s in tau_grid:
        marginal, simultaneous = [], []
        for offset in range(replicates):
            rng = np.random.default_rng(SEED + 1000 * offset)
            values = coverage(trace(0.0, sf, n, rng, tau_s=tau_s), (k,))
            marginal.append(values[0])
            simultaneous.append(values[k])
        marginal_deficit = float(np.mean(marginal)) - nominal_marginal
        simultaneous_deficit = float(np.mean(simultaneous)) - nominal_simultaneous
        rows.append({
            "tau_s": float(tau_s),
            "phi": float(np.exp(-DT_S / tau_s)),
            "marginal_mean": float(np.mean(marginal)),
            "simultaneous_mean": float(np.mean(simultaneous)),
            "marginal_deficit": marginal_deficit,
            "simultaneous_deficit": simultaneous_deficit,
            "observed_ratio": (
                simultaneous_deficit / marginal_deficit
                if abs(marginal_deficit) > 1e-9 else None
            ),
            "predicted_ratio": predicted,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    args = parser.parse_args()
    if args.replicates < 2:
        raise SystemExit("REFUSED: need at least two replicates for a sd")
    started = time.time()

    all_k = tuple(sorted(set(K_GRID) | {K_PRIMARY}))
    by_sf = {
        str(sf): sweep(sf, all_k, T_PRIMARY_S, args.replicates)
        for sf in SF_GRID
    }
    by_duration = {
        str(t): sweep(SF_PRIMARY, (K_PRIMARY,), t, args.replicates)
        for t in T_GRID_S if t != T_PRIMARY_S
    }
    primary = by_sf[str(SF_PRIMARY)]
    by_duration[str(T_PRIMARY_S)] = primary

    key = f"simultaneous_mean_k{K_PRIMARY}"
    sd_key = f"simultaneous_sd_k{K_PRIMARY}"
    simultaneous = np.array([r[key] for r in primary])
    marginal = np.array([r["marginal_mean"] for r in primary])
    amplitude = float(simultaneous.max() - simultaneous.min())
    worst_step = float(np.min(np.diff(simultaneous)))
    pooled_sd = float(np.sqrt(np.mean([r[sd_key] ** 2 for r in primary])))
    snr = amplitude / pooled_sd if pooled_sd > 0.0 else float("inf")
    analytic_independent = (1.0 - ALPHA) ** K_PRIMARY
    # The independence anchor for a FINITE trace with an interval built from
    # the trace's own sd is the product of the ACHIEVED marginals, not the
    # product of the nominal ones: the estimated interval is slightly narrow,
    # so the marginal sits just under 1-alpha and the K-fold product inherits
    # that shortfall K times over. Testing against (1-alpha)^K would charge
    # the estimator for an interval-calibration effect that COV-1 already
    # measures separately.
    empirical_independent = float(marginal[0] ** K_PRIMARY)
    cov0_error = abs(simultaneous[0] - empirical_independent)
    marginal_error = float(np.max(np.abs(marginal - (1.0 - ALPHA))))

    checks = [
        {"id": "COV-0", "description": "omega=0 matches marginal^K (independence)",
         "value": cov0_error, "gate": GATE_COV0_ANALYTIC,
         "verdict": "PASS" if cov0_error <= GATE_COV0_ANALYTIC else "FAIL"},
        {"id": "COV-1", "description": "marginal coverage flat across omega",
         "value": marginal_error, "gate": GATE_COV1_MARGINAL,
         "verdict": "PASS" if marginal_error <= GATE_COV1_MARGINAL else "FAIL"},
        {"id": "COV-2", "description": "simultaneous coverage amplitude",
         "value": amplitude, "gate": GATE_COV2_AMPLITUDE,
         "verdict": "PASS" if amplitude >= GATE_COV2_AMPLITUDE else "FAIL"},
        {"id": "COV-3", "description": "monotone in omega",
         "value": worst_step, "gate": GATE_COV3_MONOTONE,
         "verdict": "PASS" if worst_step >= GATE_COV3_MONOTONE else "FAIL"},
        {"id": "COV-4", "description": "effect to single-trace noise ratio",
         "value": snr, "gate": GATE_COV4_SNR,
         "verdict": "PASS" if snr >= GATE_COV4_SNR else "FAIL"},
    ]
    overall = all(c["verdict"] == "PASS" for c in checks)

    artifact = {
        "schema": "dt4n.phase_g.g3_omega_coverage_dryrun.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "adjudicates": None,
        "amends": None,
        "git_hash": git_hash(),
        "elapsed_s": round(time.time() - started, 1),
        "design": {
            "tau_s": TAU_S, "kappa": 1, "alpha": ALPHA, "z": Z,
            "omega_grid": list(OMEGA_GRID), "sf_grid": list(SF_GRID),
            "sf_primary": SF_PRIMARY, "k_grid": list(all_k),
            "k_primary": K_PRIMARY, "t_grid_s": list(T_GRID_S),
            "t_primary_s": T_PRIMARY_S, "replicates": args.replicates,
            "seed": SEED, "links": list(LINKS),
            "analytic_independent_coverage": analytic_independent,
            "cov0_anchor": "product of achieved marginals; see COV-1 for level",
            "interval": "symmetric Gaussian, z*sd estimated from the trace",
        },
        "empirical_independent_coverage_at_omega_zero": empirical_independent,
        "primary": primary,
        "reported": {
            "COV-7": {
                "description": "regime channel independent of omega coupling",
                "adjudicated": False,
                "amplification_factor": amplification_factor(),
                "rows": tau_amplification_sweep(replicates=args.replicates),
            }
        },
        "robustness": {"by_signal_fraction": by_sf, "by_duration_s": by_duration},
        "checks": checks,
        "overall": "PASS" if overall else "FAIL",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("omega | marginal | simultaneous K=8 | sd")
    for row in primary:
        print("%5.2f |  %.4f  |      %.4f      | %.4f" % (
            row["omega"], row["marginal_mean"], row[key], row[sd_key]))
    print()
    for c in checks:
        print("%-6s %10.5f  gate %9.5f  %s  %s" % (
            c["id"], c["value"], c["gate"], c["verdict"], c["description"]))
    print("\nOMEGA COVERAGE DRY-RUN: %s" % artifact["overall"])
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()

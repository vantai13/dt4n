#!/usr/bin/env python3
"""D-A002 diagnosis: run the PC-C2 tau estimator on a PERFECT synthetic generator.

The question A002 asks is not "did the generator obey ``tau ~ 1/sigma^2``" but
"could the signed threshold have been met even if it had".  This tool answers
that by feeding the exact PC-C2'/PC-C2'' estimator an AR(1) process whose true
``tau`` is known and whose ratio is exactly the theoretical ``11.11x``, at the
trace lengths and lag ceilings of each branch.

No experimental data is read and no threshold is touched.  Output is the ratio
a *flawless* experiment would have produced under each estimator.

    python -m tools.phase_d_estimator_bias_sim
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

OUT = Path("results/SMOKE/phase-D/estimator_bias_sim.json")

# Locked before running.  Truth values come from the branch metadata, not fits.
DT_S = 0.01
TAU_TRUE_A_S = 29.3          # edge tau at sigma = 0.03 (tau_by_link_from_meta)
TAU_TRUE_C_S = 2.64          # edge tau at sigma = 0.10
N_REPLICATES = 64
SEED = 2026_08_29

BRANCHES = (
    # label,                       n_samples, tau_true,      nlag_cap, estimator
    ("PC_C2_prime_cell_A",             12_000, TAU_TRUE_A_S,    3_000, "PC-C2'"),
    ("PC_C2_prime_cell_C",             24_000, TAU_TRUE_C_S,    3_000, "PC-C2'"),
    ("PC_C2_second_cell_A_long",      150_500, TAU_TRUE_A_S,   50_000, "PC-C2''"),
    ("PC_C2_second_cell_C",            24_000, TAU_TRUE_C_S,   50_000, "PC-C2''"),
)


def acf_prefix(values: np.ndarray, nlag: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    centered = values - float(values.mean())
    denominator = float(centered @ centered)
    if denominator <= 0:
        return np.concatenate(([1.0], np.zeros(nlag)))
    fft_len = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_len)
    autocov = np.fft.irfft(spectrum * np.conjugate(spectrum), fft_len)[: nlag + 1]
    return np.asarray(autocov / denominator, dtype=float)


def tau_int(values: np.ndarray, dt: float, cap: int) -> tuple[float, bool]:
    nlag = min(len(values) // 4, cap)
    curve = acf_prefix(values, nlag)
    cut = nlag
    for lag in range(1, len(curve)):
        if curve[lag] <= 0:
            cut = lag - 1
            break
    return float(dt * (0.5 + curve[1 : cut + 1].sum())), bool(cut == nlag)


def ar1(n: int, tau: float, dt: float, rng: np.random.Generator) -> np.ndarray:
    """Exponential-ACF process with exactly the requested integral time scale."""
    phi = float(np.exp(-dt / tau))
    noise = rng.standard_normal(n) * np.sqrt(1.0 - phi * phi)
    out = np.empty(n)
    out[0] = rng.standard_normal()
    for i in range(1, n):
        out[i] = phi * out[i - 1] + noise[i]
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    branches: dict[str, object] = {}
    for label, n, tau_true, cap, estimator in BRANCHES:
        estimates, ceilings = [], 0
        for _ in range(N_REPLICATES):
            tau_hat, at_ceiling = tau_int(ar1(n, tau_true, DT_S, rng), DT_S, cap)
            estimates.append(tau_hat)
            ceilings += int(at_ceiling)
        median = float(np.median(estimates))
        branches[label] = {
            "estimator": estimator,
            "n_samples": n,
            "duration_s": float(n * DT_S),
            "tau_true_s": tau_true,
            "T_over_tau_true": float(n * DT_S / tau_true),
            "nlag_cap": cap,
            "max_lag_s": float(min(n // 4, cap) * DT_S),
            "tau_hat_median_s": median,
            "tau_hat_p05_s": float(np.percentile(estimates, 5)),
            "tau_hat_p95_s": float(np.percentile(estimates, 95)),
            "bias_factor": float(median / tau_true),
            "cut_at_ceiling_fraction": float(ceilings / N_REPLICATES),
        }

    ratio_prime = float(
        branches["PC_C2_prime_cell_A"]["tau_hat_median_s"]
        / branches["PC_C2_prime_cell_C"]["tau_hat_median_s"]
    )
    ratio_second = float(
        branches["PC_C2_second_cell_A_long"]["tau_hat_median_s"]
        / branches["PC_C2_second_cell_C"]["tau_hat_median_s"]
    )
    ratio_true = float(TAU_TRUE_A_S / TAU_TRUE_C_S)

    artifact = {
        "schema": "dt4n.phase_d.estimator_bias_sim.v1",
        "status": "SYNTHETIC_DIAGNOSTIC_NO_EXPERIMENTAL_DATA",
        "diagnosis": "docs/phase-D/A002-amendment-pc-c2-prime.md",
        "question": (
            "Given a generator that obeys tau ~ 1/sigma^2 EXACTLY, what ratio "
            "does each signed estimator return?"
        ),
        "locked_constants": {
            "dt_s": DT_S,
            "tau_true_A_s": TAU_TRUE_A_S,
            "tau_true_C_s": TAU_TRUE_C_S,
            "n_replicates": N_REPLICATES,
            "seed": SEED,
            "process": "AR(1), exponential ACF, integral time scale = tau_true",
        },
        "branches": branches,
        "ratio_true": ratio_true,
        "ratio_under_PC_C2_prime": ratio_prime,
        "ratio_under_PC_C2_second": ratio_second,
        "threshold": 5.0,
        "perfect_generator_could_pass_PC_C2_prime": bool(ratio_prime >= 5.0),
        "perfect_generator_could_pass_PC_C2_second": bool(ratio_second >= 5.0),
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_estimator_bias_sim.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("%-28s %10s %10s %9s %8s" % ("branch", "tau_true", "tau_hat", "bias", "ceil"))
    for label, row in branches.items():
        print(
            "%-28s %10.3f %10.3f %9.3f %8.2f"
            % (label, row["tau_true_s"], row["tau_hat_median_s"],
               row["bias_factor"], row["cut_at_ceiling_fraction"])
        )
    print()
    print("true ratio                      %.3f" % ratio_true)
    print("ratio a PERFECT generator gives under PC-C2'   %.3f   (threshold 5.0 -> %s)"
          % (ratio_prime, "PASS" if ratio_prime >= 5.0 else "UNREACHABLE"))
    print("ratio a PERFECT generator gives under PC-C2''  %.3f   (threshold 5.0 -> %s)"
          % (ratio_second, "PASS" if ratio_second >= 5.0 else "UNREACHABLE"))
    print("artifact: %s" % OUT)


if __name__ == "__main__":
    main()

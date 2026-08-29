#!/usr/bin/env python3
"""G.0 step 2: test the signed estimator against synthetic ground truth."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OUT = Path("results/SMOKE/phase-G/g0_estimator_bias.json")
N_REP = 200
SEED = 2026_09_01
GATE_TOL = 0.20


def acf_prefix(values: np.ndarray, nlag: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    centered = values - float(values.mean())
    denominator = float(centered @ centered)
    if denominator <= 0:
        return np.concatenate(([1.0], np.zeros(nlag)))
    fft_len = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_len)
    autocov = np.fft.irfft(
        spectrum * np.conjugate(spectrum), fft_len
    )[: nlag + 1]
    return np.asarray(autocov / denominator, dtype=float)


def tau_int(values: np.ndarray, dt: float) -> tuple[float, bool]:
    nlag = len(values) // 4
    curve = acf_prefix(values, nlag)
    cut = nlag
    for lag in range(1, len(curve)):
        if curve[lag] <= 0:
            cut = lag - 1
            break
    return float(dt * (0.5 + curve[1 : cut + 1].sum())), bool(cut == nlag)


def ar1(
    n: int, tau: float, dt: float, rng: np.random.Generator
) -> np.ndarray:
    phi = float(np.exp(-dt / tau))
    noise = rng.standard_normal(n) * np.sqrt(1.0 - phi * phi)
    out = np.empty(n)
    out[0] = rng.standard_normal()
    for index in range(1, n):
        out[index] = phi * out[index - 1] + noise[index]
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    tau, dt = 1.0, 0.05
    rows = []
    for t_over_tau in (55, 100, 200, 400, 800):
        n = int(t_over_tau * tau / dt)
        singles = np.array(
            [tau_int(ar1(n, tau, dt, rng), dt)[0] / tau for _ in range(N_REP)]
        )
        median8 = np.array(
            [
                np.median(
                    [
                        tau_int(ar1(n, tau, dt, rng), dt)[0] / tau
                        for _ in range(8)
                    ]
                )
                for _ in range(N_REP)
            ]
        )
        rows.append(
            {
                "T_over_tau": t_over_tau,
                "n_samples": n,
                "single_median": float(np.median(singles)),
                "single_p05": float(np.percentile(singles, 5)),
                "single_p95": float(np.percentile(singles, 95)),
                "median8_median": float(np.median(median8)),
                "median8_p05": float(np.percentile(median8, 5)),
                "median8_p95": float(np.percentile(median8, 95)),
                "P_pass_gate_20pct": float(
                    np.mean(np.abs(median8 - 1.0) <= GATE_TOL)
                ),
            }
        )

    artifact = {
        "schema": "dt4n.phase_g.g0_estimator_bias.v1",
        "status": "SYNTHETIC_DIAGNOSTIC_NO_EXPERIMENTAL_DATA",
        "principle": "NT 53: test thresholds against synthetic ground truth before signing",
        "gate_tolerance": GATE_TOL,
        "n_replicates": N_REP,
        "seed": SEED,
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        "%9s %8s | %-24s | %-24s | %s"
        % ("T/tau", "n", "1 run: med/p05/p95", "median-8: med/p05/p95", "P(pass 20%)")
    )
    for row in rows:
        print(
            "%9d %8d | %6.3f %6.3f %6.3f    | %6.3f %6.3f %6.3f    | %.3f"
            % (
                row["T_over_tau"],
                row["n_samples"],
                row["single_median"],
                row["single_p05"],
                row["single_p95"],
                row["median8_median"],
                row["median8_p05"],
                row["median8_p95"],
                row["P_pass_gate_20pct"],
            )
        )
    print("\nartifact: %s" % OUT)
    print("choose the smallest T/tau with P(pass) >= 0.95")


if __name__ == "__main__":
    main()

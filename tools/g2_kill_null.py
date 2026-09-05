#!/usr/bin/env python3
"""G'.2 -- calibrate the null of KILL-1 before the gate is signed.

Why this exists
---------------
`KILL-1` reads the MAXIMUM of |r| over 28 link pairs. A maximum over many
noisy estimates is biased upward even when every true correlation is zero, so
a threshold chosen by intuition can be unreachable by construction. That is
the `G-L90` failure mode, and this tool is the check that prevents it.

The null is the signed rate path itself at `omega = 0`
(`tools.g3_dryrun.physical_trace`), where `r_true = 0` by construction: the
shared component enters with weight `sqrt(omega)`, so at `omega = 0` only the
per-link private components vary, and they are independent by construction.

What this null DOES include: finite-sample correlation noise of the true
process at the signed run length, and the Fisher-z pooling over replicates.
What it does NOT include: measurement nugget. An INDEPENDENT nugget attenuates
`r` toward zero, so omitting it is conservative for an upper gate. A COMMON
nugget is the thing the kill test is looking for, and must not be in the null.

    python -m tools.g2_kill_null
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tools.g1_estimator_bias_sim import provenance
from tools import g3_dryrun
from tools.g3_dryrun import LINKS, physical_trace

OUT = Path("results/SMOKE/phase-G2/g2_kill_null.json")
SCHEMA = "dt4n.phase_g2.kill_null.v1"

TAU_S = 2.0
DT_S = 0.1
T_RUN_S = 410.0          # 205*tau, the signed T-1 rule
N_REPLICATES = 4
N_TRIALS = 400
SEED = 2026_09_05
N_PAIRS = len(LINKS) * (len(LINKS) - 1) // 2

# ★ `tools.g3_dryrun.ar1` reads the module-level `DT_S` (0.2 s) rather than a
# caller-supplied step, so `physical_trace(tau_s=...)` silently generates
# `phi = exp(-DT_S/tau)`. Driving that series at a different `dt` realises
# `tau_eff = -dt/log(phi)`, not `tau`. Run 1 of the kill test was executed at
# `tau_eff = 1.0 s` instead of the signed 2.0 s for exactly this reason, and
# was recorded invalid. Bind the constant to the step actually used, and put
# the value in the artifact so the realised tau is never implicit again.
g3_dryrun.DT_S = DT_S


def fisher_pool(rs: np.ndarray) -> np.ndarray:
    """Pool replicate correlations on the Fisher z scale, then transform back."""
    z = np.arctanh(np.clip(rs, -0.999999, 0.999999))
    return np.tanh(z.mean(axis=0))


def main() -> None:
    n = int(round(T_RUN_S / DT_S))
    rng = np.random.default_rng(SEED)
    upper = np.triu_indices(len(LINKS), 1)
    maxes = np.empty(N_TRIALS)
    medians = np.empty(N_TRIALS)
    for trial in range(N_TRIALS):
        reps = []
        for _ in range(N_REPLICATES):
            trace = physical_trace(0.0, TAU_S, TAU_S, n, rng)
            reps.append(np.corrcoef(trace["rho_target"])[upper])
        pooled = np.abs(fisher_pool(np.array(reps)))
        maxes[trial] = pooled.max()
        medians[trial] = np.median(pooled)

    pct = lambda a, q: float(np.percentile(a, q))
    payload = {
        "schema": SCHEMA,
        "status": "SYNTHETIC_NULL_CALIBRATION_NO_EXPERIMENTAL_DATA",
        "principle": "G-L90: calibrate a gate's null before signing the gate",
        "provenance": provenance(),
        "design": {
            "omega": 0.0, "tau_s": TAU_S, "dt_s": DT_S, "T_run_s": T_RUN_S,
            "n_windows": n, "n_replicates": N_REPLICATES,
            "n_trials": N_TRIALS, "n_links": len(LINKS), "n_pairs": N_PAIRS,
            "seed": SEED,
            "rate_path": "tools.g3_dryrun.physical_trace",
            "pooling": "Fisher z mean over replicates",
        },
        "max_abs_r_over_pairs": {
            "median": pct(maxes, 50), "p95": pct(maxes, 95),
            "p99": pct(maxes, 99), "max": float(maxes.max()),
        },
        "median_abs_r_over_pairs": {
            "median": pct(medians, 50), "p95": pct(medians, 95),
            "p99": pct(medians, 99),
        },
        "gate_feasibility": [
            {
                "gate": g,
                "p_pass_under_null": float(np.mean(maxes <= g)),
                "safety_factor_over_null_p99": g / pct(maxes, 99),
            }
            for g in (0.10, 0.15, 0.20)
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT}: null p99 = {pct(maxes, 99):.4f}, "
          f"P(pass 0.10) = {np.mean(maxes <= 0.10):.4f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Re-adjudicate G'.3a from the stored series, without rerunning the host.

This is what persisting the raw series buys. The measured artifact
`g3a_omega_sweep.json` is preserved exactly as produced, including its defect;
this recomputes the gates from `g3a_omega_series.npz` and records both
readings side by side.

The defect: P-7 was implemented as the maximum over per-replicate maxima, while
its null (doc 62) is computed on the Fisher-z POOLED statistic. Those are
different statistics with different nulls, and the signed 0.040 threshold is
infeasible on the per-replicate one.

    python -m tools.g3a_readjudicate
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tools.artifact_guard import write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g3_dryrun import INCIDENCE
from tools.g3a_omega_estimator import design_matrix

SERIES = Path("results/SMOKE/phase-G2/g3a_omega_series.npz")
MEASURED = Path("results/SMOKE/phase-G2/g3a_omega_sweep.json")
OUT = Path("results/SMOKE/phase-G2/g3a_readjudicated.json")
SCHEMA = "dt4n.phase_g2.g3a_readjudicated.v1"
N_NULL_TRIALS = 400
SEED = 2026_09_05


def pool(mats: np.ndarray) -> np.ndarray:
    return np.tanh(np.arctanh(np.clip(mats, -0.999999, 0.999999)).mean(axis=0))


def nulls(n_rep: int, n_win: int, n_link: int, trials: int, rng) -> dict:
    iu = np.triu_indices(n_link, 1)
    pooled = np.empty(trials)
    per_rep = np.empty(trials)
    for t in range(trials):
        reps = []
        for _ in range(n_rep):
            u = rng.standard_normal((n_win + 1, n_link))
            reps.append(np.corrcoef((u[1:] - u[:-1]).T)[iu])
        arr = np.array(reps)
        pooled[t] = np.abs(pool(arr)).max()
        per_rep[t] = np.abs(arr).max()
    pct = lambda a, q: float(np.percentile(a, q))
    return {
        "pooled": {"median": pct(pooled, 50), "p95": pct(pooled, 95),
                   "p99": pct(pooled, 99), "samples": pooled},
        "per_replicate": {"median": pct(per_rep, 50), "p95": pct(per_rep, 95),
                          "p99": pct(per_rep, 99), "samples": per_rep},
    }


def main() -> None:
    z = np.load(SERIES, allow_pickle=True)
    measured, target = z["rho_measured"], z["rho_target"]
    omega_grid = z["omega_grid"]
    eps = measured - target
    n_lvl, n_rep, n_win, n_link = eps.shape
    iu = np.triu_indices(n_link, 1)

    rng = np.random.default_rng(SEED)
    null = nulls(n_rep, n_win, n_link, N_NULL_TRIALS, rng)

    levels = []
    for lvl in range(n_lvl):
        per = np.array([np.corrcoef(eps[lvl, r].T)[iu] for r in range(n_rep)])
        pooled_val = float(np.abs(pool(per)).max())
        per_val = float(np.abs(per).max())
        levels.append({
            "omega": float(omega_grid[lvl]),
            "rho_eps_pooled_max": pooled_val,
            "rho_eps_per_replicate_max": per_val,
            "p_null_ge_pooled": float(
                np.mean(null["pooled"]["samples"] >= pooled_val)),
            "p_null_ge_per_replicate": float(
                np.mean(null["per_replicate"]["samples"] >= per_val)),
            "pooled_inside_null": bool(
                np.mean(null["pooled"]["samples"] >= pooled_val) > 0.05),
            "per_replicate_inside_null": bool(
                np.mean(null["per_replicate"]["samples"] >= per_val) > 0.05),
        })

    gate = 0.040
    payload = {
        "schema": SCHEMA,
        "status": "READJUDICATED_FROM_STORED_SERIES",
        "source_series": str(SERIES),
        "measured_artifact": str(MEASURED),
        "provenance": provenance(),
        "defect": (
            "P-7 was implemented as max over per-replicate maxima while its "
            "null is computed on the Fisher-z pooled statistic. The signed "
            "0.040 threshold is infeasible on the per-replicate statistic, "
            "whose own null p99 is higher than the gate."),
        "null_3_replicates": {
            k: {kk: vv for kk, vv in v.items() if kk != "samples"}
            for k, v in null.items()},
        "gate": gate,
        "p_pass_gate_under_null": {
            "pooled": float(np.mean(null["pooled"]["samples"] <= gate)),
            "per_replicate": float(
                np.mean(null["per_replicate"]["samples"] <= gate)),
        },
        "levels": levels,
        "verdict": {
            "P7_pooled": bool(max(l["rho_eps_pooled_max"] for l in levels) <= gate),
            "P7_per_replicate": bool(
                max(l["rho_eps_per_replicate_max"] for l in levels) <= gate),
            "all_levels_inside_own_null_pooled": all(
                l["pooled_inside_null"] for l in levels),
            "all_levels_inside_own_null_per_replicate": all(
                l["per_replicate_inside_null"] for l in levels),
        },
    }
    print(write_contract_artifact(OUT, payload)[:16] + f"  -> {OUT}")
    print(json.dumps(payload["verdict"], indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""G'.1 -- check that a signed gate SET admits at least one configuration.

Why this exists
---------------
`G-L90`/`G-L96` record the same accident: `EMIT-1` and `EMIT-4` were both
signed, and only a 64-minute run revealed that no configuration satisfies
both. The joint pass probability was 4.26e-34, computable in one line
BEFORE signing. This tool is that line, made routine.

Three checks, applied to the G'.1 error budget:

  PAIR     for each pair of gates constraining a common physical variable,
           compute each gate's feasible interval and their INTERSECTION.
           An empty intersection means the pair must not be signed.

  BOOLEAN  a tolerance-free boolean gate asserted over N repeated random
           trials has P(pass) = (1-p)^N, which collapses for large N. Any
           such gate is reported and refused.

  BUDGET   run-length rules are checked against the wall-clock budget.

No network, no data, no adjudication.

    python -m tools.g1_mutual_satisfiability
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from tools.g1_estimator_bias_sim import provenance

OUT = Path("results/SMOKE/phase-G2/g1_mutual_sat.json")
SCHEMA = "dt4n.phase_g2.mutual_satisfiability.v1"

# Signed physical constants, docs/phase-G/00-prereg-g0.md:12,28
C_BPS = 8_000_000.0
RHO_BAR = 0.857
RHO_MAX = 0.995
PAYLOAD_B = 1400.0
Z_TAIL = 2.58

# Budget targets from the G'.1 table
SF_TARGET = 0.95
SF_LIMIT = 0.90
T_OVER_TAU = 200
BURN_IN_TAU = 5
WALL_CLOCK_BUDGET_S = 6.0 * 3600.0
N_REPLICATES = 3
TAU_GRID = (1.0, 3.0, 5.0, 10.0, 20.0, 30.0)


def dt_of(tau: float) -> float:
    """Gate T-2: the 0.2 s instrument step, never coarser than tau/20."""
    return min(0.2, tau / 20.0)


def sigma_quantisation_floor(dt: float) -> float:
    """Relative sd of the load residual forced by PACKET quantisation.

    A window carries `C*dt*rho_bar/8` bytes, delivered in whole payloads of
    `PAYLOAD_B`. The load can therefore only move in steps of
    `8*PAYLOAD_B/(C*dt)` in rho units, and a uniform quantiser of step `q`
    has sd `q/sqrt(12)`.

    ★ The step is one PACKET, not one byte. `G-L43` records the consequence
      already observed in the v2 static smoke: 45 of 48 cells came back
      QUANT_LIMITED.
    """
    step = 8.0 * PAYLOAD_B / (C_BPS * dt)
    return step / math.sqrt(12.0)


def sigma_upper_from_tail() -> float:
    """G.0 headroom: rho_bar + z*sigma <= rho_max, docs/phase-G/00-prereg-g0.md:28."""
    return (RHO_MAX - RHO_BAR) / Z_TAIL


def sigma_lower_from_sf(dt: float, sf: float) -> float:
    """B-1: sf = sigma^2/(sigma^2+v) >= sf  with v at least the quantisation floor.

    sf >= s  <=>  v <= sigma^2 (1-s)/s  <=>  sigma >= v_floor^(1/2) * sqrt(s/(1-s))
    """
    v_floor = sigma_quantisation_floor(dt) ** 2
    return math.sqrt(v_floor * sf / (1.0 - sf))


def pair_checks() -> list[dict[str, object]]:
    rows = []
    hi = sigma_upper_from_tail()
    for tau in TAU_GRID:
        dt = dt_of(tau)
        for sf, label in ((SF_TARGET, "target"), (SF_LIMIT, "limit")):
            lo = sigma_lower_from_sf(dt, sf)
            rows.append({
                "pair": "B-1 (sf floor) vs G.0 tail headroom",
                "tau_s": tau,
                "dt_s": dt,
                "sf_level": label,
                "sf": sf,
                "sigma_quantisation_floor": sigma_quantisation_floor(dt),
                "sigma_lower_required": lo,
                "sigma_upper_allowed": hi,
                "intersection_empty": bool(lo > hi),
                "headroom_ratio": (hi / lo) if lo > 0 else None,
            })
    return rows


def budget_checks() -> list[dict[str, object]]:
    rows = []
    for tau in TAU_GRID:
        run_s = (T_OVER_TAU + BURN_IN_TAU) * tau
        total = run_s * N_REPLICATES
        rows.append({
            "check": "T-1 run length vs wall-clock budget",
            "tau_s": tau,
            "T_run_s": run_s,
            "n_replicates": N_REPLICATES,
            "total_s": total,
            "total_h": total / 3600.0,
            "within_budget": bool(total <= WALL_CLOCK_BUDGET_S),
        })
    return rows


def boolean_scan() -> list[dict[str, object]]:
    """Any tolerance-free boolean over N random trials, plus the G-L90 regression."""
    cases = [
        {
            "gate": "EMIT-4 alignment_exact (HISTORICAL, G-L90)",
            "in_this_budget": False,
            "p_per_trial": 0.001,
            "n_trials": 300 * 16 * 2 * 8,
        },
    ]
    for case in cases:
        p, n = case["p_per_trial"], case["n_trials"]
        case["p_pass"] = float((1.0 - p) ** n)
        case["log10_p_pass"] = float(n * math.log10(1.0 - p))
        case["signable"] = bool(case["p_pass"] >= 0.5)
    return cases


def main() -> None:
    pairs = pair_checks()
    budgets = budget_checks()
    booleans = boolean_scan()
    empty = [r for r in pairs if r["intersection_empty"]]
    over = [r for r in budgets if not r["within_budget"]]
    payload = {
        "schema": SCHEMA,
        "status": "DESK_CHECK_NO_DATA",
        "principle": "G-L90: a gate SET must be checked for mutual "
                     "satisfiability before it is signed",
        "provenance": provenance(),
        "constants": {
            "C_bps": C_BPS, "rho_bar": RHO_BAR, "rho_max": RHO_MAX,
            "payload_bytes": PAYLOAD_B, "z_tail": Z_TAIL,
            "source": "docs/phase-G/00-prereg-g0.md:12,28",
        },
        "pair_checks": pairs,
        "budget_checks": budgets,
        "boolean_scan": booleans,
        "summary": {
            "n_pairs_checked": len(pairs),
            "n_pairs_empty": len(empty),
            "empty_pairs": [
                {"tau_s": r["tau_s"], "sf_level": r["sf_level"]} for r in empty
            ],
            "n_cells_over_budget": len(over),
            "cells_over_budget": [r["tau_s"] for r in over],
            "any_tolerance_free_boolean_in_budget": any(
                c["in_this_budget"] for c in booleans
            ),
            "all_pairs_satisfiable": not empty,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(pairs)} pair checks, {len(empty)} empty")


if __name__ == "__main__":
    main()

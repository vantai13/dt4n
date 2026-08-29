#!/usr/bin/env python3
"""G.0 step 4: round-trip sigma and tau on the preregistered feasible grid."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from mininet.rate_modulator import ModulatorConfig, modulate, quantize
from tools.g0_estimator_bias_sim import tau_int

C_BPS = 8e6
RHO_BAR = 0.857
N_SEED = 16
T_RUN_FACTOR = 200
SEED0 = 20260901

FEASIBILITY = Path("results/SMOKE/phase-G/g0_feasibility.json")
OUT = Path("results/SMOKE/phase-G/g0_roundtrip.json")


def one_cell(sigma: float, tau: float, seed: int) -> dict[str, float]:
    dt = tau / 10.0
    cfg = ModulatorConfig(
        cap_bps=C_BPS,
        rho_bar=RHO_BAR,
        sigma=sigma,
        tau_s=tau,
        dt_s=dt,
    )
    rng = np.random.default_rng(seed)
    n_samples = int(T_RUN_FACTOR * tau / dt)
    modulation = modulate(cfg, n_samples, rng)
    packetized = quantize(modulation["rho_offered"], cfg)

    tau_offered, offered_at_ceiling = tau_int(modulation["rho_offered"], dt)
    tau_measured, measured_at_ceiling = tau_int(
        packetized["rho_measured"], dt
    )
    sigma_measured = float(packetized["rho_measured"].std(ddof=1))
    signal_fraction_empirical = float(
        modulation["sigma_realized"] ** 2 / max(sigma_measured**2, 1e-18)
    )

    return {
        "sigma_hat_offered": modulation["sigma_realized"],
        "sigma_hat_measured": sigma_measured,
        "tau_hat_offered": tau_offered,
        "tau_hat_measured": tau_measured,
        "tau_offered_at_ceiling": float(offered_at_ceiling),
        "tau_measured_at_ceiling": float(measured_at_ceiling),
        "clip_fraction": modulation["clip_fraction"],
        "sigma_headroom": modulation["sigma_headroom"],
        "sf_theory": packetized["signal_fraction_theory"],
        "sf_empirical": signal_fraction_empirical,
    }


def aggregate(replicates: list[dict[str, float]], key: str) -> dict[str, float]:
    values = np.array([row[key] for row in replicates])
    return {
        "median": float(np.median(values)),
        "p05": float(np.percentile(values, 5)),
        "p95": float(np.percentile(values, 95)),
    }


def main() -> None:
    if not FEASIBILITY.exists():
        raise SystemExit(
            f"missing {FEASIBILITY}; run python -m tools.g0_feasibility first"
        )
    feasibility = json.loads(FEASIBILITY.read_text(encoding="utf-8"))

    cells = []
    skipped = []
    for planned in feasibility["cells"]:
        sigma = float(planned["sigma"])
        tau = float(planned["tau_s"])
        if not planned["feasible"]:
            skipped.append(
                {"sigma": sigma, "tau_s": tau, "reason": planned["reason"]}
            )
            continue

        replicates = [
            one_cell(sigma, tau, SEED0 + 1000 * seed_index)
            for seed_index in range(N_SEED)
        ]
        sigma_offered = aggregate(replicates, "sigma_hat_offered")
        tau_offered = aggregate(replicates, "tau_hat_offered")
        sf_empirical = aggregate(replicates, "sf_empirical")
        cell = {
            "sigma": sigma,
            "tau_s": tau,
            "dt_s": tau / 10.0,
            "n_seed": N_SEED,
            "T_over_tau": T_RUN_FACTOR,
            "sigma_hat_offered": sigma_offered,
            "sigma_hat_measured": aggregate(replicates, "sigma_hat_measured"),
            "tau_hat_offered": tau_offered,
            "tau_hat_measured": aggregate(replicates, "tau_hat_measured"),
            "clip_fraction": aggregate(replicates, "clip_fraction"),
            "sigma_headroom": aggregate(replicates, "sigma_headroom"),
            "sf_theory": replicates[0]["sf_theory"],
            "sf_empirical": sf_empirical,
            "sigma_ratio": sigma_offered["median"] / sigma,
            "tau_ratio": tau_offered["median"] / tau,
        }
        cell["gates"] = {
            "G0-1_tau": abs(cell["tau_ratio"] - 1.0) <= 0.20,
            "G0-2_sigma": abs(cell["sigma_ratio"] - 1.0) <= 0.10,
            "G0-3_clip": cell["clip_fraction"]["p95"] <= 0.01,
            "G0-4_headroom": cell["sigma_headroom"]["median"] >= 5.0,
            "G0-5_signal_fraction": abs(
                cell["sf_empirical"]["median"] / cell["sf_theory"] - 1.0
            )
            <= 0.10,
        }
        cells.append(cell)

    tau_independence = []
    for tau in sorted({float(row["tau_s"]) for row in feasibility["cells"]}):
        ratios = [row["tau_ratio"] for row in cells if row["tau_s"] == tau]
        evaluable = len(ratios) >= 2
        spread = float(max(ratios) - min(ratios)) if evaluable else None
        tau_independence.append(
            {
                "tau_s": tau,
                "spread": spread,
                "n_sigma": len(ratios),
                "evaluable": evaluable,
                "pass": bool(evaluable and spread <= 0.05),
            }
        )

    cell_gates_pass = all(all(row["gates"].values()) for row in cells)
    independence_evaluable = [row for row in tau_independence if row["evaluable"]]
    artifact = {
        "schema": "dt4n.phase_g.g0_roundtrip.v1",
        "status": "SYNTHETIC_DRY_RUN_NO_NETWORK",
        "T_over_tau": T_RUN_FACTOR,
        "n_seed": N_SEED,
        "seed0": SEED0,
        "cells": cells,
        "skipped_infeasible": skipped,
        "tau_independence_of_sigma": tau_independence,
        "gate_summary": {
            "cell_gates_pass": cell_gates_pass,
            "G0-1b_pass_on_evaluable_tau": bool(
                independence_evaluable
                and all(row["pass"] for row in independence_evaluable)
            ),
            "G0-1b_coverage": (
                f"{len(independence_evaluable)}/{len(tau_independence)} tau levels"
            ),
        },
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "prereg_tag": "phase-G-g0-prereg",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g0_roundtrip.py",
        },
    }
    artifact["gate_summary"]["overall_pass"] = bool(
        artifact["gate_summary"]["cell_gates_pass"]
        and artifact["gate_summary"]["G0-1b_pass_on_evaluable_tau"]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        "%7s %7s | %9s %9s | %9s %8s %8s | %s"
        % (
            "sigma",
            "tau",
            "sig_hat/s",
            "tau_hat/t",
            "tau_meas/t",
            "clip95",
            "sf_emp",
            "gates",
        )
    )
    for cell in cells:
        print(
            "%7.2f %7.1f | %9.3f %9.3f | %9.3f %8.4f %8.3f | %s"
            % (
                cell["sigma"],
                cell["tau_s"],
                cell["sigma_ratio"],
                cell["tau_ratio"],
                cell["tau_hat_measured"]["median"] / cell["tau_s"],
                cell["clip_fraction"]["p95"],
                cell["sf_empirical"]["median"],
                "PASS" if all(cell["gates"].values()) else "FAIL",
            )
        )
    print("\nG0-1b: tau-ratio spread across feasible sigma values (<= 0.05)")
    for row in tau_independence:
        verdict = (
            "NOT_EVALUABLE"
            if not row["evaluable"]
            else ("PASS" if row["pass"] else "FAIL")
        )
        spread = "n/a" if row["spread"] is None else f"{row['spread']:.4f}"
        print(
            "  tau=%5.1f  spread=%s  n_sigma=%d  %s"
            % (row["tau_s"], spread, row["n_sigma"], verdict)
        )
    print("\nskipped infeasible cells:")
    for row in skipped:
        print(
            "  sigma=%.2f tau=%4.1f  %s"
            % (row["sigma"], row["tau_s"], row["reason"])
        )
    print("\noverall: %s" % ("PASS" if artifact["gate_summary"]["overall_pass"] else "FAIL"))
    print("artifact: %s" % OUT)


if __name__ == "__main__":
    main()

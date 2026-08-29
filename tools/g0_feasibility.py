#!/usr/bin/env python3
"""G.0 step 1: build the feasibility map before running any grid cell."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

C_BPS = 8e6
RHO_BAR = 0.857
PAYLOAD_BITS = 1400 * 8
HEADROOM_MIN = 5.0
DT_TAU_RATIO = 10.0
Z_FEASIBLE = 2.58
RHO_MAX = 0.995

SIGMA_GRID = (0.01, 0.03, 0.05, 0.10)
TAU_GRID = (0.5, 1.0, 3.0, 10.0, 30.0)

OUT = Path("results/SMOKE/phase-G/g0_feasibility.json")


def tau_floor_flow(
    sigma: float, size_min_kb: float = 20.0, kappa: float = 2.5
) -> float:
    """Flow-level floor for comparison only; not used by packet modulation."""
    mean_size_bits = kappa * size_min_kb * 1024 * 8 / (kappa - 1.0)
    return float(RHO_BAR * mean_size_bits / (sigma**2 * C_BPS))


def tau_floor_packet(sigma: float) -> float:
    k = DT_TAU_RATIO * HEADROOM_MIN / np.sqrt(12.0)
    return float(k * PAYLOAD_BITS / (C_BPS * sigma))


def dt_for(_sigma: float, tau: float) -> float:
    return tau / DT_TAU_RATIO


def main() -> None:
    rows: list[dict[str, object]] = []
    n_ok = 0
    for sigma in SIGMA_GRID:
        for tau in TAU_GRID:
            dt = dt_for(sigma, tau)
            floor = PAYLOAD_BITS / (C_BPS * dt * np.sqrt(12.0))
            headroom = sigma / floor
            clip_ok = RHO_BAR + Z_FEASIBLE * sigma <= RHO_MAX
            ok = headroom >= HEADROOM_MIN and clip_ok
            n_ok += int(ok)
            reasons = []
            if headroom < HEADROOM_MIN:
                reasons.append("headroom")
            if not clip_ok:
                reasons.append("clip")
            rows.append(
                {
                    "sigma": sigma,
                    "tau_s": tau,
                    "dt_s": dt,
                    "sigma_quant_floor": floor,
                    "sigma_headroom": headroom,
                    "tau_floor_packet_s": tau_floor_packet(sigma),
                    "tau_floor_flow_s_20kB": tau_floor_flow(sigma),
                    "n_pkt_per_window": RHO_BAR * C_BPS * dt / PAYLOAD_BITS,
                    "clip_headroom_ok": bool(clip_ok),
                    "feasible": bool(ok),
                    "reason": "+".join(reasons),
                }
            )

    artifact = {
        "schema": "dt4n.phase_g.g0_feasibility.v1",
        "constants": {
            "C_bps": C_BPS,
            "rho_bar": RHO_BAR,
            "payload_bits": PAYLOAD_BITS,
            "headroom_min": HEADROOM_MIN,
            "dt_tau_ratio": DT_TAU_RATIO,
            "z_feasible": Z_FEASIBLE,
            "rho_max": RHO_MAX,
            "sigma_tau_product_floor": float(
                DT_TAU_RATIO
                * HEADROOM_MIN
                / np.sqrt(12.0)
                * PAYLOAD_BITS
                / C_BPS
            ),
        },
        "n_cells": len(rows),
        "n_feasible": n_ok,
        "cells": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("sigma*tau product floor = %.5f s\n" % artifact["constants"]["sigma_tau_product_floor"])
    print(
        "%7s %7s %8s %9s %9s %8s  %s"
        % ("sigma", "tau", "dt", "floor", "headroom", "n_pkt", "verdict")
    )
    for row in rows:
        print(
            "%7.2f %7.1f %8.3f %9.5f %9.2f %8.1f  %s"
            % (
                row["sigma"],
                row["tau_s"],
                row["dt_s"],
                row["sigma_quant_floor"],
                row["sigma_headroom"],
                row["n_pkt_per_window"],
                "OK" if row["feasible"] else "EXCLUDE (" + row["reason"] + ")",
            )
        )
    print("\n%d/%d feasible cells -> %s" % (n_ok, len(rows), OUT))


if __name__ == "__main__":
    main()

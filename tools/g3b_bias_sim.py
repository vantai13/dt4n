#!/usr/bin/env python3
"""G'.3b -- estimator bias simulation for the tau-scaled lag window.

NT 53: a threshold on an ESTIMATED quantity must pass a bias simulation
BEFORE it is signed. This runs no network and takes seconds.

The question it answers is narrow and specific:

    with `lag_lo = 2` and `n_lags = round(LAG_SPAN*tau/dt)`, is the
    median-of-replicates `tau_hat` inside claim B's 20 percent at EVERY
    cell of the planned grid, given the nugget actually measured on this
    host (v = 6.5e-5, MA(1), G-A019 section 1)?

A cell that fails here is removed from the grid BEFORE the campaign, not
explained away after it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.g1_estimator_bias_sim import provenance
from tools.measurement_path_calib import estimate_nugget
from tools.artifact_guard import write_contract_artifact

OUT = Path("results/SMOKE/phase-G2/g3b_bias_sim.json")

DT_S = 0.1
LAG_SPAN = 0.4          # cửa sổ fit tính bằng bội số của tau  -> gate T-5
LAG_LO = 2              # G-A019 / G-L103
T_OVER_TAU = 205.0
V_NUGGET = 6.5e-05      # ĐO ĐƯỢC ở run 3, doc 61 mục 1
N_REPLICATES = 40
SEED = 2026_09_06

GRID = [(2.0, 0.028), (2.0, 0.045), (5.0, 0.028), (5.0, 0.045), (30.0, 0.036)]
GATE_TAU = 0.20         # claim B
GATE_SIGMA = 0.10       # claim C


def n_lags_for(tau_s: float, dt: float) -> int:
    return max(8, int(round(LAG_SPAN * tau_s / dt)))


def synth(tau_s: float, sigma: float, n: int, rng, nugget: str) -> np.ndarray:
    """AR(1) signal plus a nugget of the requested colour."""
    phi = np.exp(-DT_S / tau_s)
    u = np.empty(n)
    u[0] = rng.standard_normal()
    eps = rng.standard_normal(n)
    for k in range(1, n):
        u[k] = phi * u[k - 1] + np.sqrt(1.0 - phi * phi) * eps[k]
    signal = sigma * u
    if nugget == "ma1":                       # đường đo BẢO TOÀN (thực tế)
        # Var(w[k] - w[k-1]) = 2 Var(w); V_NUGGET is Var(eps), doc 61.
        w = rng.standard_normal(n + 1) * np.sqrt(V_NUGGET / 2.0)
        return signal + (w[1:] - w[:-1])
    if nugget == "white":                     # đối chứng: nếu nhiễu trắng
        return signal + rng.standard_normal(n) * np.sqrt(V_NUGGET)
    return signal                             # đối chứng: không nhiễu


def cell(tau_s: float, sigma: float, nugget: str, lag_lo: int, rng) -> dict:
    n = int(round(T_OVER_TAU * tau_s / DT_S))
    n_lags = n_lags_for(tau_s, DT_S)
    tau_hat, sigma_hat = [], []
    for _ in range(N_REPLICATES):
        x = synth(tau_s, sigma, n, rng, nugget)
        fit = estimate_nugget(x, DT_S, n_lags, lag_lo=lag_lo)
        tau_hat.append(fit.get("tau_from_fit_s", np.nan))
        sigma_hat.append(fit.get("sigma_true", np.nan))
    tau_hat = np.asarray(tau_hat, float)
    sigma_hat = np.asarray(sigma_hat, float)
    tau_med = float(np.nanmedian(tau_hat))
    sigma_med = float(np.nanmedian(sigma_hat))
    return {
        "tau_s": tau_s, "sigma_ref": sigma, "nugget": nugget, "lag_lo": lag_lo,
        "n_windows": n, "n_lags": n_lags,
        "lag_span_over_tau": n_lags * DT_S / tau_s,          # gate T-5
        "tau_hat_median": tau_med,
        "tau_rel_error": float(tau_med / tau_s - 1.0),
        "sigma_hat_median": sigma_med,
        "sigma_rel_error": float(sigma_med / sigma - 1.0),
        "n_finite": int(np.isfinite(tau_hat).sum()),
        "tau_ok": bool(abs(tau_med / tau_s - 1.0) <= GATE_TAU),
        "sigma_ok": bool(abs(sigma_med / sigma - 1.0) <= GATE_SIGMA),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    rows = []
    for tau_s, sigma in GRID:
        # ô thật, đúng estimator đã ký
        rows.append(cell(tau_s, sigma, "ma1", LAG_LO, rng))
        # đối chứng dương cho G-L103: cùng ô, estimator CŨ, phải TỆ HƠN
        rows.append(cell(tau_s, sigma, "ma1", 1, rng))
        # đối chứng: không nhiễu -> phải gần như hoàn hảo
        rows.append(cell(tau_s, sigma, "none", LAG_LO, rng))

    signed = [r for r in rows if r["nugget"] == "ma1" and r["lag_lo"] == LAG_LO]
    legacy = [r for r in rows if r["nugget"] == "ma1" and r["lag_lo"] == 1]
    payload = {
        "schema": "dt4n.phase_g2.g3b_bias_sim.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "prereg": "docs/phase-G/65-prereg-g3b-sigma-tau-roundtrip.md",
        "provenance": provenance(),
        "design": {
            "dt_s": DT_S, "lag_span": LAG_SPAN, "lag_lo": LAG_LO,
            "T_over_tau": T_OVER_TAU, "v_nugget": V_NUGGET,
            "n_replicates": N_REPLICATES, "seed": SEED,
            "v_source": "docs/phase-G/61 section 1, run 3 direct measurement",
        },
        "cells": rows,
        "summary": {
            "max_abs_tau_rel_error_signed": max(
                abs(r["tau_rel_error"]) for r in signed),
            "max_abs_sigma_rel_error_signed": max(
                abs(r["sigma_rel_error"]) for r in signed),
            "min_lag_span_over_tau": min(r["lag_span_over_tau"] for r in signed),
            "legacy_estimator_worse_everywhere": all(
                abs(a["tau_rel_error"]) <= abs(b["tau_rel_error"])
                or not np.isfinite(b["tau_rel_error"])
                for a, b in zip(signed, legacy)),
            "all_cells_feasible": all(
                r["tau_ok"] and r["sigma_ok"] for r in signed),
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_contract_artifact(out, payload)

    print(f"{'tau':>5} {'sigma':>7} {'nug':>5} {'lo':>3} {'nlag':>5} "
          f"{'span/tau':>9} {'tau_err':>9} {'sig_err':>9}  ok")
    for r in rows:
        print(f"{r['tau_s']:>5.0f} {r['sigma_ref']:>7.3f} {r['nugget']:>5} "
              f"{r['lag_lo']:>3} {r['n_lags']:>5} {r['lag_span_over_tau']:>9.2f} "
              f"{r['tau_rel_error']:>+9.3f} {r['sigma_rel_error']:>+9.3f}  "
              f"{'OK' if r['tau_ok'] and r['sigma_ok'] else 'FAIL'}")
    print(f"\n{out}")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()

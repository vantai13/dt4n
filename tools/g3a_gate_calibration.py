#!/usr/bin/env python3
"""Calibrate every G'.3a gate before it is signed.

`G-L90` has now recurred twice in this branch: once as a threshold no
configuration could meet, and once as a threshold whose supporting null was
computed in the wrong configuration. Every gate below is therefore calibrated
against synthetic ground truth pushed through the SAME estimator, on the SAME
INCIDENCE, at the SAME run length, with the nugget model actually measured on
this hardware (MA(1), G-L103).

    python -m tools.g3a_gate_calibration
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from tools import g3_dryrun
from tools.artifact_guard import write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g3_dryrun import INCIDENCE, LINKS, physical_trace
from tools.g3a_omega_estimator import design_matrix, fit_omega

OUT = Path("results/SMOKE/phase-G2/g3a_gate_calibration.json")
SCHEMA = "dt4n.phase_g2.g3a_gate_calibration.v1"

TAU_S = 2.0
DT_S = 0.1
T_RUN_S = 410.0
N_REPLICATES = 3
OMEGA_GRID = (0.00, 0.25, 0.50, 0.75, 1.00)
N_TRIALS = 200
# ★ Per-link nugget VARIANCE measured in run 3 (doc 62), not a uniform sf.
#   The nugget is set by frame size and C*dt, so it is roughly ABSOLUTE, while
#   sigma_l scales with sqrt(deg_l). That makes sf_l differ across links
#   (G-L104), and that difference is what puts the K=0.7071 group (deg2 x deg1)
#   under more attenuation than the K=0.5 group (deg2 x deg2). Injecting a
#   sigma-proportional nugget instead makes sf uniform and erases the effect.
V_PER_LINK = None          # filled from the measured artifact at run time
SERIES_ANALYSIS = Path("results/SMOKE/phase-G2/g2_series_analysis.json")
SEED = 2026_09_05

# G-L101: bind the generator's step to the step actually driven.
g3_dryrun.DT_S = DT_S


def main() -> None:
    n_win = int(round(T_RUN_S / DT_S))
    n_link = len(LINKS)
    k_tilde = design_matrix(INCIDENCE)
    rng = np.random.default_rng(SEED)
    meas = json.loads(SERIES_ANALYSIS.read_text(encoding="utf-8"))
    v_link = np.asarray(meas["nugget_direct"]["v_per_link"], dtype=float)
    sf_vec = np.asarray(meas["fits"]["lags_2_to_8"]["sf_per_link"], dtype=float)

    rows = []
    for omega in OMEGA_GRID:
        acc = {k: [] for k in ("omega_hat", "intercept", "null_pairs_mean_r",
                               "null_pairs_max_abs_r", "level_ratio",
                               "level_ratio_corrected", "residual_rms")}
        for _ in range(N_TRIALS):
            per_rep = []
            for _ in range(N_REPLICATES):
                trace = physical_trace(omega, TAU_S, TAU_S, n_win, rng)
                rho = trace["rho_target"].T                     # (n_win, n_link)
                # MA(1) nugget: the conserving path measured in G'.2
                # absolute MA(1) nugget at the measured per-link variance
                u = rng.standard_normal((n_win + 1, n_link)) * np.sqrt(v_link / 2.0)
                per_rep.append(np.corrcoef((rho + (u[1:] - u[:-1])).T))
            pooled = np.tanh(np.mean(
                [np.arctanh(np.clip(R, -0.999999, 0.999999)) for R in per_rep],
                axis=0))
            np.fill_diagonal(pooled, 1.0)
            out = fit_omega(pooled, k_tilde, sf_vec)
            # Attenuation-corrected ratio: dividing by A removes the per-link
            # sf structure, so the ratio tests TOPOLOGY rather than nugget
            # structure and returns to the exact sqrt(2).
            iu2 = np.triu_indices(n_link, 1)
            a_pair = np.sqrt(np.outer(sf_vec, sf_vec))[iu2]
            rc = pooled[iu2] / a_pair
            kk = k_tilde[iu2]
            hi2, lo2 = kk > 0.6, (kk > 0.3) & (kk < 0.6)
            out["level_ratio_corrected"] = (
                float(rc[hi2].mean() / rc[lo2].mean())
                if abs(rc[lo2].mean()) > 1e-9 else float("nan"))
            for key in acc:
                acc[key].append(out[key])
        # A gate is read on the ABSOLUTE deviation, so calibrate the absolute
        # percentiles too. Reading a gate off an SD assumes symmetry and
        # normality; neither is guaranteed for a ratio or a residual RMS.
        stat = lambda a: {
            "median": float(np.nanmedian(a)), "sd": float(np.nanstd(a, ddof=1)),
            "p05": float(np.nanpercentile(a, 5)),
            "p95": float(np.nanpercentile(a, 95)),
            "abs_p95": float(np.nanpercentile(np.abs(a), 95)),
            "abs_p99": float(np.nanpercentile(np.abs(a), 99)),
            "max_abs": float(np.nanmax(np.abs(a))),
        }
        rows.append({"omega": omega,
                     **{k: stat(np.array(vals)) for k, vals in acc.items()}})
        print(f"  omega={omega:.2f}  omega_hat {rows[-1]['omega_hat']['median']:+.4f}"
              f" (sd {rows[-1]['omega_hat']['sd']:.4f})"
              f"  intercept {rows[-1]['intercept']['median']:+.5f}"
              f"  ratio raw {rows[-1]['level_ratio']['median']:.4f}"
              f"  corr {rows[-1]['level_ratio_corrected']['median']:.4f}")

    payload = {
        "schema": SCHEMA,
        "status": "SYNTHETIC_GATE_CALIBRATION_NO_EXPERIMENTAL_DATA",
        "principle": "G-L90 twice over: calibrate each gate against the same "
                     "estimator, INCIDENCE, run length and NUGGET MODEL that "
                     "the run will use",
        "provenance": provenance(),
        "design": {"tau_s": TAU_S, "dt_s": DT_S, "T_run_s": T_RUN_S,
                   "n_windows": n_win, "n_replicates": N_REPLICATES,
                   "n_trials": N_TRIALS, "omega_grid": list(OMEGA_GRID),
                   "nugget_model": "ma1_absolute_measured_per_link",
                   "v_per_link_source": str(SERIES_ANALYSIS),
                   "seed": SEED,
                   "k_tilde_norm_sq": float(
                       design_matrix(INCIDENCE)[np.triu_indices(n_link, 1)]
                       @ design_matrix(INCIDENCE)[np.triu_indices(n_link, 1)]),
                   "theoretical_level_ratio": math.sqrt(2.0)},
        "rows": rows,
    }
    print(write_contract_artifact(OUT, payload)[:16] + f"  -> {OUT}")


if __name__ == "__main__":
    main()

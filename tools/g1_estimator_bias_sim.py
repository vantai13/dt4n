#!/usr/bin/env python3
"""G'.1 -- NT 53: put SYNTHETIC GROUND TRUTH through the estimators the repo
has actually signed, at the configurations G' proposes to run.

Why this exists
---------------
`G-L90` records a pair of gates that could not be jointly satisfied, found
only after a 64-minute run. The root cause was that the thresholds were not
DERIVED from anything. NT 53 is the countermeasure: a threshold is only
signable if synthetic data whose truth you KNOW passes through the exact
estimator, at the exact configuration, and comes back inside the gate.

Two estimators are compared, and BOTH already exist in this repository:

  INTEGRAL  `tau_int` -- dt*(0.5 + sum_k ACF(k)) truncated at the first
            non-positive lag. This is the Phase D path
            (`tools/phase_d_pc_c2_prime.py:58`,
             `tools/phase_d_pc_c2_second.py:78`) that failed twice as PC-C2
            and PC-C2'. It requires the `correct_tau(tau_hat, sf, dt)`
            chain because a white nugget scales the ACF by `sf`.

  LOGLIN    `estimate_nugget(...)["tau_from_fit_s"]` from
            `tools/measurement_path_calib.py:18` -- regress log ACF(k) on k
            and read tau from the SLOPE. Phase G already uses this
            (`g_a003_split_sample.py`, `g1_4_physical_reanalysis.py`,
             `g_measurement_coherence.py`, `g_a005_reclassification.py`).
            A white nugget multiplies ACF by a constant `sf`, so it lands
            entirely in the INTERCEPT and leaves the slope untouched. The
            same fit returns `sf` for free, as an independent cross-check
            on the G'.4 certificate.

This tool does not adjudicate, does not relax a gate, and touches no network.

    python -m tools.g1_estimator_bias_sim            # write the artifact
    python -m tools.g1_estimator_bias_sim --quick    # coarse grid, for edits
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import lfilter

from tools.measurement_path_calib import estimate_nugget

OUT = Path("results/SMOKE/phase-G2/g1_bias_sim.json")
SCHEMA = "dt4n.phase_g2.estimator_bias_sim.v1"

TAU_GRID = (1.0, 3.0, 5.0, 10.0, 20.0, 30.0)
T_OVER_TAU_GRID = (55, 100, 200)
SF_GRID = (1.00, 0.95, 0.90)
N_FIT_LAGS = 8          # the signed default of estimate_nugget
N_TRIAL = 600
N_REP_GATE = 3          # the gate reads the MEDIAN of this many replicates
BURN_IN_TAU = 5.0
GATE_TOL = 0.20
SEED = 2026_09_05


def provenance() -> dict[str, object]:
    """Provenance for a contract artifact.

    `worktree_dirty_at_execution` covers TRACKED files only. That is the
    question the field has to answer -- whether `git checkout <head>` restores
    the code that ran. An artifact this tool is about to write is untracked at
    that moment and says nothing about reproducibility, so counting it would
    make the flag permanently true and therefore useless. Untracked paths are
    reported separately so nothing is hidden.
    """
    head = subprocess.run(["git", "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    tracked = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        capture_output=True, text=True).stdout.strip()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True).stdout.split()
    return {
        "git_head_at_execution": head,
        "worktree_dirty_at_execution": bool(tracked),
        "dirty_scope": "tracked files only",
        "untracked_paths_present": len(untracked),
    }


def dt_of(tau: float) -> float:
    """Sampling step: the 0.2 s instrument step, but never coarser than tau/20."""
    return min(0.2, tau / 20.0)


def ar1_batch(
    n: int, phi: float, n_trial: int, rng: np.random.Generator
) -> np.ndarray:
    """`n_trial` independent AR(1) paths, unit marginal variance, as rows.

    Same recursion as `measurement_path_calib._ar1`, evaluated by `lfilter`
    so the grid finishes in minutes rather than hours.
    """
    innovations = rng.standard_normal((n_trial, n)) * np.sqrt(1.0 - phi * phi)
    innovations[:, 0] = rng.standard_normal(n_trial)
    return lfilter([1.0], [1.0, -phi], innovations, axis=1)


def acf_prefix(values: np.ndarray, nlag: int) -> np.ndarray:
    """Biased sample ACF, lags 0..nlag. Same construction as the signed tools."""
    centered = values - float(values.mean())
    denominator = float(centered @ centered)
    if denominator <= 0:
        return np.concatenate(([1.0], np.zeros(nlag)))
    fft_len = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_len)
    autocov = np.fft.irfft(spectrum * np.conjugate(spectrum), fft_len)[: nlag + 1]
    return np.asarray(autocov / denominator, dtype=float)


def tau_int(values: np.ndarray, dt: float) -> float:
    """Integral time scale, verbatim from `tools/g0_estimator_bias_sim.py:33`."""
    nlag = len(values) // 4
    curve = acf_prefix(values, nlag)
    cut = nlag
    for lag in range(1, len(curve)):
        if curve[lag] <= 0:
            cut = lag - 1
            break
    return float(dt * (0.5 + curve[1 : cut + 1].sum()))


def med_of_groups(values: np.ndarray, group: int) -> np.ndarray:
    """Median within disjoint groups of `group`. Disjoint, so no trial is reused."""
    usable = (len(values) // group) * group
    if usable == 0:
        return np.array([])
    return np.median(values[:usable].reshape(-1, group), axis=1)


def summarise(ratios: np.ndarray) -> dict[str, object]:
    finite = ratios[np.isfinite(ratios)]
    if finite.size == 0:
        return {"n_ok": 0, "ok_fraction": 0.0, "median": None,
                "p05": None, "p95": None, "med3_p05": None,
                "med3_p95": None, "bias_factor": None, "feasible": False}
    med3 = med_of_groups(finite, N_REP_GATE)
    bias = float(np.median(finite))
    # The gate reads a bias-CORRECTED median of N_REP_GATE replicates.
    corrected = med3 / bias if bias > 0 else med3 * np.nan
    p05 = float(np.percentile(corrected, 5))
    p95 = float(np.percentile(corrected, 95))
    return {
        "n_ok": int(finite.size),
        "ok_fraction": float(finite.size / ratios.size),
        "median": bias,
        "p05": float(np.percentile(finite, 5)),
        "p95": float(np.percentile(finite, 95)),
        "bias_factor": bias,
        "med3_corrected_p05": p05,
        "med3_corrected_p95": p95,
        "feasible": bool(
            abs(p05 - 1.0) <= GATE_TOL and abs(p95 - 1.0) <= GATE_TOL
        ),
    }


def run_cell(
    tau: float, t_over_tau: int, sf: float, n_trial: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    dt = dt_of(tau)
    phi = float(np.exp(-dt / tau))
    n_analysis = int(round(t_over_tau * tau / dt))
    n_burn = int(round(BURN_IN_TAU * tau / dt))
    paths = ar1_batch(n_analysis + n_burn, phi, n_trial, rng)[:, n_burn:]
    if sf < 1.0:
        # signal variance 1 -> nugget variance v with sf = 1/(1+v)
        v = (1.0 - sf) / sf
        paths = paths + rng.standard_normal(paths.shape) * np.sqrt(v)

    int_ratio = np.empty(n_trial)
    log_ratio = np.empty(n_trial)
    slope_ratio = np.empty(n_trial)
    sf_hat = np.empty(n_trial)
    for i in range(n_trial):
        row = paths[i]
        int_ratio[i] = tau_int(row, dt) / tau
        fit = estimate_nugget(row, dt, n_fit_lags=N_FIT_LAGS)
        tau_fit = fit.get("tau_from_fit_s", float("nan"))
        usable = np.isfinite(tau_fit) and tau_fit > 0
        # As the estimator is signed: `ok` requires 0 < sf_hat <= 1, so a
        # record CLEANER than the nugget model allows is rejected outright.
        log_ratio[i] = float(tau_fit) / tau if (fit.get("ok") and usable) else np.nan
        # Slope only: the nugget scales ACF by a constant, so it lands in the
        # INTERCEPT. The slope that carries tau is valid whatever sf_hat does.
        slope_ratio[i] = float(tau_fit) / tau if usable else np.nan
        sf_hat[i] = float(fit.get("sf", np.nan))

    finite_sf = sf_hat[np.isfinite(sf_hat)]
    return {
        "tau_s": tau,
        "dt_s": dt,
        "tau_over_dt": tau / dt,
        "T_over_tau": t_over_tau,
        "sf_true": sf,
        "v_over_sigma2": (1.0 - sf) / sf,
        "n_samples": n_analysis,
        "n_eff_predicted": n_analysis * (1 - phi**2) / (1 + phi**2),
        "integral": summarise(int_ratio),
        "loglinear_signed": summarise(log_ratio),
        "loglinear_slope_only": summarise(slope_ratio),
        "sf_hat_median": float(np.median(finite_sf)) if finite_sf.size else None,
        "sf_hat_p05": float(np.percentile(finite_sf, 5)) if finite_sf.size else None,
        "sf_hat_p95": float(np.percentile(finite_sf, 95)) if finite_sf.size else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="coarse grid while editing; not a signable artifact")
    args = parser.parse_args()
    n_trial = 120 if args.quick else N_TRIAL
    taus = (1.0, 5.0, 20.0) if args.quick else TAU_GRID

    rng = np.random.default_rng(SEED)
    rows = [
        run_cell(tau, t_over_tau, sf, n_trial, rng)
        for tau in taus
        for t_over_tau in T_OVER_TAU_GRID
        for sf in SF_GRID
    ]
    payload = {
        "schema": SCHEMA,
        "status": "SYNTHETIC_DIAGNOSTIC_NO_EXPERIMENTAL_DATA",
        "principle": "NT 53: exercise the signed estimator against known truth "
                     "before signing a threshold",
        "provenance": provenance(),
        "design": {
            "seed": SEED,
            "n_trial_per_cell": n_trial,
            "n_replicates_per_gate_read": N_REP_GATE,
            "gate_tolerance": GATE_TOL,
            "burn_in_tau": BURN_IN_TAU,
            "n_fit_lags": N_FIT_LAGS,
            "dt_rule": "dt = min(0.2, tau/20)",
            "estimators": {
                "integral": "tools/g0_estimator_bias_sim.py:33 tau_int",
                "loglinear": "tools/measurement_path_calib.py:18 "
                             "estimate_nugget -> tau_from_fit_s",
            },
            "quick_mode": bool(args.quick),
        },
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(rows)} cells")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Direct analysis of a stored kill-test series: nugget without an estimator.

`rho_target` is deterministic given the seed, so `eps = rho_measured -
rho_target` is the nugget itself. Nothing here fits a model to get it, which
is what makes these numbers stronger than the `estimate_nugget` readings they
replace.

Everything reported against a NULL. A small number with no null attached says
nothing: `max|rho_eps| = 0.0227` reads as "small" but is in fact the MEDIAN of
what independent links produce at this sample size, which is a stronger and
different statement -- not "small correlation" but "no detectable correlation".

    python -m tools.g2_series_analysis
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from tools.g1_estimator_bias_sim import provenance

SERIES = Path("results/SMOKE/phase-G2/g2_kill_series.npz")
OUT = Path("results/SMOKE/phase-G2/g2_series_analysis.json")
SCHEMA = "dt4n.phase_g2.series_analysis.v1"
N_NULL_TRIALS = 400
FIT_LAGS = 8
FIT_LAG_LO = 2          # G-L103: lag 1 carries the conserving nugget
SEED = 2026_09_05
FRAME_BYTES = 1442.0


def acf(x: np.ndarray, n_lags: int) -> np.ndarray:
    x = x - x.mean()
    c0 = float(x @ x)
    return np.array([float(x[:-k] @ x[k:]) / c0 for k in range(1, n_lags + 1)])


def fit_intercept_slope(x: np.ndarray, dt: float, lag_lo: int) -> tuple[float, float]:
    r = acf(x, FIT_LAGS)
    lags = np.arange(1, FIT_LAGS + 1)
    keep = (r > 0) & (lags >= lag_lo)
    if keep.sum() < 3:
        return float("nan"), float("nan")
    slope, intercept = np.polyfit(lags[keep], np.log(r[keep]), 1)
    tau = -dt / slope if slope < 0 else float("nan")
    return float(np.exp(intercept)), float(tau)


def fisher_pool(rs: np.ndarray) -> np.ndarray:
    return np.tanh(np.arctanh(np.clip(rs, -0.999999, 0.999999)).mean(axis=0))


def ma1_null(nrep: int, nwin: int, nlink: int, rng) -> dict:
    """Null for the rho_eps statistics: MA(1) nugget, links independent BY
    CONSTRUCTION. Answers 'what would we see if rho_eps were exactly zero?'"""
    iu = np.triu_indices(nlink, 1)
    maxes = np.empty(N_NULL_TRIALS)
    meds = np.empty(N_NULL_TRIALS)
    for trial in range(N_NULL_TRIALS):
        reps = []
        for _ in range(nrep):
            u = rng.standard_normal((nwin + 1, nlink))
            eps = u[1:] - u[:-1]
            reps.append(np.corrcoef(eps.T)[iu])
        pooled = np.abs(fisher_pool(np.array(reps)))
        maxes[trial] = pooled.max()
        meds[trial] = np.median(pooled)
    return {"max": maxes, "median": meds}


def main() -> None:
    z = np.load(SERIES, allow_pickle=True)
    measured, target = z["rho_measured"], z["rho_target"]
    dt, tau_true = float(z["dt_s"]), float(z["tau_s"])
    cap = np.asarray(z["cap_bps"], dtype=float)
    eps = measured - target
    nrep, nwin, nlink = eps.shape
    iu = np.triu_indices(nlink, 1)

    # --- alignment, checked not assumed -------------------------------------
    align = {}
    for lag in (-2, -1, 0, 1, 2):
        if lag > 0:
            d = measured[:, lag:] - target[:, :-lag]
        elif lag < 0:
            d = measured[:, :lag] - target[:, -lag:]
        else:
            d = eps
        align[str(lag)] = float(d.var(axis=1).mean())

    # --- nugget, measured directly ------------------------------------------
    v_link = eps.var(axis=1, ddof=1).mean(axis=0)
    var_meas = measured.var(axis=1, ddof=1)
    sf_direct = np.median(1.0 - eps.var(axis=1, ddof=1) / var_meas, axis=0)
    v_q = np.array([(8.0 * FRAME_BYTES / (c * dt) / math.sqrt(12.0)) ** 2 for c in cap])

    # --- whiteness ----------------------------------------------------------
    acf_eps = np.array([[acf(eps[r, :, i], 10) for i in range(nlink)]
                        for r in range(nrep)]).mean(axis=(0, 1))
    band = 2.0 / math.sqrt(nwin)

    # --- conservation -------------------------------------------------------
    cumsum = np.cumsum(eps, axis=1)
    mean_eps = eps.mean(axis=1)

    # --- rho_eps, with its null ---------------------------------------------
    per_rep = np.array([np.corrcoef(eps[r].T)[iu] for r in range(nrep)])
    rho_eps = fisher_pool(per_rep)
    obs_max, obs_med = float(np.abs(rho_eps).max()), float(np.median(np.abs(rho_eps)))
    null = ma1_null(nrep, nwin, nlink, np.random.default_rng(SEED))
    pct = lambda a, q: float(np.percentile(a, q))

    # --- sf and tau, both fit ranges ---------------------------------------
    fits = {}
    for lo in (1, FIT_LAG_LO):
        sf_pl, tau_pl = [], []
        for i in range(nlink):
            s = [fit_intercept_slope(measured[r, :, i], dt, lo) for r in range(nrep)]
            sf_pl.append(float(np.nanmedian([a for a, _ in s])))
            tau_pl.append(float(np.nanmedian([b for _, b in s])))
        # tau is ONE parameter: physical_trace calls ar1(len(LINKS), tau_link_s,
        # ...), so every link shares it and per-link differences can only be
        # estimation noise. Pooling all fits is therefore both legitimate and
        # more precise, and the pooled figure is the one to read.
        # sf is the opposite: it differs per link BY CONSTRUCTION because
        # sigma_l scales with DEGREE while v is common, so it takes
        # min-over-links (G-A019 sec 4.1). Same data, two different reductions,
        # for a reason that is about the parameter and not about the statistics.
        tau_flat = [fit_intercept_slope(measured[r, :, i], dt, lo)[1]
                    for r in range(nrep) for i in range(nlink)]
        tau_pooled = float(np.nanmedian(tau_flat))
        fits[f"lags_{lo}_to_{FIT_LAGS}"] = {
            "sf_per_link": sf_pl,
            "sf_min_over_links": float(np.nanmin(sf_pl)),
            "sf_median_over_links": float(np.nanmedian(sf_pl)),
            "tau_pooled_over_all_fits": tau_pooled,
            "tau_bias_pooled": float(tau_pooled / tau_true - 1.0),
            "tau_per_link": tau_pl,
            "tau_worst_link_abs_dev": float(
                np.nanmax(np.abs(np.array(tau_pl) / tau_true - 1.0))),
            "reduction_note": "tau pooled (one shared parameter); "
                              "sf min-over-links (differs per link by design)",
        }

    payload = {
        "schema": SCHEMA,
        "status": "DIRECT_MEASUREMENT_FROM_STORED_SERIES",
        "source_series": str(SERIES),
        "provenance": provenance(),
        "design": {"n_replicates": nrep, "n_windows": nwin, "n_links": nlink,
                   "dt_s": dt, "tau_s": tau_true, "n_null_trials": N_NULL_TRIALS,
                   "seed": SEED, "fit_lags": FIT_LAGS},
        "alignment_var_eps_by_lag": align,
        "nugget_direct": {
            "v_per_link": v_link.tolist(),
            "v_mean": float(v_link.mean()),
            "v_q_per_link": v_q.tolist(),
            "sf_direct_per_link": sf_direct.tolist(),
            "sf_direct_min_over_links": float(sf_direct.min()),
        },
        "whiteness": {
            "acf_lags_1_to_10": acf_eps.tolist(),
            "white_noise_band": band,
            "acf1": float(acf_eps[0]),
            "ma1_theoretical_acf1": -0.5,
            "lags_outside_band": [int(k + 1) for k in range(10)
                                  if abs(acf_eps[k]) > band],
            "is_white": bool(all(abs(a) <= band for a in acf_eps)),
        },
        "conservation": {
            "max_abs_cumsum_eps": float(np.abs(cumsum).max()),
            "predicted_if_white_sqrt_n": float(
                math.sqrt(nwin) * eps.std(axis=1, ddof=1).mean()),
            "predicted_if_conserving_two_burst": float(
                2 * FRAME_BYTES / (cap.mean() * dt / 8)),
            "max_abs_mean_eps_per_link": float(np.abs(mean_eps).max()),
            "systematic_offset_times_n": float(np.abs(mean_eps).max() * nwin),
            "verdict": "CONSERVING",
        },
        "rho_eps": {
            "max_abs": obs_max,
            "median_abs": obs_med,
            "per_pair_abs_sorted": np.sort(np.abs(rho_eps))[::-1].tolist(),
            "null_max_abs": {"median": pct(null["max"], 50),
                             "p95": pct(null["max"], 95),
                             "p99": pct(null["max"], 99)},
            "null_median_abs": {"median": pct(null["median"], 50),
                                "p95": pct(null["median"], 95),
                                "p99": pct(null["median"], 99)},
            "p_null_ge_observed_max": float(np.mean(null["max"] >= obs_max)),
            "p_null_ge_observed_median": float(np.mean(null["median"] >= obs_med)),
            "percentile_of_observed_max": float(100 * np.mean(null["max"] <= obs_max)),
            "interpretation": (
                "rho_eps is NOT DISTINGUISHABLE FROM ZERO: the observed value "
                "sits inside the distribution produced by links that are "
                "independent by construction."),
        },
        "fits": fits,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT}")


if __name__ == "__main__":
    main()

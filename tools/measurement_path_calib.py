#!/usr/bin/env python3
"""Phase G.1 measurement-path calibration estimators.

Model::

    rho_measured_l(t) = rho_true_l(t) + epsilon_l(t)

The nugget ``epsilon`` is temporally white but may be correlated across links.
This module estimates signal fraction, nugget variance, and the raw
first-difference proxy for common-mode nugget correlation.  Every estimator
must pass synthetic G1-A validation before use on experimental data.
"""
from __future__ import annotations

import numpy as np


def estimate_nugget(
    x: np.ndarray, dt: float, n_fit_lags: int = 8
) -> dict[str, object]:
    """Estimate nugget by extrapolating the positive-lag ACF to lag zero.

    For exponential true ACF,
    ``log(ACF_measured(k)) = log(sf) + k*log(phi)`` for ``k >= 1``.
    Only early lags above the approximate two-sigma ACF noise floor are fit.
    """
    values = np.asarray(x, dtype=float)
    n = len(values)
    centered = values - values.mean()
    denominator = float(centered @ centered)
    if denominator <= 0:
        return {
            "sf": float("nan"),
            "v": float("nan"),
            "ok": False,
            "reason": "zero variance",
        }

    fft_len = 1 << (2 * n - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_len)
    acf = np.fft.irfft(
        spectrum * np.conjugate(spectrum), fft_len
    )[: n_fit_lags + 1] / denominator

    lags = np.arange(1, n_fit_lags + 1)
    positive_acf = acf[1 : n_fit_lags + 1]
    noise_floor = 2.0 / np.sqrt(n)
    keep = positive_acf > noise_floor
    if keep.sum() < 4:
        return {
            "sf": float("nan"),
            "v": float("nan"),
            "ok": False,
            "reason": "ACF below noise floor; increase T_run or dt",
            "n_lags_used": int(keep.sum()),
            "acf_noise_floor": float(noise_floor),
        }

    design = np.vstack([np.ones(keep.sum()), lags[keep]]).T
    coefficients, *_ = np.linalg.lstsq(
        design, np.log(positive_acf[keep]), rcond=None
    )
    sf = float(np.exp(coefficients[0]))
    phi = float(np.exp(coefficients[1]))
    total_variance = float(values.var(ddof=1))
    return {
        "sf": sf,
        "v": float(total_variance * (1.0 - sf)),
        "sigma_true": float(np.sqrt(max(total_variance * sf, 0.0))),
        "tau_from_fit_s": (
            float(-dt / np.log(phi)) if 0.0 < phi < 1.0 else float("nan")
        ),
        "n_lags_used": int(keep.sum()),
        "acf_noise_floor": float(noise_floor),
        "ok": bool(0.0 < sf <= 1.0),
        "reason": "" if 0.0 < sf <= 1.0 else "sf outside (0,1]",
    }


def estimate_rho_eps(
    x_l: np.ndarray, x_m: np.ndarray, tau_s: float, dt: float
) -> dict[str, object]:
    """Estimate common-mode nugget with a first-difference high-pass proxy.

    The raw correlation is interpretable as ``rho_eps`` only when the reported
    signal-leakage positive control is small.
    """
    delta_l = np.diff(np.asarray(x_l, dtype=float))
    delta_m = np.diff(np.asarray(x_m, dtype=float))
    rho_eps_hat = float(np.corrcoef(delta_l, delta_m)[0, 1])

    phi = float(np.exp(-dt / tau_s))
    v_l_approx = 0.5 * float(np.var(delta_l, ddof=1))
    sigma2_l_approx = max(float(np.var(x_l, ddof=1)) - v_l_approx, 0.0)
    leakage = sigma2_l_approx * (1.0 - phi) / max(v_l_approx, 1e-18)

    return {
        "rho_eps_hat": rho_eps_hat,
        "signal_leakage_ratio": float(leakage),
        "valid": bool(leakage < 0.20),
        "note": (
            ""
            if leakage < 0.20
            else "signal leakage too large; increase tau/dt or use full estimator"
        ),
    }


def raw_diff_bias_prediction(sf: float, phi: float) -> float:
    """Predict raw difference correlation for ``r_true=0, rho_eps=1``."""
    leakage = (1.0 - phi) * sf / (1.0 - sf)
    return float(1.0 / (1.0 + leakage))


def estimate_two_band(
    x_l: np.ndarray,
    x_m: np.ndarray,
    sf_l: float,
    sf_m: float,
    phi: float,
    phi_m: float | None = None,
) -> dict[str, object]:
    """Separate true correlation and common-mode nugget using two bands.

    Level and first-difference correlations weight the slow signal and white
    nugget differently.  The resulting two-by-two system identifies
    ``r_true`` and ``rho_eps`` when it is sufficiently well conditioned.
    """
    if not (0.0 < sf_l < 1.0 and 0.0 < sf_m < 1.0):
        return {"valid": False, "reason": "sf must lie strictly inside (0,1)"}
    phi_l = float(phi)
    phi_m = phi_l if phi_m is None else float(phi_m)
    if not (0.0 < phi_l < 1.0 and 0.0 < phi_m < 1.0):
        return {"valid": False, "reason": "both phi values must lie inside (0,1)"}

    def w_of(signal_fraction: float, phi_value: float) -> float:
        numerator = signal_fraction * (1.0 - phi_value)
        return float(numerator / (numerator + 1.0 - signal_fraction))

    w_l = w_of(sf_l, phi_l)
    w_m = w_of(sf_m, phi_m)
    # For unequal AR(1) memory, Corr(diff(signal_l), diff(signal_m)) is
    # q*r_true rather than r_true.  q=1 exactly when phi_l=phi_m.
    q_signal = float(
        (2.0 - phi_l - phi_m)
        / (2.0 * np.sqrt((1.0 - phi_l) * (1.0 - phi_m)))
    )
    matrix = np.array(
        [
            [
                np.sqrt(sf_l * sf_m),
                np.sqrt((1.0 - sf_l) * (1.0 - sf_m)),
            ],
            [
                q_signal * np.sqrt(w_l * w_m),
                np.sqrt((1.0 - w_l) * (1.0 - w_m)),
            ],
        ]
    )
    observations = np.array(
        [
            float(np.corrcoef(x_l, x_m)[0, 1]),
            float(np.corrcoef(np.diff(x_l), np.diff(x_m))[0, 1]),
        ]
    )

    condition = float(np.linalg.cond(matrix))
    if not np.isfinite(condition) or condition > 10.0:
        return {
            "valid": False,
            "cond_A": condition,
            "reason": "near-degenerate system; increase tau/dt or change dt",
        }

    r_true, rho_eps = np.linalg.solve(matrix, observations)
    return {
        "r_true_hat": float(r_true),
        "rho_eps_hat": float(rho_eps),
        "r_level": float(observations[0]),
        "r_diff": float(observations[1]),
        "w_l": w_l,
        "w_m": w_m,
        "phi_l": phi_l,
        "phi_m": phi_m,
        "q_signal": q_signal,
        "cond_A": condition,
        "in_physical_range": bool(abs(r_true) <= 1.0 and abs(rho_eps) <= 1.0),
        "lambda_leakage_l": float((1.0 - phi_l) * sf_l / (1.0 - sf_l)),
        "lambda_leakage_m": float((1.0 - phi_m) * sf_m / (1.0 - sf_m)),
        "valid": True,
        "reason": "",
    }


def correct_r(
    r_measured: float, sf_l: float, sf_m: float, rho_eps: float
) -> float:
    """Remove attenuation and common-mode contamination from correlation."""
    numerator = r_measured - np.sqrt((1.0 - sf_l) * (1.0 - sf_m)) * rho_eps
    return float(numerator / np.sqrt(sf_l * sf_m))


def correct_tau(tau_hat: float, sf: float, dt: float) -> float:
    """Correct integral time scale for a temporally white nugget."""
    return float((tau_hat - 0.5 * dt * (1.0 - sf)) / sf)


def _ar1(
    n: int, phi: float, rng: np.random.Generator
) -> np.ndarray:
    values = np.empty(n)
    values[0] = rng.standard_normal()
    innovations = rng.standard_normal(n) * np.sqrt(1.0 - phi * phi)
    for index in range(1, n):
        values[index] = phi * values[index - 1] + innovations[index]
    return values


def g1a_estimator_validation(seed: int = 20260902) -> list[dict[str, object]]:
    """Inject known nugget into independent AR(1) signals and recover it."""
    rng = np.random.default_rng(seed)
    dt, tau, sigma, n = 0.20, 3.0, 0.03, 30_000
    phi = float(np.exp(-dt / tau))
    output = []

    for sf_true in (0.30, 0.50, 0.70, 0.85, 0.95):
        v_true = sigma**2 * (1.0 / sf_true - 1.0)
        rows_sf = []
        rows_rho_eps = []
        rows_leakage = []
        rows_valid = []
        rows_estimator_ok = []
        for _ in range(16):
            true_l = 0.857 + sigma * _ar1(n, phi, rng)
            true_m = 0.857 + sigma * _ar1(n, phi, rng)
            common_nugget = rng.standard_normal(n) * np.sqrt(v_true)
            x_l = true_l + common_nugget
            x_m = true_m + common_nugget

            nugget_estimate = estimate_nugget(x_l, dt)
            rho_estimate = estimate_rho_eps(x_l, x_m, tau, dt)
            rows_sf.append(float(nugget_estimate["sf"]))
            rows_rho_eps.append(float(rho_estimate["rho_eps_hat"]))
            rows_leakage.append(float(rho_estimate["signal_leakage_ratio"]))
            rows_valid.append(bool(rho_estimate["valid"]))
            rows_estimator_ok.append(bool(nugget_estimate["ok"]))

        sf_hat = float(np.nanmedian(rows_sf))
        rho_eps_hat = float(np.nanmedian(rows_rho_eps))
        true_leakage = float((1.0 - phi) * sf_true / (1.0 - sf_true))
        output.append(
            {
                "sf_true": sf_true,
                "v_true": v_true,
                "sf_hat_median": sf_hat,
                "sf_hat_p05": float(np.nanpercentile(rows_sf, 5)),
                "sf_hat_p95": float(np.nanpercentile(rows_sf, 95)),
                "sf_bias_ratio": sf_hat / sf_true,
                "nugget_estimator_ok_fraction": float(np.mean(rows_estimator_ok)),
                "rho_eps_true": 1.0,
                "rho_eps_hat_median": rho_eps_hat,
                "rho_eps_hat_p05": float(np.percentile(rows_rho_eps, 5)),
                "rho_eps_hat_p95": float(np.percentile(rows_rho_eps, 95)),
                "signal_leakage_ratio_median": float(np.median(rows_leakage)),
                "signal_leakage_valid_fraction": float(np.mean(rows_valid)),
                "signal_leakage_ratio_true": true_leakage,
                "raw_diff_corr_theory": float(1.0 / (1.0 + true_leakage)),
                "gates": {
                    "G1-0_sf": abs(sf_hat / sf_true - 1.0) <= 0.15,
                    "G1-0_rho_eps_raw": abs(rho_eps_hat - 1.0) <= 0.10,
                },
            }
        )
    return output

#!/usr/bin/env python3
"""Estimate omega from the 28-pair correlation matrix.

Model, derived from `physical_trace` rather than assumed:

    Var(rho_l) = a0^2 * deg_l                    -- independent of omega
    Cov(l, m)  = omega * a0^2 * k_topo(l, m)
    r_true     = omega * K_tilde,
                 K_tilde = k_topo / sqrt(deg_l * deg_m)

Measured correlations are attenuated PER PAIR, not by one scalar:

    r_meas(l,m) = omega * sqrt(sf_l * sf_m) * K_tilde(l,m) + (1-sf)*rho_eps

★ `sf_l` differs across links BY CONSTRUCTION -- `sigma_l` scales with
  `sqrt(deg_l)` while `v` is common (G-L104) -- so the attenuation belongs in
  the design matrix, not in a division afterwards. Using a scalar median `sf`
  biases `omega_hat` by 1 to 2 percent.
"""
from __future__ import annotations

import numpy as np


def design_matrix(incidence) -> np.ndarray:
    """K_tilde from INCIDENCE. Computed, never assumed."""
    inc = np.asarray(incidence, float)
    deg = inc.sum(axis=1)
    return (inc @ inc.T) / np.sqrt(np.outer(deg, deg))


def fit_omega(R: np.ndarray, k_tilde: np.ndarray, sf: np.ndarray) -> dict:
    n = R.shape[0]
    iu = np.triu_indices(n, 1)
    attenuation = np.sqrt(np.outer(sf, sf))
    m = (attenuation * k_tilde)[iu]
    r = R[iu]
    k = k_tilde[iu]

    omega_hat = float(r @ m / (m @ m))                       # through the origin

    design = np.vstack([np.ones_like(m), m]).T               # with intercept, P-3
    coef, *_ = np.linalg.lstsq(design, r, rcond=None)
    intercept, slope = float(coef[0]), float(coef[1])

    hi, lo, nulls = k > 0.6, (k > 0.3) & (k < 0.6), k == 0.0
    ratio = (float(r[hi].mean() / r[lo].mean())
             if abs(r[lo].mean()) > 1e-9 else float("nan"))
    residual = r - omega_hat * m

    return {
        "omega_hat": omega_hat,
        "intercept": intercept,
        "slope_with_intercept": slope,
        "null_pairs_mean_r": float(r[nulls].mean()),
        "null_pairs_max_abs_r": float(np.abs(r[nulls]).max()),
        "level_ratio": ratio,
        "residual_rms": float(np.sqrt((residual ** 2).mean())),
        "n_pairs": int(len(r)),
        "k_norm_sq": float(k @ k),
    }


def rho_eps_from_series(rho_measured: np.ndarray,
                        rho_target: np.ndarray) -> dict:
    """P-7: rho_eps straight from eps, with no estimator in the way."""
    eps = rho_measured - rho_target
    n = eps.shape[1]
    iu = np.triu_indices(n, 1)
    corr = np.corrcoef(eps.T)[iu]
    return {
        "rho_eps_max_abs": float(np.abs(corr).max()),
        "rho_eps_median_abs": float(np.median(np.abs(corr))),
        "v_direct_per_link": eps.var(axis=0, ddof=1).tolist(),
        # Must stay near -0.50 (conserving MA(1) nugget, G-L103). A drift away
        # from it means the measurement path itself changed under common drive.
        "eps_acf1_per_link": [
            float(np.corrcoef(eps[:-1, i], eps[1:, i])[0, 1])
            for i in range(n)
        ],
    }

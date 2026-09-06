"""NC: `lag_lo=1` must reproduce the pre-G-A019 estimator bit-exact.

This is a REGRESSION CONTROL, not a science test. Every artifact produced
before G-A019 referenced `estimate_nugget` with the lag-1 fit; if the default
ever drifts, those artifacts silently stop being reproducible (NT 41).
"""
import numpy as np

from tools.measurement_path_calib import estimate_nugget


def _legacy_estimate_nugget(
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



def test_lag_lo_one_is_the_legacy_estimator():
    rng = np.random.default_rng(20260906)
    phi = np.exp(-0.1 / 2.0)
    for _ in range(200):
        n = 4100
        u = np.empty(n)
        u[0] = rng.standard_normal()
        eps = rng.standard_normal(n)
        for k in range(1, n):
            u[k] = phi * u[k - 1] + np.sqrt(1 - phi * phi) * eps[k]
        x = 0.0303 * u + rng.standard_normal(n) * 0.008
        a = estimate_nugget(x, 0.1, 8)              # mặc định
        b = estimate_nugget(x, 0.1, 8, lag_lo=1)    # tường minh
        legacy = _legacy_estimate_nugget(x, 0.1, 8)
        assert a == b
        for key, value in legacy.items():
            assert a[key] == value, key


def test_lag_lo_two_beats_lag_lo_one_under_ma1_nugget():
    """PC: with a conserving (MA(1)) nugget, excluding lag 1 must reduce
    the tau bias. This encodes G-L103 as an executable claim."""
    rng = np.random.default_rng(11)
    dt, tau, sigma, v = 0.1, 5.0, 0.0303, 6.5e-5
    phi = np.exp(-dt / tau)
    n = int(205 * tau / dt)
    err1, err2 = [], []
    for _ in range(8):
        u = np.empty(n)
        u[0] = rng.standard_normal()
        eps = rng.standard_normal(n)
        for k in range(1, n):
            u[k] = phi * u[k - 1] + np.sqrt(1 - phi * phi) * eps[k]
        w = rng.standard_normal(n + 1) * np.sqrt(v)
        y = sigma * u + (w[1:] - w[:-1])          # nugget sai phân bậc nhất
        n_lags = int(round(0.4 * tau / dt))
        err1.append(abs(estimate_nugget(y, dt, n_lags, 1)["tau_from_fit_s"] / tau - 1))
        err2.append(abs(estimate_nugget(y, dt, n_lags, 2)["tau_from_fit_s"] / tau - 1))
    assert np.median(err2) < np.median(err1)
    assert np.median(err2) <= 0.20                # ngân sách claim B

import numpy as np
import pytest

from measurements import acf_nugget as N


def test_fit_nugget_recovers_exact_exponential_curve():
    signal_fraction = 0.4
    tau_s = 2.5
    curve = signal_fraction * np.exp(
        -np.asarray(N.FIT_LAGS) * N.DT_MEASURED_S / tau_s)
    fit = N.fit_nugget(curve)
    assert fit["valid"] is True
    assert fit["signal_fraction"] == pytest.approx(signal_fraction, abs=1e-12)
    assert fit["lambda_nugget"] == pytest.approx(0.6, abs=1e-12)
    assert fit["tau_measured_s"] == pytest.approx(tau_s, abs=1e-12)


def test_fit_nugget_rejects_nondecaying_curve():
    fit = N.fit_nugget(np.linspace(0.2, 0.8, len(N.FIT_LAGS)))
    assert fit["valid"] is False


def test_acf_has_unit_lag_zero():
    x = np.sin(np.arange(100) / 5.0)
    got = N.acf(x, (0, 1, 2))
    assert got[0] == 1.0
    assert got[1] < 1.0

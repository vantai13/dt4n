import numpy as np

from tools.g_measurement_coherence import (
    DT_TARGET_S,
    curve_for_trace,
    estimate_local_v,
    window_slices,
)


def test_window_slices_include_endpoint_without_fabricating_full_window_cv():
    slices, window_n, stride_n = window_slices(7524, 1505)

    assert window_n == 7524
    assert stride_n == 3762
    assert [(part.start, part.stop) for part in slices] == [(0, 7524)]
    assert curve_for_trace(np.arange(7524, dtype=float))["1505"]["cv_v_projected"] is None


def test_window_slices_use_half_window_stride_and_include_endpoint():
    slices, window_n, stride_n = window_slices(7524, 50)

    assert window_n == round(50 / DT_TARGET_S)
    assert stride_n == round(window_n / 2)
    assert slices[0] == slice(0, window_n)
    assert slices[-1] == slice(7524 - window_n, 7524)


def test_local_v_recovers_positive_nugget_on_seeded_ar1_plus_noise():
    rng = np.random.default_rng(7)
    n = 20_000
    phi = np.exp(-DT_TARGET_S / 2.0)
    signal = np.empty(n)
    signal[0] = rng.standard_normal()
    for index in range(1, n):
        signal[index] = (
            phi * signal[index - 1]
            + np.sqrt(1.0 - phi**2) * rng.standard_normal()
        )
    values = np.sqrt(0.8) * signal + np.sqrt(0.2) * rng.standard_normal(n)

    estimate = estimate_local_v(values)

    assert estimate["fit_available"] is True
    assert 0.12 < estimate["v_projected"] < 0.28
    assert estimate["at_boundary"] is False

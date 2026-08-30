import hashlib
import json
from pathlib import Path

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


def test_locked_threshold_did_not_read_physical_curve():
    artifact = json.loads(
        Path("results/SMOKE/phase-G/g_coherence_thresholds.json").read_text()
    )

    assert artifact["physical_curve_read"] is False
    for link in ("uA", "uB", "vC", "vD"):
        assert artifact["thresholds"][link]["50"]["finite_cv_repetitions"] == 400
        assert artifact["thresholds"][link]["1505"]["cv_null_p95"] is None


def test_physical_curve_preserves_threshold_bytes_and_has_no_w_star():
    artifact = json.loads(
        Path("results/SMOKE/phase-G/g_measurement_coherence.json").read_text()
    )
    threshold_path = Path(artifact["threshold_artifact"])

    assert hashlib.sha256(threshold_path.read_bytes()).hexdigest() == artifact[
        "threshold_sha256"
    ]
    assert artifact["summary"]["W_star_s_largest_all_link_pass"] is None
    assert artifact["summary"]["window_1505_status"] == "NOT_IDENTIFIABLE_ONE_WINDOW"
    assert not any(artifact["summary"]["all_link_pass_by_window"].values())

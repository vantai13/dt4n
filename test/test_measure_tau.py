#!/usr/bin/env python3
"""Pure tests for Phase 20 tau measurement helpers."""

import csv

import numpy as np
import pytest

from measurements import measure_tau as MT


def test_tau_one_over_e_interpolates_threshold_crossing():
    a = np.array([1.0, np.exp(-0.5), np.exp(-1.0), np.exp(-1.5)])
    assert MT.tau_one_over_e(a, dt_s=2.0) == pytest.approx(4.0)


def test_resolution_check_flags_white_noise_floor():
    tau = (1.0 - 1.0 / np.e) * 0.010
    result = MT.resolution_check(tau, dt_s=0.010)
    assert result["status"] == "RESOLUTION_FLOOR"
    assert result["ok"] is False


def test_within_factor_uses_symmetric_log_ratio():
    ok, dev = MT.within_factor(0.0081, 0.433, factor=2.0)
    assert ok is False
    assert dev > 5.0


def test_classify_decay_uses_r2_floor_and_residual_ratio():
    assert MT.classify_decay(0.391, 0.507)["decay_kind"] == "no_fit"
    assert MT.classify_decay(0.982, 0.992)["decay_kind"] == "ambiguous"

    exp_fit = MT.classify_decay(0.999, 0.983)
    assert exp_fit["decay_kind"] == "exp"
    assert exp_fit["decay_residual_ratio"] == pytest.approx((1.0 - 0.999) / (1.0 - 0.983))
    assert MT.classify_decay(0.9740849259105656, 0.9223984349577856)["decay_kind"] == "exp"

    power_fit = MT.classify_decay(0.942, 0.986)
    assert power_fit["decay_kind"] == "power"
    assert power_fit["decay_residual_ratio"] == pytest.approx((1.0 - 0.986) / (1.0 - 0.942))


def test_stationarity_uses_tau_based_standard_error():
    x = np.array([0.0] * 50 + [1.0] * 50)
    drift, se_sigma, stationary, cycles = MT.stationarity(x, tau_s=1.0, dt_s=1.0)

    assert drift == pytest.approx(2.0)
    assert se_sigma == pytest.approx(2.0 * np.sqrt(1.0 / 50.0))
    assert stationary is False
    assert cycles == pytest.approx(100.0)


def test_acf_matches_direct_biased_formula():
    x = np.array([1.0, 2.0, 1.0, 0.0])
    y = x - x.mean()
    denom = np.dot(y, y)
    expected = np.array([
        1.0,
        np.dot(y[:-1], y[1:]) / denom,
        np.dot(y[:-2], y[2:]) / denom,
    ])
    assert np.allclose(MT.acf(x, max_lag=2), expected)


def test_analyse_caps_acf_by_physical_window_seconds():
    t = np.arange(100)
    rho = 0.8 + 0.01 * np.sin(t / 5.0)

    result = MT.analyse(
        rho,
        dt_s=0.002,
        warmup_frac=0.0,
        acf_window_s=0.006,
        decay_windows_s=(0.006,),
        verbose=False,
    )

    assert result["acf_max_lag"] == 3
    assert result["acf_max_time_s"] == pytest.approx(0.006)


def test_decay_shape_filters_by_physical_fit_window():
    lags = np.arange(200)
    a = np.exp(-lags / 20.0)

    assert MT.decay_shape(a, dt_s=1.0, fit_window_s=15.0) is None

    fit = MT.decay_shape(a, dt_s=1.0, fit_window_s=60.0)
    assert fit is not None
    assert fit["fit_lag_max_s"] <= 60.0
    assert fit["decay_fit_points"] >= 20


def test_read_trace_long_format_uses_median_dt(tmp_path):
    path = tmp_path / "rho_trace.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_index", "timestamp_s", "link", "rho", "dt_s"],
        )
        writer.writeheader()
        writer.writerow({"sample_index": 0, "timestamp_s": 0.01, "link": "uA", "rho": 0.8, "dt_s": 0.01})
        writer.writerow({"sample_index": 1, "timestamp_s": 0.02, "link": "uA", "rho": 0.9, "dt_s": 0.02})

    by_link, dt_s = MT.read_trace(str(path))
    assert by_link["uA"] == [0.8, 0.9]
    assert dt_s == pytest.approx(0.015)

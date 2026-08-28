import numpy as np
import pytest

from measurements import snr_decomposition as D


def test_best_lag_recovers_known_delay():
    rng = np.random.default_rng(123)
    offered = rng.standard_normal(500)
    measured = np.r_[np.zeros(7), offered[:-7]]
    got = D.best_lag(measured, offered)
    assert got["best_lag_samples"] == 7
    assert got["best_lag_s"] == pytest.approx(1.4)
    assert got["r_at_best_lag"] == pytest.approx(1.0)


def test_noisy_pair_count_partitions_six_margins():
    counts = [D.noisy_pairs_in_margin(*pair) for pair in D.PATH_PAIRS]
    assert sorted(counts) == [1, 1, 1, 1, 2, 2]


def test_ratio_sensitivity_exposes_near_zero_denominator():
    acc = {"R_num": [1.0, 2.0, 1000.0], "R_den": [1.0, 1.0, 1.0],
           "abs_E_measured": [1.0, 2.0, 1.0],
           "abs_E_offered": [1.0, 1.0, 0.001],
           "sd_measured": [1.0, 1.0, 1.0],
           "sd_offered": [1.0, 1.0, 1.0]}
    got = D.ratio_sensitivity(acc)
    assert got["abs_E_offered_denominator"]["min"] == 0.001
    assert got["R_num_median_of_ratio"]["median"] == 2.0
    assert got["R_num_ratio_of_medians"] == 1.0
    assert got["R_num_relative_difference_between_summaries"] == 0.5


def test_adjudication_prioritizes_time_alignment():
    summary = {"R_num_median_of_ratio": {"median": 1.2},
               "R_den_median_of_ratio": {"median": 0.8}}
    assert D.adjudicate(summary, 2) == "TIME_MISALIGNMENT_SUSPECTED"
    assert D.adjudicate(summary, 0) == "SD_COMPRESSION_CORRELATED_RESIDUAL"

#!/usr/bin/env python3
"""Tests for the calibrated Lesson 9.0 link model."""

import sys

import numpy as np

sys.path.insert(0, ".")

from rl.routing.link_model import (  # noqa: E402
    loss_rate,
    queue_ceiling_ms,
    queueing_delay_ms,
    rho_measured_from_offered,
)


def test_queueing_matches_measurement():
    """q_delay ~= base * rho on the measured q=13, bw=4 curve."""
    obs = [
        (0.108, 0.21),
        (0.324, 0.62),
        (0.539, 1.21),
        (0.755, 1.45),
        (0.917, 1.90),
        (0.971, 2.07),
    ]
    errs = [abs(queueing_delay_ms(2.0, rho) - measured) for rho, measured in obs]
    assert np.mean(errs) < 0.35


def test_mm1_would_have_been_wrong():
    rho = 0.971
    real = 2.07
    mm1 = 2.0 * rho / (1.0 - rho)
    new = queueing_delay_ms(2.0, rho)
    assert mm1 / real > 30.0
    assert abs(new - real) < 0.3


def test_queue_ceiling_law():
    for queue_pkts, measured_ms in [(4, 10.7), (5, 13.8), (13, 37.9)]:
        pred = queue_ceiling_ms(4.0, queue_pkts)
        assert abs(pred - measured_ms) / measured_ms < 0.13


def test_saturated_measured_rho_hits_finite_queue_ceiling():
    q_delay = queueing_delay_ms(2.0, 1.0, bw_mbps=4.0, queue_pkts=13)
    assert abs(q_delay - queue_ceiling_ms(4.0, 13)) < 1e-12


def test_loss_law():
    obs = [
        (0.90, 0.0001),
        (0.95, 0.0242),
        (1.00, 0.0731),
        (1.10, 0.1576),
        (1.30, 0.2873),
    ]
    for rho_offered, measured in obs:
        assert abs(loss_rate(rho_offered) - measured) < 0.005


def test_old_threshold_was_fabricated():
    assert loss_rate(0.85) == 0.0
    assert loss_rate(0.90) == 0.0
    assert loss_rate(0.95) > 0.02


def test_rho_cap_matches_ditto():
    assert rho_measured_from_offered(1.30) == 1.0
    assert rho_measured_from_offered(0.50) < 1.0


def _run_as_script():
    tests = [
        test_queueing_matches_measurement,
        test_mm1_would_have_been_wrong,
        test_queue_ceiling_law,
        test_saturated_measured_rho_hits_finite_queue_ceiling,
        test_loss_law,
        test_old_threshold_was_fabricated,
        test_rho_cap_matches_ditto,
    ]
    for test in tests:
        test()
        print("  PASS  %s" % test.__name__)
    print("\n%d/%d passed" % (len(tests), len(tests)))


if __name__ == "__main__":
    _run_as_script()

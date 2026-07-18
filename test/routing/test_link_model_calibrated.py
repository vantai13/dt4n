#!/usr/bin/env python3
"""Tests for the calibrated Lesson 9.0 link model."""

import sys

import numpy as np

sys.path.insert(0, ".")

from rl.routing.link_model import (  # noqa: E402
    CRITICAL_CEILING_FRACTION,
    CRITICAL_TO_FULL_RHO_OFFERED,
    LOW_TO_CRITICAL_RHO_OFFERED,
    MTU_BYTES,
    OFFERED_CLIFF,
    OVERHEAD_FACTOR,
    loss_rate,
    queue_ceiling_ms,
    queueing_delay_ms,
    rho_measured_from_offered,
)


def test_subthreshold_delay_matches_bdp_occupancy():
    """Subthreshold qdisc delay is BDP/netem occupancy, not M/M/1 buildup."""
    obs = [
        (0.108, 0.21),
        (0.324, 0.62),
        (0.539, 1.21),
        (0.755, 1.45),
        (0.917, 1.90),
        (0.971, 2.07),
    ]
    errs = [
        abs(queueing_delay_ms(2.0, rho_measured / OVERHEAD_FACTOR) - measured)
        for rho_measured, measured in obs
    ]
    assert np.mean(errs) < 0.35


def test_density_matrix_mean_packets_match_bdp():
    """The three density configs are explained by mean backlog packets ~= BDP."""
    # rho_measured, base_delay_ms, bw_mbps, observed_mean_packets
    obs = [
        (0.969, 2.0, 4.0, 0.61),
        (0.969, 3.0, 6.0, 1.52),
        (0.968, 1.5, 8.0, 0.96),
    ]
    errs = []
    for rho_measured, base_delay_ms, bw_mbps, mean_packets in obs:
        pkt_ms = MTU_BYTES * 8.0 / (bw_mbps * 1e6) * 1000.0
        bdp_packets = rho_measured * base_delay_ms / pkt_ms
        errs.append(abs(bdp_packets - mean_packets))
        qdisc_ms = mean_packets * pkt_ms
        assert abs(
            queueing_delay_ms(base_delay_ms, rho_measured / OVERHEAD_FACTOR)
            - qdisc_ms
        ) < 0.20
    assert np.mean(errs) < 0.06


def test_rev5_three_regimes_from_fine_density():
    ceiling = queue_ceiling_ms(4.0, 13)
    low = queueing_delay_ms(2.0, 0.925, bw_mbps=4.0, queue_pkts=13)
    critical = queueing_delay_ms(2.0, 0.930, bw_mbps=4.0, queue_pkts=13)
    full = queueing_delay_ms(2.0, 0.935, bw_mbps=4.0, queue_pkts=13)

    assert abs(LOW_TO_CRITICAL_RHO_OFFERED - 0.925) < 1e-12
    assert abs(CRITICAL_TO_FULL_RHO_OFFERED - 0.9325) < 1e-12
    assert abs(low - 2.0 * rho_measured_from_offered(0.925)) < 1e-12
    assert abs(critical - CRITICAL_CEILING_FRACTION * ceiling) < 1e-12
    assert abs(full - ceiling) < 1e-12
    assert critical / low > 10.0


def test_mm1_would_have_been_wrong():
    rho_measured = 0.971
    rho_offered = rho_measured / OVERHEAD_FACTOR
    real = 2.07
    mm1 = 2.0 * rho_measured / (1.0 - rho_measured)
    new = queueing_delay_ms(2.0, rho_offered)
    assert mm1 / real > 30.0
    assert abs(new - real) < 0.3


def test_queue_ceiling_law():
    for queue_pkts, measured_ms in [(4, 10.7), (5, 13.8), (13, 37.9)]:
        pred = queue_ceiling_ms(4.0, queue_pkts)
        assert abs(pred - measured_ms) / measured_ms < 0.15


def test_saturated_measured_rho_hits_finite_queue_ceiling():
    q_delay = queueing_delay_ms(2.0, 0.935, bw_mbps=4.0, queue_pkts=13)
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


def test_offered_cliff_matches_density_bracket():
    assert 0.925 < OFFERED_CLIFF < 0.950
    assert rho_measured_from_offered(0.925) < 1.0
    assert rho_measured_from_offered(0.950) == 1.0


def test_rho_cap_matches_ditto():
    assert rho_measured_from_offered(1.30) == 1.0
    assert rho_measured_from_offered(0.50) < 1.0


def _run_as_script():
    tests = [
        test_subthreshold_delay_matches_bdp_occupancy,
        test_density_matrix_mean_packets_match_bdp,
        test_rev5_three_regimes_from_fine_density,
        test_mm1_would_have_been_wrong,
        test_queue_ceiling_law,
        test_saturated_measured_rho_hits_finite_queue_ceiling,
        test_loss_law,
        test_old_threshold_was_fabricated,
        test_offered_cliff_matches_density_bracket,
        test_rho_cap_matches_ditto,
    ]
    for test in tests:
        test()
        print("  PASS  %s" % test.__name__)
    print("\n%d/%d passed" % (len(tests), len(tests)))


if __name__ == "__main__":
    _run_as_script()

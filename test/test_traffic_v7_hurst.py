#!/usr/bin/env python3
"""Regression tests for Phase 20/Phase T traffic provenance metrics."""

import pytest

from mininet.traffic_v7 import TrafficConfig


def test_hurst_uses_lrd_relation_only_for_infinite_variance_durations():
    assert TrafficConfig(cap_mbps=6.0, kappa=1.5).hurst == pytest.approx(0.75)


@pytest.mark.parametrize("kappa", [2.0, 2.5, 3.0])
def test_hurst_is_neutral_when_pareto_duration_variance_is_finite(kappa):
    assert TrafficConfig(cap_mbps=6.0, kappa=kappa).hurst == pytest.approx(0.5)

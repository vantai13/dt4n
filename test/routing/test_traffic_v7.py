#!/usr/bin/env python3
"""Pure tests for Phase 20 v7 traffic design math."""

import math
import random
import sys

import pytest

sys.path.insert(0, ".")

from mininet.traffic_v7 import TrafficConfig, pareto_size_bits, traffic_profile  # noqa: E402
from twin import topology_v7 as T7  # noqa: E402


def test_sigma_target_inverts_to_per_flow_rate():
    cfg = TrafficConfig(
        cap_mbps=6.0,
        rho_target=0.92,
        sigma_target=0.20,
        kappa=2.5,
        size_min_kb=20.0,
    )

    sigma = math.sqrt(cfg.rho_target * cfg.rate_bps / cfg.cap_bps)
    assert sigma == pytest.approx(0.20)
    assert cfg.n_concurrent == pytest.approx(cfg.rho_target**2 / 0.20**2)
    assert cfg.lam * cfg.mean_size_bits / cfg.cap_bps == pytest.approx(0.92)


def test_default_profile_uses_topology_load_means():
    profile = traffic_profile()
    assert tuple(profile) == T7.LINK_NAMES
    for link, cfg in profile.items():
        assert cfg.cap_mbps == pytest.approx(T7.LINKS[link][0])
        assert cfg.rho_target == pytest.approx(T7.LOAD_MEAN[link])


def test_profile_can_use_lower_edge_sigma():
    profile = traffic_profile(sigma_target=0.20, edge_sigma_target=0.05)
    for link, cfg in profile.items():
        if link in {"ac", "ad", "bc", "bd"}:
            assert cfg.sigma_target == pytest.approx(0.20)
        else:
            assert cfg.sigma_target == pytest.approx(0.05)


def test_pareto_sample_never_goes_below_minimum():
    cfg = TrafficConfig(cap_mbps=6.0, size_min_kb=20.0)
    rng = random.Random(123)
    values = [pareto_size_bits(cfg, rng) for _ in range(200)]
    assert min(values) >= cfg.size_min_bits

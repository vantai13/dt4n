#!/usr/bin/env python3
"""Tests for the single routing utilization definition."""

import sys

sys.path.insert(0, '.')

from rl.routing_2path.util_spec import (  # noqa: E402
    UTIL_MAX,
    utilization_from_ditto_link,
    utilization_from_rate,
)
from rl.routing_2path.route_env import RouteEnv  # noqa: E402
from rl.routing_2path.topology_r import TOPO  # noqa: E402


def test_bytes_per_second_to_mbps_capacity():
    assert utilization_from_rate(500_000, 4) == 1.0
    assert utilization_from_rate(250_000, 4) == 0.5


def test_utilization_clamps_to_deployable_range():
    assert utilization_from_rate(10_000_000, 4) == UTIL_MAX
    assert utilization_from_rate(-1, 4) == 0.0
    assert utilization_from_rate(500_000, 0) == 0.0


def test_ditto_link_nested_properties():
    thing = {
        'features': {
            'traffic': {'properties': {'txRate': 250_000, 'rxRate': 1}},
            'capacity': {'properties': {'bwMbps': 4}},
        },
    }
    assert utilization_from_ditto_link(thing) == 0.5


def test_ditto_link_flat_collector_shape():
    thing = {
        'features': {
            'traffic': {'txRate': 250_000, 'rxRate': 1},
            'capacity': {'bwMbps': 4},
        },
    }
    assert utilization_from_ditto_link(thing) == 0.5


def test_route_env_never_samples_non_deployable_utilization():
    env = RouteEnv(
        TOPO,
        load_cfg={
            'base_load': (0.9, 1.3),
            'e_load': (1.1, 1.4),
            'drift_sigma': 0.5,
        },
        seed=0,
    )
    _obs, info = env.reset(seed=1)
    assert max(info['rho_snapshot'].values()) <= UTIL_MAX
    for _ in range(5):
        valid = [idx for idx, ok in enumerate(info['valid_mask']) if ok]
        _obs, _reward, terminated, truncated, info = env.step(valid[0])
        assert max(info['rho_snapshot'].values()) <= UTIL_MAX
        if terminated or truncated:
            break


def _run_as_script():
    tests = [
        test_bytes_per_second_to_mbps_capacity,
        test_utilization_clamps_to_deployable_range,
        test_ditto_link_nested_properties,
        test_ditto_link_flat_collector_shape,
        test_route_env_never_samples_non_deployable_utilization,
    ]
    for test in tests:
        test()
        print('  PASS  %s' % test.__name__)
    print('\n%d/%d passed' % (len(tests), len(tests)))


if __name__ == '__main__':
    _run_as_script()

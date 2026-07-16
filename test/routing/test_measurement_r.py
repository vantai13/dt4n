#!/usr/bin/env python3
"""Tests for the Lesson 8.4 measurement instruments."""

import sys

sys.path.insert(0, '.')

from rl.routing.baselines import ospf_calibrated, ospf_reactive
from rl.routing.metrics_r import evaluate_z
from rl.routing.oracles import (
    blind_dijkstra,
    clairvoyant_dijkstra,
    dijkstra_next_hop,
    posthoc_dijkstra,
)
from rl.routing.route_env import RouteEnv
from rl.routing.topology_r import TOPO


def test_dijkstra_flips_at_c_under_reward_v2():
    env = RouteEnv(TOPO, seed=0)
    env.reset(seed=0)
    env.current = 'C'

    low = dict(env._rho)
    low[('C', 'E')] = 0.60
    low[('C', 'F')] = 0.30
    assert dijkstra_next_hop(env, low) == 'E'

    high = dict(env._rho)
    high[('C', 'E')] = 0.90
    high[('C', 'F')] = 0.30
    assert dijkstra_next_hop(env, high) == 'F'


def test_blind_equals_clairvoyant_when_observed_is_true():
    env = RouteEnv(TOPO, seed=0)
    _obs, info = env.reset(seed=0)
    info['rho_snapshot_observed'] = dict(info['rho_snapshot'])
    assert blind_dijkstra(env, info) == clairvoyant_dijkstra(env, info)


def test_ospf_ignores_observed_snapshot():
    env = RouteEnv(TOPO, seed=0)
    _obs, info = env.reset(seed=0)
    action_1 = ospf_reactive(env, dict(info, rho_snapshot_observed={}))
    fake_obs = {link: 0.97 for link in info['rho_snapshot']}
    action_2 = ospf_reactive(env, dict(info, rho_snapshot_observed=fake_obs))
    assert action_1 == action_2


def test_ospf_calibrated_is_twin_free_and_not_strawman_at_c():
    env = RouteEnv(TOPO, load_cfg={'e_load': (0.80, 0.97)}, seed=0)
    _obs, info = env.reset(seed=0)
    env.current = 'C'
    info = dict(info, current_node='C')

    straw = ospf_reactive(env, info)
    calibrated = ospf_calibrated(env, dict(info, rho_snapshot_observed={}))
    assert env.adj['C'][straw] == 'E'
    assert env.adj['C'][calibrated] == 'F'


def test_peek_next_rho_does_not_advance_rng():
    env_a = RouteEnv(TOPO, seed=0)
    env_b = RouteEnv(TOPO, seed=0)
    env_a.reset(seed=12)
    env_b.reset(seed=12)
    _ = env_a.peek_next_rho()
    env_a.step(0)
    env_b.step(0)
    assert env_a._rho == env_b._rho


def test_posthoc_dijkstra_is_available():
    env = RouteEnv(TOPO, seed=0)
    _obs, info = env.reset(seed=0)
    action = posthoc_dijkstra(env, info)
    assert action in (0, 1)


def test_evaluate_z_schema_smoke():
    row = evaluate_z(0, seeds=range(3))
    for key in [
        'clair_return',
        'blind_return',
        'ospf_return',
        'cost_of_blindness',
        'wrong_excess',
        'voi_headroom',
    ]:
        assert key in row
    assert row['cost_of_blindness'] == 0.0


def _run_as_script():
    tests = [
        test_dijkstra_flips_at_c_under_reward_v2,
        test_blind_equals_clairvoyant_when_observed_is_true,
        test_ospf_ignores_observed_snapshot,
        test_ospf_calibrated_is_twin_free_and_not_strawman_at_c,
        test_peek_next_rho_does_not_advance_rng,
        test_posthoc_dijkstra_is_available,
        test_evaluate_z_schema_smoke,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f'  PASS  {test.__name__}')
    print(f'\n{passed}/{len(tests)} passed')


if __name__ == '__main__':
    _run_as_script()

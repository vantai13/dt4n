#!/usr/bin/env python3
"""Tests for the Lesson 8.4 measurement instruments."""

import sys

sys.path.insert(0, '.')

from rl.routing.baselines import expected_ospf_weights, ospf_calibrated, ospf_reactive
from rl.routing.metrics_r import evaluate_z
from rl.routing.oracles import (
    blind_dijkstra,
    clairvoyant_dijkstra,
    dijkstra_next_hop,
    posthoc_dijkstra,
)
from rl.routing.route_env import RouteEnv
from rl.routing.topology_r import TOPO
from rl.routing.link_model import loss_rate, rho_measured_from_offered


def _view_from_offered(offered):
    rho = {
        link: rho_measured_from_offered(value)
        for link, value in offered.items()
    }
    loss = {
        link: loss_rate(value)
        for link, value in offered.items()
    }
    return rho, loss


def test_dijkstra_flips_at_c_on_measured_queue_cliff():
    env = RouteEnv(TOPO, seed=0)
    env.reset(seed=0)
    env.current = 'C'

    low_offered = dict(env._rho_offered)
    low_offered[('C', 'E')] = 0.70
    low_offered[('C', 'F')] = 0.30
    rho, loss = _view_from_offered(low_offered)
    assert dijkstra_next_hop(env, rho, loss_view=loss) == 'E'

    high_offered = dict(env._rho_offered)
    high_offered[('C', 'E')] = 0.95
    high_offered[('C', 'F')] = 0.30
    rho, loss = _view_from_offered(high_offered)
    assert dijkstra_next_hop(env, rho, loss_view=loss) == 'F'


def test_blind_equals_clairvoyant_when_observed_is_true():
    env = RouteEnv(TOPO, seed=0)
    _obs, info = env.reset(seed=0)
    info['rho_snapshot_observed'] = dict(info['rho_snapshot'])
    info['loss_snapshot_observed'] = dict(info['loss_snapshot'])
    assert blind_dijkstra(env, info) == clairvoyant_dijkstra(env, info)


def test_ospf_ignores_observed_snapshot():
    env = RouteEnv(TOPO, seed=0)
    _obs, info = env.reset(seed=0)
    action_1 = ospf_reactive(env, dict(info, rho_snapshot_observed={}))
    fake_obs = {link: 0.97 for link in info['rho_snapshot']}
    action_2 = ospf_reactive(env, dict(info, rho_snapshot_observed=fake_obs))
    assert action_1 == action_2


def test_ospf_calibrated_uses_expected_link_cost_at_c():
    env = RouteEnv(
        TOPO,
        load_cfg={
            'base_load': (0.75, 0.95),
            'e_load': (0.70, 1.00),
        },
        seed=0,
    )
    _obs, info = env.reset(seed=0)
    env.current = 'C'
    info = dict(info, current_node='C')

    straw = ospf_reactive(env, info)
    calibrated = ospf_calibrated(env, dict(info, rho_snapshot_observed={}))
    weights = expected_ospf_weights(env)

    assert env.adj['C'][straw] == 'E'
    assert env.adj['C'][calibrated] == 'F'
    assert weights[('C', 'E')] + weights[('E', 'F')] > weights[('C', 'F')]


def test_ospf_expected_weights_fail_loud_without_queue_metadata():
    env = RouteEnv(TOPO, seed=0)
    env.reset(seed=0)
    del env.link[('C', 'E')]['queue_pkts']
    try:
        expected_ospf_weights(env)
    except KeyError as exc:
        assert exc.args[0] == 'queue_pkts'
    else:
        raise AssertionError('missing queue_pkts should fail loudly')


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
        test_dijkstra_flips_at_c_on_measured_queue_cliff,
        test_blind_equals_clairvoyant_when_observed_is_true,
        test_ospf_ignores_observed_snapshot,
        test_ospf_calibrated_uses_expected_link_cost_at_c,
        test_ospf_expected_weights_fail_loud_without_queue_metadata,
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

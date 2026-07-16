#!/usr/bin/env python3
"""Tests for Ditto sync-period staleness."""

import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.ditto_staleness_r import DittoStalenessWrapper
from rl.routing.metrics_r import evaluate_sync_period
from rl.routing.route_env import RouteEnv
from rl.routing.state_r import AOI_DIMS
from rl.routing.topology_r import TOPO


def _rollout(env, seed, actions):
    obs, info = env.reset(seed=seed)
    trace = [(obs.copy(), None, dict(info))]
    for action in actions:
        obs, reward, terminated, truncated, info = env.step(action)
        trace.append((obs.copy(), reward, dict(info)))
        if terminated or truncated:
            break
    return trace


def test_reset_uses_sync_phase_as_initial_aoi():
    env = DittoStalenessWrapper(
        RouteEnv(TOPO, seed=0),
        sync_period_s=0.5,
        phase_s=0.25,
    )
    obs, info = env.reset(seed=1)

    assert info['sync_period_s'] == 0.5
    assert info['phase_s'] == 0.25
    assert info['last_sync_time_s'] == -0.25
    assert info['aoi_measured_s'] == 0.25 + env.aoi_floor_s
    assert obs[AOI_DIMS[0]] > 0.0


def test_aoi_advances_by_physical_time_before_next_sync():
    env = DittoStalenessWrapper(
        RouteEnv(TOPO, seed=0),
        sync_period_s=10.0,
        phase_s=0.25,
    )
    _obs, _info0 = env.reset(seed=2)
    _obs, _reward, _terminated, _truncated, info1 = env.step(0)

    expected = env.aoi_floor_s + 0.25 + info1['link_delay_ms'] / 1000.0
    assert abs(info1['aoi_measured_s'] - expected) < 1e-12


def test_fast_sync_refreshes_observed_snapshot():
    env = DittoStalenessWrapper(
        RouteEnv(TOPO, seed=0),
        sync_period_s=0.001,
        phase_s=0.0,
    )
    _obs, _info0 = env.reset(seed=3)
    _obs, _reward, _terminated, _truncated, info1 = env.step(0)

    assert info1['last_sync_time_s'] >= 0.001
    assert env.aoi_floor_s <= info1['aoi_measured_s']
    assert info1['aoi_measured_s'] < env.aoi_floor_s + info1['sync_period_s']
    assert info1['rho_snapshot_observed'] == info1['rho_snapshot']


def test_reward_invariance_to_sync_period():
    actions = [0, 0, 0, 0]
    rewards_by_period = {}
    for period in (0.01, 0.5, 5.0):
        env = DittoStalenessWrapper(
            RouteEnv(TOPO, seed=0),
            sync_period_s=period,
            phase_s=0.0,
        )
        rewards_by_period[period] = [
            reward for (_obs, reward, _info) in _rollout(env, 11, actions)
            if reward is not None
        ]
    assert rewards_by_period[0.01] == rewards_by_period[0.5]
    assert rewards_by_period[0.5] == rewards_by_period[5.0]


def test_mask_only_touches_aoi_dims():
    env_visible = DittoStalenessWrapper(
        RouteEnv(TOPO, seed=0),
        sync_period_s=0.5,
        phase_s=0.25,
        mask_aoi_dims=False,
    )
    env_masked = DittoStalenessWrapper(
        RouteEnv(TOPO, seed=0),
        sync_period_s=0.5,
        phase_s=0.25,
        mask_aoi_dims=True,
    )
    obs_visible, _info = env_visible.reset(seed=3)
    obs_masked, _info = env_masked.reset(seed=3)
    diff = set(np.flatnonzero(obs_visible != obs_masked).tolist())
    assert diff <= set(AOI_DIMS)


def test_evaluate_sync_period_schema_smoke():
    row = evaluate_sync_period(0.5, seeds=range(3))
    for key in [
        'sync_period_s',
        'clair_return',
        'blind_return',
        'ospf_return',
        'cost_of_blindness',
        'wrong_excess',
        'voi_headroom',
        'blind_stale_steps',
    ]:
        assert key in row
    assert row['sync_period_s'] == 0.5


def _run_as_script():
    tests = [
        test_reset_uses_sync_phase_as_initial_aoi,
        test_aoi_advances_by_physical_time_before_next_sync,
        test_fast_sync_refreshes_observed_snapshot,
        test_reward_invariance_to_sync_period,
        test_mask_only_touches_aoi_dims,
        test_evaluate_sync_period_schema_smoke,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f'  PASS  {test.__name__}')
    print(f'\n{passed}/{len(tests)} passed')


if __name__ == '__main__':
    _run_as_script()

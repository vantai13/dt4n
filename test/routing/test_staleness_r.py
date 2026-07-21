#!/usr/bin/env python3
"""Tests for RouteEnv observation staleness."""

import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.state_r import AOI_DIMS
from rl.routing.topology_r import OFFERED_LOAD_MIN, SCENARIOS_DYNAMIC, TOPO


def _rollout(env, seed, actions):
    obs, info = env.reset(seed=seed)
    trace = [(obs.copy(), None, dict(info))]
    for action in actions:
        obs, reward, terminated, truncated, info = env.step(action)
        trace.append((obs.copy(), reward, dict(info)))
        if terminated or truncated:
            break
    return trace


def test_zero_divergence():
    bare = RouteEnv(TOPO, seed=0)
    wrapped = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(0,))
    actions = [0, 0, 0, 0]
    t_bare = _rollout(bare, 7, actions)
    t_wrapped = _rollout(wrapped, 7, actions)

    assert len(t_bare) == len(t_wrapped)
    for idx, ((obs_b, reward_b, _info_b),
              (obs_w, reward_w, _info_w)) in enumerate(zip(t_bare, t_wrapped)):
        diff = np.abs(obs_b - obs_w).max()
        assert diff == 0.0, f'step {idx}: obs differs by {diff} at z=0'
        if reward_b is not None:
            assert reward_b == reward_w, f'step {idx}: reward differs at z=0'


def test_reward_invariance_to_z():
    actions = [0, 0, 0, 0]
    rewards_by_z = {}
    for z in (0, 2, 5):
        env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(z,))
        rewards_by_z[z] = [
            reward for (_obs, reward, _info) in _rollout(env, 11, actions)
            if reward is not None
        ]
    assert rewards_by_z[0] == rewards_by_z[2] == rewards_by_z[5]


def test_staleness_is_alive():
    env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(3,))
    trace = _rollout(env, 5, [0, 0, 0, 0])
    stale_steps = sum(1 for (_obs, _reward, info) in trace
                      if info.get('util_is_stale'))
    assert stale_steps >= 2
    assert trace[-1][2]['aoi_measured_s'] > 0.0


def test_aoi_uses_simulated_time():
    env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(3,))
    _obs, info = env.reset(seed=5)
    assert info['aoi_measured_s'] == 3 * RouteEnv.STEP_DURATION_S


def test_history_is_copied_not_referenced():
    env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(3,))
    env.reset(seed=1)
    for _ in range(3):
        env.step(0)
    snapshots = [snap for (_ts, _offered, snap, _loss_snap) in env._hist]
    assert len(snapshots) >= 2
    assert snapshots[0] is not snapshots[-1]
    diffs = [link for link in snapshots[0]
             if snapshots[0][link] != snapshots[-1][link]]
    assert diffs


def test_warmup_timestamps_are_oldest_first():
    env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(3,))
    env.reset(seed=1)
    times = [ts for (ts, _offered, _snap, _loss_snap) in env._hist]
    assert times == sorted(times)
    assert times[-1] == 0.0


def test_warmup_past_is_shared_across_z_for_same_seed():
    e3 = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(3,))
    e5 = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(5,))
    e3.reset(seed=7)
    e5.reset(seed=7)

    by_time3 = {
        ts: (offered, snap, loss_snap)
        for ts, offered, snap, loss_snap in e3._hist
    }
    by_time5 = {
        ts: (offered, snap, loss_snap)
        for ts, offered, snap, loss_snap in e5._hist
    }
    common_times = set(by_time3) & set(by_time5)
    assert common_times
    for ts in common_times:
        assert by_time3[ts] == by_time5[ts]


def test_mask_only_touches_aoi_dims():
    env_visible = StalenessWrapper(
        RouteEnv(TOPO, seed=0), z_steps_choices=(3,), mask_aoi_dims=False)
    env_masked = StalenessWrapper(
        RouteEnv(TOPO, seed=0), z_steps_choices=(3,), mask_aoi_dims=True)
    obs_visible, _info = env_visible.reset(seed=3)
    obs_masked, _info = env_masked.reset(seed=3)
    diff = set(np.flatnonzero(obs_visible != obs_masked).tolist())
    assert diff <= set(AOI_DIMS)


def test_z_is_deterministic_from_seed():
    zs = []
    for _ in range(2):
        env = StalenessWrapper(
            RouteEnv(TOPO, seed=0), z_steps_choices=(0, 1, 3, 5))
        env.reset(seed=123)
        zs.append(env._z_steps)
    assert zs[0] == zs[1]


def test_observed_utils_belong_to_current_node():
    env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(2,))
    _obs, _info = env.reset(seed=2)
    _obs, _reward, _terminated, _truncated, _info = env.step(0)
    _obs, _reward, _terminated, _truncated, info = env.step(0)

    assert info['current_node'] == 'C'
    snap_seen_by_agent = info['rho_snapshot_observed']
    expected = [snap_seen_by_agent[('C', 'E')],
                snap_seen_by_agent[('C', 'F')]]
    assert info['neighbor_utils_observed'] == expected

    loss_seen_by_agent = info['loss_snapshot_observed']
    expected_loss = [loss_seen_by_agent[('C', 'E')],
                     loss_seen_by_agent[('C', 'F')]]
    assert info['neighbor_losses_observed'] == expected_loss

    offered_seen_by_oracle = info['rho_offered_snapshot_observed']
    assert set(snap_seen_by_agent) == set(offered_seen_by_oracle)


def test_fixed_z_reaches_decision_node_with_matching_aoi():
    for z in (0, 2, 4, 6):
        env = StalenessWrapper(RouteEnv(TOPO, seed=0), z_steps_choices=(z,))
        obs, info = env.reset(seed=9)
        obs, _reward, _terminated, _truncated, info = env.step(0)
        obs, _reward, _terminated, _truncated, info = env.step(0)

        expected_aoi_s = z * RouteEnv.STEP_DURATION_S
        assert info['current_node'] == 'C'
        assert info['z_steps'] == z
        assert info['aoi_measured_s'] == expected_aoi_s
        assert np.isclose(obs[AOI_DIMS[0]], min(expected_aoi_s / 6.0, 1.0))


def test_warmup_uses_normal_offered_load_floor():
    load_cfg = {
        'scenarios': {'S5_E_rising': SCENARIOS_DYNAMIC['S5_E_rising']},
        'scenario_mix': ('S5_E_rising',),
    }
    env = StalenessWrapper(
        RouteEnv(TOPO, load_cfg=load_cfg, seed=0),
        z_steps_choices=(6,),
    )
    _obs, _info = env.reset(seed=42)
    _obs, _reward, _terminated, _truncated, _info = env.step(0)
    _obs, _reward, _terminated, _truncated, info = env.step(0)

    assert info['current_node'] == 'C'
    assert min(info['rho_offered_snapshot_observed'].values()) >= OFFERED_LOAD_MIN


def _run_as_script():
    tests = [
        test_zero_divergence,
        test_reward_invariance_to_z,
        test_staleness_is_alive,
        test_aoi_uses_simulated_time,
        test_history_is_copied_not_referenced,
        test_warmup_timestamps_are_oldest_first,
        test_warmup_past_is_shared_across_z_for_same_seed,
        test_mask_only_touches_aoi_dims,
        test_z_is_deterministic_from_seed,
        test_observed_utils_belong_to_current_node,
        test_fixed_z_reaches_decision_node_with_matching_aoi,
        test_warmup_uses_normal_offered_load_floor,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f'  PASS  {test.__name__}')
    print(f'\n{passed}/{len(tests)} passed')


if __name__ == '__main__':
    _run_as_script()

#!/usr/bin/env python3
"""Tests for the minimal RouteEnv stage."""

import re
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.link_model import (
    CRITICAL_TO_FULL_RHO_OFFERED,
    LOW_TO_CRITICAL_RHO_OFFERED,
    loss_rate,
    total_delay_ms,
)
from rl.routing.reward_r import step_reward
from rl.routing.route_env import RouteEnv
from rl.routing.state_r import (
    AOI_DIMS,
    AOI_NORM_DIVISOR_S,
    R_STATE_DIM,
    aoi_features,
    build_route_state,
    mask_aoi,
)
from rl.routing.topology_r import (
    BUSY_LOAD,
    DIRECT_F_LINKS,
    DYNAMIC_TREND_RANGE,
    FREE_LOAD,
    LOAD_PRESETS,
    NEAR_CLIFF_LOAD,
    OFFERED_LOAD_MIN,
    SAFE_LOAD,
    SCENARIOS,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
    TRAIN_SCENARIO_MIX,
    VIA_E_LINKS,
)


def _base_delay(topo, src, dst):
    for edge_src, edge_dst, delay_ms, _bw_mbps in topo['edges']:
        if edge_src == src and edge_dst == dst:
            return float(delay_ms)
    raise KeyError((src, dst))


def test_dim():
    state = build_route_state(0, 8, 0, 15, [0.3, 0.4], [1, 1], aoi_s=0.0)
    assert state.shape == (R_STATE_DIM,)
    assert R_STATE_DIM == 9
    assert R_STATE_DIM <= 16


def test_topology_v2_link_budget_and_degree():
    bws = [float(edge[3]) for edge in TOPO['edges']]
    assert min(bws) == 4.0
    assert max(bws) == 8.0

    degree = {node: 0 for node in TOPO['nodes']}
    for src, _dst, _delay, _bw in TOPO['edges']:
        degree[src] += 1
    assert max(degree.values()) <= 2
    assert TOPO['default_queue_pkts'] == 13
    assert _base_delay(TOPO, 'C', 'F') == 6.0
    assert _base_delay(TOPO, 'D', 'F') == 6.0


def test_load_scenarios_pinch_decision_links_independently():
    assert set(TRAIN_SCENARIO_MIX) == set(SCENARIOS_TRAIN)
    assert SCENARIOS_TRAIN['S1_viaE_better']['e_load'] == FREE_LOAD
    assert SCENARIOS_TRAIN['S1_viaE_better']['f_load'] == BUSY_LOAD
    assert SCENARIOS_TRAIN['S2_direct_better']['e_load'] == BUSY_LOAD
    assert SCENARIOS_TRAIN['S2_direct_better']['f_load'] == FREE_LOAD
    assert FREE_LOAD[1] < LOW_TO_CRITICAL_RHO_OFFERED
    assert BUSY_LOAD[0] > CRITICAL_TO_FULL_RHO_OFFERED
    assert VIA_E_LINKS == (('C', 'E'), ('D', 'E'))
    assert DIRECT_F_LINKS == (('C', 'F'), ('D', 'F'))
    assert SCENARIOS['S1_via_E_free']['direct_load'] == BUSY_LOAD
    assert LOAD_PRESETS['normal'] == SCENARIOS['S3_both_free']
    assert LOAD_PRESETS['bottleneck_E'] == SCENARIOS['S2_direct_F_free']
    assert LOAD_PRESETS['S1_viaE_better'] == SCENARIOS_TRAIN['S1_viaE_better']
    assert LOAD_PRESETS['borderline']['e_load'][0] <= LOW_TO_CRITICAL_RHO_OFFERED
    assert LOAD_PRESETS['borderline']['e_load'][1] >= CRITICAL_TO_FULL_RHO_OFFERED


def test_mask_touches_only_aoi():
    state = build_route_state(3, 8, 5, 15, [0.7, 0.2], [1, 1], aoi_s=3.0)
    masked = mask_aoi(state)
    diff = np.flatnonzero(state != masked)
    assert set(diff.tolist()) <= set(AOI_DIMS)
    assert all(masked[dim] == 0.0 for dim in AOI_DIMS)


def test_mask_does_not_mutate():
    state = build_route_state(3, 8, 5, 15, [0.7, 0.2], [1, 1], aoi_s=3.0)
    before = state.copy()
    _ = mask_aoi(state)
    assert np.array_equal(state, before)


def test_aoi_norm_not_saturated_in_range():
    max_aoi_in_sweep = 5.0
    a3, _ = aoi_features(3.0)
    a5, _ = aoi_features(max_aoi_in_sweep)
    assert a3 != a5
    assert AOI_NORM_DIVISOR_S >= max_aoi_in_sweep


def test_calibrated_delay_has_rev5_cliff_and_finite_ceiling():
    prev = -1.0
    for rho in [0.3, 0.5, 0.7, 0.9, 0.925, 0.930, 0.935, 0.95]:
        delay = total_delay_ms(2.0, rho, bw_mbps=4.0, queue_pkts=13)
        assert delay >= prev
        prev = delay
    assert (total_delay_ms(2.0, 0.930, bw_mbps=4.0, queue_pkts=13) - 2.0) > (
        10.0 * (total_delay_ms(2.0, 0.925, bw_mbps=4.0, queue_pkts=13) - 2.0)
    )
    assert total_delay_ms(2.0, 1.30, bw_mbps=4.0, queue_pkts=13) < 42.0


def _link_reward(topo, src, dst, rho_offered):
    env = RouteEnv(topo, seed=0)
    link = env.link[(src, dst)]
    delay = total_delay_ms(
        link['base_delay'],
        rho_offered,
        bw_mbps=link.get('base_bw'),
        queue_pkts=link.get('queue_pkts'),
    )
    return step_reward(delay, loss_rate(rho_offered)).total


def test_topology_v2_flips_on_measured_queue_cliff_at_c():
    base_ce = _base_delay(TOPO, 'C', 'E')
    base_cf = _base_delay(TOPO, 'C', 'F')
    assert base_ce < base_cf

    r_f = _link_reward(TOPO, 'C', 'F', 0.30)
    r_e_low = _link_reward(TOPO, 'C', 'E', 0.70)
    r_e_high = _link_reward(TOPO, 'C', 'E', 0.95)

    assert r_e_low > r_f
    assert r_e_high < r_f


def test_route_env_splits_offered_measured_and_loss():
    env = RouteEnv(
        TOPO,
        load_cfg={
            'base_load': (0.25, 0.25),
            'e_load': (1.30, 1.30),
            'drift_sigma': 0.0,
        },
        seed=0,
    )
    _obs, info = env.reset(seed=0)

    offered = info['rho_offered_snapshot'][('C', 'E')]
    measured = info['rho_snapshot'][('C', 'E')]
    loss = info['loss_snapshot'][('C', 'E')]

    assert offered == 1.30
    assert measured == 1.0
    assert loss > 0.25


def test_route_env_samples_direct_load_separately_from_via_e():
    env = RouteEnv(
        TOPO,
        load_cfg={
            'base_load': (0.25, 0.25),
            'e_load': (0.40, 0.40),
            'direct_load': (1.10, 1.10),
            'drift_sigma': 0.0,
        },
        seed=0,
    )
    _obs, info = env.reset(seed=0)
    offered = info['rho_offered_snapshot']

    assert offered[('C', 'E')] == 0.40
    assert offered[('D', 'E')] == 0.40
    assert offered[('C', 'F')] == 1.10
    assert offered[('D', 'F')] == 1.10
    assert offered[('E', 'F')] == 0.25


def test_route_env_accepts_f_load_alias_for_direct_path():
    env = RouteEnv(
        TOPO,
        load_cfg={
            'base_load': (0.25, 0.25),
            'e_load': (0.40, 0.40),
            'f_load': (1.10, 1.10),
            'drift_sigma': 0.0,
        },
        seed=0,
    )
    _obs, info = env.reset(seed=0)
    offered = info['rho_offered_snapshot']

    assert offered[('C', 'E')] == 0.40
    assert offered[('D', 'E')] == 0.40
    assert offered[('C', 'F')] == 1.10
    assert offered[('D', 'F')] == 1.10


def test_route_env_applies_directed_dynamic_trends_to_decision_links():
    assert SCENARIOS_DYNAMIC['S5_E_rising']['e_trend_range'] == DYNAMIC_TREND_RANGE
    assert SCENARIOS_DYNAMIC['S5_E_rising']['f_trend'] == 0.0
    assert SCENARIOS_DYNAMIC['S6_F_rising']['e_trend'] == 0.0
    assert SCENARIOS_DYNAMIC['S6_F_rising']['f_trend_range'] == DYNAMIC_TREND_RANGE
    assert SCENARIOS_DYNAMIC['S5_E_rising']['e_load'] == NEAR_CLIFF_LOAD
    assert SCENARIOS_DYNAMIC['S6_F_rising']['f_load'] == NEAR_CLIFF_LOAD
    assert SCENARIOS_DYNAMIC['S5_E_rising']['f_load'] == SAFE_LOAD
    assert SCENARIOS_DYNAMIC['S6_F_rising']['e_load'] == SAFE_LOAD
    assert SCENARIOS_DYNAMIC['S5_E_rising']['offered_load_max'] == 1.60
    assert SCENARIOS_DYNAMIC['S6_F_rising']['offered_load_max'] == 1.60

    load_cfg = {
        'scenarios': {
            'trend_probe': {
                'base_load': (0.30, 0.30),
                'e_load': (0.40, 0.40),
                'f_load': (0.50, 0.50),
                'e_trend': 0.10,
                'f_trend': 0.20,
                'drift_sigma': 0.0,
            },
        },
        'scenario_mix': ('trend_probe',),
    }
    env = RouteEnv(TOPO, load_cfg=load_cfg, seed=0)
    env.reset(seed=0)
    before = dict(env._rho_offered)
    env._drift()

    assert np.isclose(env._rho_offered[('C', 'E')], before[('C', 'E')] + 0.10)
    assert np.isclose(env._rho_offered[('D', 'E')], before[('D', 'E')] + 0.10)
    assert np.isclose(env._rho_offered[('C', 'F')], before[('C', 'F')] + 0.20)
    assert np.isclose(env._rho_offered[('D', 'F')], before[('D', 'F')] + 0.20)
    assert np.isclose(env._rho_offered[('E', 'F')], before[('E', 'F')])


def test_route_env_samples_episode_trend_from_range():
    load_cfg = {
        'scenarios': {
            'trend_range_probe': {
                'base_load': (0.30, 0.30),
                'e_load': (0.90, 0.90),
                'f_load': (0.30, 0.30),
                'e_trend_range': (0.05, 0.30),
                'f_trend': 0.0,
                'drift_sigma': 0.0,
            },
        },
        'scenario_mix': ('trend_range_probe',),
    }
    env0 = RouteEnv(TOPO, load_cfg=load_cfg, seed=0)
    env1 = RouteEnv(TOPO, load_cfg=load_cfg, seed=1)
    env0.reset(seed=0)
    env1.reset(seed=1)

    t0 = env0._active_load_cfg['e_trend']
    t1 = env1._active_load_cfg['e_trend']
    assert 0.05 <= t0 <= 0.30
    assert 0.05 <= t1 <= 0.30
    assert t0 != t1
    assert np.isclose(env0._drift_trend(('C', 'E')), t0)


def test_route_env_uses_normal_floor_for_drift():
    load_cfg = {
        'scenarios': {
            'floor_probe': {
                'base_load': (0.30, 0.30),
                'e_load': (0.20, 0.20),
                'f_load': (0.20, 0.20),
                'e_trend': -1.0,
                'f_trend': -1.0,
                'drift_sigma': 0.0,
            },
        },
        'scenario_mix': ('floor_probe',),
    }
    env = RouteEnv(TOPO, load_cfg=load_cfg, seed=0)
    env.reset(seed=0)
    env._drift()

    assert env._rho_offered[('C', 'E')] == OFFERED_LOAD_MIN
    assert env._rho_offered[('C', 'F')] == OFFERED_LOAD_MIN


def test_route_env_uses_active_scenario_offered_load_cap_for_drift():
    load_cfg = {
        'scenarios': {
            'cap_probe': {
                'base_load': (0.30, 0.30),
                'e_load': (0.90, 0.90),
                'f_load': (0.20, 0.20),
                'e_trend': 1.0,
                'f_trend': 0.0,
                'drift_sigma': 0.0,
                'offered_load_max': 1.60,
            },
        },
        'scenario_mix': ('cap_probe',),
    }
    env = RouteEnv(TOPO, load_cfg=load_cfg, seed=0)
    env.reset(seed=0)
    env._drift()

    assert env._rho_offered[('C', 'E')] == 1.60
    assert env._rho_offered[('D', 'E')] == 1.60


def test_terminated_is_real():
    env = RouteEnv(TOPO, seed=0)
    _obs, info = env.reset(seed=0)
    terminated = False
    truncated = False
    for _ in range(20):
        valid = np.flatnonzero(info['valid_mask'])
        action = int(valid[0])
        _obs, _reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    assert terminated
    assert not truncated
    assert info['arrived']
    assert info['current_node'] == TOPO['destination']


def test_sim_time_advances_by_physical_link_delay():
    env = RouteEnv(TOPO, seed=0)
    _obs, info0 = env.reset(seed=0)
    assert info0['sim_time_s'] == 0.0

    _obs, _reward, _terminated, _truncated, info1 = env.step(0)
    expected = info1['link_delay_ms'] / 1000.0
    assert abs(info1['sim_time_s'] - expected) < 1e-12


def test_no_staleness_code_in_env():
    with open('rl/routing/route_env.py', encoding='utf-8') as fh:
        src = fh.read()
    code_lines = [
        line for line in src.splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]
    body_no_docstrings = re.sub(r'"""[\s\S]*?"""', '', '\n'.join(code_lines))
    for bad in ['deque(', 'z_steps', '_hist', 'monotonic()']:
        assert bad not in body_no_docstrings


def _run_as_script():
    tests = [
        test_aoi_norm_not_saturated_in_range,
        test_dim,
        test_load_scenarios_pinch_decision_links_independently,
        test_mask_does_not_mutate,
        test_mask_touches_only_aoi,
        test_calibrated_delay_has_rev5_cliff_and_finite_ceiling,
        test_no_staleness_code_in_env,
        test_sim_time_advances_by_physical_link_delay,
        test_terminated_is_real,
        test_route_env_splits_offered_measured_and_loss,
        test_route_env_samples_direct_load_separately_from_via_e,
        test_route_env_accepts_f_load_alias_for_direct_path,
        test_route_env_applies_directed_dynamic_trends_to_decision_links,
        test_route_env_samples_episode_trend_from_range,
        test_route_env_uses_normal_floor_for_drift,
        test_route_env_uses_active_scenario_offered_load_cap_for_drift,
        test_topology_v2_flips_on_measured_queue_cliff_at_c,
        test_topology_v2_link_budget_and_degree,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f'  PASS  {test.__name__}')
    print(f'\n{passed}/{len(tests)} passed')


if __name__ == '__main__':
    _run_as_script()

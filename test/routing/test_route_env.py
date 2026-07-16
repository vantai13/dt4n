#!/usr/bin/env python3
"""Tests for the minimal RouteEnv stage."""

import re
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.link_model import loss_rate, total_delay_ms
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
from rl.routing.topology_r import LOAD_PRESETS, TOPO


def _base_delay(topo, src, dst):
    for edge_src, edge_dst, delay_ms, _bw_mbps in topo['edges']:
        if edge_src == src and edge_dst == dst:
            return float(delay_ms)
    raise KeyError((src, dst))


def test_dim():
    state = build_route_state(0, 8, 0, 15, [0.3, 0.4], [1, 1], aoi_s=0.0)
    assert state.shape == (R_STATE_DIM,)
    assert R_STATE_DIM == 7
    assert R_STATE_DIM <= 16


def test_topology_v2_link_budget_and_degree():
    bws = [float(edge[3]) for edge in TOPO['edges']]
    assert min(bws) == 4.0
    assert max(bws) == 8.0

    degree = {node: 0 for node in TOPO['nodes']}
    for src, _dst, _delay, _bw in TOPO['edges']:
        degree[src] += 1
    assert max(degree.values()) <= 2


def test_load_presets_are_slices_of_one_axis():
    assert set(LOAD_PRESETS) == {'normal', 'borderline', 'bottleneck_E'}
    assert LOAD_PRESETS['normal']['e_load'][1] < LOAD_PRESETS['borderline']['e_load'][1]
    assert LOAD_PRESETS['borderline']['e_load'][0] < LOAD_PRESETS['bottleneck_E']['e_load'][0]


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


def test_mm1_monotone_and_unbounded():
    prev = -1.0
    for rho in [0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.97]:
        delay = total_delay_ms(2.0, rho)
        assert delay > prev
        prev = delay
    assert total_delay_ms(2.0, 0.97) > 4 * total_delay_ms(2.0, 0.8)


def test_topology_v2_decision_flips_at_c():
    base_ce = _base_delay(TOPO, 'C', 'E')
    base_cf = _base_delay(TOPO, 'C', 'F')
    r_f = step_reward(total_delay_ms(base_cf, 0.30), loss_rate(0.30)).total
    r_e_low = step_reward(total_delay_ms(base_ce, 0.60), loss_rate(0.60)).total
    r_e_high = step_reward(total_delay_ms(base_ce, 0.90), loss_rate(0.90)).total

    assert r_e_low > r_f
    assert r_e_high < r_f


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
        test_load_presets_are_slices_of_one_axis,
        test_mask_does_not_mutate,
        test_mask_touches_only_aoi,
        test_mm1_monotone_and_unbounded,
        test_no_staleness_code_in_env,
        test_sim_time_advances_by_physical_link_delay,
        test_terminated_is_real,
        test_topology_v2_decision_flips_at_c,
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

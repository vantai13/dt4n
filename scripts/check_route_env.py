#!/usr/bin/env python3
"""Smoke checks and measurements for the Phase 8.2 RouteEnv."""

import sys
import time

import numpy as np

sys.path.insert(0, '.')

from rl.routing.link_model import (
    loss_rate,
    rho_measured_from_offered,
    total_delay_ms,
)
from rl.routing.reward_r import step_reward
from rl.routing.route_env import RouteEnv
from rl.routing.state_r import R_STATE_DIM
from rl.routing.topology_r import TOPO


def _base_delay(topo, src, dst):
    for edge_src, edge_dst, delay_ms, _bw_mbps in topo['edges']:
        if edge_src == src and edge_dst == dst:
            return float(delay_ms)
    raise KeyError((src, dst))


def _masked_episode(env, rng, seed):
    obs, info = env.reset(seed=seed)
    total = 0.0
    steps = 0
    last = info
    while True:
        valid = np.flatnonzero(info['valid_mask'])
        if len(valid) == 0:
            return total, steps, False, True, dict(info, no_valid_action=True)
        action = int(rng.choice(valid))
        obs, reward, terminated, truncated, info = env.step(action)
        total += float(reward)
        steps += 1
        last = info
        if terminated or truncated:
            return total, steps, terminated, truncated, last


def check_env():
    env = RouteEnv(TOPO, seed=0)
    obs, info = env.reset(seed=0)
    assert obs.shape == (R_STATE_DIM,), obs.shape
    assert env.action_space.n == 2
    assert info['current_node'] == TOPO['source']
    print(f'check_env PASS, dim = {obs.shape}, action_space = {env.action_space}')


def run_random_episodes(n_episodes=500):
    env = RouteEnv(TOPO, seed=0)
    rng = np.random.default_rng(123)
    returns = []
    lengths = []
    arrived = loop = timeout = invalid = 0
    for ep in range(n_episodes):
        ret, length, terminated, truncated, info = _masked_episode(env, rng, ep)
        returns.append(ret)
        lengths.append(length)
        arrived += int(bool(info.get('arrived')))
        loop += int(bool(info.get('loop')))
        timeout += int(bool(info.get('timeout')))
        invalid += int(bool(info.get('invalid_action')))

    print(f'\n{n_episodes} ep random policy (masked):')
    print(f'  arrived : {arrived}')
    print(f'  loop    : {loop}')
    print(f'  timeout : {timeout}')
    print(f'  invalid : {invalid}')
    print(f'  return  : {np.mean(returns):.3f} +- {np.std(returns):.3f}')
    print(f'  ep len  : {np.mean(lengths):.2f}')


def consequence_sweep():
    print('\n=== Consequence width at node C (sweep offered rho_E) ===')
    print(' rho_off | rho_meas |   loss |  r(choose E) |  r(choose F) |    diff')
    print('--------------------------------------------------------------------')
    max_gap = 0.0
    rho_f_off = 0.30
    rho_f_meas = rho_measured_from_offered(rho_f_off)
    loss_f = loss_rate(rho_f_off)
    base_e = _base_delay(TOPO, 'C', 'E')
    base_f = _base_delay(TOPO, 'C', 'F')
    env = RouteEnv(TOPO, seed=0)
    q_e = env.link[('C', 'E')].get('queue_pkts')
    q_f = env.link[('C', 'F')].get('queue_pkts')
    bw_e = env.link[('C', 'E')].get('base_bw')
    bw_f = env.link[('C', 'F')].get('base_bw')
    r_f = step_reward(
        total_delay_ms(base_f, rho_f_meas, bw_mbps=bw_f, queue_pkts=q_f),
        loss_f,
    ).total
    for rho_e_off in [0.3, 0.5, 0.7, 0.85, 0.90, 0.927, 0.95, 1.0, 1.1]:
        rho_e_meas = rho_measured_from_offered(rho_e_off)
        loss_e = loss_rate(rho_e_off)
        r_e = step_reward(
            total_delay_ms(base_e, rho_e_meas, bw_mbps=bw_e, queue_pkts=q_e),
            loss_e,
        ).total
        diff = r_e - r_f
        max_gap = max(max_gap, abs(diff))
        print(
            f'{rho_e_off:8.3f} | {rho_e_meas:8.3f} | {loss_e:6.3f} | '
            f'{r_e:12.4f} | {r_f:12.4f} | {diff:+7.4f}'
        )
    print(f'\nmax wrong-decision width: {max_gap:.4f}')


def speed_check(n_episodes=1000):
    env = RouteEnv(TOPO, seed=0)
    rng = np.random.default_rng(456)
    t0 = time.perf_counter()
    for ep in range(n_episodes):
        _masked_episode(env, rng, ep)
    dt = time.perf_counter() - t0
    print(f'\n{n_episodes} ep in {dt:.2f}s => {1000 * dt / n_episodes:.3f} ms/ep')


def main():
    check_env()
    run_random_episodes()
    consequence_sweep()
    speed_check()


if __name__ == '__main__':
    main()

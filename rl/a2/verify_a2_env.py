#!/usr/bin/env python3
"""A2 gate: run scripted policies and verify the trade-off is real.

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 /usr/bin/python3 rl/a2/verify_a2_env.py --seeds 8
"""

import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from rl.a2.policies_a2 import (
    policy_equal,
    policy_greedy,
    policy_greedy_strong,
    policy_noop,
    policy_myopic_oracle,
)
from rl.a2.twin_env_a2 import TwinEnvA2


POLICIES = {
    'myopic_oracle': policy_myopic_oracle,
    'greedy': policy_greedy,
    'greedy_strong': policy_greedy_strong,
    'equal': policy_equal,
    'noop': policy_noop,
}


def run_episode(env, policy_fn, seed):
    obs, info = env.reset(seed=seed)
    total_reward = 0.0
    total_sat = 0.0
    terminated = False
    truncated = False
    while not (terminated or truncated):
        action = policy_fn(env, obs, info)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)
        total_sat += float(info.get('total_sat', 0.0))
    return total_reward, total_sat / max(env._t, 1)


def parse_args():
    ap = argparse.ArgumentParser(description='Verify A2 env trade-off gate.')
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--seed-start', type=int, default=500)
    ap.add_argument('--t-max', type=int, default=8)
    ap.add_argument('--delta-s', type=float, default=1.8)
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--gap-threshold', type=float, default=0.5)
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def main():
    args = parse_args()
    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    print('[a2] start()...', flush=True)
    runner.start()
    env = TwinEnvA2(
        runner,
        cfg={'delta_s': args.delta_s, 't_max_steps': args.t_max},
    )

    results = {name: {'return': [], 'sat': []} for name in POLICIES}
    try:
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            for name, policy_fn in POLICIES.items():
                ret, sat = run_episode(env, policy_fn, seed)
                results[name]['return'].append(ret)
                results[name]['sat'].append(sat)
                scenario = env._scenario
                print('[a2] seed=%d %-8s return=%7.2f avg_sat=%.3f  '
                      '(demand A=%.1f B=%.1f %s)'
                      % (seed, name, ret, sat, scenario.demand_A,
                         scenario.demand_B, scenario.kind),
                      flush=True)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[a2] ===== SUMMARY =====')
    summary = {}
    for name in POLICIES:
        ret_mean = float(np.mean(results[name]['return']))
        sat_mean = float(np.mean(results[name]['sat']))
        summary[name] = (ret_mean, sat_mean)
        print('[a2] %-8s return_mean=%7.2f  sat_mean=%.3f'
              % (name, ret_mean, sat_mean))

    oracle_return = summary['myopic_oracle'][0]
    equal_return = summary['equal'][0]
    gap = oracle_return - equal_return
    print('\n[a2] === GATE TRADE-OFF ===')
    print('[a2] myopic_oracle return=%.2f vs equal return=%.2f -> gap=%.2f'
          % (oracle_return, equal_return, gap))
    if gap > args.gap_threshold:
        print('[a2] RESULT: OK, myopic oracle beats fixed equal allocation.')
        print('[a2] RL has room: no single fixed allocation is optimal for all demand.')
    else:
        print('[a2] RESULT: WARN, trade-off is weak.')
        print('[a2] Increase demand skew or reduce budget, then run this gate again.')


if __name__ == '__main__':
    main()

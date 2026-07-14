#!/usr/bin/env python3
"""Verify that dynamic A2 env runs and demand flips at t_shift."""

import os
import sys
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from rl.a2.policies_a2 import policy_myopic_oracle
from rl.a2.twin_env_a2 import TwinEnvA2


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify A2 dynamic demand env over a few seeds.')
    ap.add_argument('--seed-start', type=int, default=500)
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--t-max', type=int, default=8)
    ap.add_argument('--delta-s', type=float, default=1.8)
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def main():
    args = parse_args()
    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    print('[dyn] start()...', flush=True)
    runner.start()
    env = TwinEnvA2(
        runner,
        cfg={'delta_s': args.delta_s, 't_max_steps': args.t_max,
             'dynamic': True},
    )
    try:
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            obs, info = env.reset(seed=seed)
            sc = info['scenario']
            print('\n[dyn] seed=%d t_shift=%d %s ph1=%s ph2=%s'
                  % (seed, sc['t_shift'], sc['kind'],
                     sc['phase1'], sc['phase2']),
                  flush=True)
            for t in range(8):
                action = policy_myopic_oracle(env, obs, info)
                obs, reward, terminated, truncated, info = env.step(action)
                dA, dB = env._cur_demand
                marker = (
                    ' SHIFT'
                    if info.get('demand_changed') or t == sc['t_shift']
                    else ''
                )
                print('   t=%d env_t=%d demand=(%.1f,%.1f) alloc=%s '
                      'gA=%.1f gB=%.1f r=%.2f%s'
                      % (t, env._t, dA, dB, info['alloc'],
                         info['goodput_A'], info['goodput_B'],
                         reward, marker),
                      flush=True)
                if terminated or truncated:
                    break
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)
    print('\n[dyn] OK if demand flips at t_shift and myopic oracle follows it.')


if __name__ == '__main__':
    main()

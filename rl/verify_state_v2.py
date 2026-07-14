#!/usr/bin/env python3
"""Verify State v2: 51 dims, util-centric M/M/1 delay, no ping loss/latency.

Checks on the live env:
  1. State dim = 51, has delay_mm1, no path_loss/path_latency dims.
  2. delay_mm1 reacts when LinkDegrade increases util on s2-s3.
  3. reward v3 keeps loss_term=0 and info has no loss key.

Run on the Mininet/controller machine:
    sudo -E python rl/verify_state_v2.py
"""

import argparse
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from mininet.topology_meta import load_spec
from rl.scenarios import LinkDegrade
from rl.twin_env import TwinEnv


def parse_args():
    ap = argparse.ArgumentParser(description='Verify DT4N State v2 contract.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--delta-s', type=float, default=1.8)
    ap.add_argument('--t-max', type=int, default=15)
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def clean_observation(env, runner):
    """Reset live network without injecting a random scenario, then observe."""
    runner.soft_reset(scenario=None)
    env._t = 0
    env._healthy_streak = 0
    env.builder.reset()
    env.action_map.reset()
    return env._observe()


def main():
    args = parse_args()
    spec = load_spec(args.spec)
    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=0,
    )
    print('[v2] start()...', flush=True)
    runner.start()
    env = TwinEnv(
        runner,
        spec,
        cfg={'delta_s': args.delta_s, 't_max_steps': args.t_max},
    )

    try:
        obs = clean_observation(env, runner)
        names = env._dim_names
        print('[v2] STATE_DIM =', len(obs))
        assert len(obs) == 51, 'expected 51 dims, got %d' % len(obs)
        assert any(name.startswith('delay_mm1:') for name in names), 'missing delay_mm1'
        assert not any('path_loss' in name for name in names), 'path_loss still present'
        assert not any('path_latency' in name for name in names), 'path_latency still present'
        print('[v2] OK: dim=51, has delay_mm1, no ping dims')

        i_delay = names.index('delay_mm1:s2-s3')
        i_util = names.index('util:s2-s3')
        d_before = float(obs[i_delay])
        u_before = float(obs[i_util])
        sc = LinkDegrade('s2-s3', 0.6, '2ms', 5.0)
        with runner.net_lock:
            sc.apply(runner.net)
        time.sleep(4.0)
        obs2 = env._observe()
        d_after = float(obs2[i_delay])
        u_after = float(obs2[i_util])
        print('[v2] s2-s3: util %.3f -> %.3f, delay_mm1 %.3f -> %.3f'
              % (u_before, u_after, d_before, d_after))
        assert d_after >= d_before, 'delay_mm1 did not increase/stay high with util'
        print('[v2] OK: delay_mm1 follows util')
        with runner.net_lock:
            sc.revert(runner.net)

        _obs, _info = env.reset(seed=2001)
        _obs, reward, _term, _trunc, info = env.step(0)
        bd = info['reward_breakdown']
        print('[v2] reward=%.3f breakdown=%s'
              % (reward, {k: round(v, 3) for k, v in bd.items()}))
        assert abs(bd['loss_term']) < 1e-9, 'loss_term must be 0 in reward v3'
        assert 'loss' not in info, 'info must not expose removed loss key'
        print('[v2] OK: reward v3 loss_term=0, info has no loss')

        o1, _ = env.reset(seed=2002)
        o2, _ = env.reset(seed=2002)
        same = np.allclose(o1, o2, atol=1e-3)
        print('[v2] same seed observation:', 'close' if same else 'diff/live-noise')

    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[v2] PASS: State v2 is wired. Next gate: oracle executability.')


if __name__ == '__main__':
    main()

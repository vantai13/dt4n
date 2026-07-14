#!/usr/bin/env python3
"""Oracle executability: run oracle/no-op through the live TwinEnv.

This answers:
  1. Which scenario types are solvable with the current action space?
  2. How many steps does the oracle need when it wins?
  3. Is there a useful gap between oracle and no-op?

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 python rl/oracle_executability.py --seeds 40
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from mininet.topology_meta import load_spec
from rl.action_space import ActionSpace
from rl.oracle_policy import oracle_actions
from rl.twin_env import TwinEnv


def parse_args():
    ap = argparse.ArgumentParser(
        description='Measure oracle executability on the live DT4N env.')
    ap.add_argument('--seeds', type=int, default=40)
    ap.add_argument('--seed-start', type=int, default=1000)
    ap.add_argument('--t-max', type=int, default=15)
    ap.add_argument('--delta-s', type=float, default=1.8)
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--hard-every', type=int, default=50)
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--out',
                    default='docs/phase-6/artifacts/oracle_executability.json')
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def action_index(action_space, action_tuple):
    """Translate ('bw_up', 's1-s2') into an ActionSpace index."""
    for idx, row in enumerate(action_space._table):
        if row == action_tuple:
            return idx
    return None


def run_episode(env, action_space, seed, t_max, use_oracle):
    """Run one episode. Env generates the scenario from seed."""
    _obs, _reset_info = env.reset(seed=seed)
    scenario = env._scenario
    label = type(scenario).__name__

    if use_oracle:
        plan = [
            action_index(action_space, action)
            for action in oracle_actions(scenario)
        ]
        plan = [idx for idx in plan if idx is not None]
    else:
        plan = []

    info = {'throughput': 0.0}
    for t in range(t_max):
        action = plan[t] if t < len(plan) else 0
        _obs, _reward, terminated, truncated, info = env.step(action)
        if terminated:
            return label, True, t + 1, info.get('throughput', 0.0), plan
        if truncated:
            break
    return label, False, t_max, info.get('throughput', 0.0), plan


def summarize(results):
    summary = {}
    for label, row in sorted(results.items()):
        n = max(row['n'], 1)
        steps = row['oracle_steps']
        summary[label] = {
            'n': row['n'],
            'oracle_win_rate': round(row['oracle_win'] / n, 3),
            'noop_win_rate': round(row['noop_win'] / n, 3),
            'oracle_steps_mean': (
                round(float(np.mean(steps)), 1) if steps else None
            ),
            'oracle_steps_p95': (
                int(np.percentile(steps, 95)) if steps else None
            ),
            'oracle_final_thr_mean': (
                round(float(np.mean(row['oracle_thr'])), 3)
                if row['oracle_thr'] else None
            ),
            'noop_final_thr_mean': (
                round(float(np.mean(row['noop_thr'])), 3)
                if row['noop_thr'] else None
            ),
        }
    all_steps = [
        step for row in results.values() for step in row['oracle_steps']
    ]
    if all_steps:
        summary['_t_max_recommended'] = int(np.percentile(all_steps, 95)) + 5
    return summary


def main():
    args = parse_args()
    spec = load_spec(args.spec)
    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=args.hard_every,
    )
    print('[oracle] start()...', flush=True)
    runner.start()

    action_space = ActionSpace(spec)
    env = TwinEnv(
        runner,
        spec,
        cfg={'delta_s': args.delta_s, 't_max_steps': args.t_max},
    )
    results = defaultdict(lambda: {
        'n': 0,
        'oracle_win': 0,
        'noop_win': 0,
        'oracle_steps': [],
        'oracle_thr': [],
        'noop_thr': [],
    })

    try:
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            label, o_win, o_steps, o_thr, plan = run_episode(
                env, action_space, seed, args.t_max, use_oracle=True)
            _label2, n_win, n_steps, n_thr, _ = run_episode(
                env, action_space, seed, args.t_max, use_oracle=False)

            row = results[label]
            row['n'] += 1
            row['oracle_win'] += int(o_win)
            row['noop_win'] += int(n_win)
            row['oracle_thr'].append(float(o_thr))
            row['noop_thr'].append(float(n_thr))
            if o_win:
                row['oracle_steps'].append(o_steps)

            plan_text = ','.join(action_space.describe(i) for i in plan[:4])
            if len(plan) > 4:
                plan_text += ',...'
            print('[oracle] seed=%d %-16s oracle=%s(%2d) noop=%s(%2d) '
                  'thr=%.3f plan=[%s]'
                  % (seed, label, 'W' if o_win else 'L', o_steps,
                     'W' if n_win else 'L', n_steps, o_thr, plan_text),
                  flush=True)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    summary = summarize(results)
    print('\n[oracle] ===== TONG KET =====')
    for label in sorted(k for k in summary if not k.startswith('_')):
        row = summary[label]
        print('[oracle] %-16s oracle=%3.0f%%  noop=%3.0f%%  '
              'steps=%s/%s  thr(o/noop)=%s/%s  n=%d'
              % (label,
                 100 * row['oracle_win_rate'],
                 100 * row['noop_win_rate'],
                 row['oracle_steps_mean'],
                 row['oracle_steps_p95'],
                 row['oracle_final_thr_mean'],
                 row['noop_final_thr_mean'],
                 row['n']))
    if '_t_max_recommended' in summary:
        print('\n[oracle] t_max de xuat = p95+5 = %d'
              % summary['_t_max_recommended'])

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('[oracle] wrote %s' % args.out)


if __name__ == '__main__':
    main()

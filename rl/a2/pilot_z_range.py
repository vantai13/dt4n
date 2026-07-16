#!/usr/bin/env python3
"""Pilot the useful staleness range before training AoI-aware agents."""

import argparse
import json
import os
import sys

import numpy as np


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner  # noqa: E402
from rl.a2.policies_a2 import (  # noqa: E402
    policy_blind_oracle,
    policy_clairvoyant,
    policy_noop,
)
from rl.a2.scenarios.demand_scenarios import SCENARIO_NAMES  # noqa: E402
from rl.a2.staleness import StalenessWrapper  # noqa: E402
from rl.a2.twin_env_a2 import TwinEnvA2  # noqa: E402


def run_episode(env, policy, seed, scenario):
    obs, info = env.reset(seed=seed, options={'scenario': scenario})
    total_return = 0.0
    wrong = 0
    noop = 0
    aois = []
    steps = 0

    while True:
        action = policy(env, obs, info)
        obs, reward, terminated, truncated, info = env.step(action)
        total_return += float(reward)
        wrong += int(info.get('wrong_target', False))
        noop += int(action == 0)
        aois.append(float(info.get('aoi_measured_s', 0.0)))
        steps += 1
        if terminated or truncated:
            break

    return {
        'return': total_return,
        'wrong_rate': wrong / max(steps, 1),
        'noop_freq': noop / max(steps, 1),
        'aoi_mean_s': float(np.mean(aois)) if aois else 0.0,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pilot cost of blindness across staleness levels.')
    parser.add_argument('--z-list', default='0,1,2,3,5,8')
    parser.add_argument('--episodes', type=int, default=8)
    parser.add_argument('--scenarios',
                        default='S3_flip_near,S4_flip_far,S5_scarce_flip')
    parser.add_argument('--delta-s', type=float, default=1.1)
    parser.add_argument('--t-max', type=int, default=8)
    parser.add_argument('--sync-period', type=float, default=0.5)
    parser.add_argument('--out', default='results/pilot/z_range.json')
    parser.add_argument('--cleanup-mn', action='store_true')
    parser.add_argument(
        '--quiet-progress',
        action='store_true',
        help='Disable per-policy-episode progress logs.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    z_list = [int(z.strip()) for z in args.z_list.split(',') if z.strip()]
    scenarios = [s.strip() for s in args.scenarios.split(',') if s.strip()]
    unknown = [s for s in scenarios if s not in SCENARIO_NAMES]
    if unknown:
        raise SystemExit(
            'unknown scenario(s): %s\nknown: %s'
            % (', '.join(unknown), ', '.join(SCENARIO_NAMES))
        )
    seeds = list(range(500, 500 + args.episodes))

    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    runner.start()
    rows = []
    raw = {}
    policies = [
        ('blind', policy_blind_oracle),
        ('clair', policy_clairvoyant),
        ('noop', policy_noop),
    ]
    total_runs = len(z_list) * len(scenarios) * len(seeds) * len(policies)
    done_runs = 0
    try:
        cfg = {'delta_s': args.delta_s, 't_max_steps': args.t_max}
        for z_steps in z_list:
            if not args.quiet_progress:
                print('[pilot] START z=%d (%d scenarios x %d seeds x %d policies)'
                      % (z_steps, len(scenarios), len(seeds), len(policies)),
                      flush=True)
            env = StalenessWrapper(
                TwinEnvA2(runner, cfg=cfg),
                z_steps_choices=(z_steps,),
            )
            acc = {'blind': [], 'clair': [], 'noop': []}
            for scenario in scenarios:
                for seed in seeds:
                    for policy_name, policy_fn in policies:
                        result = run_episode(env, policy_fn, seed, scenario)
                        acc[policy_name].append(result)
                        done_runs += 1
                        if not args.quiet_progress:
                            print(
                                '[pilot] %3d/%3d z=%d scenario=%s seed=%d '
                                'policy=%s return=%.3f aoi=%.2fs '
                                'wrong=%.1f%% noop=%.1f%%'
                                % (
                                    done_runs,
                                    total_runs,
                                    z_steps,
                                    scenario,
                                    seed,
                                    policy_name,
                                    result['return'],
                                    result['aoi_mean_s'],
                                    100.0 * result['wrong_rate'],
                                    100.0 * result['noop_freq'],
                                ),
                                flush=True,
                            )

            raw[str(z_steps)] = acc

            def avg(policy_name, field):
                return float(np.mean([row[field] for row in acc[policy_name]]))

            row = {
                'z_steps': z_steps,
                'aoi_measured_s': round(avg('blind', 'aoi_mean_s'), 3),
                'blind_return': round(avg('blind', 'return'), 3),
                'clair_return': round(avg('clair', 'return'), 3),
                'noop_return': round(avg('noop', 'return'), 3),
                'blind_wrong_rate': round(avg('blind', 'wrong_rate'), 3),
                'clair_wrong_rate': round(avg('clair', 'wrong_rate'), 3),
            }
            row['cost_of_blindness'] = round(
                row['clair_return'] - row['blind_return'], 3)
            row['dynamic_range'] = round(
                row['clair_return'] - row['noop_return'], 3)
            # Ideal AoI-aware ceiling: trust the twin when blind beats noop,
            # otherwise stay conservative.  This is the headroom available for
            # an agent that can read AoI and choose when not to trust stale data.
            row['aoi_aware_ceiling'] = round(
                max(row['blind_return'], row['noop_return']), 3)
            row['voi_headroom'] = round(
                row['aoi_aware_ceiling'] - row['blind_return'], 3)
            row['blind_minus_noop'] = round(
                row['blind_return'] - row['noop_return'], 3)
            # wrong_target has its own noise floor: even clairvoyant can be
            # counted wrong on ties or edge timing.  Report the excess over it.
            row['wrong_excess'] = round(
                row['blind_wrong_rate'] - row['clair_wrong_rate'], 3)
            rows.append(row)
            print(
                'z=%d aoi=%.2fs | clair=%.2f blind=%.2f noop=%.2f | '
                'cost_blind=%+.2f range=%.2f voi=%.2f b-noop=%+.2f | '
                'wrong blind=%.0f%% clair=%.0f%% excess=%.0f%%'
                % (
                    z_steps,
                    row['aoi_measured_s'],
                    row['clair_return'],
                    row['blind_return'],
                    row['noop_return'],
                    row['cost_of_blindness'],
                    row['dynamic_range'],
                    row['voi_headroom'],
                    row['blind_minus_noop'],
                    100 * row['blind_wrong_rate'],
                    100 * row['clair_wrong_rate'],
                    100 * row['wrong_excess'],
                ),
                flush=True,
            )
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    payload = {'args': vars(args), 'rows': rows, 'raw': raw}
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write('\n')

    print('\n===== GATE =====')
    max_cost = max(row['cost_of_blindness'] for row in rows)
    max_range = max(row['dynamic_range'] for row in rows)
    max_voi = max(row['voi_headroom'] for row in rows)
    bp = next((row for row in rows if row['blind_minus_noop'] < 0.0), None)

    print('RQ2  cost_of_blindness = %.2f  (>= 1.0)  %s'
          % (max_cost, 'PASS' if max_cost >= 1.0 else 'FAIL'))
    print('RQ2  breaking point    = %s'
          % ('AoI ~ %.2fs (z=%d)' % (bp['aoi_measured_s'], bp['z_steps'])
             if bp else 'KHONG CO trong dai do'))
    print('RQ2b VoI headroom      = %.2f  (>= 1.0)  %s'
          % (max_voi, 'PASS' if max_voi >= 1.0 else 'FAIL'))
    print('RQ1  dynamic_range     = %.2f  (>= 3.0)  %s'
          % (max_range, 'PASS' if max_range >= 3.0 else 'FAIL'))

    if max_voi < 1.0:
        print('\n>> VoI headroom qua nho: agent-AoI co it dat de thang')
        print('>> agent-no-AoI. Train bay gio de ra inconclusive.')
        print('>> Sua tiep: c_switch/t_max/periodic flip, roi do lai.')
    elif max_cost >= 1.0 and bp and max_range >= 3.0:
        best = max(rows, key=lambda row: row['voi_headroom'])
        print('\nPASS. best VoI z=%d (AoI %.2fs)'
              % (best['z_steps'], best['aoi_measured_s']))


if __name__ == '__main__':
    main()

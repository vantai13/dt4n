#!/usr/bin/env python3
"""Run a small RuleBasedPolicy pilot and save diagnostics artifacts.

This is a convenience wrapper for Lesson 6.4. It does not train DQN; it only
runs the fixed rule-based baseline through TwinEnv, gathers reward/action
signals, then calls rl.diagnostics.diagnose_run().
"""

import argparse
import json
import os

import numpy as np

from mininet.env_runner import EnvRunner
from mininet.topology_meta import load_spec
from rl.baselines import RuleBasedPolicy
from rl.diagnostics import diagnose_run
from rl.twin_env import TwinEnv


def parse_args():
    p = argparse.ArgumentParser(description='Rule-based pilot diagnostics')
    p.add_argument('--episodes', type=int, default=5)
    p.add_argument('--seed-start', type=int, default=500)
    p.add_argument('--out', default='docs/phase-6/artifacts/rulebased_diag.json')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--sync-period', type=float, default=0.5)
    p.add_argument('--delta-s', type=float, default=1.8)
    p.add_argument('--t-max', type=int, default=15)
    p.add_argument('--hard-every', type=int, default=20)
    p.add_argument('--mininet-log-level', default='warning')
    return p.parse_args()


def main():
    args = parse_args()

    spec = load_spec(args.spec)
    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=args.hard_every,
        mininet_log_level=args.mininet_log_level,
    )

    print('[pilot] starting EnvRunner...', flush=True)
    runner.start()

    component_sums = {}
    returns = []
    throughputs = []
    all_actions = []
    sample_action_seq = []
    episodes = []

    try:
        env = TwinEnv(
            runner,
            spec,
            cfg={'delta_s': args.delta_s, 't_max_steps': args.t_max},
        )
        policy = RuleBasedPolicy(spec_path=args.spec)

        for ep in range(args.episodes):
            seed = args.seed_start + ep
            obs, reset_info = env.reset(seed=seed)
            scenario = reset_info.get('scenario', {}).get('type', 'unknown')
            print('[episode %d/%d] seed=%d scenario=%s'
                  % (ep + 1, args.episodes, seed, scenario), flush=True)

            done = False
            ep_return = 0.0
            ep_throughputs = []
            ep_actions = []
            terminated = truncated = False
            info = {}

            while not done:
                action = int(policy.select_action(obs, epsilon=0.0))
                obs, reward, terminated, truncated, info = env.step(action)

                ep_return += float(reward)
                ep_actions.append(action)
                all_actions.append(action)

                thr = float(info.get('throughput', 0.0))
                ep_throughputs.append(thr)
                throughputs.append(thr)

                for k, v in info.get('reward_breakdown', {}).items():
                    component_sums[k] = component_sums.get(k, 0.0) + float(v)

                done = terminated or truncated

            if not sample_action_seq:
                sample_action_seq = list(ep_actions)
            returns.append(ep_return)

            row = {
                'episode': ep + 1,
                'seed': seed,
                'scenario': scenario,
                'steps': int(info.get('t', len(ep_actions))),
                'return': ep_return,
                'mean_throughput': float(np.mean(ep_throughputs)) if ep_throughputs else 0.0,
                'n_interventions': int(sum(1 for a in ep_actions if a != 0)),
                'terminated': int(terminated),
                'truncated': int(truncated),
                'actions': ep_actions,
            }
            episodes.append(row)

            status = 'TERM' if terminated else 'TRUNC'
            print('[episode %d/%d] %s steps=%d return=%.3f thr=%.3f actions=%d'
                  % (ep + 1, args.episodes, status, row['steps'], row['return'],
                     row['mean_throughput'], row['n_interventions']),
                  flush=True)

        return_mean = float(np.mean(returns)) if returns else 0.0
        throughput_mean = float(np.mean(throughputs)) if throughputs else 0.0

        red_flag = diagnose_run(
            component_sums,
            return_mean,
            throughput_mean,
            all_actions,
            sample_action_seq,
        )

        artifact = {
            'policy': 'RuleBasedPolicy',
            'episodes': episodes,
            'summary': {
                'n_episodes': len(episodes),
                'return_mean': return_mean,
                'mean_throughput_mean': throughput_mean,
                'n_interventions_mean': float(np.mean([
                    e['n_interventions'] for e in episodes
                ])) if episodes else 0.0,
                'fail_rate': float(np.mean([
                    e['truncated'] for e in episodes
                ])) if episodes else 0.0,
                'diagnostics_red_flag': bool(red_flag),
            },
            'component_sums': component_sums,
            'all_actions': all_actions,
            'sample_action_seq': sample_action_seq,
        }

        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print('[artifact] wrote %s' % args.out, flush=True)
        return 1 if red_flag else 0
    finally:
        print('[pilot] closing EnvRunner...', flush=True)
        runner.close()


if __name__ == '__main__':
    raise SystemExit(main())

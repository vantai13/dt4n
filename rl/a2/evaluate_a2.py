#!/usr/bin/env python3
"""Evaluate A2 policies by named scenario, with CI95 reporting."""

import argparse
import json
import os
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rl.a2.scenarios.demand_scenarios import (  # noqa: E402
    SCENARIO_DESC,
    SCENARIO_NAMES,
    eval_seeds,
)
from rl.a2.state_a2 import A2_STATE_DIM  # noqa: E402
from rl.a2.train_a2 import agent_config, parse_z_steps  # noqa: E402
from rl.a2.utils.stats import (  # noqa: E402
    format_stat,
    significantly_better,
    summarize,
)


def run_episode(env, policy_fn, seed, scenario_name):
    """Run one policy for one scenario+seed and return episode metrics."""
    obs, info = env.reset(seed=seed, options={'scenario': scenario_name})
    total_return = 0.0
    total_sat = 0.0
    wrong = 0
    noop = 0
    aois = []
    steps = 0
    terminated = False
    truncated = False

    while not (terminated or truncated):
        action = policy_fn(env, obs, info)
        obs, reward, terminated, truncated, info = env.step(action)
        total_return += float(reward)
        total_sat += float(info.get('total_sat', float(obs[5]) + float(obs[6])))
        wrong += int(info.get('wrong_target', False))
        noop += int(action == 0)
        aois.append(float(info.get('aoi_measured_s', 0.0)))
        steps += 1

    return {
        'return': total_return,
        'sat': total_sat,
        'sat_mean': total_sat / max(steps, 1),
        'wrong_rate': wrong / max(steps, 1),
        'noop_freq': noop / max(steps, 1),
        'aoi_mean_s': sum(aois) / max(len(aois), 1),
        'z_steps': int(info.get('z_steps', 0)),
        'steps': steps,
    }


def build_policies(model_path, cfg, include_diagnostics=False):
    """Build policy callables. Load DQN only when a checkpoint exists."""
    from rl.a2.policies_a2 import (
        policy_equal,
        policy_blind_oracle,
        policy_clairvoyant,
        policy_greedy,
        policy_greedy_strong,
        policy_noop,
        policy_oracle_dynamic,
    )

    policies = {
        'noop': policy_noop,
        'equal': policy_equal,
        'greedy': policy_greedy,
        'greedy_strong': policy_greedy_strong,
        'myopic_oracle': policy_oracle_dynamic,
    }
    if include_diagnostics:
        policies['blind_oracle'] = policy_blind_oracle
        policies['clairvoyant'] = policy_clairvoyant

    if not model_path or not os.path.exists(model_path):
        print('[eval-a2] warning: model %r not found; skipping agent'
              % model_path)
        return policies

    from rl.agent.dqn_agent import DQNAgent

    agent = DQNAgent(state_size=A2_STATE_DIM, action_size=3, config=cfg)
    agent.load(model_path)

    def policy_agent(env, obs, info):
        return agent.select_action(obs, epsilon=0.0)

    # Put agent first in JSON/plots while keeping baselines available.
    return {'agent': policy_agent, **policies}


def print_table(scenario, stats_return, stats_sat):
    """Print one scenario summary table."""
    print('\n' + '=' * 74)
    print('  %s' % scenario)
    print('  %s' % SCENARIO_DESC.get(scenario, ''))
    print('=' * 74)
    print('  %-16s %16s %16s %12s'
          % ('policy', 'return', 'sat_mean', 'n'))
    print('  ' + '-' * 68)

    order = sorted(
        stats_return.keys(),
        key=lambda policy: -(stats_return[policy]['mean'] or -9e9),
    )
    for policy in order:
        print('  %-16s %16s %16s %12d'
              % (
                  policy,
                  format_stat(stats_return[policy]),
                  format_stat(stats_sat[policy]),
                  stats_return[policy]['n'],
              ))

    if 'agent' not in stats_return:
        return

    print('  ' + '-' * 68)
    for baseline in ('greedy', 'greedy_strong', 'myopic_oracle'):
        if baseline not in stats_return:
            continue
        agent_mean = stats_return['agent']['mean']
        base_mean = stats_return[baseline]['mean']
        gap = (
            agent_mean - base_mean
            if agent_mean is not None and base_mean is not None
            else 0.0
        )
        verdict = significantly_better(
            stats_return['agent'],
            stats_return[baseline],
        )
        note = {
            'yes': 'agent better (CI does not overlap)',
            'no': 'agent worse (CI does not overlap)',
            'inconclusive': 'inconclusive (CI overlaps)',
        }[verdict]
        print('  agent - %-14s = %+6.3f   -> %s'
              % (baseline, gap, note))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Evaluate A2 policies on named demand scenarios.'
    )
    parser.add_argument('--model', default='results/train/a2_dqn_dynamic_clean.pt')
    parser.add_argument('--episodes', type=int, default=30,
                        help='number of eval seeds per scenario')
    parser.add_argument('--scenarios', default=','.join(SCENARIO_NAMES),
                        help='comma-separated scenario names')
    parser.add_argument('--delta-s', type=float, default=1.1)
    parser.add_argument('--t-max', type=int, default=12)
    parser.add_argument('--n-levels', type=int, default=7)
    parser.add_argument('--sync-period', type=float, default=0.5)
    parser.add_argument('--base-mbps', type=float, default=3.0)
    parser.add_argument('--burst-mbps', type=float, default=None)
    parser.add_argument('--stale-z', default='0',
                        help='comma-separated demand staleness in steps')
    parser.add_argument('--mask-aoi', action='store_true',
                        help='zero out AoI dimensions for no-AoI ablation')
    parser.add_argument('--include-diagnostics', action='store_true',
                        help='include blind_oracle and clairvoyant policies')
    parser.add_argument('--out', default='results/eval/eval_a2.json')
    parser.add_argument('--plot-dir', default='results/eval/plots')
    parser.add_argument('--cleanup-mn', action='store_true',
                        help='also run mn -c on exit')

    # Keep these defaults aligned with rl/a2/train_a2.py so checkpoints load.
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--learning-rate', type=float, default=1e-3)
    parser.add_argument('--epsilon-decay', type=float, default=0.97)
    return parser.parse_args()


def main():
    args = parse_args()
    z_choices = parse_z_steps(args.stale_z)
    scenarios = [s.strip() for s in args.scenarios.split(',') if s.strip()]
    unknown = [s for s in scenarios if s not in SCENARIO_NAMES]
    if unknown:
        raise SystemExit(
            'unknown scenario(s): %s\nknown: %s'
            % (', '.join(unknown), ', '.join(SCENARIO_NAMES))
        )

    seeds = eval_seeds(args.episodes)
    cfg = agent_config(args)

    from mininet.env_runner import EnvRunner
    from rl.a2.twin_env_a2 import TwinEnvA2

    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    runner.start()

    results_return = {}
    results_sat_mean = {}
    results_wrong_rate = {}
    results_noop_freq = {}
    results_aoi_mean = {}
    raw = {}
    t0 = time.monotonic()

    try:
        env_cfg = {
            'delta_s': args.delta_s,
            't_max_steps': args.t_max,
            'n_levels': args.n_levels,
            'base_mbps': args.base_mbps,
        }
        if args.burst_mbps is not None:
            env_cfg['burst_mbps'] = args.burst_mbps
        env = TwinEnvA2(runner=runner, cfg=env_cfg)
        use_wrapper = (z_choices != (0,)) or args.mask_aoi
        if use_wrapper:
            from rl.a2.staleness import StalenessWrapper

            env = StalenessWrapper(
                env,
                z_steps_choices=z_choices,
                mask_aoi_dims=args.mask_aoi,
            )
            print('[eval-a2] StalenessWrapper: z_steps=%s mask_aoi=%s'
                  % (list(z_choices), args.mask_aoi), flush=True)
        else:
            print('[eval-a2] no StalenessWrapper (z=0, mask_aoi=False)',
                  flush=True)
        policies = build_policies(
            args.model,
            cfg,
            include_diagnostics=args.include_diagnostics,
        )

        for scenario in scenarios:
            raw[scenario] = {policy: [] for policy in policies}
            for idx, seed in enumerate(seeds, 1):
                for policy_name, policy_fn in policies.items():
                    row = run_episode(env, policy_fn, seed, scenario)
                    row['seed'] = seed
                    raw[scenario][policy_name].append(row)
                print(
                    '[eval-a2] %-18s seed %d/%d done'
                    % (scenario, idx, len(seeds)),
                    flush=True,
                )

            results_return[scenario] = {
                policy: summarize(row['return'] for row in rows)
                for policy, rows in raw[scenario].items()
            }
            results_sat_mean[scenario] = {
                policy: summarize(row['sat_mean'] for row in rows)
                for policy, rows in raw[scenario].items()
            }
            results_wrong_rate[scenario] = {
                policy: summarize(row['wrong_rate'] for row in rows)
                for policy, rows in raw[scenario].items()
            }
            results_noop_freq[scenario] = {
                policy: summarize(row['noop_freq'] for row in rows)
                for policy, rows in raw[scenario].items()
            }
            results_aoi_mean[scenario] = {
                policy: summarize(row['aoi_mean_s'] for row in rows)
                for policy, rows in raw[scenario].items()
            }
            print_table(
                scenario,
                results_return[scenario],
                results_sat_mean[scenario],
            )
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    payload = {
        'measured': True,
        'episodes_per_scenario': args.episodes,
        'eval_seeds': seeds,
        'scenarios': scenarios,
        'scenario_desc': {s: SCENARIO_DESC.get(s, '') for s in scenarios},
        'policies': list(policies.keys()),
        'model': args.model,
        'stale_z_steps': list(z_choices),
        'mask_aoi': bool(args.mask_aoi),
        'state_dim': A2_STATE_DIM,
        'args': vars(args),
        'elapsed_s': round(time.monotonic() - t0, 1),
        'notes': [
            'All policies use the same eval seeds for fair paired comparison.',
            'eval_seeds start at 500 and are separate from train_seeds 1000+.',
            'If CI95 intervals overlap, do not claim a reliable winner.',
        ],
        'return': results_return,
        'sat_mean': results_sat_mean,
        'wrong_rate': results_wrong_rate,
        'noop_freq': results_noop_freq,
        'aoi_mean_s': results_aoi_mean,
        'raw': raw,
    }

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write('\n')
    print('\n[eval-a2] artifact -> %s' % args.out)

    try:
        from rl.a2.utils.visualize import bar_by_scenario, gap_heatmap

        os.makedirs(args.plot_dir, exist_ok=True)
        path = bar_by_scenario(
            results_return,
            os.path.join(args.plot_dir, 'return_by_scenario.png'),
            metric='return',
        )
        print('[eval-a2] plot -> %s' % path)
        path = bar_by_scenario(
            results_sat_mean,
            os.path.join(args.plot_dir, 'sat_mean_by_scenario.png'),
            metric='sat_mean',
        )
        print('[eval-a2] plot -> %s' % path)
        if 'agent' in policies:
            path = gap_heatmap(
                results_return,
                os.path.join(args.plot_dir, 'gap_heatmap.png'),
            )
            print('[eval-a2] plot -> %s' % path)
    except Exception as exc:
        print('[eval-a2] plotting skipped: %s' % exc)


if __name__ == '__main__':
    main()

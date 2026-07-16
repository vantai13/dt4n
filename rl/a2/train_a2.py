#!/usr/bin/env python3
"""A2 train: static-demand pipeline check or dynamic-demand A2.

This is not meant to make DQN look dramatic against greedy. The A2 static gate
already showed greedy is near-oracle with fresh static observations. The goal is
pipeline verification: DQN should beat weak baselines and approach greedy.

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 PYTHONPATH=$PWD \
      /path/to/python-with-torch rl/a2/train_a2.py --episodes 150
"""

import argparse
import csv
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from rl.a2.policies_a2 import (
    policy_equal,
    policy_greedy,
    policy_greedy_strong,
    policy_myopic_oracle,
    policy_noop,
)
from rl.a2.scenarios.demand_scenarios import SCENARIO_NAMES
from rl.a2.state_a2 import A2_STATE_DIM
from rl.a2.twin_env_a2 import TwinEnvA2


def agent_config(args):
    return {
        'agent': {
            'gamma': 0.95,
            'learning_rate': args.learning_rate,
            'batch_size': args.batch_size,
            'buffer_capacity': 20000,
            'target_update_freq': 200,
            'hidden_layers': [64, 64],
            'epsilon_start': 1.0,
            'epsilon_end': 0.05,
            'epsilon_decay': args.epsilon_decay,
            'use_double': True,
            'use_dueling': True,
            'device': 'cpu',
        }
    }


def set_global_seed(seed):
    """Seed Python, NumPy, and Torch for reproducible agent initialization."""
    import random
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def parse_z_steps(text):
    z_steps = tuple(int(z.strip()) for z in str(text).split(',') if z.strip())
    if not z_steps:
        raise ValueError('--stale-z must contain at least one integer')
    if any(z < 0 for z in z_steps):
        raise ValueError('--stale-z values must be >= 0')
    return z_steps


def _scenario_opts(scenarios, seed):
    """Pick one named scenario deterministically for this seed."""
    if not scenarios:
        return None
    return {'scenario': scenarios[int(seed) % len(scenarios)]}


def eval_policy(env, policy_fn, seeds, scenarios=None):
    returns = []
    sats = []
    for seed in seeds:
        obs, info = env.reset(seed=seed, options=_scenario_opts(scenarios, seed))
        terminated = False
        truncated = False
        total_return = 0.0
        total_sat = 0.0
        while not (terminated or truncated):
            action = policy_fn(env, obs, info)
            obs, reward, terminated, truncated, info = env.step(action)
            total_return += float(reward)
            total_sat += float(info.get('total_sat', 0.0))
        returns.append(total_return)
        sats.append(total_sat / max(env._t, 1))
    return float(np.mean(returns)), float(np.mean(sats))


def eval_agent(env, agent, seeds, scenarios=None):
    returns = []
    sats = []
    for seed in seeds:
        obs, info = env.reset(seed=seed, options=_scenario_opts(scenarios, seed))
        terminated = False
        truncated = False
        total_return = 0.0
        total_sat = 0.0
        while not (terminated or truncated):
            action = agent.select_action(obs, epsilon=0.0)
            obs, reward, terminated, truncated, info = env.step(action)
            total_return += float(reward)
            total_sat += float(info.get('total_sat', 0.0))
        returns.append(total_return)
        sats.append(total_sat / max(env._t, 1))
    return float(np.mean(returns)), float(np.mean(sats))


def train_episode(env, agent, seed, scenarios=None):
    obs, info = env.reset(seed=seed, options=_scenario_opts(scenarios, seed))
    terminated = False
    truncated = False
    total_return = 0.0
    steps = 0
    losses = []

    while not (terminated or truncated):
        action = agent.select_action(obs)
        next_obs, reward, terminated, truncated, info = env.step(action)

        # State includes step_progress, so this is a finite-horizon MDP.  At
        # the time limit there is no future reward to bootstrap from.
        done_for_bootstrap = bool(terminated or truncated)
        agent.remember(obs, action, reward, next_obs, done_for_bootstrap)
        loss = agent.train_step()
        if loss is not None:
            losses.append(float(loss))

        obs = next_obs
        total_return += float(reward)
        steps += 1

    agent.decay_epsilon()
    return {
        'return': total_return,
        'steps': steps,
        'loss': float(np.mean(losses)) if losses else None,
        'epsilon': float(agent.epsilon),
    }


def sidecar_path(out_path, suffix):
    root, _ext = os.path.splitext(out_path)
    return root + suffix


def write_csv(path, rows, fieldnames):
    if not rows:
        return
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print('[train-a2] csv -> %s' % path, flush=True)


def parse_args():
    ap = argparse.ArgumentParser(
        description='Train DQN on A2 static or dynamic demand.')
    ap.add_argument('--episodes', type=int, default=150)
    ap.add_argument('--seed', type=int, default=0,
                    help='agent seed for Torch/NumPy/exploration')
    ap.add_argument('--t-max', type=int, default=12)
    ap.add_argument('--n-levels', type=int, default=7)
    ap.add_argument('--eval-every', type=int, default=30)
    ap.add_argument('--val-seeds', type=int, default=8)
    ap.add_argument('--train-seed-start', type=int, default=1000)
    ap.add_argument('--val-seed-start', type=int, default=500)
    ap.add_argument('--scenarios', default=None,
                    help='comma-separated named A2 scenarios; empty keeps '
                         'the old static/dynamic generator')
    ap.add_argument('--delta-s', type=float, default=1.1)
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--dynamic', action='store_true',
                    help='enable phase-5 dynamic demand shift scenarios')
    ap.add_argument('--base-mbps', type=float, default=3.0,
                    help='always-on base Mbps per branch in dynamic mode')
    ap.add_argument('--burst-mbps', type=float, default=None,
                    help='fixed burst Mbps; default derives burst from demand')
    ap.add_argument('--batch-size', type=int, default=64)
    ap.add_argument('--learning-rate', type=float, default=1e-3)
    ap.add_argument('--epsilon-decay', type=float, default=0.97)
    ap.add_argument('--stale-z', default='0',
                    help='comma-separated demand staleness in steps, e.g. '
                         '"0,1,2,3,5"; "0" keeps the env unwrapped')
    ap.add_argument('--mask-aoi', action='store_true',
                    help='zero out AoI dimensions for no-AoI ablation')
    ap.add_argument('--out', default='docs/phase-6/artifacts/a2_train_static.json')
    ap.add_argument('--save-model', default='docs/phase-6/artifacts/a2_dqn_static.pt')
    ap.add_argument('--episode-csv',
                    help='write one row per train episode; default: <out>.episodes.csv')
    ap.add_argument('--eval-csv',
                    help='write one row per eval point; default: <out>.eval.csv')
    ap.add_argument('--plot-svg',
                    help='write train/eval SVG chart; default: <out>.svg')
    ap.add_argument('--print-every', type=int, default=1,
                    help='print every N train episodes; 0 disables per-episode prints')
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def import_agent_or_exit():
    try:
        from rl.agent.dqn_agent import DQNAgent
        return DQNAgent
    except ModuleNotFoundError as exc:
        if exc.name == 'torch':
            raise SystemExit(
                'PyTorch is missing in this Python. Run with a Python/venv that '
                'can import torch, or install torch there. Quick check:\n'
                '  $PYTHON_BIN -c "import torch, numpy; print(torch.__version__)"'
            ) from exc
        raise


def main():
    args = parse_args()
    DQNAgent = import_agent_or_exit()
    set_global_seed(args.seed)
    z_choices = parse_z_steps(args.stale_z)
    scenarios = (
        [s.strip() for s in args.scenarios.split(',') if s.strip()]
        if args.scenarios else None
    )
    if scenarios:
        unknown = [s for s in scenarios if s not in SCENARIO_NAMES]
        if unknown:
            raise SystemExit(
                'unknown scenario(s): %s\nknown: %s'
                % (', '.join(unknown), ', '.join(SCENARIO_NAMES))
            )
        print('[train-a2] scenarios: %s' % ', '.join(scenarios), flush=True)
    if args.dynamic:
        if args.out == 'docs/phase-6/artifacts/a2_train_static.json':
            args.out = 'docs/phase-6/artifacts/a2_train_dynamic.json'
        if args.save_model == 'docs/phase-6/artifacts/a2_dqn_static.pt':
            args.save_model = 'docs/phase-6/artifacts/a2_dqn_dynamic.pt'

    train_seeds = list(range(args.train_seed_start,
                             args.train_seed_start + args.episodes))
    val_seeds = list(range(args.val_seed_start,
                           args.val_seed_start + args.val_seeds))

    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    print('[train-a2] start()...', flush=True)
    runner.start()
    env_cfg = {
        'delta_s': args.delta_s,
        't_max_steps': args.t_max,
        'n_levels': args.n_levels,
        'dynamic': args.dynamic,
        'base_mbps': args.base_mbps,
    }
    if args.burst_mbps is not None:
        env_cfg['burst_mbps'] = args.burst_mbps
    env = TwinEnvA2(runner, cfg=env_cfg)
    use_wrapper = (z_choices != (0,)) or args.mask_aoi
    if use_wrapper:
        from rl.a2.staleness import StalenessWrapper

        env = StalenessWrapper(
            env,
            z_steps_choices=z_choices,
            mask_aoi_dims=args.mask_aoi,
        )
        print('[train-a2] StalenessWrapper: z_steps=%s mask_aoi=%s'
              % (list(z_choices), args.mask_aoi), flush=True)
    else:
        print('[train-a2] no StalenessWrapper (z=0, mask_aoi=False)',
              flush=True)
    agent = DQNAgent(
        state_size=A2_STATE_DIM,
        action_size=env.action_space.n,
        config=agent_config(args),
    )

    log = []
    episode_log = []
    baselines = {}
    best_agent_return = -float('inf')
    t0 = time.monotonic()
    try:
        print('[train-a2] precompute validation baselines...', flush=True)
        baseline_policies = [
            ('myopic_oracle', policy_myopic_oracle),
            ('greedy', policy_greedy),
            ('greedy_strong', policy_greedy_strong),
            ('equal', policy_equal),
            ('noop', policy_noop),
        ]
        for name, policy in baseline_policies:
            ret, sat = eval_policy(env, policy, val_seeds, scenarios)
            baselines[name] = {'return': ret, 'sat': sat}
            print('[train-a2] baseline %-6s return=%.2f sat=%.3f'
                  % (name, ret, sat), flush=True)

        for episode, seed in enumerate(train_seeds, 1):
            row = train_episode(env, agent, seed, scenarios)
            episode_row = {
                'episode': episode,
                'seed': seed,
                'epsilon': round(row['epsilon'], 6),
                'train_return': round(row['return'], 6),
                'train_loss': (
                    None if row['loss'] is None else round(row['loss'], 8)
                ),
                'steps': int(row['steps']),
            }
            episode_log.append(episode_row)
            if args.print_every and (
                    episode == 1 or episode % args.print_every == 0):
                print('[train-a2] train_ep=%3d seed=%d eps=%.3f return=%.2f '
                      'loss=%s steps=%d'
                      % (
                          episode,
                          seed,
                          row['epsilon'],
                          row['return'],
                          '-' if row['loss'] is None else '%.4f' % row['loss'],
                          row['steps'],
                      ),
                      flush=True)

            if episode % args.eval_every == 0 or episode == args.episodes:
                agent_ret, agent_sat = eval_agent(env, agent, val_seeds, scenarios)
                best_agent_return = max(best_agent_return, agent_ret)
                eval_row = {
                    'episode': episode,
                    'epsilon': round(row['epsilon'], 4),
                    'train_return': round(row['return'], 4),
                    'train_loss': (
                        None if row['loss'] is None else round(row['loss'], 6)
                    ),
                    'agent_return': round(agent_ret, 4),
                    'agent_sat': round(agent_sat, 4),
                    'myopic_oracle_return': round(
                        baselines['myopic_oracle']['return'], 4),
                    # Compatibility with early A2 logs before the baseline was
                    # named precisely.
                    'oracle_return': round(
                        baselines['myopic_oracle']['return'], 4),
                    'greedy_return': round(baselines['greedy']['return'], 4),
                    'greedy_strong_return': round(
                        baselines['greedy_strong']['return'], 4),
                    'equal_return': round(baselines['equal']['return'], 4),
                    'noop_return': round(baselines['noop']['return'], 4),
                }
                eval_row['agent_minus_greedy'] = round(
                    agent_ret - baselines['greedy']['return'], 4)
                eval_row['agent_minus_greedy_strong'] = round(
                    agent_ret - baselines['greedy_strong']['return'], 4)
                eval_row['agent_minus_myopic_oracle'] = round(
                    agent_ret - baselines['myopic_oracle']['return'], 4)
                log.append(eval_row)
                print('[train-a2] ep=%3d eps=%.3f train=%.2f loss=%s | '
                      'agent=%.2f myopic=%.2f greedy=%.2f greedy_strong=%.2f '
                      'equal=%.2f noop=%.2f gap_g=%.2f gap_gs=%.2f'
                      % (
                          episode,
                          row['epsilon'],
                          row['return'],
                          '-' if row['loss'] is None else '%.4f' % row['loss'],
                          agent_ret,
                          baselines['myopic_oracle']['return'],
                          baselines['greedy']['return'],
                          baselines['greedy_strong']['return'],
                          baselines['equal']['return'],
                          baselines['noop']['return'],
                          agent_ret - baselines['greedy']['return'],
                          agent_ret - baselines['greedy_strong']['return'],
                      ),
                      flush=True)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    artifact = {
        'args': vars(args),
        'agent_seed': args.seed,
        'stale_z_steps': list(z_choices),
        'mask_aoi': bool(args.mask_aoi),
        'state_dim': A2_STATE_DIM,
        'mode': (
            'mixed_named_scenarios_stale'
            if scenarios and use_wrapper else
            'mixed_named_scenarios'
            if scenarios else
            'stale'
            if use_wrapper else
            ('dynamic' if args.dynamic else 'static')
        ),
        'scenarios': scenarios,
        'baseline_notes': {
            'myopic_oracle': (
                'Knows current demand immediately but greedily optimizes the '
                'current step only; it is not an optimal episode oracle.'
            ),
        },
        'baselines': baselines,
        'episode_log': episode_log,
        'log': log,
        'elapsed_s': round(time.monotonic() - t0, 3),
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(artifact, f, indent=2)
        f.write('\n')

    episode_csv = args.episode_csv or sidecar_path(args.out, '.episodes.csv')
    eval_csv = args.eval_csv or sidecar_path(args.out, '.eval.csv')
    plot_svg = args.plot_svg or sidecar_path(args.out, '.svg')
    write_csv(
        episode_csv,
        episode_log,
        ['episode', 'seed', 'epsilon', 'train_return', 'train_loss', 'steps'],
    )
    write_csv(
        eval_csv,
        log,
        [
            'episode', 'epsilon', 'train_return', 'train_loss',
            'agent_return', 'agent_sat', 'myopic_oracle_return',
            'oracle_return', 'greedy_return', 'greedy_strong_return',
            'equal_return', 'noop_return', 'agent_minus_greedy',
            'agent_minus_greedy_strong', 'agent_minus_myopic_oracle',
        ],
    )
    try:
        from rl.a2.plot_train_a2 import write_reports
        write_reports(args.out, plot_svg=plot_svg,
                      episode_csv=episode_csv, eval_csv=eval_csv)
    except Exception as exc:
        print('[train-a2] plot skipped: %s' % exc, flush=True)

    try:
        agent.save(args.save_model)
    except Exception as exc:
        print('[train-a2] model save skipped: %s' % exc, flush=True)

    if not log:
        print('[train-a2] no eval row collected; lower --eval-every or increase episodes')
        return

    last = log[-1]
    agent_ret = float(last['agent_return'])
    noop_ret = float(last['noop_return'])
    equal_ret = float(last['equal_return'])
    greedy_ret = float(last['greedy_return'])
    greedy_strong_ret = float(last.get('greedy_strong_return', greedy_ret))
    myopic_ret = float(last.get('myopic_oracle_return',
                                last.get('oracle_return', greedy_ret)))
    print('\n[train-a2] === VERIFY PIPELINE ===')
    print('[train-a2] agent=%.2f vs noop=%.2f equal=%.2f greedy=%.2f '
          'greedy_strong=%.2f myopic_oracle=%.2f'
          % (agent_ret, noop_ret, equal_ret, greedy_ret, greedy_strong_ret,
             myopic_ret))
    print('[train-a2] gaps: agent-greedy=%+.2f agent-greedy_strong=%+.2f '
          'agent-myopic=%+.2f'
          % (agent_ret - greedy_ret, agent_ret - greedy_strong_ret,
             agent_ret - myopic_ret))
    if agent_ret >= noop_ret and agent_ret >= equal_ret:
        print('[train-a2] RESULT: OK, DQN beats weak baselines.')
        if args.dynamic:
            if agent_ret > greedy_ret:
                print('[train-a2] Dynamic result: DQN is above greedy.')
            else:
                print('[train-a2] Dynamic result: DQN is not above greedy yet.')
            if agent_ret > greedy_strong_ret:
                print('[train-a2] Strong-baseline result: DQN is above greedy_strong.')
            else:
                print('[train-a2] Strong-baseline result: DQN is not above greedy_strong yet.')
            print('[train-a2] myopic_oracle is current-demand greedy, not an optimal oracle.')
        elif agent_ret >= greedy_ret - 0.3:
            print('[train-a2] It is near greedy, which is the expected static-A2 ceiling.')
        else:
            print('[train-a2] It still trails greedy; acceptable for a short pipeline check.')
        if not args.dynamic:
            print('[train-a2] Next: move to dynamic demand, where greedy should weaken.')
    else:
        print('[train-a2] RESULT: WARN, DQN is below weak baselines. Debug train pipeline.')
    print('[train-a2] artifact -> %s' % args.out)


if __name__ == '__main__':
    main()

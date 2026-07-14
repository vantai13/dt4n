#!/usr/bin/env python3
"""A2 stage 4: train DQN on static-demand A2 to verify the train pipeline.

This is not meant to make DQN look dramatic against greedy. The A2 static gate
already showed greedy is near-oracle with fresh static observations. The goal is
pipeline verification: DQN should beat weak baselines and approach greedy.

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 PYTHONPATH=$PWD \
      /path/to/python-with-torch rl/a2/train_a2.py --episodes 150
"""

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from rl.a2.policies_a2 import policy_equal, policy_greedy, policy_noop
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


def eval_policy(env, policy_fn, seeds):
    returns = []
    sats = []
    for seed in seeds:
        obs, info = env.reset(seed=seed)
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


def eval_agent(env, agent, seeds):
    returns = []
    sats = []
    for seed in seeds:
        obs, info = env.reset(seed=seed)
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


def train_episode(env, agent, seed):
    obs, info = env.reset(seed=seed)
    terminated = False
    truncated = False
    total_return = 0.0
    steps = 0
    losses = []

    while not (terminated or truncated):
        action = agent.select_action(obs)
        next_obs, reward, terminated, truncated, info = env.step(action)

        # A2 is continuing optimization. Horizon truncation stops collection but
        # is not natural termination, so keep bootstrapping through time limits.
        agent.remember(obs, action, reward, next_obs, terminated)
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


def parse_args():
    ap = argparse.ArgumentParser(
        description='Train DQN on A2 static demand as a pipeline check.')
    ap.add_argument('--episodes', type=int, default=150)
    ap.add_argument('--t-max', type=int, default=8)
    ap.add_argument('--eval-every', type=int, default=30)
    ap.add_argument('--val-seeds', type=int, default=8)
    ap.add_argument('--train-seed-start', type=int, default=1000)
    ap.add_argument('--val-seed-start', type=int, default=500)
    ap.add_argument('--delta-s', type=float, default=1.8)
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--batch-size', type=int, default=64)
    ap.add_argument('--learning-rate', type=float, default=1e-3)
    ap.add_argument('--epsilon-decay', type=float, default=0.97)
    ap.add_argument('--out', default='docs/phase-6/artifacts/a2_train_static.json')
    ap.add_argument('--save-model', default='docs/phase-6/artifacts/a2_dqn_static.pt')
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

    train_seeds = list(range(args.train_seed_start,
                             args.train_seed_start + args.episodes))
    val_seeds = list(range(args.val_seed_start,
                           args.val_seed_start + args.val_seeds))

    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    print('[train-a2] start()...', flush=True)
    runner.start()
    env = TwinEnvA2(
        runner,
        cfg={'delta_s': args.delta_s, 't_max_steps': args.t_max},
    )
    agent = DQNAgent(
        state_size=A2_STATE_DIM,
        action_size=env.action_space.n,
        config=agent_config(args),
    )

    log = []
    baselines = {}
    best_agent_return = -float('inf')
    t0 = time.monotonic()
    try:
        print('[train-a2] precompute validation baselines...', flush=True)
        for name, policy in (
            ('greedy', policy_greedy),
            ('equal', policy_equal),
            ('noop', policy_noop),
        ):
            ret, sat = eval_policy(env, policy, val_seeds)
            baselines[name] = {'return': ret, 'sat': sat}
            print('[train-a2] baseline %-6s return=%.2f sat=%.3f'
                  % (name, ret, sat), flush=True)

        for episode, seed in enumerate(train_seeds, 1):
            row = train_episode(env, agent, seed)

            if episode % args.eval_every == 0 or episode == args.episodes:
                agent_ret, agent_sat = eval_agent(env, agent, val_seeds)
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
                    'greedy_return': round(baselines['greedy']['return'], 4),
                    'equal_return': round(baselines['equal']['return'], 4),
                    'noop_return': round(baselines['noop']['return'], 4),
                }
                log.append(eval_row)
                print('[train-a2] ep=%3d eps=%.3f train=%.2f loss=%s | '
                      'agent=%.2f greedy=%.2f equal=%.2f noop=%.2f'
                      % (
                          episode,
                          row['epsilon'],
                          row['return'],
                          '-' if row['loss'] is None else '%.4f' % row['loss'],
                          agent_ret,
                          baselines['greedy']['return'],
                          baselines['equal']['return'],
                          baselines['noop']['return'],
                      ),
                      flush=True)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    artifact = {
        'args': vars(args),
        'baselines': baselines,
        'log': log,
        'elapsed_s': round(time.monotonic() - t0, 3),
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(artifact, f, indent=2)
        f.write('\n')

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
    print('\n[train-a2] === VERIFY PIPELINE ===')
    print('[train-a2] agent=%.2f vs noop=%.2f equal=%.2f greedy=%.2f'
          % (agent_ret, noop_ret, equal_ret, greedy_ret))
    if agent_ret >= noop_ret and agent_ret >= equal_ret:
        print('[train-a2] RESULT: OK, DQN beats weak baselines.')
        if agent_ret >= greedy_ret - 0.3:
            print('[train-a2] It is near greedy, which is the expected static-A2 ceiling.')
        else:
            print('[train-a2] It still trails greedy; acceptable for a short pipeline check.')
        print('[train-a2] Next: move to dynamic demand, where greedy should weaken.')
    else:
        print('[train-a2] RESULT: WARN, DQN is below weak baselines. Debug train pipeline.')
    print('[train-a2] artifact -> %s' % args.out)


if __name__ == '__main__':
    main()

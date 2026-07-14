#!/usr/bin/env python3
"""One-seed TwinEnv training trial.

This is a practical wrapper around the Phase 6 training loop:
  - start EnvRunner + TwinEnv
  - train one DQN seed
  - plot train curves
  - optionally compare the trained agent with the three Lesson 6.2 baselines

It is intentionally a trial harness, not the final RQ1 runner. Keep heldout
seeds untouched for the final experiment; use VAL here while debugging.
"""

import argparse
import json
import os
import time

import numpy as np
import yaml

from mininet.env_runner import EnvRunner
from mininet.topology_meta import load_spec
from rl.agent.dqn_agent import DQNAgent
from rl.baselines import NoOpPolicy, RandomPolicy, RuleBasedPolicy
from rl.eval import eval_policy, load_seeds, summarize, write_csv
from rl.plot_run import plot as plot_train_log
from rl.train import train
from rl.twin_env import TwinEnv


def parse_args():
    p = argparse.ArgumentParser(description='Train one DQN seed on TwinEnv')
    p.add_argument('--smoke', action='store_true',
                   help='short run for timing and integration checks')
    p.add_argument('--episodes', type=int, default=None)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--warmup', type=int, default=None)
    p.add_argument('--eval-every', type=int, default=None)
    p.add_argument('--ckpt-every', type=int, default=None)
    p.add_argument('--val-count', type=int, default=None,
                   help='number of VAL seeds to use during trial eval')
    p.add_argument('--skip-baselines', action='store_true')
    p.add_argument('--log-dir', default=None)
    p.add_argument('--env-config', default='rl/configs/env_v1.yaml')
    p.add_argument('--agent-config', default='rl/configs/agent_v1.yaml')
    p.add_argument('--train-config', default='rl/configs/train_v1.yaml')
    p.add_argument('--eval-config', default='rl/configs/eval_v1.yaml')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--mininet-log-level', default='warning')
    return p.parse_args()


def _load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _seed_everything(seed):
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except Exception:
        pass


def _env_cfg(env_yaml):
    timing = env_yaml.get('timing', {})
    return {
        'delta_s': float(timing.get('delta_s', 1.8)),
        't_max_steps': int(timing.get('t_max_steps', 15)),
    }


def _runner_kwargs(env_yaml, mininet_log_level):
    timing = env_yaml.get('timing', {})
    budget = env_yaml.get('budget', {})
    return {
        'sync_period': float(timing.get('period_s', 0.5)),
        'hard_every': int(budget.get('hard_every', 20)),
        'mininet_log_level': mininet_log_level,
    }


def _trial_configs(args):
    env_yaml = _load_yaml(args.env_config)
    agent_cfg = _load_yaml(args.agent_config)
    train_cfg = _load_yaml(args.train_config)
    eval_cfg = _load_yaml(args.eval_config)

    tcfg = dict(train_cfg.get('train', {}))
    if args.smoke:
        tcfg['n_episodes'] = args.episodes if args.episodes is not None else 10
        tcfg['warmup_steps'] = args.warmup if args.warmup is not None else 20
        tcfg['eval_every'] = args.eval_every if args.eval_every is not None else 5
        tcfg['ckpt_every'] = args.ckpt_every if args.ckpt_every is not None else 5
        val_count = args.val_count if args.val_count is not None else 2
    else:
        if args.episodes is not None:
            tcfg['n_episodes'] = args.episodes
        if args.warmup is not None:
            tcfg['warmup_steps'] = args.warmup
        if args.eval_every is not None:
            tcfg['eval_every'] = args.eval_every
        if args.ckpt_every is not None:
            tcfg['ckpt_every'] = args.ckpt_every
        val_count = args.val_count if args.val_count is not None else 5

    if args.log_dir is not None:
        tcfg['log_dir'] = args.log_dir

    cfg = {
        'train': tcfg,
        'agent': agent_cfg['agent'],
    }

    train_seeds = load_seeds(eval_cfg['seeds']['train'])
    val_seeds = load_seeds(eval_cfg['seeds']['val'])[:val_count]
    return env_yaml, cfg, eval_cfg, train_seeds, val_seeds


def _make_agent(env, cfg):
    state_size = int(env.observation_space.shape[0])
    action_size = int(env.action_space.n)
    return DQNAgent(state_size=state_size, action_size=action_size, config=cfg)


def _write_eval_summary(run_dir, summaries):
    path = os.path.join(run_dir, 'baseline_summary.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('Da luu baseline summary:', path, flush=True)


def _compare_baselines(agent, env, val_seeds, t_max, run_dir, action_size):
    policies = {
        'agent_best': agent,
        'noop': NoOpPolicy(action_size=action_size),
        'random': RandomPolicy(action_size=action_size, seed=123),
        'rule_based': RuleBasedPolicy(),
    }
    summaries = {}
    print('\n== VAL baseline comparison ==', flush=True)
    for name, policy in policies.items():
        rows = eval_policy(policy, env, val_seeds, t_max=t_max, epsilon=0.0)
        write_csv(rows, os.path.join(run_dir, 'eval_%s.csv' % name))
        summary = summarize(rows)
        summaries[name] = summary
        print(
            '%-10s return=%7.3f throughput=%5.3f rec_time=%5.2f '
            'interv=%5.2f fail=%4.0f%%'
            % (
                name,
                summary['return_mean'],
                summary['mean_throughput_mean'],
                summary['recovery_time_mean'],
                summary['n_interventions_mean'],
                100.0 * summary['fail_rate'],
            ),
            flush=True,
        )
    _write_eval_summary(run_dir, summaries)


def main():
    args = parse_args()
    _seed_everything(args.seed)

    env_yaml, cfg, eval_cfg, train_seeds, val_seeds = _trial_configs(args)
    env_cfg = _env_cfg(env_yaml)
    runner_kwargs = _runner_kwargs(env_yaml, args.mininet_log_level)
    config_paths = (
        args.env_config,
        args.agent_config,
        args.train_config,
        args.eval_config,
    )

    print('== Trial config ==', flush=True)
    print('seed=%d episodes=%d warmup=%d val_count=%d smoke=%s'
          % (args.seed, cfg['train']['n_episodes'],
             cfg['train']['warmup_steps'], len(val_seeds), args.smoke),
          flush=True)
    print('env delta_s=%.2f t_max=%d sync_period=%.2f'
          % (env_cfg['delta_s'], env_cfg['t_max_steps'],
             runner_kwargs['sync_period']),
          flush=True)

    spec = load_spec(args.spec)
    runner = EnvRunner(spec_path=args.spec, **runner_kwargs)

    t0 = time.monotonic()
    print('[trial] starting EnvRunner...', flush=True)
    runner.start()
    try:
        env = TwinEnv(runner, spec, cfg=env_cfg)
        agent = _make_agent(env, cfg)

        run_dir, best_val = train(
            agent,
            env,
            cfg,
            train_seeds=train_seeds,
            val_seeds=val_seeds,
            seed=args.seed,
            config_paths=config_paths,
        )
        elapsed = time.monotonic() - t0
        log_path = os.path.join(run_dir, 'train_log.csv')
        print('Thoi gian trial: %.1fs (%.1f phut)' % (elapsed, elapsed / 60.0),
              flush=True)

        try:
            plot_train_log(log_path)
        except Exception as exc:
            print('WARN: khong ve duoc plot: %s' % exc, flush=True)

        best_path = os.path.join(run_dir, 'checkpoints', 'best.pt')
        if os.path.exists(best_path):
            agent.load(best_path)
            print('Da load checkpoint tot nhat:', best_path, flush=True)
        else:
            print('Chua co best.pt; dung agent cuoi cung de eval.', flush=True)

        if not args.smoke and not args.skip_baselines:
            _compare_baselines(
                agent,
                env,
                val_seeds=val_seeds,
                t_max=env_cfg['t_max_steps'],
                run_dir=run_dir,
                action_size=int(env.action_space.n),
            )

        print('\nXONG trial. Run dir: %s best_val=%.3f' % (run_dir, best_val),
              flush=True)
        return 0
    finally:
        print('[trial] closing EnvRunner...', flush=True)
        runner.close()


if __name__ == '__main__':
    raise SystemExit(main())

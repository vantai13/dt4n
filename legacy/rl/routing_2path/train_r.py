#!/usr/bin/env python3
"""Minimal RouteEnv training loop for Phase 9.

Principles:
  1. Same seed -> same result.
  2. Every run has identity: git hash + config hash + agent seed.
  3. Training uses randomized z so AoI dimensions stay informative.
"""

import argparse
import csv
import hashlib
import json
import os
import random
import subprocess
import sys
import time

import numpy as np
import torch
import yaml

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.baselines import ecmp_static, ospf_calibrated, random_valid
from rl.routing_2path.metrics_r import EpisodeStats, SAFE_HOP, run_episode
from rl.routing_2path.metrics_r import summarize_episode_stats
from rl.routing_2path.oracles import clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.topology_r import (
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    LOAD_CFG_DYNAMIC,
    LOAD_CFG_TRAIN,
    LOAD_CFG_V1,
    LOAD_PRESETS,
    SCENARIOS_TRAIN,
    TOPO,
)


NOISE_FLOOR = 0.04


def set_global_seed(seed):
    """Seed Python, NumPy, Torch, and CuDNN determinism knobs.

    Call before constructing ``DQNAgent`` because network initialization
    consumes Torch RNG in ``QNetwork.__init__``.
    """
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def git_hash():
    """Return short git hash, suffixed with ``-dirty`` for any local changes."""
    try:
        h = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return f'{h}-dirty' if status else h
    except Exception:
        return 'nogit'


def config_hash(cfg):
    """Stable hash for a config dictionary."""
    blob = json.dumps(cfg, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:7]


def file_sha256(path):
    """Return sha256 for a local file."""
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read_text_or_none(path):
    """Read a small text file if present."""
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read().strip()
    except OSError:
        return None


def make_run_dir(cfg, seed, root='results/train'):
    run_id = f'r_seed{int(seed)}_{git_hash()}_{config_hash(cfg)}'
    path = os.path.join(root, run_id)
    os.makedirs(path, exist_ok=True)
    return path, run_id


def _load_cfg(cfg):
    value = cfg['env']['load_cfg']
    if isinstance(value, dict):
        return value
    if value == 'LOAD_CFG_TRAIN':
        return LOAD_CFG_TRAIN
    if value == 'LOAD_CFG_V1':
        return LOAD_CFG_V1
    if value == 'LOAD_CFG_ABLATION':
        return LOAD_CFG_ABLATION
    if value == 'LOAD_CFG_DYNAMIC':
        return LOAD_CFG_DYNAMIC
    if value == 'LOAD_CFG_ASYM':
        return LOAD_CFG_ASYM
    if value == 'SCENARIOS_TRAIN':
        # Independent-congestion training mix. RouteEnv picks one named
        # scenario per episode from topology_r.SCENARIOS_TRAIN.
        return {
            'scenarios': SCENARIOS_TRAIN,
            'scenario_mix': tuple(SCENARIOS_TRAIN),
        }
    return LOAD_PRESETS[value]


def make_train_env(cfg, seed):
    """Training env: z is chosen deterministically from each episode seed."""
    base = RouteEnv(
        TOPO,
        load_cfg=_load_cfg(cfg),
        max_steps=cfg['env']['max_steps'],
        seed=seed,
    )
    return StalenessWrapper(
        base,
        z_steps_choices=tuple(cfg['train']['z_steps_choices']),
        mask_aoi_dims=bool(cfg['train'].get('mask_aoi', False)),
    )


def make_eval_env(cfg, seed, z):
    """Evaluation env: z is fixed for paired comparison."""
    base = RouteEnv(
        TOPO,
        load_cfg=_load_cfg(cfg),
        max_steps=cfg['env']['max_steps'],
        seed=seed,
    )
    return StalenessWrapper(
        base,
        z_steps_choices=(int(z),),
        mask_aoi_dims=bool(cfg['train'].get('mask_aoi', False)),
    )


def _valid_action(info, action):
    valid = np.flatnonzero(info['valid_mask'])
    if len(valid) == 0:
        return 0
    action = int(action)
    return action if action in set(valid.tolist()) else int(valid[0])


def train_episode(env, agent, seed, warmup_steps=0):
    """Run one training episode and return summary scalars."""
    obs, info = env.reset(seed=seed)
    total, steps, losses = 0.0, 0, []
    terminated = truncated = False

    while not (terminated or truncated):
        action = agent.select_action(obs, valid_mask=info['valid_mask'])
        next_obs, reward, terminated, truncated, next_info = env.step(action)

        # State includes hop_progress, so this is an explicit finite-horizon MDP.
        # At timeout there is no future reward inside this task definition.
        done_for_bootstrap = bool(terminated or truncated)
        agent.remember(
            obs,
            action,
            reward,
            next_obs,
            done_for_bootstrap,
            next_info['valid_mask'],
        )

        if len(agent.buffer) >= max(int(warmup_steps), agent.batch_size):
            loss = agent.train_step()
            if loss is not None:
                losses.append(float(loss))

        obs, info = next_obs, next_info
        total += float(reward)
        steps += 1

    return {
        'return': float(total),
        'steps': int(steps),
        'loss': float(np.mean(losses)) if losses else None,
        'z_steps': int(info.get('z_steps', 0)),
    }


def run_agent_episode(env, agent, seed, target_fn=None):
    """Evaluate the DQN agent while using the current observation directly."""
    obs, info = env.reset(seed=seed)
    stats = EpisodeStats(path=[info['current_node']])

    for _ in range(env.max_steps + 1):
        node = info['current_node']
        valid = np.flatnonzero(info['valid_mask'])
        n_valid = len(valid)
        action = agent.select_action(obs, epsilon=0.0, valid_mask=info['valid_mask'])
        action = _valid_action(info, action)

        if target_fn is not None and n_valid > 1:
            best = _valid_action(info, target_fn(env, info))
            stats.decisions += 1
            stats.wrong += int(action != best)

        neighbors = env.adj[node]
        if n_valid > 1 and SAFE_HOP in neighbors:
            stats.safe_opportunities += 1
            stats.safe_choices += int(neighbors[action] == SAFE_HOP)

        stats.aoi_samples.append(float(info.get('aoi_measured_s', 0.0)))
        stats.stale_steps += int(bool(info.get('util_is_stale', False)))

        obs, reward, terminated, truncated, info = env.step(action)
        stats.total_reward += float(reward)
        stats.steps += 1
        stats.path.append(info['current_node'])

        if terminated or truncated:
            stats.arrived = bool(info.get('arrived', False))
            stats.truncated = bool(truncated)
            break

    return stats


def eval_agent(cfg, agent, seeds, z=0):
    """Greedy eval at fixed z over fixed seeds."""
    rows = []
    for seed in seeds:
        env = make_eval_env(cfg, seed, z)
        rows.append(
            run_agent_episode(
                env,
                agent,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows)


def eval_baselines(cfg, seeds, z=0):
    """Evaluate non-learning policies on the same paired seeds."""
    out = {}
    for name, fn in [
        ('clairvoyant', clairvoyant_dijkstra),
        ('ospf_calibrated', ospf_calibrated),
        ('ecmp', ecmp_static),
        ('random_valid', random_valid),
    ]:
        rows = []
        for seed in seeds:
            env = make_eval_env(cfg, seed, z)
            rows.append(
                run_episode(
                    env,
                    fn,
                    seed=seed,
                    target_fn=posthoc_dijkstra,
                ).as_dict()
            )
        out[name] = summarize_episode_stats(rows)
    return out


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='rl/routing/configs/train_r_v1.yaml')
    parser.add_argument('--seed', type=int, default=0,
                        help='agent seed for Torch/NumPy/Python/exploration')
    parser.add_argument('--episodes', type=int, default=None,
                        help='override config train.episodes for pilots')
    parser.add_argument('--out-root', default='results/train')
    parser.add_argument('--print-every', type=int, default=10)
    return parser.parse_args(argv)


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    args = parse_args(argv)
    set_global_seed(args.seed)

    with open(args.config, encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)
    if args.episodes is not None:
        cfg['train']['episodes'] = int(args.episodes)

    run_dir, run_id = make_run_dir(cfg, args.seed, args.out_root)
    print(f'[train-r] run_id = {run_id}', flush=True)
    print(f'[train-r] dir    = {run_dir}', flush=True)
    if 'dirty' in run_id:
        print('[train-r] WARNING: working tree is dirty; run is marked dirty.',
              flush=True)

    seed_cfg = cfg['seeds']
    train_base = (
        int(seed_cfg['train_seed_start'])
        + int(args.seed) * int(seed_cfg['train_seed_stride'])
    )
    train_seeds = list(range(train_base, train_base + int(cfg['train']['episodes'])))
    val_seeds = list(range(
        int(seed_cfg['val_seed_start']),
        int(seed_cfg['val_seed_start']) + int(seed_cfg['val_seeds']),
    ))

    print(f'[train-r] agent_seed={args.seed} train_seeds[:3]={train_seeds[:3]}',
          flush=True)
    print(f'[train-r] val_seeds[:3]={val_seeds[:3]} fixed for all agents',
          flush=True)
    print(f'[train-r] z_choices={cfg["train"]["z_steps_choices"]} '
          f'mask_aoi={cfg["train"].get("mask_aoi", False)}',
          flush=True)

    t0 = time.time()
    agent = DQNAgent(R_STATE_DIM, 2, cfg)
    env = make_train_env(cfg, seed=args.seed)

    baseline_start = eval_baselines(cfg, val_seeds, z=0)
    print('[train-r] baseline(start): ' + '  '.join(
        f'{name}={row["return"]:.3f}'
        for name, row in baseline_start.items()
    ), flush=True)

    episode_rows, eval_rows, epsilon_trace = [], [], []
    last_eval = None
    eval_every = int(cfg['train']['eval_every'])
    warmup_steps = int(cfg['train'].get('warmup_steps', 0))
    print_every = max(int(args.print_every), 1)

    for idx, seed in enumerate(train_seeds, 1):
        epsilon_trace.append(float(agent.epsilon))
        row = train_episode(env, agent, seed, warmup_steps=warmup_steps)
        agent.decay_epsilon()

        episode_rows.append({
            'episode': idx,
            'seed': seed,
            'epsilon': round(epsilon_trace[-1], 8),
            'train_return': round(row['return'], 8),
            'train_loss': None if row['loss'] is None else round(row['loss'], 8),
            'steps': row['steps'],
            'z_steps': row['z_steps'],
        })

        if idx % eval_every == 0:
            ev = eval_agent(cfg, agent, val_seeds, z=0)
            ev['episode'] = idx
            eval_rows.append(ev)
            last_eval = ev

        if idx % print_every == 0 or idx == len(train_seeds):
            recent10 = [r['train_return'] for r in episode_rows[-10:]]
            recent25 = [r['train_return'] for r in episode_rows[-25:]]
            loss = row['loss']
            loss_str = 'n/a' if loss is None else f'{loss:.4f}'
            if last_eval is None:
                val_str = 'val_ret=n/a arrived=n/a'
            else:
                val_str = (
                    f'val_ret={last_eval["return"]:.3f}'
                    f'@{last_eval["episode"]} '
                    f'arrived={last_eval["arrived"]:.2f}'
                )
            print(
                f'  ep {idx:>4}/{len(train_seeds):<4} '
                f'eps={agent.epsilon:.3f} '
                f'train10={np.mean(recent10):.3f} '
                f'train25={np.mean(recent25):.3f} '
                f'loss={loss_str} z={row["z_steps"]} {val_str}',
                flush=True,
            )

    if not eval_rows:
        ev = eval_agent(cfg, agent, val_seeds, z=0)
        ev['episode'] = len(train_seeds)
        eval_rows.append(ev)

    baseline_end = eval_baselines(cfg, val_seeds, z=0)
    drift = {
        name: abs(baseline_end[name]['return'] - baseline_start[name]['return'])
        for name in baseline_start
    }
    max_drift = max(drift.values()) if drift else 0.0
    print('[train-r] baseline(end) drift: ' + '  '.join(
        f'{name}={value:.4f}' for name, value in drift.items()
    ), flush=True)
    if max_drift > NOISE_FLOOR:
        print(f'[train-r] WARNING: drift {max_drift:.4f} > {NOISE_FLOOR}',
              flush=True)
    else:
        print(f'[train-r] drift {max_drift:.4f} <= {NOISE_FLOOR}', flush=True)

    agent.save(os.path.join(run_dir, 'model.pt'))
    payload = {
        'run_id': run_id,
        'git_hash': git_hash(),
        'config_hash': config_hash(cfg),
        'agent_seed': int(args.seed),
        'train_seeds': [train_seeds[0], train_seeds[-1]] if train_seeds else [],
        'val_seeds': val_seeds,
        'state_dim': R_STATE_DIM,
        'action_dim': 2,
        'config_version': cfg.get('version'),
        'link_model_sha256': file_sha256('rl/routing/link_model.py'),
        'link_model_version': read_text_or_none(
            'frozen_policies/v1/link_model_version.txt'
        ),
        'z_steps_choices': cfg['train']['z_steps_choices'],
        'mask_aoi': bool(cfg['train'].get('mask_aoi', False)),
        'config': cfg,
        'baseline_start': baseline_start,
        'baseline_end': baseline_end,
        'baseline_drift': drift,
        'noise_floor': NOISE_FLOOR,
        'epsilon_trace_head': epsilon_trace[:20],
        'wall_time_s': time.time() - t0,
    }
    with open(os.path.join(run_dir, 'train.json'), 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)

    _write_csv(os.path.join(run_dir, 'episodes.csv'), episode_rows)
    _write_csv(os.path.join(run_dir, 'eval.csv'), eval_rows)
    print(f'[train-r] done in {time.time() - t0:.1f}s -> {run_dir}', flush=True)


if __name__ == '__main__':
    main()

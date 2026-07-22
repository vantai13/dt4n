#!/usr/bin/env python3
"""Train one debug policy and report whether the avg-return curve has flattened."""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from collections import deque
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.state_r import R_STATE_DIM
from rl.routing.topology_r import (
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
)


def set_seed(seed: int) -> None:
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def parse_hidden_layers(value: str) -> list[int]:
    return [int(x.strip()) for x in str(value).split(',') if x.strip()]


def build_agent_config(hidden_layers: list[int]) -> dict:
    return {
        'version': 'check_convergence',
        'agent': {
            'hidden_layers': list(hidden_layers),
            'device': 'cpu',
            'use_double': True,
            'use_dueling': True,
            'exploration': 'epsilon_greedy',
            'gamma': 0.95,
            'learning_rate': 0.001,
            'batch_size': 64,
            'buffer_capacity': 20000,
            'target_update_freq': 200,
            'epsilon_start': 1.0,
            'epsilon_end': 0.05,
            'epsilon_decay': 0.995,
            'temp_start': 2.0,
            'temp_end': 0.1,
            'temp_decay': 0.9985,
        },
    }


def build_load_cfg(kind: str) -> dict:
    if kind == 'dynamic':
        return {
            'scenarios': SCENARIOS_DYNAMIC,
            'scenario_mix': tuple(SCENARIOS_DYNAMIC),
        }
    if kind == 'static':
        return {
            'scenarios': SCENARIOS_TRAIN,
            'scenario_mix': tuple(SCENARIOS_TRAIN),
        }
    if kind == 'asym':
        return LOAD_CFG_ASYM
    return LOAD_CFG_ABLATION


def write_curve(path: str | None, rows: list[dict]) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        'episode',
        'epsilon',
        'return',
        'avg50',
        'loss',
        'steps',
        'z_steps',
        'arrived',
    ]
    with open(out, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'[CSV] wrote {out}', flush=True)


def convergence_slope(curve: list[tuple[int, float]]) -> tuple[float, float, float]:
    """Compare early-vs-late avg50 values inside the second half of training."""
    if len(curve) < 6:
        values = np.array([avg for _ep, avg in curve], dtype=float)
        mean = float(values.mean()) if len(values) else 0.0
        return mean, mean, 0.0

    half = curve[len(curve) // 2:]
    chunk = max(1, len(half) // 3)
    early = float(np.mean([avg for _ep, avg in half[:chunk]]))
    late = float(np.mean([avg for _ep, avg in half[-chunk:]]))
    return early, late, late - early


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--episodes', type=int, default=2000)
    parser.add_argument('--scenario', choices=['dynamic', 'static', 'mix', 'asym'],
                        default='dynamic')
    parser.add_argument('--mask-aoi', '--mask_aoi', action='store_true',
                        dest='mask_aoi')
    parser.add_argument('--z-max', '--z_max', type=int, default=6,
                        dest='z_max')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    parser.add_argument('--warmup-steps', '--warmup_steps', type=int,
                        default=500, dest='warmup_steps')
    parser.add_argument('--print-every', '--print_every', type=int, default=50,
                        dest='print_every')
    parser.add_argument('--flat-threshold', '--flat_threshold', type=float,
                        default=0.02, dest='flat_threshold')
    parser.add_argument('--hidden-layers', default='64,32')
    parser.add_argument('--out', default=None)
    parser.add_argument('--curve-out', '--curve_out', default=None,
                        dest='curve_out')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    set_seed(args.seed)

    hidden_layers = parse_hidden_layers(args.hidden_layers)
    cfg = build_agent_config(hidden_layers)
    load_cfg = build_load_cfg(args.scenario)
    z_choices = tuple(range(0, int(args.z_max) + 1))
    branch = 'mask' if args.mask_aoi else 'aoi'

    out = args.out
    if out is None:
        out = f'frozen_policies/debug/{branch}_conv_s{args.seed}.pt'
    curve_out = args.curve_out
    if curve_out is None:
        curve_out = f'results/debug/convergence_{branch}_s{args.seed}.csv'

    base = RouteEnv(
        TOPO,
        load_cfg=load_cfg,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    env = StalenessWrapper(
        base,
        z_steps_choices=z_choices,
        mask_aoi_dims=args.mask_aoi,
    )
    agent = DQNAgent(R_STATE_DIM, env.action_space.n, cfg)

    window = deque(maxlen=50)
    rows = []
    curve = []
    print(
        f"{'ep':>6} {'return':>9} {'avg50':>9} {'eps':>7} "
        f"{'loss':>9} {'steps':>6} {'z':>3} {'arrived':>7}",
        flush=True,
    )

    print_every = max(1, int(args.print_every))
    for ep in range(1, int(args.episodes) + 1):
        obs, info = env.reset(seed=args.seed * 100000 + ep)
        terminated = truncated = False
        ep_return = 0.0
        losses = []
        steps = 0

        while not (terminated or truncated):
            action = agent.select_action(obs, valid_mask=info['valid_mask'])
            next_obs, reward, terminated, truncated, next_info = env.step(action)
            done = bool(terminated or truncated)
            agent.remember(
                obs,
                action,
                reward,
                next_obs,
                done,
                next_info['valid_mask'],
            )
            if len(agent.buffer) >= max(int(args.warmup_steps), agent.batch_size):
                loss = agent.train_step()
                if loss is not None:
                    losses.append(float(loss))

            obs, info = next_obs, next_info
            ep_return += float(reward)
            steps += 1

        agent.decay_epsilon()
        window.append(ep_return)
        avg50 = float(np.mean(window))
        mean_loss = float(np.mean(losses)) if losses else float('nan')
        row = {
            'episode': ep,
            'epsilon': round(float(agent.epsilon), 8),
            'return': round(float(ep_return), 8),
            'avg50': round(avg50, 8),
            'loss': None if np.isnan(mean_loss) else round(mean_loss, 8),
            'steps': int(steps),
            'z_steps': int(info.get('z_steps', 0)),
            'arrived': bool(info.get('arrived', False)),
        }
        rows.append(row)
        curve.append((ep, avg50))

        if ep <= 5 or ep % print_every == 0 or ep == int(args.episodes):
            loss_str = 'n/a' if np.isnan(mean_loss) else f'{mean_loss:.4f}'
            print(
                f'{ep:6d} {ep_return:9.3f} {avg50:9.3f} '
                f'{agent.epsilon:7.3f} {loss_str:>9} {steps:6d} '
                f'{int(info.get("z_steps", 0)):3d} '
                f'{str(bool(info.get("arrived", False))):>7}',
                flush=True,
            )

    early, late, slope = convergence_slope(curve)
    print('\n--- CONVERGENCE CHECK ---', flush=True)
    print(f'avg50 early second-half = {early:.4f}', flush=True)
    print(f'avg50 late second-half  = {late:.4f}', flush=True)
    print(f'slope late-early        = {slope:+.4f}', flush=True)
    if abs(slope) < float(args.flat_threshold):
        print(f'VERDICT: flat enough (|slope| < {args.flat_threshold})', flush=True)
    else:
        print(f'VERDICT: not flat yet (|slope| >= {args.flat_threshold})', flush=True)

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    agent.save(out)
    print(f'Saved policy -> {out}', flush=True)
    write_curve(curve_out, rows)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

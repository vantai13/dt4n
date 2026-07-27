#!/usr/bin/env python3
"""Measure std_agent and cost_of_blindness on the redesigned trend scenarios."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.metrics_r import run_episode, summarize_episode_stats
from rl.routing_2path.oracles import blind_dijkstra, clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.topology_r import (
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
)
from rl.routing_2path.train_r import run_agent_episode


def parse_int_list(value: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in str(value).split(',') if x.strip())


def load_checkpoint(path: str) -> dict:
    return torch.load(path, map_location='cpu', weights_only=False)


def infer_agent_config(policy_path: str) -> dict:
    """Build the minimum DQN config needed to load a saved checkpoint."""
    ckpt = load_checkpoint(policy_path)
    state = ckpt.get('main_net_state', ckpt)
    trunk_weights = []
    for key, tensor in state.items():
        if not key.startswith('trunk.') or not key.endswith('.weight'):
            continue
        if getattr(tensor, 'ndim', 0) == 2:
            trunk_weights.append((int(key.split('.')[1]), tensor))
    hidden = [int(tensor.shape[0]) for _idx, tensor in sorted(trunk_weights)]
    if not hidden:
        raise ValueError(
            f'cannot infer hidden layers from {policy_path}; pass a standard DQN checkpoint'
        )

    flags = ckpt.get('config_flags', {})
    use_dueling = bool(flags.get('use_dueling', 'value_head.0.weight' in state))
    return {
        'version': 'measure_baseline_v2',
        'agent': {
            'hidden_layers': hidden,
            'device': 'cpu',
            'use_double': bool(flags.get('use_double', True)),
            'use_dueling': use_dueling,
            'exploration': flags.get('exploration', 'epsilon_greedy'),
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


def load_agent(policy_path: str) -> DQNAgent:
    agent = DQNAgent(R_STATE_DIM, 2, infer_agent_config(policy_path))
    agent.load(policy_path)
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


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


def make_env(load_cfg: dict, z: int, seed: int, max_steps: int,
             mask_aoi: bool = False):
    base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=max_steps, seed=seed)
    return StalenessWrapper(
        base,
        z_steps_choices=(int(z),),
        mask_aoi_dims=bool(mask_aoi),
    )


def eval_agent_return(agent, load_cfg: dict, eval_seeds: range,
                      max_steps: int, mask_aoi: bool) -> dict:
    rows = []
    for seed in eval_seeds:
        env = make_env(load_cfg, z=0, seed=seed, max_steps=max_steps,
                       mask_aoi=mask_aoi)
        rows.append(
            run_agent_episode(
                env,
                agent,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows)


def measure_std_agent(policy_paths: list[str], load_cfg: dict, eval_seeds: range,
                      max_steps: int, mask_aoi: bool) -> dict | None:
    if not policy_paths:
        print('=== std_agent ===')
        print('skipped: pass --policies to measure seed-to-seed agent noise')
        return None

    per_policy = []
    for path in policy_paths:
        agent = load_agent(path)
        stats = eval_agent_return(
            agent,
            load_cfg,
            eval_seeds,
            max_steps=max_steps,
            mask_aoi=mask_aoi,
        )
        per_policy.append({
            'policy': path,
            'return': float(stats['return']),
            'wrong_rate': float(stats['wrong_rate']),
            'arrived': float(stats['arrived']),
        })

    returns = np.array([row['return'] for row in per_policy], dtype=float)
    std = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
    mean = float(returns.mean())
    ci95 = float(1.96 * std / math.sqrt(len(returns))) if len(returns) > 1 else 0.0

    print('\n=== std_agent on redesigned load at z=0 ===')
    print('return per policy:', [round(float(x), 4) for x in returns])
    print(f'mean_return = {mean:.4f}')
    print(f'std_agent   = {std:.4f}')
    print(f'ci95        = {ci95:.4f}')
    return {
        'per_policy': per_policy,
        'mean_return': mean,
        'std_agent': std,
        'ci95': ci95,
    }


def measure_cost_of_blindness(load_cfg: dict, z_values: tuple[int, ...],
                              eval_seeds: range, max_steps: int) -> list[dict]:
    rows = []
    print('\n=== cost_of_blindness on redesigned load ===')
    print(
        f"{'z':>3} {'AoI(s)':>7} {'clair':>9} {'blind':>9} "
        f"{'CoB':>9} {'wrong_ex':>9}"
    )
    for z in z_values:
        clair_rows = []
        blind_rows = []
        for seed in eval_seeds:
            clair_env = make_env(load_cfg, z=z, seed=seed, max_steps=max_steps)
            blind_env = make_env(load_cfg, z=z, seed=seed, max_steps=max_steps)
            clair_rows.append(
                run_episode(
                    clair_env,
                    clairvoyant_dijkstra,
                    seed=seed,
                    target_fn=posthoc_dijkstra,
                ).as_dict()
            )
            blind_rows.append(
                run_episode(
                    blind_env,
                    blind_dijkstra,
                    seed=seed,
                    target_fn=posthoc_dijkstra,
                ).as_dict()
            )

        clair = summarize_episode_stats(clair_rows)
        blind = summarize_episode_stats(blind_rows)
        row = {
            'z': int(z),
            'aoi_mean_s': float(blind['aoi_mean_s']),
            'clair_return': float(clair['return']),
            'blind_return': float(blind['return']),
            'cost_of_blindness': float(clair['return'] - blind['return']),
            'wrong_excess': float(blind['wrong_rate'] - clair['wrong_rate']),
            'clair_wrong_rate': float(clair['wrong_rate']),
            'blind_wrong_rate': float(blind['wrong_rate']),
        }
        rows.append(row)
        print(
            f"{row['z']:3d} {row['aoi_mean_s']:7.2f} "
            f"{row['clair_return']:9.4f} {row['blind_return']:9.4f} "
            f"{row['cost_of_blindness']:9.4f} {row['wrong_excess']:9.4f}"
        )
    return rows


def write_baseline_csv(path: str | None, rows: list[dict]) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        'z',
        'aoi_mean_s',
        'clair_return',
        'blind_return',
        'cost_of_blindness',
        'wrong_excess',
        'clair_wrong_rate',
        'blind_wrong_rate',
    ]
    with open(out, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'[CSV] wrote {out}')


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--policies', nargs='*', default=[])
    parser.add_argument('--scenario', choices=['dynamic', 'static', 'mix', 'asym'],
                        default='dynamic')
    parser.add_argument('--eval-seeds', '--eval_seeds', type=int, default=50,
                        dest='eval_seeds')
    parser.add_argument('--eval-seed-start', '--eval_seed_start', type=int,
                        default=0, dest='eval_seed_start')
    parser.add_argument('--z-values', '--z_values', default='0,2,4,6',
                        dest='z_values')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    parser.add_argument('--mask-aoi', '--mask_aoi', action='store_true',
                        dest='mask_aoi',
                        help='evaluate supplied policies with AoI dimensions masked')
    parser.add_argument('--out', default='results/debug/baseline_v2.csv')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    load_cfg = build_load_cfg(args.scenario)
    eval_seeds = range(
        int(args.eval_seed_start),
        int(args.eval_seed_start) + int(args.eval_seeds),
    )
    z_values = parse_int_list(args.z_values)

    std = measure_std_agent(
        args.policies,
        load_cfg,
        eval_seeds,
        max_steps=args.max_steps,
        mask_aoi=args.mask_aoi,
    )
    cob_rows = measure_cost_of_blindness(
        load_cfg,
        z_values,
        eval_seeds,
        max_steps=args.max_steps,
    )
    write_baseline_csv(args.out, cob_rows)

    cob_max = max(row['cost_of_blindness'] for row in cob_rows) if cob_rows else 0.0
    print('\n=== interpretation frame ===')
    if std is None:
        print('std_agent            = skipped')
        print('VoI noise threshold  = skipped')
    else:
        threshold = 2.0 * std['std_agent']
        print(f"std_agent            = {std['std_agent']:.4f}")
        print(f'VoI noise threshold  = {threshold:.4f}  (2 x std_agent)')
    print(f'cost_of_blindness max= {cob_max:.4f}  (oracle upper-bound context)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

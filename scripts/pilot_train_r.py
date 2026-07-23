#!/usr/bin/env python3
"""[9.3] One-seed pilot for routing DQN training.

The point is manual inspection: paths, Q-spread, and whether the policy reacts
to load instead of collapsing into a static next-hop rule.
"""

import argparse
import json
import os
import sys
from collections import Counter

import numpy as np
import yaml

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.topology_r import LOAD_PRESETS, TOPO
from rl.routing_2path.oracles import posthoc_dijkstra
from rl.routing_2path.metrics_r import summarize_episode_stats
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.train_r import (
    make_eval_env,
    make_train_env,
    run_agent_episode,
    set_global_seed,
    train_episode,
)


GATE_SAFE_DELTA = 0.20
GATE_Q_SPREAD = 0.05
GATE_ARRIVED = 0.95
GATE_REVISIT = 0.05


def q_spread(agent, env, seeds=range(20)):
    """Mean Q spread on states with two valid actions."""
    spreads = []
    for seed in seeds:
        obs, info = env.reset(seed=seed)
        for _ in range(6):
            valid = np.flatnonzero(info['valid_mask'])
            if len(valid) > 1:
                q = agent.main_net.get_action_values(obs, agent.device).cpu().numpy()
                spreads.append(float(q[valid].max() - q[valid].min()))
            action = agent.select_action(obs, epsilon=0.0, valid_mask=info['valid_mask'])
            obs, _reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
    return float(np.mean(spreads)) if spreads else 0.0


def _preset_load(name):
    load = dict(LOAD_PRESETS[name])
    load.setdefault('drift_sigma', 0.15)
    return load


def eval_on_preset(agent, cfg, preset_name, seeds):
    """Evaluate the agent at z=0 on a named load preset."""
    rows = []
    for seed in seeds:
        base = RouteEnv(
            TOPO,
            load_cfg=_preset_load(preset_name),
            max_steps=cfg['env']['max_steps'],
            seed=seed,
        )
        env = StalenessWrapper(
            base,
            z_steps_choices=(0,),
            mask_aoi_dims=bool(cfg['train'].get('mask_aoi', False)),
        )
        rows.append(
            run_agent_episode(
                env,
                agent,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows), rows


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='rl/routing/configs/train_r_v1.yaml')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--episodes', type=int, default=400)
    parser.add_argument('--out', default='docs/phase-9/artifacts/pilot.json')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    with open(args.config, encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)
    cfg['train']['episodes'] = int(args.episodes)

    set_global_seed(args.seed)
    agent = DQNAgent(R_STATE_DIM, 2, cfg)
    env = make_train_env(cfg, seed=args.seed)

    seed_cfg = cfg['seeds']
    base_seed = (
        int(seed_cfg['train_seed_start'])
        + int(args.seed) * int(seed_cfg['train_seed_stride'])
    )
    train_seeds = list(range(base_seed, base_seed + int(args.episodes)))
    warmup_steps = int(cfg['train'].get('warmup_steps', 0))

    curve = []
    print('=== TRAIN: inspect one path every 50 episodes ===')
    for idx, seed in enumerate(train_seeds, 1):
        row = train_episode(env, agent, seed, warmup_steps=warmup_steps)
        agent.decay_epsilon()
        curve.append(row['return'])
        if idx % 50 == 0:
            ev_env = make_eval_env(cfg, 900, z=0)
            stats = run_agent_episode(
                ev_env,
                agent,
                seed=900,
                target_fn=posthoc_dijkstra,
            )
            print(
                f'  ep {idx:>4} eps={agent.epsilon:.3f} '
                f'ma20={np.mean(curve[-20:]):>7.3f} '
                f'path: {" -> ".join(stats.path)}',
                flush=True,
            )

    print('\n=== (1) 10 paths: read manually ===')
    paths = []
    for seed in range(900, 910):
        ev_env = make_eval_env(cfg, seed, z=0)
        stats = run_agent_episode(
            ev_env,
            agent,
            seed=seed,
            target_fn=posthoc_dijkstra,
        )
        path = tuple(stats.path)
        paths.append(path)
        revisit = len(set(path)) < len(path)
        suffix = ' <-- REVISIT' if revisit else ''
        print(
            f'  seed {seed}: {" -> ".join(path):<34} '
            f'ret={stats.total_reward:>7.3f} arrived={stats.arrived}{suffix}',
            flush=True,
        )

    path_counts = Counter(paths)
    path_unique = len(path_counts)
    print(f'\n  unique_paths={path_unique}/10 distribution={dict(path_counts)}')

    print('\n=== (2) Q-spread ===')
    spread = q_spread(agent, make_eval_env(cfg, 0, z=0))
    ok_q = spread > GATE_Q_SPREAD
    print(f'  q_spread={spread:.4f} gate>{GATE_Q_SPREAD} -> {"PASS" if ok_q else "FAIL"}')

    print('\n=== (3) safe_path_freq by load preset ===')
    safe_freq = {}
    preset_summaries = {}
    for preset in ('normal', 'borderline', 'bottleneck_E'):
        summary, _rows = eval_on_preset(agent, cfg, preset, range(900, 1000))
        preset_summaries[preset] = summary
        safe_freq[preset] = summary['safe_path_freq']
        print(
            f'  {preset:>14}: safe_path_freq={safe_freq[preset]:.4f} '
            f'return={summary["return"]:.3f}',
            flush=True,
        )
    safe_delta = safe_freq['bottleneck_E'] - safe_freq['normal']
    ok_static = safe_delta > GATE_SAFE_DELTA
    print(f'  delta={safe_delta:.4f} gate>{GATE_SAFE_DELTA} -> {"PASS" if ok_static else "FAIL"}')

    bottleneck_summary, bottleneck_rows = eval_on_preset(
        agent,
        cfg,
        'bottleneck_E',
        range(900, 1000),
    )
    arrived_rate = bottleneck_summary['arrived']
    revisit_rate = float(np.mean([
        len(set(row['path'])) < len(row['path'])
        for row in bottleneck_rows
    ]))
    ok_arrived = arrived_rate > GATE_ARRIVED
    ok_revisit = revisit_rate < GATE_REVISIT

    print('\n=== Auxiliary gates ===')
    print(f'  arrived_rate={arrived_rate:.4f} gate>{GATE_ARRIVED} -> {"PASS" if ok_arrived else "FAIL"}')
    print(f'  revisit_rate={revisit_rate:.4f} gate<{GATE_REVISIT} -> {"PASS" if ok_revisit else "FAIL"}')

    go = ok_q and ok_static and ok_arrived and ok_revisit and path_unique > 1
    verdict = 'GO' if go else 'NO-GO'
    print(f'\n{"=" * 56}\n  VERDICT: {verdict}\n{"=" * 56}')

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump({
            'agent_seed': int(args.seed),
            'episodes': int(args.episodes),
            'curve_ma20_last': float(np.mean(curve[-20:])) if curve else None,
            'paths_sample': [list(path) for path in paths],
            'path_unique': path_unique,
            'q_spread': spread,
            'safe_path_freq': safe_freq,
            'safe_delta': safe_delta,
            'arrived_rate': arrived_rate,
            'revisit_rate': revisit_rate,
            'gates': {
                'q_spread': ok_q,
                'static_policy': ok_static,
                'arrived': ok_arrived,
                'revisit': ok_revisit,
                'path_unique': path_unique > 1,
            },
            'verdict': verdict,
            'preset_summaries': preset_summaries,
        }, fh, indent=2)
    print(f'-> {args.out}')


if __name__ == '__main__':
    main()

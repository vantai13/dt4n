#!/usr/bin/env python3
"""[9.4] Analyze five routing DQN seeds: behavior gates and std_agent."""

import argparse
import glob
import json
import os
import sys
from collections import Counter

import numpy as np
import yaml

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing.metrics_r import summarize_episode_stats
from rl.routing.oracles import posthoc_dijkstra
from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.state_r import R_STATE_DIM
from rl.routing.oracle_gate import DEFAULT_DRIFT_STEPS, estimate_oracle_headroom
from rl.routing.topology_r import LOAD_CFG_TRAIN, LOAD_CFG_V1, LOAD_PRESETS, TOPO
from rl.routing.train_r import make_eval_env, run_agent_episode


GATE_SAFE_DELTA = 0.20
GATE_ARRIVED = 0.95
GATE_REVISIT = 0.05
GATE_PATH_UNIQUE = 2

HEADROOM_SWEEP_FALLBACK = 0.2235
STD_ORACLE_REF = 0.0390
SNR_PASS = 3.0
SNR_WARN = 2.0


def load_agent(run_dir, cfg):
    agent = DQNAgent(R_STATE_DIM, 2, cfg)
    agent.load(os.path.join(run_dir, 'model.pt'))
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def _preset_load(name):
    load = dict(LOAD_PRESETS[name])
    load.setdefault('drift_sigma', 0.15)
    return load


def _cfg_load_cfg(cfg):
    value = cfg['env']['load_cfg']
    if isinstance(value, dict):
        return value
    if value == 'LOAD_CFG_TRAIN':
        return LOAD_CFG_TRAIN
    if value == 'LOAD_CFG_V1':
        return LOAD_CFG_V1
    return LOAD_PRESETS[value]


def eval_preset(agent, cfg, preset, seeds):
    rows = []
    for seed in seeds:
        base = RouteEnv(
            TOPO,
            load_cfg=_preset_load(preset),
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


def eval_z0(agent, cfg, seeds):
    rows = []
    for seed in seeds:
        env = make_eval_env(cfg, seed, z=0)
        rows.append(
            run_agent_episode(
                env,
                agent,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows), rows


def _agent_seed_from_run(meta, run_dir):
    if 'agent_seed' in meta:
        return int(meta['agent_seed'])
    name = os.path.basename(run_dir)
    if name.startswith('r_seed'):
        return int(name.split('_', 1)[0].replace('r_seed', ''))
    raise ValueError(f'cannot infer agent seed from {run_dir}')


def _select_run_dirs(pattern):
    all_dirs = sorted(path for path in glob.glob(pattern) if os.path.isdir(path))
    by_seed = {}
    for path in all_dirs:
        meta_path = os.path.join(path, 'train.json')
        model_path = os.path.join(path, 'model.pt')
        if not os.path.exists(meta_path) or not os.path.exists(model_path):
            continue
        with open(meta_path, encoding='utf-8') as fh:
            meta = json.load(fh)
        seed = _agent_seed_from_run(meta, path)
        by_seed.setdefault(seed, []).append((path, meta))

    selected = []
    for seed in range(5):
        candidates = by_seed.get(seed, [])
        if not candidates:
            continue
        candidates.sort(key=lambda item: os.path.getmtime(item[0]), reverse=True)
        selected.append(candidates[0])
    return selected


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='rl/routing/configs/train_r_v1.yaml')
    parser.add_argument('--runs-glob', default='results/train/r_seed*')
    parser.add_argument('--heldout-start', type=int, default=2000)
    parser.add_argument('--heldout-n', type=int, default=50)
    parser.add_argument('--out', default='docs/phase-9/artifacts/analyze_5seed.json')
    parser.add_argument('--headroom-samples', type=int, default=50_000)
    parser.add_argument('--drift-steps', type=int, default=DEFAULT_DRIFT_STEPS)
    parser.add_argument(
        '--headroom-sweep',
        type=float,
        default=None,
        help='override dynamic oracle headroom, mainly for audit replay',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    with open(args.config, encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)

    if args.headroom_sweep is None:
        try:
            gate = estimate_oracle_headroom(
                load_cfg=_cfg_load_cfg(cfg),
                n_samples=int(args.headroom_samples),
                drift_steps=int(args.drift_steps),
            )
            headroom_sweep = float(gate.regret_always_f)
            print(
                'Dynamic headroom_sweep from oracle gate: %.4f '
                '(samples=%d, drift_steps=%d)'
                % (headroom_sweep, args.headroom_samples, args.drift_steps)
            )
        except Exception as exc:
            headroom_sweep = HEADROOM_SWEEP_FALLBACK
            print(
                'WARNING: dynamic headroom failed (%s); using fallback %.4f'
                % (exc, headroom_sweep)
            )
    else:
        headroom_sweep = float(args.headroom_sweep)
        print('Using overridden headroom_sweep: %.4f' % headroom_sweep)

    selected = _select_run_dirs(args.runs_glob)
    if len(selected) < 5:
        print(f'ERROR: found {len(selected)} usable seed runs; need one each for seeds 0..4.')
        print(f'       runs_glob={args.runs_glob}')
        return 1

    heldout = list(range(args.heldout_start, args.heldout_start + args.heldout_n))
    print(f'Heldout seeds: {heldout[0]}..{heldout[-1]}')

    per_seed = []
    for run_dir, meta in selected:
        agent_seed = _agent_seed_from_run(meta, run_dir)
        agent = load_agent(run_dir, cfg)

        normal, _rows_normal = eval_preset(agent, cfg, 'normal', heldout)
        bottleneck, rows_bottleneck = eval_preset(agent, cfg, 'bottleneck_E', heldout)
        z0, rows_z0 = eval_z0(agent, cfg, heldout)

        paths = [tuple(row['path']) for row in rows_bottleneck]
        paths_z0 = [tuple(row['path']) for row in rows_z0]
        revisit_rate = float(np.mean([
            len(set(row['path'])) < len(row['path'])
            for row in rows_bottleneck
        ]))
        path_unique = len(Counter(paths))
        path_unique_z0 = len(Counter(paths_z0))
        safe_delta = bottleneck['safe_path_freq'] - normal['safe_path_freq']

        row = {
            'agent_seed': agent_seed,
            'run_dir': run_dir,
            'git_hash': meta.get('git_hash'),
            'run_id': meta.get('run_id'),
            'return_z0': z0['return'],
            'arrived': z0['arrived'],
            'safe_freq_normal': normal['safe_path_freq'],
            'safe_freq_bottleneck': bottleneck['safe_path_freq'],
            'safe_delta': safe_delta,
            'safe_path_freq_aoi0': z0['safe_path_freq'],
            'revisit_rate': revisit_rate,
            'path_unique': path_unique,
            'path_unique_bottleneck': path_unique,
            'path_unique_z0': path_unique_z0,
            'gate_static': safe_delta > GATE_SAFE_DELTA,
            'gate_arrived': z0['arrived'] > GATE_ARRIVED,
            'gate_revisit': revisit_rate < GATE_REVISIT,
            'gate_diversity': path_unique >= GATE_PATH_UNIQUE,
        }
        per_seed.append(row)

        ok = (
            row['gate_static']
            and row['gate_arrived']
            and row['gate_revisit']
            and row['gate_diversity']
        )
        print(
            f"seed {agent_seed}: ret={row['return_z0']:.4f} "
            f"safe_delta={safe_delta:.4f} "
            f"anchor={row['safe_path_freq_aoi0']:.4f} "
            f"paths_bottleneck={path_unique} paths_z0={path_unique_z0} "
            f"{'PASS' if ok else 'FAIL'}"
        )

    per_seed.sort(key=lambda row: row['agent_seed'])
    returns = np.array([row['return_z0'] for row in per_seed], dtype=float)
    mean_return = float(returns.mean())
    std_agent = float(returns.std(ddof=1))
    ci95 = float(1.96 * std_agent / np.sqrt(len(returns)))
    snr = float(headroom_sweep / std_agent) if std_agent > 0 else float('inf')

    if snr >= SNR_PASS:
        verdict = 'PASS'
    elif snr >= SNR_WARN:
        verdict = 'WARN'
    else:
        verdict = 'FAIL'

    anchors = np.array([row['safe_path_freq_aoi0'] for row in per_seed], dtype=float)
    anchor_std = float(anchors.std(ddof=1))
    anchor_ci95 = float(1.96 * anchor_std / np.sqrt(len(anchors)))

    print('\n' + '=' * 60)
    print('Phase 9 self-check #3: std_agent vs headroom')
    print('=' * 60)
    print(f'return_z0      = {mean_return:.4f} +/- {ci95:.4f} CI95')
    print(f'std_agent      = {std_agent:.4f} ({100 * std_agent / abs(mean_return):.1f}% of mean)')
    print(f'headroom_sweep = {headroom_sweep:.4f}')
    print(f'SNR            = {snr:.2f} -> {verdict}')
    print(f'std_agent/std_oracle_ref = {std_agent / STD_ORACLE_REF:.1f}x')
    print(
        f'safe_path_freq(AoI=0) anchor = {float(anchors.mean()):.4f} '
        f'+/- {anchor_ci95:.4f} CI95'
    )

    gates = {
        'all_static': all(row['gate_static'] for row in per_seed),
        'all_arrived': all(row['gate_arrived'] for row in per_seed),
        'all_revisit': all(row['gate_revisit'] for row in per_seed),
        'all_diversity': all(row['gate_diversity'] for row in per_seed),
        'snr': verdict,
    }

    z_scores = np.abs(returns - mean_return) / (std_agent + 1e-9)
    outliers = [
        {'agent_seed': per_seed[idx]['agent_seed'], 'z_score': float(z)}
        for idx, z in enumerate(z_scores)
        if z > 2.0
    ]

    payload = {
        'per_seed': per_seed,
        'mean_return': mean_return,
        'std_agent': std_agent,
        'ci95': ci95,
        'headroom_sweep': headroom_sweep,
        'snr': snr,
        'snr_verdict': verdict,
        'std_oracle_ref': STD_ORACLE_REF,
        'safe_path_freq_aoi0_anchor': float(anchors.mean()),
        'safe_path_freq_aoi0_ci95': anchor_ci95,
        'gates': gates,
        'outliers': outliers,
        'gate_thresholds': {
            'safe_delta': GATE_SAFE_DELTA,
            'arrived': GATE_ARRIVED,
            'revisit': GATE_REVISIT,
            'path_unique': GATE_PATH_UNIQUE,
            'snr_pass': SNR_PASS,
            'snr_warn': SNR_WARN,
            'headroom_sweep': headroom_sweep,
        },
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)
    print(f'\n-> {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

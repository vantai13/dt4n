#!/usr/bin/env python3
"""Evaluate frozen routing policies without training.

Examples:
    python scripts/evaluate_frozen.py --version v1
    python scripts/evaluate_frozen.py --version v1 --episodes 100
"""

import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent  # noqa: E402
from rl.routing_2path.route_env import RouteEnv  # noqa: E402
from rl.routing_2path.state_r import MAX_NEIGHBORS, R_STATE_DIM  # noqa: E402
from rl.routing_2path.topology_r import SCENARIOS_TRAIN, TOPO_V2  # noqa: E402


def read_json(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def write_json(path, payload):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write('\n')


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_agent(model_path, cfg):
    agent = DQNAgent(R_STATE_DIM, MAX_NEIGHBORS, cfg)
    agent.load(model_path)
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def eval_scenario(agent, scenario_cfg, max_steps, n_episodes=50, seed0=900):
    e_used = 0
    returns = []
    arrived = []
    for offset in range(int(n_episodes)):
        seed = int(seed0) + offset
        env = RouteEnv(
            TOPO_V2,
            load_cfg=scenario_cfg,
            max_steps=max_steps,
            seed=seed,
        )
        obs, info = env.reset(seed=seed)
        done = False
        total = 0.0
        while not done:
            action = agent.select_action(
                obs,
                epsilon=0.0,
                valid_mask=env.valid_mask(),
            )
            obs, reward, terminated, truncated, info = env.step(action)
            total += float(reward)
            done = bool(terminated or truncated)
        e_used += int('E' in info['path'])
        returns.append(total)
        arrived.append(bool(info.get('arrived', False)))

    return {
        'E_usage': e_used / max(int(n_episodes), 1),
        'return_mean': float(np.mean(returns)),
        'return_std': float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0,
        'arrived': float(np.mean(arrived)),
    }


def manifest_seed_map(manifest):
    return {
        int(row['seed']): row
        for row in manifest.get('seeds', [])
    }


def evaluate_frozen(frozen_dir, episodes, seed0, delta_min):
    manifest = read_json(os.path.join(frozen_dir, 'manifest.json'))
    cfg = read_json(os.path.join(frozen_dir, 'config.json'))
    max_steps = int(cfg['env']['max_steps'])
    manifest_by_seed = manifest_seed_map(manifest)

    per_seed = []
    for seed in sorted(manifest_by_seed):
        seed_dir = os.path.join(frozen_dir, 'seed%d' % seed)
        model_path = os.path.join(seed_dir, 'model.pt')
        expected_sha = manifest_by_seed[seed].get('model_sha256')
        actual_sha = sha256_file(model_path)
        sha_ok = actual_sha == expected_sha
        if not sha_ok:
            print(
                'seed %d: SHA256 MISMATCH expected=%s actual=%s'
                % (seed, expected_sha, actual_sha),
                flush=True,
            )

        agent = load_agent(model_path, cfg)
        scenarios = {}
        for name, scenario_cfg in SCENARIOS_TRAIN.items():
            scenarios[name] = eval_scenario(
                agent,
                scenario_cfg,
                max_steps=max_steps,
                n_episodes=episodes,
                seed0=seed0,
            )

        delta = (
            scenarios['S1_viaE_better']['E_usage']
            - scenarios['S2_direct_better']['E_usage']
        )
        audit_pass = sha_ok and delta >= float(delta_min)
        per_seed.append({
            'seed': seed,
            'model_sha256_ok': sha_ok,
            'delta_S1_S2': round(float(delta), 6),
            'scenarios': scenarios,
            'audit_pass': audit_pass,
        })
        scenario_text = '  '.join(
            '%s:E=%.2f,R=%.2f'
            % (
                name.split('_', 1)[0],
                row['E_usage'],
                row['return_mean'],
            )
            for name, row in scenarios.items()
        )
        print(
            'seed %d: delta=%.2f %s  %s'
            % (seed, delta, 'PASS' if audit_pass else 'FAIL', scenario_text),
            flush=True,
        )

    deltas = np.array([row['delta_S1_S2'] for row in per_seed], dtype=float)
    payload = {
        'version': manifest.get('version'),
        'frozen_dir': frozen_dir,
        'episodes': int(episodes),
        'seed0': int(seed0),
        'delta_min': float(delta_min),
        'delta_mean': float(np.mean(deltas)),
        'delta_std': float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
        'per_seed': per_seed,
        'all_pass': all(row['audit_pass'] for row in per_seed),
    }
    return payload


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default='v1')
    parser.add_argument('--frozen', default='frozen_policies')
    parser.add_argument('--episodes', type=int, default=50)
    parser.add_argument('--seed0', type=int, default=900)
    parser.add_argument('--delta-min', type=float, default=0.5)
    parser.add_argument('--out', default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    frozen_dir = os.path.join(args.frozen, args.version)
    payload = evaluate_frozen(
        frozen_dir,
        episodes=args.episodes,
        seed0=args.seed0,
        delta_min=args.delta_min,
    )

    out_path = args.out or os.path.join(frozen_dir, 'evaluation.json')
    write_json(out_path, payload)
    print('\nsaved: %s' % out_path)
    print(
        'delta mean = %.3f  std = %.3f'
        % (payload['delta_mean'], payload['delta_std'])
    )
    print('behavioral audit: %s' % ('PASS' if payload['all_pass'] else 'FAIL'))
    return 0 if payload['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

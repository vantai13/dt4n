#!/usr/bin/env python3
"""[9.3] Diagnose whether the E/F decision is alive under a load config."""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.metrics_r import evaluate_policy
from rl.routing.oracles import clairvoyant_dijkstra, edge_cost
from rl.routing.reward_r import W_HOP
from rl.routing.route_env import RouteEnv
from rl.routing.topology_r import TOPO


def frac_E_better(load_cfg, n=400):
    """Fraction of seeds where C->E->F is cheaper than C->F."""
    n_better = 0
    for seed in range(int(n)):
        env = RouteEnv(TOPO, load_cfg=load_cfg, seed=seed)
        _obs, info = env.reset(seed=seed)
        rho = info['rho_snapshot']

        cost_e = (
            edge_cost(env.link[('C', 'E')]['base_delay'], rho[('C', 'E')]) + W_HOP
            + edge_cost(env.link[('E', 'F')]['base_delay'], rho[('E', 'F')]) + W_HOP
        )
        cost_f = edge_cost(env.link[('C', 'F')]['base_delay'], rho[('C', 'F')]) + W_HOP
        n_better += int(cost_e < cost_f)
    return n_better / max(int(n), 1)


def util_variability(load_cfg, n=400):
    """Std of rho(C,E), the state-side variability check."""
    values = []
    for seed in range(int(n)):
        env = RouteEnv(TOPO, load_cfg=load_cfg, seed=seed)
        _obs, info = env.reset(seed=seed)
        values.append(info['rho_snapshot'][('C', 'E')])
    return float(np.std(values))


def verdict(frac):
    if 0.25 <= frac <= 0.75:
        return 'BALANCED'
    if 0.15 <= frac <= 0.85:
        return 'ACCEPTABLE'
    return 'STATIC_POLICY_RISK'


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=400)
    parser.add_argument('--out', default='docs/phase-9/artifacts/decision_balance.json')
    args = parser.parse_args(argv)

    candidates = [
        (0.30, 0.50),
        (0.50, 0.70),
        (0.55, 0.75),
        (0.60, 0.80),
        (0.60, 0.85),
        (0.60, 0.97),
        (0.62, 0.88),
        (0.65, 0.85),
        (0.70, 0.85),
        (0.75, 0.95),
        (0.80, 0.97),
    ]

    rows = []
    print(f"{'e_load':>16} {'%E good':>8} {'util_std':>9} {'safe_freq':>10} {'verdict':>20}")
    for lo, hi in candidates:
        cfg = {
            'base_load': (0.25, 0.40),
            'e_load': (lo, hi),
            'drift_sigma': 0.15,
        }
        frac = frac_E_better(cfg, args.n)
        util_std = util_variability(cfg, args.n)
        safe_freq = evaluate_policy(
            clairvoyant_dijkstra,
            0,
            range(200),
            cfg,
        )['safe_path_freq']
        tag = verdict(frac)
        print(f'  ({lo:.2f}, {hi:.2f}) {100 * frac:7.1f}% {util_std:9.4f} {safe_freq:10.4f} {tag:>20}')
        rows.append({
            'e_load': [lo, hi],
            'frac_E_better': frac,
            'util_std': util_std,
            'clair_safe_path_freq': safe_freq,
            'verdict': tag,
        })

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump({'n': int(args.n), 'rows': rows}, fh, indent=2)
    print(f'\n-> {args.out}')


if __name__ == '__main__':
    main()

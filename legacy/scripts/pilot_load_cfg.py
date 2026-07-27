#!/usr/bin/env python3
"""[9.3] Choose a training load config before running the DQN pilot."""

import argparse
import json
import os
import sys

sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')

from diag_decision_balance import frac_E_better
from rl.routing_2path.metrics_r import evaluate_z_range


GATE_BALANCE = (0.20, 0.80)
GATE_COST_MIN = 0.30
Z_VALUES = (0, 1, 3, 5, 8, 12)


def _is_monotone(values, tol=1e-9):
    return all(values[i] <= values[i + 1] + tol for i in range(len(values) - 1))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=300)
    parser.add_argument('--out', default='docs/phase-9/artifacts/load_cfg_pilot.json')
    args = parser.parse_args(argv)

    candidates = [
        ('V1_current', (0.80, 0.97)),
        ('V2b_balanced', (0.65, 0.85)),
        ('V2d_covering', (0.60, 0.97)),
        ('V2e_covering', (0.65, 0.97)),
    ]

    results = []
    for name, e_load in candidates:
        cfg = {
            'base_load': (0.25, 0.40),
            'e_load': tuple(e_load),
            'drift_sigma': 0.15,
        }
        balance = frac_E_better(cfg, 300)
        rows = evaluate_z_range(z_values=Z_VALUES, seeds=range(args.seeds), load_cfg=cfg)
        costs = [row['cost_of_blindness'] for row in rows]
        peak_idx = max(range(len(costs)), key=lambda idx: costs[idx])

        gate_balance = GATE_BALANCE[0] <= balance <= GATE_BALANCE[1]
        gate_cost = max(costs) > GATE_COST_MIN
        result = {
            'name': name,
            'e_load': list(e_load),
            'frac_E_better': balance,
            'cost_of_blindness': costs,
            'z_values': list(Z_VALUES),
            'monotone': _is_monotone(costs),
            'peak_z': Z_VALUES[peak_idx],
            'gate_balance': gate_balance,
            'gate_cost': gate_cost,
            'verdict': 'PASS' if gate_balance and gate_cost else 'FAIL',
        }
        results.append(result)

        print(f'\n=== {name} e_load={e_load} ===')
        print(f'  frac_E_better = {balance:.3f} gate{GATE_BALANCE} -> {"OK" if gate_balance else "FAIL"}')
        print(f'  cost_bl max   = {max(costs):.4f} gate>{GATE_COST_MIN} -> {"OK" if gate_cost else "FAIL"}')
        print(f'  cost_bl curve = {[round(x, 3) for x in costs]}')
        print(f'  monotone={result["monotone"]} peak_z={result["peak_z"]}')
        print(f'  => {result["verdict"]}')

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump({
            'gates': {'balance': list(GATE_BALANCE), 'cost_min': GATE_COST_MIN},
            'results': results,
        }, fh, indent=2)
    print(f'\n-> {args.out}')


if __name__ == '__main__':
    main()

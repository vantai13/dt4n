#!/usr/bin/env python3
"""Systematic GO/NO-GO sweep for Lesson 8.6."""

import argparse
import sys

sys.path.insert(0, '.')

from rl.routing_2path.metrics_r import evaluate_z_range
from rl.routing_2path.topology_r import LOAD_CFG_V1


E_LOADS = (
    (0.55, 0.90),
    (0.65, 0.97),
    (0.75, 0.97),
    (0.80, 0.97),
)
DRIFT_SIGMAS = (0.05, 0.15, 0.30)
Z_VALUES = (0, 1, 3, 5, 8, 12)


def _is_monotone(values, tol=1e-9):
    return all(values[i] <= values[i + 1] + tol for i in range(len(values) - 1))


def _breaking_point(rows):
    for row in rows:
        if row['blind_return'] < row['ospf_return']:
            return row
    return None


def _run_cfg(e_load, sigma, seeds):
    load_cfg = {
        'base_load': (0.25, 0.40),
        'e_load': tuple(e_load),
        'drift_sigma': float(sigma),
    }
    rows = evaluate_z_range(z_values=Z_VALUES, seeds=seeds, load_cfg=load_cfg)
    cobs = [row['cost_of_blindness'] for row in rows]
    bp = _breaking_point(rows)
    return {
        'load_cfg': load_cfg,
        'rows': rows,
        'cob_zmax': cobs[-1],
        'monotone': _is_monotone(cobs),
        'bp': bp,
        'go': cobs[-1] >= 0.5 and _is_monotone(cobs) and bp is not None,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=100,
                        help='episode seeds per z/config')
    parser.add_argument('--locate', action='store_true',
                        help='also locate final LOAD_CFG_V1 breaking point over z=0..4')
    return parser.parse_args()


def main():
    args = parse_args()
    seeds = range(args.seeds)
    results = []

    print('=== LESSON 8.6 GO/NO-GO SWEEP ===')
    print(f'seeds={args.seeds} z_values={Z_VALUES}')
    print('        e_load  sigma | CoB(zmax)  mono |   blind    OSPF  BP?  GO?')
    print('-----------------------------------------------------------------------')
    for e_load in E_LOADS:
        for sigma in DRIFT_SIGMAS:
            result = _run_cfg(e_load, sigma, seeds)
            results.append(result)
            last = result['rows'][-1]
            print(
                f'{str(tuple(e_load)):>15s} {sigma:6.2f} | '
                f'{result["cob_zmax"]:9.4f} '
                f'{str(result["monotone"]):>5s} | '
                f'{last["blind_return"]:7.4f} '
                f'{last["ospf_return"]:7.4f} '
                f'{str(result["bp"] is not None):>4s} '
                f'{str(result["go"]):>4s}'
            )

    go_configs = [r for r in results if r['go']]
    print()
    if go_configs:
        chosen = min(
            go_configs,
            key=lambda r: (
                r['load_cfg'] != LOAD_CFG_V1,
                r['load_cfg']['drift_sigma'],
                -r['cob_zmax'],
            ),
        )
        print('GO: at least one config satisfies CoB>=0.5, monotone, and BP.')
        print(f"chosen_load_cfg={chosen['load_cfg']}")
    else:
        print('NO-GO: no config satisfied all criteria. Do not continue to Phase 11.')

    if args.locate:
        print()
        print('=== BREAKING POINT CHECK FOR LOAD_CFG_V1 ===')
        rows = evaluate_z_range(z_values=(0, 1, 2, 3, 4), seeds=seeds, load_cfg=LOAD_CFG_V1)
        print('  z  AoI(s) |   blind    OSPF | blind-OSPF')
        print('-------------------------------------------')
        for row in rows:
            diff = row['blind_return'] - row['ospf_return']
            print(
                f'{row["z_steps"]:3d} {row["aoi_mean_s"]:7.2f} | '
                f'{row["blind_return"]:7.4f} {row["ospf_return"]:7.4f} | '
                f'{diff:+10.4f}'
            )

    return 0 if go_configs else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Pilot the Lesson 8.4 measurement instruments across z."""

import argparse
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.metrics_r import evaluate_z_range


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=100,
                        help='number of deterministic episode seeds')
    parser.add_argument('--z', type=str, default='0,1,2,3,5,8',
                        help='comma-separated z step values')
    parser.add_argument('--drift-sigma', type=float, default=0.15)
    parser.add_argument('--base-load', type=str, default='0.25,0.40')
    parser.add_argument('--e-load', type=str, default='0.80,0.97')
    return parser.parse_args()


def _pair(text):
    lo, hi = text.split(',')
    return float(lo), float(hi)


def main():
    args = parse_args()
    z_values = tuple(int(x.strip()) for x in args.z.split(',') if x.strip())
    load_cfg = {
        'base_load': _pair(args.base_load),
        'e_load': _pair(args.e_load),
        'drift_sigma': float(args.drift_sigma),
    }
    seeds = range(int(args.seeds))
    rows = evaluate_z_range(z_values=z_values, seeds=seeds, load_cfg=load_cfg)

    clair_values = [row['clair_return'] for row in rows]
    print('=== PILOT: Dijkstra instruments over z ===')
    print(f'seeds={args.seeds} load_cfg={load_cfg}')
    print('  z  AoI(s) |   clair   blind ospf_cal   ospf0 |     CoB   w_exc  headrm  safe_b')
    print('------------------------------------------------------------------------------------')
    for row in rows:
        print(
            f"{row['z_steps']:3d} {row['aoi_mean_s']:7.3f} | "
            f"{row['clair_return']:7.4f} {row['blind_return']:7.4f} "
            f"{row['ospf_return']:8.4f} {row['ospf_reactive_return']:7.4f} | "
            f"{row['cost_of_blindness']:7.4f} "
            f"{row['wrong_excess']:7.4f} "
            f"{row['voi_headroom']:7.4f} "
            f"{row['blind_safe_path_freq']:7.4f}"
        )
    print()
    print(f"GATE clair flat std: {np.std(clair_values):.6f}")
    print(f"GATE CoB(z=0): {rows[0]['cost_of_blindness']:.6f}")


if __name__ == '__main__':
    main()

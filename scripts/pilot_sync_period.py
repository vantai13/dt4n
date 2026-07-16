#!/usr/bin/env python3
"""Pilot the Ditto-calibrated routing instruments across sync periods."""

import argparse
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.metrics_r import evaluate_sync_range
from rl.routing.topology_r import LOAD_CFG_V1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=100,
                        help='number of deterministic episode seeds')
    parser.add_argument(
        '--sync-periods',
        type=str,
        default='0.05,0.1,0.25,0.5,1.0,2.0,5.0',
        help='comma-separated Ditto sync periods in seconds',
    )
    parser.add_argument('--drift-sigma', type=float,
                        default=LOAD_CFG_V1['drift_sigma'])
    parser.add_argument(
        '--base-load',
        type=str,
        default=f"{LOAD_CFG_V1['base_load'][0]},{LOAD_CFG_V1['base_load'][1]}",
    )
    parser.add_argument(
        '--e-load',
        type=str,
        default=f"{LOAD_CFG_V1['e_load'][0]},{LOAD_CFG_V1['e_load'][1]}",
    )
    parser.add_argument(
        '--fixed-phase',
        type=float,
        default=None,
        help='optional fixed phase_s for debugging; default samples phase per seed',
    )
    return parser.parse_args()


def _pair(text):
    lo, hi = text.split(',')
    return float(lo), float(hi)


def _periods(text):
    return tuple(float(x.strip()) for x in text.split(',') if x.strip())


def main():
    args = parse_args()
    sync_periods = _periods(args.sync_periods)
    load_cfg = {
        'base_load': _pair(args.base_load),
        'e_load': _pair(args.e_load),
        'drift_sigma': float(args.drift_sigma),
    }
    seeds = range(int(args.seeds))
    rows = evaluate_sync_range(
        sync_periods=sync_periods,
        seeds=seeds,
        load_cfg=load_cfg,
        phase_s=args.fixed_phase,
    )

    clair_values = [row['clair_return'] for row in rows]
    print('=== PILOT: Ditto sawtooth instruments over sync_period_s ===')
    print(f'seeds={args.seeds} load_cfg={load_cfg} fixed_phase={args.fixed_phase}')
    print(' T_sync  AoI(s) |   clair   blind ospf_cal   ospf0 |     CoB   w_exc  headrm  stale')
    print('---------------------------------------------------------------------------------------')
    for row in rows:
        print(
            f"{row['sync_period_s']:7.3f} {row['aoi_mean_s']:7.3f} | "
            f"{row['clair_return']:7.4f} {row['blind_return']:7.4f} "
            f"{row['ospf_return']:8.4f} {row['ospf_reactive_return']:7.4f} | "
            f"{row['cost_of_blindness']:7.4f} "
            f"{row['wrong_excess']:7.4f} "
            f"{row['voi_headroom']:7.4f} "
            f"{row['blind_stale_steps']:6.2f}"
        )

    bp = next((row for row in rows if row['blind_return'] < row['ospf_return']), None)
    print()
    print(f'GATE clair flat std: {np.std(clair_values):.6f}')
    if bp is None:
        print('BP blind<ospf_cal: none in this sync-period range')
    else:
        print(
            'BP blind<ospf_cal: '
            f"sync_period_s={bp['sync_period_s']:.3f} "
            f"(blind={bp['blind_return']:.4f}, ospf_cal={bp['ospf_return']:.4f})"
        )


if __name__ == '__main__':
    main()

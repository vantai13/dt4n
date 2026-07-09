#!/usr/bin/env python3
"""Soak-test EnvRunner soft resets.

Run this with Ditto and the static Ryu controller already running. It starts one
EnvRunner, performs N resets, prints timing/dirty flags, and optionally writes a
CSV for plotting reset_total_s/reset_wait_s.
"""

import argparse
import csv
import os
import statistics
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner  # noqa: E402


def summarize(values):
    if not values:
        return None
    values = sorted(values)
    p95 = values[int(0.95 * (len(values) - 1))]
    return {
        'mean': statistics.mean(values),
        'p95': p95,
        'min': values[0],
        'max': values[-1],
    }


def fmt_stats(label, stats):
    if not stats:
        return '%s: no samples' % label
    return ('%s mean=%.2fs p95=%.2fs min=%.2fs max=%.2fs' %
            (label, stats['mean'], stats['p95'], stats['min'], stats['max']))


def main():
    p = argparse.ArgumentParser(description='Soak-test EnvRunner soft resets')
    p.add_argument('--resets', type=int, default=10)
    p.add_argument('--period', type=float, default=1.0)
    p.add_argument('--hard-every', type=int, default=0,
                   help='0 disables periodic hard reset during this soak')
    p.add_argument('--steady-cycles', type=int, default=5)
    p.add_argument('--steady-tol', type=float, default=0.05)
    p.add_argument('--steady-timeout', type=float, default=20.0)
    p.add_argument('--csv', default='logs/env_runner_soak.csv')
    args = p.parse_args()

    runner = EnvRunner(
        sync_period=args.period,
        hard_every=args.hard_every,
        steady_cycles=args.steady_cycles,
        steady_tol=args.steady_tol,
        steady_timeout=args.steady_timeout,
        do_pingall=False,
        mininet_log_level='info',
    )

    rows = []
    try:
        runner.start()
        for idx in range(1, args.resets + 1):
            info = runner.soft_reset()
            row = {
                'idx': idx,
                'reset_mode': info['reset_mode'],
                'reset_total_s': info['reset_total_s'],
                'reset_wait_s': info['reset_wait_s'],
                'reset_steady_ok': int(info['reset_steady_ok']),
                'reset_dirty': int(info['reset_dirty']),
                'iperf_count': info['iperf_count'],
            }
            rows.append(row)
            print('%03d mode=%s total=%.2fs wait=%.2fs dirty=%s iperf=%d' %
                  (idx, info['reset_mode'], info['reset_total_s'],
                   info['reset_wait_s'], info['reset_dirty'],
                   info['iperf_count']))
    finally:
        runner.close()

    if args.csv:
        parent = os.path.dirname(os.path.abspath(args.csv))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'idx', 'reset_mode', 'reset_total_s', 'reset_wait_s',
                'reset_steady_ok', 'reset_dirty', 'iperf_count',
            ])
            writer.writeheader()
            writer.writerows(rows)
        print('CSV -> %s' % args.csv)

    totals = [row['reset_total_s'] for row in rows]
    waits = [row['reset_wait_s'] for row in rows]
    dirty = sum(row['reset_dirty'] for row in rows)
    print(fmt_stats('reset_total_s', summarize(totals)))
    print(fmt_stats('reset_wait_s ', summarize(waits)))
    print('dirty=%d/%d' % (dirty, len(rows)))


if __name__ == '__main__':
    main()

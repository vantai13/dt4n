#!/usr/bin/env python3
"""Collect Phase 4.5 regression metrics into one JSON report."""

import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from measurements.stats import percentile


CYCLE_RE = re.compile(
    r'Cycle #\d+ \[(?P<tag>[^\]]+)\]: (?P<ok>\d+)/(?P<total>\d+) patch, '
    r'elapsed=(?P<elapsed>[0-9.]+)ms'
)
P95_RE = re.compile(r'p95[:=]\s*([0-9.]+)\s*ms', re.IGNORECASE)


def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def stats(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return None
    return {
        'n': len(values),
        'mean': statistics.mean(values),
        'p50': statistics.median(values),
        'p95': percentile(values, 0.95),
        'max': max(values),
        'min': min(values),
    }


def parse_sync_log(path):
    if not path or not os.path.exists(path):
        return {'measured': False, 'reason': 'missing %s' % path}
    elapsed = []
    patches_total = []
    patches_delta = []
    overruns = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'Cycle overran' in line:
                overruns += 1
            match = CYCLE_RE.search(line)
            if not match:
                continue
            total = int(match.group('total'))
            elapsed.append(float(match.group('elapsed')))
            patches_total.append(total)
            if match.group('tag') == 'delta':
                patches_delta.append(total)
    return {
        'measured': bool(elapsed),
        'cycle_elapsed_ms': stats(elapsed),
        'patches_per_cycle': stats(patches_total),
        'patches_per_delta_cycle': stats(patches_delta),
        'overruns': overruns,
    }


def parse_latency_text(path):
    if not path or not os.path.exists(path):
        return {'measured': False, 'reason': 'missing %s' % path}
    text = open(path, encoding='utf-8', errors='replace').read()
    matches = [float(m.group(1)) for m in P95_RE.finditer(text)]
    if not matches:
        return {'measured': False, 'reason': 'no p95 field in %s' % path}
    return {'measured': True, 'p95_ms': matches[-1], 'path': path}


def parse_verify(path):
    data = load_json(path)
    if data is None:
        return {'measured': False, 'reason': 'missing %s' % path}
    results = data.get('results', {})
    accuracy = results.get('accuracy') or {}
    fidelity = results.get('event_fidelity') or {}
    return {
        'measured': True,
        'accuracy_rate': accuracy.get('accuracy_rate'),
        'event_fidelity_pct': fidelity.get('fidelity_pct'),
        'raw': data,
    }


def parse_soak_csv(path):
    if not path or not os.path.exists(path):
        return {'measured': False, 'reason': 'missing %s' % path}
    totals = []
    waits = []
    totals_by_mode = {}
    dirty = 0
    iperf = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total = float(row['reset_total_s'])
            mode = row.get('reset_mode', 'unknown')
            totals.append(total)
            totals_by_mode.setdefault(mode, []).append(total)
            waits.append(float(row['reset_wait_s']))
            dirty += int(float(row['reset_dirty']))
            iperf.append(int(float(row['iperf_count'])))
    return {
        'measured': bool(totals),
        'reset_total_s': stats(totals),
        'reset_total_s_by_mode': {
            mode: stats(values)
            for mode, values in sorted(totals_by_mode.items())
        },
        'reset_wait_s': stats(waits),
        'dirty_count': dirty,
        'iperf_first': iperf[0] if iperf else None,
        'iperf_last': iperf[-1] if iperf else None,
        'iperf_slope_count': (iperf[-1] - iperf[0]) if len(iperf) >= 2 else 0,
    }


def gate(value, op, threshold):
    if value is None or threshold is None:
        return 'unknown'
    if op == '<':
        return 'pass' if value < threshold else 'fail'
    if op == '<=':
        return 'pass' if value <= threshold else 'fail'
    if op == '>=':
        return 'pass' if value >= threshold else 'fail'
    raise ValueError(op)


def budget(delta_s, soft_reset_s, hard_reset_s, avg_steps, hard_every,
           eval_episodes, eval_policies):
    if None in (delta_s, soft_reset_s, hard_reset_s, avg_steps):
        return {'measured': False}
    if hard_every and hard_every > 0:
        reset_avg = (((hard_every - 1) * soft_reset_s) + hard_reset_s) / hard_every
    else:
        reset_avg = soft_reset_s
    sec_per_episode = reset_avg + avg_steps * delta_s

    table = {}
    for n_ep in (200, 300, 500):
        train_1 = n_ep * sec_per_episode / 3600.0
        train_5 = n_ep * 5 * sec_per_episode / 3600.0
        eval_extra = eval_episodes * 5 * eval_policies * sec_per_episode / 3600.0
        table[str(n_ep)] = {
            '1_seed_h': train_1,
            '5_seed_h': train_5,
            '5_seed_plus_eval_h': train_5 + eval_extra,
        }
    phase7_h = 5 * 4 * 5 * 20 * sec_per_episode / 3600.0
    return {
        'measured': True,
        'avg_reset_s': reset_avg,
        'sec_per_episode': sec_per_episode,
        'table_h': table,
        'phase7_sweep_h': phase7_h,
    }


def main():
    p = argparse.ArgumentParser(description='Phase 4.5 regression report')
    p.add_argument('--run-sync-log', default='logs/run_sync.log')
    p.add_argument('--verify-report', default='docs/phase-2/verify_report.json')
    p.add_argument('--sync-latency-report', default='')
    p.add_argument('--command-latency-report', default='')
    p.add_argument('--soak-csv', default='logs/env_runner_soak_50.csv')
    p.add_argument('--delta-json', default='docs/phase-4.5/delta.json')
    p.add_argument('--equivalence-json', default='docs/phase-4.5/equivalence.json')
    p.add_argument('--out', default='docs/phase-4.5/regression_report.json')
    p.add_argument('--baseline-cycle-p95-ms', type=float, default=None)
    p.add_argument('--baseline-patches-p95', type=float, default=None)
    p.add_argument('--baseline-verify-accuracy', type=float, default=None)
    p.add_argument('--avg-steps', type=float, default=20.0)
    p.add_argument('--hard-every', type=int, default=20)
    p.add_argument('--eval-episodes', type=int, default=20)
    p.add_argument('--eval-policies', type=int, default=4)
    p.add_argument('--delta-s', type=float, default=None)
    p.add_argument('--soft-reset-s', type=float, default=None)
    p.add_argument('--hard-reset-s', type=float, default=None)
    args = p.parse_args()

    sync_log = parse_sync_log(args.run_sync_log)
    sync_latency = parse_latency_text(args.sync_latency_report)
    command_latency = parse_latency_text(args.command_latency_report)
    verify = parse_verify(args.verify_report)
    soak = parse_soak_csv(args.soak_csv)
    delta = load_json(args.delta_json) or {'measured': False}
    equivalence = load_json(args.equivalence_json) or {'measured': False}

    cycle_p95 = None
    patches_p95 = None
    if sync_log.get('cycle_elapsed_ms'):
        cycle_p95 = sync_log['cycle_elapsed_ms']['p95']
    if sync_log.get('patches_per_delta_cycle'):
        patches_p95 = sync_log['patches_per_delta_cycle']['p95']

    soft_p95 = None
    if soak.get('reset_total_s'):
        soft_p95 = soak['reset_total_s']['p95']
    soft_mean = args.soft_reset_s
    if soft_mean is None:
        soft_mean = (soak.get('reset_total_s_by_mode', {})
                     .get('soft', {})
                     .get('mean'))
    hard_reset_s = args.hard_reset_s
    if hard_reset_s is None:
        hard_reset_s = (soak.get('reset_total_s_by_mode', {})
                        .get('hard', {})
                        .get('mean'))
    delta_s = args.delta_s if args.delta_s is not None else delta.get('delta_s')

    report = {
        'generated_at_epoch': time.time(),
        'inputs': vars(args),
        'delta': delta,
        'equivalence': equivalence,
        'sync_log': sync_log,
        'sync_latency': sync_latency,
        'command_latency': command_latency,
        'verify': verify,
        'soak': soak,
        'gates': {
            'sync_latency_p95_lt_2s': gate(
                sync_latency.get('p95_ms') if sync_latency.get('measured') else None,
                '<', 2000.0),
            'command_latency_p95_lt_2s': gate(
                command_latency.get('p95_ms') if command_latency.get('measured') else None,
                '<', 2000.0),
            'cycle_elapsed_p95_le_baseline_x1_2': gate(
                cycle_p95, '<=',
                args.baseline_cycle_p95_ms * 1.2
                if args.baseline_cycle_p95_ms is not None else None),
            'patches_per_delta_cycle_p95_le_baseline': gate(
                patches_p95, '<=', args.baseline_patches_p95),
            'verify_accuracy_ge_baseline': gate(
                verify.get('accuracy_rate') if verify.get('measured') else None,
                '>=', args.baseline_verify_accuracy),
            'soft_reset_p95_le_12s': gate(soft_p95, '<=', 12.0),
            'equivalence_rejected_le_2': gate(
                equivalence.get('n_rejected') if equivalence.get('measured') else None,
                '<=', 2),
        },
        'budget': budget(
            delta_s=delta_s,
            soft_reset_s=soft_mean,
            hard_reset_s=hard_reset_s,
            avg_steps=args.avg_steps,
            hard_every=args.hard_every,
            eval_episodes=args.eval_episodes,
            eval_policies=args.eval_policies,
        ),
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')

    print('Gates:')
    for name, status in report['gates'].items():
        print('  %-45s %s' % (name, status))
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

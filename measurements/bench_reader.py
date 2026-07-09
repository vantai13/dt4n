#!/usr/bin/env python3
"""Benchmark Ditto reader modes A (direct GET) and B (/search).

This script measures both speed and correctness. The tSource skew check is the
important part: if search returns older tSource values than direct GET, search
is not suitable for AoI-sensitive agent observations.
"""

import argparse
import json
import os
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_reader import (  # noqa: E402
    expected_thing_ids,
    extract_t_source,
    fetch_all_things,
    fetch_all_things_search,
    make_session,
)
from measurements.stats import percentile  # noqa: E402


def summarize_ms(values):
    if not values:
        return None
    sorted_values = sorted(values)
    return {
        'p50': statistics.median(sorted_values),
        'p95': percentile(sorted_values, 0.95),
        'max': max(sorted_values),
        'min': min(sorted_values),
        'mean': statistics.mean(sorted_values),
    }


def print_speed_row(label, times, counts):
    stats = summarize_ms(times)
    if stats is None:
        print('%-14s no samples' % label)
        return
    try:
        mode_count = statistics.mode(counts)
    except statistics.StatisticsError:
        mode_count = counts[-1] if counts else 0
    print('%-14s p50=%6.1fms  p95=%6.1fms  max=%6.1fms  n_things=%d' %
          (label, stats['p50'], stats['p95'], stats['max'], mode_count))


def main():
    p = argparse.ArgumentParser(description='Benchmark DT4N Ditto reader')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--samples', type=int, default=100)
    p.add_argument('--sleep', type=float, default=0.05)
    p.add_argument('--skew-samples', type=int, default=30)
    p.add_argument('--skew-sleep', type=float, default=0.2)
    args = p.parse_args()

    spec = json.load(open(args.spec, encoding='utf-8'))
    ids = expected_thing_ids(spec)
    session = make_session()

    print('Expected Thing ids: %d' % len(ids))
    print('Warmup...')
    fetch_all_things(session, ids)
    time.sleep(1.0)

    for label, fn in (
            ('A (direct)', lambda: fetch_all_things(session, ids)),
            ('B (search)', lambda: fetch_all_things_search(session))):
        times = []
        counts = []
        for _ in range(args.samples):
            _things, meta = fn()
            times.append(meta['fetch_ms'])
            counts.append(meta['n_ok'])
            time.sleep(args.sleep)
        print_speed_row(label, times, counts)

    print('\n--- tSource skew: B - A (negative means search is older) ---')
    skews = []
    for _ in range(args.skew_samples):
        things_a, _meta_a = fetch_all_things(session, ids)
        things_b, _meta_b = fetch_all_things_search(session)
        for tid, body_a in things_a.items():
            body_b = things_b.get(tid)
            if body_b is None:
                continue
            t_a = extract_t_source(body_a)
            t_b = extract_t_source(body_b)
            if t_a is not None and t_b is not None:
                skews.append(t_b - t_a)
        time.sleep(args.skew_sleep)

    if not skews:
        print('No comparable tSource samples.')
        return

    skews.sort()
    p50 = statistics.median(skews)
    p05 = percentile(skews, 0.05)
    print('n=%d  p50=%+.3fs  p05=%+.3fs  min=%+.3fs  max=%+.3fs' %
          (len(skews), p50, p05, skews[0], skews[-1]))
    if p50 < -0.1:
        print('WARN: search tSource is older than direct GET by >100ms. Prefer A.')
    else:
        print('OK: no large median tSource skew detected.')


if __name__ == '__main__':
    main()

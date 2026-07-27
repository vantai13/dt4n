#!/usr/bin/env python3
"""Measure AoI for A2 host Things in Ditto.

AoI = local read time - features.meta.properties.tSource.  A2 currently reads
fresh collector data directly, but this baseline tells us how stale the twin
would be if A2 read goodput through Ditto.
"""

import argparse
import json
import os
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_common import make_thing_id_host  # noqa: E402
from bridge.ditto_reader import fetch_all_things, make_session  # noqa: E402
from mininet.traffic import (  # noqa: E402
    IPERF_PORT,
    run_host_shell,
    start_iperf_server,
    stop_all_iperf,
)


def resolve_thing(args):
    return args.thing if args.thing else make_thing_id_host(args.host)


def start_a2_branch_traffic(net, demand_a, demand_b, duration):
    h1, h2 = net.get('h1'), net.get('h2')
    srv1, srv2 = net.get('srv1'), net.get('srv2')
    stop_all_iperf(*net.hosts)
    start_iperf_server(srv1, udp=True)
    start_iperf_server(srv2, udp=True)
    run_host_shell(
        h1,
        'iperf -c %s -u -b %gM -p %d -t %d > /tmp/a2_aoi_a.log 2>&1 &'
        % (srv1.IP(), float(demand_a), IPERF_PORT, int(duration)),
    )
    run_host_shell(
        h2,
        'iperf -c %s -u -b %gM -p %d -t %d > /tmp/a2_aoi_b.log 2>&1 &'
        % (srv2.IP(), float(demand_b), IPERF_PORT, int(duration)),
    )


def read_t_source(session, thing_id):
    things, meta = fetch_all_things(session, [thing_id])
    thing = things.get(thing_id, {})
    t_source = (thing.get('features', {}).get('meta', {})
                .get('properties', {}).get('tSource'))
    read_wall = meta.get('read_times', {}).get(thing_id, meta.get('t_read'))
    return t_source, read_wall, meta


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    idx = int(float(q) * (len(ordered) - 1))
    idx = max(0, min(idx, len(ordered) - 1))
    return ordered[idx]


def summarize(values, tsources, polling_period):
    if not values:
        return {}

    mean = statistics.mean(values)
    aoi_min = min(values)
    expected = aoi_min + polling_period / 2.0
    ratio = mean / expected if expected > 0 else None
    distinct_tsources = len(set(round(t, 3) for t in tsources))
    quiet_threshold = max(2, len(values) // 20)
    thing_is_quiet = distinct_tsources <= quiet_threshold

    if thing_is_quiet:
        diagnosis = (
            'THING_YEN: tSource rarely changed. Measure again while traffic is active.'
        )
    elif ratio is not None and ratio > 3.0:
        diagnosis = (
            'PIPELINE_TUT_HAU: tSource changes, but measured AoI is far above d+T/2.'
        )
    else:
        diagnosis = 'LANH: AoI is close to the d + T/2 baseline.'

    return {
        'aoi_mean_s': mean,
        'aoi_median_s': statistics.median(values),
        'aoi_p95_s': percentile(values, 0.95),
        'aoi_min_s': aoi_min,
        'aoi_max_s': max(values),
        'polling_period_s': polling_period,
        'expected_d_plus_T_half_s': expected,
        'ratio_measured_over_expected': ratio,
        'distinct_tsources': distinct_tsources,
        'quiet_threshold': quiet_threshold,
        'thing_is_quiet': thing_is_quiet,
        'diagnosis': diagnosis,
    }


def parse_args():
    parser = argparse.ArgumentParser(description='Measure AoI for A2 host Thing')
    parser.add_argument('--host', default='srv1',
                        help='host name used when --thing is omitted')
    parser.add_argument('--thing',
                        help='full Ditto Thing id, e.g. org.dt4n:host-srv1')
    parser.add_argument('--interval', type=float, default=0.2)
    parser.add_argument('--samples', type=int, default=100)
    parser.add_argument('--polling-period', type=float, default=0.5)
    parser.add_argument('--start-runner', action='store_true',
                        help='start EnvRunner and A2-style traffic for this measurement')
    parser.add_argument('--sync-period', type=float, default=0.5)
    parser.add_argument('--settle', type=float, default=3.0)
    parser.add_argument('--demand-a', type=float, default=8.0)
    parser.add_argument('--demand-b', type=float, default=6.0)
    parser.add_argument('--flow-duration', type=int, default=100000)
    parser.add_argument('--cleanup-mn', action='store_true',
                        help='also run mn -c on exit; may stop external controllers')
    parser.add_argument('--out', default='results/aoi/aoi_a2_host_srv1.json')
    return parser.parse_args()


def main():
    args = parse_args()
    thing_id = resolve_thing(args)
    runner = None

    try:
        if args.start_runner:
            from mininet.env_runner import EnvRunner  # noqa: E402

            runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
            runner.start()
            start_a2_branch_traffic(
                runner.net, args.demand_a, args.demand_b, args.flow_duration)
            if args.settle > 0:
                print('settle %.1fs for runner/sync/traffic...' % args.settle)
                time.sleep(args.settle)

        session = make_session()
        values = []
        tsources = []
        records = []

        print('thing=%s interval=%.3fs samples=%d' %
              (thing_id, args.interval, args.samples))
        print('i    tSource          AoI_s')
        for idx in range(1, args.samples + 1):
            try:
                t_source, read_wall, meta = read_t_source(session, thing_id)
                if t_source is None:
                    print('%-4d %-16s missing tSource' % (idx, '-'))
                    records.append({
                        'i': idx,
                        'ok': False,
                        't_source': None,
                        'aoi_s': None,
                        'error': 'missing tSource',
                        'fetch_ms': meta.get('fetch_ms'),
                    })
                else:
                    t_source = float(t_source)
                    aoi = float(read_wall) - t_source
                    values.append(aoi)
                    tsources.append(t_source)
                    note = '  <clock skew?>' if aoi < -0.05 else ''
                    print('%-4d %-16.3f %.3f%s' %
                          (idx, t_source, aoi, note))
                    records.append({
                        'i': idx,
                        'ok': True,
                        't_source': t_source,
                        'read_wall': read_wall,
                        'aoi_s': aoi,
                        'fetch_ms': meta.get('fetch_ms'),
                    })
            except Exception as exc:
                print('%-4d ERROR %s' % (idx, exc))
                records.append({
                    'i': idx,
                    'ok': False,
                    't_source': None,
                    'aoi_s': None,
                    'error': str(exc),
                })

            if idx < args.samples:
                time.sleep(args.interval)
    finally:
        if runner is not None:
            runner.close(cleanup_mn=args.cleanup_mn)

    summary = summarize(values, tsources, args.polling_period)
    result = {
        'measured': True,
        'thing': thing_id,
        'host': args.host,
        'start_runner': args.start_runner,
        'samples_requested': args.samples,
        'samples_valid': len(values),
        'interval_s': args.interval,
        'generated_at_epoch': time.time(),
        'summary': summary,
        'records': records,
        'notes': [
            'AoI = per-Thing read time - features.meta.properties.tSource.',
            'thing_is_quiet means tSource rarely changed; measure while traffic is active.',
            'This is Ditto/twin AoI, not direct A2 collector AoI.',
        ],
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')

    print('\n== KET QUA AOI ==')
    if not summary:
        print('No valid AoI samples.')
    else:
        print('AoI mean=%.3fs p95=%.3fs min=%.3fs max=%.3fs' %
              (summary['aoi_mean_s'], summary['aoi_p95_s'],
               summary['aoi_min_s'], summary['aoi_max_s']))
        print('distinct tSource=%d quiet=%s' %
              (summary['distinct_tsources'], summary['thing_is_quiet']))
        print('diagnosis=%s' % summary['diagnosis'])
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

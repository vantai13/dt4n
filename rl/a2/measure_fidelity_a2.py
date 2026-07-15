#!/usr/bin/env python3
"""Measure A2 fidelity: direct collector goodput vs Ditto twin goodput.

For each sample, read host goodput two ways:
  - real: runner.net.dt4n_collector.collect_all(), same source TwinEnvA2 uses
  - twin: Ditto Thing features.traffic.properties.rxRate

Then regress absolute error against AoI to separate fidelity bugs from
staleness effects.
"""

import argparse
import json
import math
import os
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


TWIN_GOOD_INTERCEPT_MBPS = 0.15


def resolve_thing(args):
    return args.thing if args.thing else make_thing_id_host(args.host)


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    idx = int(float(q) * (len(ordered) - 1))
    idx = max(0, min(idx, len(ordered) - 1))
    return ordered[idx]


def linear_regression(xs, ys):
    n = len(xs)
    if n < 2:
        return float('nan'), float('nan'), float('nan')
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    if sxx == 0:
        return mean_y, 0.0, 0.0
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2
                 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return intercept, slope, r2


def classify_dominant_source(intercept, r2,
                             twin_good_intercept_mbps=TWIN_GOOD_INTERCEPT_MBPS):
    """Classify fidelity error source without overcalling tiny errors as bugs."""
    if math.isfinite(r2) and r2 > 0.5:
        return 'staleness'
    if (math.isfinite(intercept) and
            intercept <= float(twin_good_intercept_mbps)):
        return 'twin_good'
    if math.isfinite(r2) and r2 < 0.2:
        return 'fidelity_bug'
    return 'mixed'


def start_a2_branch_traffic(net, demand_a, demand_b, duration):
    h1, h2 = net.get('h1'), net.get('h2')
    srv1, srv2 = net.get('srv1'), net.get('srv2')
    stop_all_iperf(*net.hosts)
    start_iperf_server(srv1, udp=True)
    start_iperf_server(srv2, udp=True)
    run_host_shell(
        h1,
        'iperf -c %s -u -b %gM -p %d -t %d > /tmp/a2_fidelity_a.log 2>&1 &'
        % (srv1.IP(), float(demand_a), IPERF_PORT, int(duration)),
    )
    run_host_shell(
        h2,
        'iperf -c %s -u -b %gM -p %d -t %d > /tmp/a2_fidelity_b.log 2>&1 &'
        % (srv2.IP(), float(demand_b), IPERF_PORT, int(duration)),
    )


def read_real_goodput_mbps(collector, host):
    snap = collector.collect_all()
    short_id = 'host-%s' % host
    rate = (snap.get('things', {}).get(short_id, {})
            .get('features', {}).get('traffic', {}).get('rxRate', 0.0) or 0.0)
    return float(rate) * 8.0 / 1e6


def read_twin_goodput_and_aoi(session, thing_id):
    things, meta = fetch_all_things(session, [thing_id])
    thing = things.get(thing_id, {})
    features = thing.get('features', {})
    rate = (features.get('traffic', {}).get('properties', {})
            .get('rxRate', 0.0) or 0.0)
    t_source = (features.get('meta', {}).get('properties', {})
                .get('tSource'))
    read_wall = meta.get('read_times', {}).get(thing_id, meta.get('t_read'))
    aoi = None if t_source is None else float(read_wall) - float(t_source)
    return float(rate) * 8.0 / 1e6, aoi, meta


def analyze(samples, twin_good_intercept_mbps=TWIN_GOOD_INTERCEPT_MBPS):
    if not samples:
        return {'n': 0}

    aois = [row['aoi_s'] for row in samples]
    abs_errors = [row['abs_error_mbps'] for row in samples]
    rel_errors = [row['rel_error'] for row in samples]
    intercept, slope, r2 = linear_regression(aois, abs_errors)
    dominant = classify_dominant_source(
        intercept, r2, twin_good_intercept_mbps)
    return {
        'n': len(samples),
        'abs_error_mean_mbps': sum(abs_errors) / len(abs_errors),
        'abs_error_p95_mbps': percentile(abs_errors, 0.95),
        'abs_error_max_mbps': max(abs_errors),
        'rel_error_mean': sum(rel_errors) / len(rel_errors),
        'rel_error_p95': percentile(rel_errors, 0.95),
        'aoi_mean_s': sum(aois) / len(aois),
        'aoi_p95_s': percentile(aois, 0.95),
        'aoi_max_s': max(aois),
        'fidelity_error_intercept_mbps': intercept,
        'staleness_error_slope_mbps_per_s': slope,
        'r2_aoi_explains_abs_error': r2,
        'dominant_source': dominant,
        'dominant_source_thresholds': {
            'staleness_r2_gt': 0.5,
            'fidelity_bug_r2_lt': 0.2,
            'twin_good_intercept_mbps_lte': twin_good_intercept_mbps,
        },
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description='Measure A2 twin-vs-real goodput fidelity')
    parser.add_argument('--host', default='srv1',
                        help='host name used for real key host-<name>')
    parser.add_argument('--thing',
                        help='full Ditto Thing id, e.g. org.dt4n:host-srv1')
    parser.add_argument('--samples', type=int, default=200)
    parser.add_argument('--interval', type=float, default=0.5)
    parser.add_argument('--sync-period', type=float, default=0.5)
    parser.add_argument('--settle', type=float, default=4.0)
    parser.add_argument('--demand-a', type=float, default=8.0)
    parser.add_argument('--demand-b', type=float, default=6.0)
    parser.add_argument('--flow-duration', type=int, default=100000)
    parser.add_argument('--min-real-mbps', type=float, default=0.05,
                        help='discard samples below this real goodput')
    parser.add_argument('--twin-good-intercept-mbps', type=float,
                        default=TWIN_GOOD_INTERCEPT_MBPS,
                        help='if intercept is at or below this Mbps, label low-r2 runs twin_good')
    parser.add_argument('--progress-every', type=int, default=10)
    parser.add_argument('--cleanup-mn', action='store_true',
                        help='also run mn -c on exit; may stop external controllers')
    parser.add_argument('--out', default='results/fidelity/fidelity_a2_srv1.json')
    return parser.parse_args()


def main():
    args = parse_args()
    thing_id = resolve_thing(args)

    from mininet.env_runner import EnvRunner  # noqa: E402

    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    samples = []
    records = []
    try:
        runner.start()
        collector = getattr(runner.net, 'dt4n_collector', None)
        if collector is None:
            raise RuntimeError('runner.net.dt4n_collector is not available')

        start_a2_branch_traffic(
            runner.net, args.demand_a, args.demand_b, args.flow_duration)
        if args.settle > 0:
            print('settle %.1fs for runner/sync/traffic...' % args.settle)
            time.sleep(args.settle)

        session = make_session()
        print('i    aoi_s    real    twin    abs_err  kept')
        for idx in range(1, args.samples + 1):
            t_real = time.monotonic()
            real_mbps = read_real_goodput_mbps(collector, args.host)
            twin_mbps, aoi, meta = read_twin_goodput_and_aoi(session, thing_id)
            dt_read = time.monotonic() - t_real

            record = {
                'i': idx,
                'real_mbps': real_mbps,
                'twin_mbps': twin_mbps,
                'aoi_s': aoi,
                'dt_read_s': dt_read,
                'fetch_ms': meta.get('fetch_ms'),
                'kept': False,
            }
            if aoi is not None and real_mbps >= args.min_real_mbps:
                abs_error = abs(real_mbps - twin_mbps)
                rel_error = abs_error / max(abs(real_mbps), 1e-9)
                record.update({
                    'abs_error_mbps': abs_error,
                    'rel_error': rel_error,
                    'kept': True,
                })
                samples.append(record)

            records.append(record)
            if (idx == 1 or idx % max(1, args.progress_every) == 0 or
                    idx == args.samples):
                print('%-4d %7s %7.3f %7.3f %7s  %s' %
                      (idx,
                       '-' if aoi is None else '%.3f' % aoi,
                       real_mbps,
                       twin_mbps,
                       '-' if 'abs_error_mbps' not in record else
                       '%.3f' % record['abs_error_mbps'],
                       'yes' if record['kept'] else 'no'),
                      flush=True)

            if idx < args.samples:
                time.sleep(args.interval)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    analysis = analyze(samples, args.twin_good_intercept_mbps)
    dt_reads = [row['dt_read_s'] for row in records if row.get('dt_read_s') is not None]
    result = {
        'measured': True,
        'host': args.host,
        'thing': thing_id,
        'samples_requested': args.samples,
        'samples_kept': len(samples),
        'interval_s': args.interval,
        'sync_period_s': args.sync_period,
        'demand_a_mbps': args.demand_a,
        'demand_b_mbps': args.demand_b,
        'min_real_mbps': args.min_real_mbps,
        'analysis': analysis,
        'dt_read': {
            'mean_ms': (
                sum(dt_reads) / len(dt_reads) * 1000.0 if dt_reads else None
            ),
            'max_ms': max(dt_reads) * 1000.0 if dt_reads else None,
        },
        'units': {
            'real': 'Mbps from direct collector host rxRate',
            'twin': 'Mbps from Ditto host traffic.rxRate',
            'fidelity_error_intercept': 'Mbps absolute error at AoI=0',
            'staleness_error_slope': 'Mbps absolute error per second of AoI',
        },
        'generated_at_epoch': time.time(),
        'notes': [
            'intercept large -> fidelity/collector/sync bug, not staleness.',
            'low r2 with small intercept is labeled twin_good, not fidelity_bug.',
            'slope large with r2 > 0.5 -> error is mainly explained by AoI.',
            'Samples below min_real_mbps are discarded to avoid divide-by-near-zero relative error.',
        ],
        'records': records,
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')

    print('\n== KET QUA FIDELITY ==')
    if analysis.get('n', 0) == 0:
        print('No valid samples. Check traffic, Ditto Thing id, and min-real-mbps.')
    else:
        intercept = analysis['fidelity_error_intercept_mbps']
        slope = analysis['staleness_error_slope_mbps_per_s']
        r2 = analysis['r2_aoi_explains_abs_error']
        print('n=%d kept/%d requested' % (analysis['n'], args.samples))
        print('abs_error mean=%.4fMbps p95=%.4fMbps max=%.4fMbps' %
              (analysis['abs_error_mean_mbps'],
               analysis['abs_error_p95_mbps'],
               analysis['abs_error_max_mbps']))
        print('AoI mean=%.3fs p95=%.3fs max=%.3fs' %
              (analysis['aoi_mean_s'],
               analysis['aoi_p95_s'],
               analysis['aoi_max_s']))
        print('intercept(sai-vi-LOI)=%.4fMbps slope(sai-vi-CU)=%.4fMbps/s r2=%.3f'
              % (intercept if math.isfinite(intercept) else float('nan'),
                 slope if math.isfinite(slope) else float('nan'),
                 r2 if math.isfinite(r2) else float('nan')))
        print('dominant_source=%s' % analysis['dominant_source'])
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

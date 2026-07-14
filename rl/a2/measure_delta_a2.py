#!/usr/bin/env python3
"""Measure A2 Delta: branch bandwidth change -> host goodput becomes stable.

This script measures the wait time that should back TwinEnvA2's ``delta_s``:
after changing the A2 branch bandwidths, how long until host-srv goodput has
settled at the new level?
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

from mininet.topology_meta import canonical  # noqa: E402
from mininet.traffic import (  # noqa: E402
    IPERF_PORT,
    run_host_shell,
    start_iperf_server,
    stop_all_iperf,
)


BRANCH_A_LINK = 's1-s2'
BRANCH_B_LINK = 's1-s3'


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    idx = int(float(q) * (len(ordered) - 1))
    idx = max(0, min(idx, len(ordered) - 1))
    return ordered[idx]


def find_link(net, key):
    target = str(key)
    if target.startswith('link-'):
        target = target[len('link-'):]
    for link in net.links:
        if canonical(link.intf1.node.name, link.intf2.node.name) == target:
            return link
    raise ValueError('link not found: %s' % key)


def set_link_bw(runner, key, bw):
    link = find_link(runner.net, key)
    cfg = {'bw': float(bw)}
    delay = getattr(link, 'dt4n_delay', None)
    if delay:
        cfg['delay'] = delay
    with runner.net_lock:
        link.intf1.config(**cfg)
        link.intf2.config(**cfg)
        link.dt4n_bw = float(bw)


def set_branch_bw(runner, bw_a, bw_b):
    set_link_bw(runner, BRANCH_A_LINK, bw_a)
    set_link_bw(runner, BRANCH_B_LINK, bw_b)


def start_a2_branch_traffic(net, demand_a, demand_b, duration):
    """Start A2-style UDP demand h1->srv1 and h2->srv2."""
    h1, h2 = net.get('h1'), net.get('h2')
    srv1, srv2 = net.get('srv1'), net.get('srv2')
    stop_all_iperf(*net.hosts)
    start_iperf_server(srv1, udp=True)
    start_iperf_server(srv2, udp=True)
    run_host_shell(
        h1,
        'iperf -c %s -u -b %gM -p %d -t %d > /tmp/a2_delta_a.log 2>&1 &'
        % (srv1.IP(), float(demand_a), IPERF_PORT, int(duration)),
    )
    run_host_shell(
        h2,
        'iperf -c %s -u -b %gM -p %d -t %d > /tmp/a2_delta_b.log 2>&1 &'
        % (srv2.IP(), float(demand_b), IPERF_PORT, int(duration)),
    )


def read_goodput_mbps(collector):
    """Read host-srv1/srv2 rxRate the same way TwinEnvA2 does."""
    snap = collector.collect_all()
    things = snap.get('things', {})
    g_a = (things.get('host-srv1', {}).get('features', {})
           .get('traffic', {}).get('rxRate', 0.0) or 0.0)
    g_b = (things.get('host-srv2', {}).get('features', {})
           .get('traffic', {}).get('rxRate', 0.0) or 0.0)
    return float(g_a) * 8.0 / 1e6, float(g_b) * 8.0 / 1e6


def is_stable(values, tol):
    if not values:
        return False
    high = max(values)
    low = min(values)
    return high > 0.01 and (high - low) / high < tol


def wait_goodput_stable(collector, poll, timeout, stable_n, tol, min_total_mbps):
    """Wait for stable total host goodput and return timing + last sample."""
    hist = []
    t0 = time.monotonic()
    last = {'gA': 0.0, 'gB': 0.0, 'total': 0.0}
    while time.monotonic() - t0 < timeout:
        g_a, g_b = read_goodput_mbps(collector)
        total = g_a + g_b
        last = {'gA': g_a, 'gB': g_b, 'total': total}
        hist.append(total)
        hist = hist[-stable_n:]
        if (len(hist) == stable_n and total >= min_total_mbps and
                is_stable(hist, tol)):
            return time.monotonic() - t0, True, last
        time.sleep(poll)
    return time.monotonic() - t0, False, last


def measure_once(runner, collector, args):
    set_branch_bw(runner, args.bw_low, args.bw_low)
    wait_goodput_stable(
        collector, args.poll, args.timeout, args.stable_n,
        args.stable_tol, args.min_total_mbps)

    t0 = time.monotonic()
    set_branch_bw(runner, args.bw_high, args.bw_high)
    dt, ok, last = wait_goodput_stable(
        collector, args.poll, args.timeout, args.stable_n,
        args.stable_tol, args.min_total_mbps)
    return {
        'delta_s': dt,
        'stable': ok,
        'click_monotonic': t0,
        'last_goodput': last,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description='Measure A2 Delta from branch bandwidth change to stable goodput')
    parser.add_argument('--repeats', type=int, default=20)
    parser.add_argument('--sync-period', type=float, default=0.5)
    parser.add_argument('--settle', type=float, default=3.0,
                        help='seconds to wait after starting traffic')
    parser.add_argument('--bw-low', type=float, default=5.0)
    parser.add_argument('--bw-high', type=float, default=15.0)
    parser.add_argument('--demand-a', type=float, default=18.0)
    parser.add_argument('--demand-b', type=float, default=18.0)
    parser.add_argument('--flow-duration', type=int, default=100000)
    parser.add_argument('--poll', type=float, default=0.2)
    parser.add_argument('--timeout', type=float, default=10.0)
    parser.add_argument('--stable-n', type=int, default=3)
    parser.add_argument('--stable-tol', type=float, default=0.05)
    parser.add_argument('--min-total-mbps', type=float, default=1.0)
    parser.add_argument('--margin', type=float, default=0.3)
    parser.add_argument('--cleanup-mn', action='store_true',
                        help='also run mn -c on exit; may stop external controllers')
    parser.add_argument('--out', default='results/delta/delta_a2.json')
    return parser.parse_args()


def main():
    args = parse_args()

    from mininet.env_runner import EnvRunner  # noqa: E402

    runner = EnvRunner(sync_period=args.sync_period, hard_every=0)
    samples = []
    try:
        runner.start()
        collector = getattr(runner.net, 'dt4n_collector', None)
        if collector is None:
            raise RuntimeError('runner.net.dt4n_collector is not available')

        start_a2_branch_traffic(
            runner.net, args.demand_a, args.demand_b, args.flow_duration)
        if args.settle > 0:
            print('settle %.1fs for A2 branch traffic...' % args.settle)
            time.sleep(args.settle)

        for idx in range(1, args.repeats + 1):
            sample = measure_once(runner, collector, args)
            samples.append(sample)
            last = sample['last_goodput']
            print('%02d/%02d delta=%.3fs stable=%s total=%.3fMbps A=%.3f B=%.3f'
                  % (idx, args.repeats, sample['delta_s'], sample['stable'],
                     last['total'], last['gA'], last['gB']),
                  flush=True)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    ok_values = [row['delta_s'] for row in samples if row['stable']]
    all_values = [row['delta_s'] for row in samples]
    p95 = percentile(ok_values, 0.95)
    recommended = (p95 + args.margin) if p95 is not None else None
    result = {
        'measured': True,
        'repeats': args.repeats,
        'stable_repeats': len(ok_values),
        'failed_repeats': len(samples) - len(ok_values),
        'bw_low_mbps': args.bw_low,
        'bw_high_mbps': args.bw_high,
        'demand_a_mbps': args.demand_a,
        'demand_b_mbps': args.demand_b,
        'poll_s': args.poll,
        'stable_n': args.stable_n,
        'stable_tol': args.stable_tol,
        'delta_mean_s': statistics.mean(ok_values) if ok_values else None,
        'delta_p95_s': p95,
        'delta_max_s': max(ok_values) if ok_values else None,
        'delta_all_max_s': max(all_values) if all_values else None,
        'margin_s': args.margin,
        'delta_s_recommended': recommended,
        'generated_at_epoch': time.time(),
        'notes': [
            'delta_s_recommended = p95(stable measurements) + margin.',
            'Goodput is read from host-srv1/host-srv2 rxRate, matching TwinEnvA2.',
            'If failed_repeats is non-zero, inspect samples before trusting p95.',
        ],
        'samples': samples,
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')

    print('\nWrote %s' % args.out)
    if recommended is not None:
        print('delta_s recommended = %.3fs' % recommended)
    else:
        print('No stable samples; do not update delta_s from this run.')


if __name__ == '__main__':
    main()

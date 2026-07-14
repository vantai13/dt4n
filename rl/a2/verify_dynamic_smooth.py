#!/usr/bin/env python3
"""Verify that A2 dynamic demand shift does not create a fake zero-goodput dip.

The test runs two branches:
  A: h1 -> srv1 via s1-s2
  B: h2 -> srv2 via s1-s3

Each branch has an always-on base flow. A demand shift toggles only the burst
flow, so the branch losing burst should stay near the base rate instead of
falling to zero.
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from mininet.topology_meta import canonical
from rl.a2.demand_dynamic import DynamicDemand


DEFAULT_BRANCH_A = 's1-s2'
DEFAULT_BRANCH_B = 's1-s3'


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify smooth A2 demand shift with base+burst traffic.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--branch-a', default=DEFAULT_BRANCH_A)
    ap.add_argument('--branch-b', default=DEFAULT_BRANCH_B)
    ap.add_argument('--branch-bw', type=float, default=20.0,
                    help='Mbps capacity used on each branch during the probe')
    ap.add_argument('--base', type=float, default=3.0,
                    help='always-on base demand per branch in Mbps')
    ap.add_argument('--high-demand', type=float, default=16.0)
    ap.add_argument('--low-demand', type=float, default=3.0)
    ap.add_argument('--burst', type=float, default=None,
                    help='burst Mbps; defaults to high-demand - base')
    ap.add_argument('--warmup', type=float, default=3.0)
    ap.add_argument('--sample-interval', type=float, default=1.2)
    ap.add_argument('--pre-samples', type=int, default=4)
    ap.add_argument('--post-samples', type=int, default=5)
    ap.add_argument('--smooth-floor', type=float, default=2.0,
                    help='minimum Mbps expected on branch A after burst off')
    ap.add_argument('--flow-duration', type=int, default=3600)
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def normalize_link_key(key):
    key = str(key).strip()
    if key.startswith('link-'):
        key = key[len('link-'):]
    parts = key.split('-')
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError('invalid link key: %r' % key)
    return canonical(parts[0], parts[1])


def find_link(net, link_key):
    target = normalize_link_key(link_key)
    for link in net.links:
        a = link.intf1.node.name
        b = link.intf2.node.name
        if canonical(a, b) == target:
            return link
    return None


def set_bw(net, link_key, bw_mbps):
    link = find_link(net, link_key)
    if link is None:
        raise ValueError('link not found: %s' % link_key)

    cfg = {'bw': float(bw_mbps)}
    delay = getattr(link, 'dt4n_delay', None)
    if delay:
        cfg['delay'] = delay
    link.intf1.config(**cfg)
    link.intf2.config(**cfg)
    link.dt4n_bw = float(bw_mbps)


def read_goodput(net):
    collector = getattr(net, 'dt4n_collector', None)
    if collector is None:
        raise RuntimeError('net.dt4n_collector is not available')

    snap = collector.collect_all()
    things = snap.get('things', {})
    out = []
    for name in ('srv1', 'srv2'):
        data = things.get('host-%s' % name, {})
        traffic = data.get('features', {}).get('traffic', {})
        rx_bytes_per_sec = float(traffic.get('rxRate') or 0.0)
        out.append(rx_bytes_per_sec * 8.0 / 1e6)
    return tuple(out)


def sample_goodput(net, interval):
    time.sleep(interval)
    return read_goodput(net)


def main():
    args = parse_args()
    args.branch_a = normalize_link_key(args.branch_a)
    args.branch_b = normalize_link_key(args.branch_b)
    burst = (
        max(0.0, args.high_demand - args.base)
        if args.burst is None else float(args.burst)
    )

    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=0,
    )
    dd = None
    print('[smooth] start()...', flush=True)
    runner.start()
    net = runner.net

    try:
        with runner.net_lock:
            set_bw(net, args.branch_a, args.branch_bw)
            set_bw(net, args.branch_b, args.branch_bw)
        print('[smooth] branch bw: %s=%.1f Mbps, %s=%.1f Mbps'
              % (args.branch_a, args.branch_bw,
                 args.branch_b, args.branch_bw),
              flush=True)

        dd = DynamicDemand(
            net,
            base_mbps=args.base,
            flow_duration=args.flow_duration,
        )
        dd.start()
        time.sleep(args.warmup)
        read_goodput(net)  # seed collector counters before printed samples

        print('[smooth] PHASE 1: A=%.1f (base+burst), B=%.1f (base)'
              % (args.high_demand, args.low_demand),
              flush=True)
        dd.set_demand('A', args.high_demand, burst_mbps=burst)
        dd.set_demand('B', args.low_demand, burst_mbps=burst)
        for i in range(args.pre_samples):
            g_a, g_b = sample_goodput(net, args.sample_interval)
            print('[smooth]   pre[%d]   gA=%6.2f Mbps  gB=%6.2f Mbps'
                  % (i, g_a, g_b), flush=True)

        print('[smooth] SHIFT: A %.1f->%.1f, B %.1f->%.1f'
              % (args.high_demand, args.low_demand,
                 args.low_demand, args.high_demand),
              flush=True)
        dd.set_demand('A', args.low_demand, burst_mbps=burst)
        dd.set_demand('B', args.high_demand, burst_mbps=burst)

        post_rows = []
        for i in range(args.post_samples):
            g_a, g_b = sample_goodput(net, args.sample_interval)
            post_rows.append((g_a, g_b))
            print('[smooth]   post[%d]  gA=%6.2f Mbps  gB=%6.2f Mbps'
                  % (i, g_a, g_b), flush=True)

    finally:
        if dd is not None:
            dd.stop()
        runner.close(cleanup_mn=args.cleanup_mn)

    min_g_a = min(row[0] for row in post_rows) if post_rows else 0.0
    print('\n[smooth] === ANALYSIS ===')
    print('[smooth] min gA after shift = %.2f Mbps (base=%.1f)'
          % (min_g_a, args.base))
    if min_g_a >= args.smooth_floor:
        print('[smooth] RESULT: OK, base flow kept branch A above floor.')
        print('[smooth] Next: integrate dynamic demand into A2 env.')
    else:
        print('[smooth] RESULT: WARN, branch A still dipped near zero.')
        print('[smooth] Next: use fallback B or inspect burst kill pattern.')


if __name__ == '__main__':
    main()

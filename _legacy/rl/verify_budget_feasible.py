#!/usr/bin/env python3
"""Verify hard budget feasibility for the A2 branch-allocation idea.

This is a Phase-1 gate before implementing the RL action loop:
  1a. Controllability: changing branch bandwidth changes branch goodput.
  1b. Scarcity: a fixed cA + cB budget can create a real trade-off.

Branch A is h1 -> srv1 through s1-s2.
Branch B is h2 -> srv2 through s1-s3.

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 /usr/bin/python3 rl/verify_budget_feasible.py
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.collector import Collector
from mininet.env_runner import EnvRunner
from mininet.topology_meta import canonical
from mininet.traffic import (
    IPERF_PORT,
    run_host_shell,
    start_iperf_server,
    stop_all_iperf,
)


DEFAULT_BRANCH_A = 's1-s2'
DEFAULT_BRANCH_B = 's1-s3'


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify hard bandwidth-budget controllability/scarcity.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--branch-a', default=DEFAULT_BRANCH_A,
                    help='canonical link for branch A, e.g. s1-s2')
    ap.add_argument('--branch-b', default=DEFAULT_BRANCH_B,
                    help='canonical link for branch B, e.g. s1-s3')
    ap.add_argument('--total-budget', type=float, default=20.0,
                    help='fixed cA+cB bandwidth budget in Mbps')
    ap.add_argument('--demand', type=float, default=12.0,
                    help='UDP demand per branch in Mbps')
    ap.add_argument('--settle', type=float, default=5.0,
                    help='seconds to wait after each allocation before reading')
    ap.add_argument('--warmup', type=float, default=4.0,
                    help='seconds to wait after starting the two iperf flows')
    ap.add_argument('--flow-duration', type=int, default=100000,
                    help='iperf client duration in seconds')
    ap.add_argument('--saturation-threshold', type=float, default=0.80,
                    help='branch is satisfied when goodput >= threshold*demand')
    ap.add_argument('--control-delta', type=float, default=2.0,
                    help='minimum Mbps goodput delta considered controllable')
    ap.add_argument('--allocations', default=None,
                    help='optional cA:cB list, e.g. 16:4,13:7,10:10')
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


def parse_allocations(text, total_budget):
    if not text:
        shares = (0.80, 0.65, 0.50, 0.35, 0.20)
        return [
            (round(total_budget * share, 3),
             round(total_budget * (1.0 - share), 3))
            for share in shares
        ]

    out = []
    for chunk in text.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ':' not in chunk:
            raise ValueError(
                'allocation must use cA:cB form, got %r' % chunk)
        left, right = chunk.split(':', 1)
        out.append((float(left), float(right)))
    if not out:
        raise ValueError('no allocations parsed from %r' % text)
    for c_a, c_b in out:
        if abs((c_a + c_b) - total_budget) > 1e-6:
            raise ValueError(
                'allocation %.3f:%.3f does not sum to total budget %.3f'
                % (c_a, c_b, total_budget))
    return out


def find_link(net, link_key):
    target = normalize_link_key(link_key)
    for link in net.links:
        a = link.intf1.node.name
        b = link.intf2.node.name
        if canonical(a, b) == target:
            return link
    return None


def set_branch_bw(net, link_key, bw_mbps):
    """Set one branch link bandwidth on both TC interfaces."""
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


def start_two_flows(net, demand_mbps, duration):
    """Start h1->srv1 and h2->srv2 UDP flows at the requested demand."""
    h1 = net.get('h1')
    h2 = net.get('h2')
    srv1 = net.get('srv1')
    srv2 = net.get('srv2')
    rate = '%gM' % float(demand_mbps)

    start_iperf_server(srv1, udp=True)
    start_iperf_server(srv2, udp=True)
    run_host_shell(
        h1,
        'iperf -c %s -u -b %s -p %d -t %d '
        '> /tmp/verify_budget_a.log 2>&1 &'
        % (srv1.IP(), rate, IPERF_PORT, duration),
    )
    run_host_shell(
        h2,
        'iperf -c %s -u -b %s -p %d -t %d '
        '> /tmp/verify_budget_b.log 2>&1 &'
        % (srv2.IP(), rate, IPERF_PORT, duration),
    )
    print('[budget] traffic: h1->srv1 UDP @%s, h2->srv2 UDP @%s'
          % (rate, rate), flush=True)


def read_goodput_mbps(collector):
    """Read srv1/srv2 RX rates from Collector and convert B/s to Mbps."""
    snap = collector.collect_all()
    things = snap.get('things', {})
    out = {}
    for name in ('srv1', 'srv2'):
        data = things.get('host-%s' % name, {})
        traffic = data.get('features', {}).get('traffic', {})
        rx_bytes_per_sec = float(traffic.get('rxRate') or 0.0)
        out[name] = rx_bytes_per_sec * 8.0 / 1e6
    return out


def measure_goodput(collector, settle):
    # First read seeds this probe collector's previous counters; the second read
    # reports the rate over the settle window.
    read_goodput_mbps(collector)
    time.sleep(settle)
    return read_goodput_mbps(collector)


def print_summary(rows, args):
    print('\n[budget] === ANALYSIS ===')

    if 2.0 * args.demand <= args.total_budget:
        print('[budget] WARN: total demand %.1f <= C_total %.1f; '
              'scarcity may not appear.'
              % (2.0 * args.demand, args.total_budget))

    by_a = sorted(rows, key=lambda row: row['cA'])
    low_a = by_a[0]
    high_a = by_a[-1]
    delta_a = high_a['gA'] - low_a['gA']
    delta_b = low_a['gB'] - high_a['gB']

    a_ok = delta_a > args.control_delta
    b_ok = delta_b > args.control_delta
    print('[budget] 1a CONTROLLABILITY:')
    print('[budget]    A: cA %.1f -> %.1f, gA %.2f -> %.2f Mbps, '
          'delta=%+.2f => %s'
          % (low_a['cA'], high_a['cA'], low_a['gA'], high_a['gA'],
             delta_a, 'OK' if a_ok else 'WARN'))
    print('[budget]    B: cB %.1f -> %.1f, gB %.2f -> %.2f Mbps, '
          'delta=%+.2f => %s'
          % (high_a['cB'], low_a['cB'], high_a['gB'], low_a['gB'],
             delta_b, 'OK' if b_ok else 'WARN'))
    if a_ok and b_ok:
        print('[budget]    RESULT: goodput reacts to branch bandwidth changes.')
    else:
        print('[budget]    RESULT: not clearly controllable. Check routing and '
              'whether branch traffic actually crosses the target links.')

    any_fail = any(not row['both_ok'] for row in rows)
    any_ok = any(row['both_ok'] for row in rows)
    print('[budget] 1b SCARCITY: total demand %.1f Mbps vs C_total %.1f Mbps'
          % (2.0 * args.demand, args.total_budget))
    if any_fail and any_ok:
        print('[budget]    RESULT: OK, there is a useful scarce region.')
        print('[budget]    Next: keep this C_total/demand region for A2, then '
              'verify dynamic demand shift.')
    elif not any_fail:
        print('[budget]    RESULT: WARN, every allocation satisfied both '
              'branches. Lower --total-budget or raise --demand.')
    else:
        print('[budget]    RESULT: WARN, no allocation satisfied both branches. '
              'Raise --total-budget or lower --demand.')


def main():
    args = parse_args()
    args.branch_a = normalize_link_key(args.branch_a)
    args.branch_b = normalize_link_key(args.branch_b)
    allocations = parse_allocations(args.allocations, args.total_budget)

    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=0,
    )
    print('[budget] start()...', flush=True)
    runner.start()
    net = runner.net

    rows = []
    try:
        stop_all_iperf(*net.hosts)
        collector = Collector(net, interval=args.sync_period,
                              net_lock=runner.net_lock)
        start_two_flows(net, args.demand, args.flow_duration)
        time.sleep(args.warmup)

        print('[budget] sweep: C_total=%.1f Mbps, demand=%.1f Mbps/branch'
              % (args.total_budget, args.demand), flush=True)
        for c_a, c_b in allocations:
            with runner.net_lock:
                set_branch_bw(net, args.branch_a, c_a)
                set_branch_bw(net, args.branch_b, c_b)
            goodput = measure_goodput(collector, args.settle)
            g_a = goodput.get('srv1', 0.0)
            g_b = goodput.get('srv2', 0.0)
            sat_a = g_a / max(args.demand, 1e-9)
            sat_b = g_b / max(args.demand, 1e-9)
            both_ok = (
                sat_a >= args.saturation_threshold and
                sat_b >= args.saturation_threshold
            )
            row = {
                'cA': float(c_a),
                'cB': float(c_b),
                'gA': g_a,
                'gB': g_b,
                'satA': sat_a,
                'satB': sat_b,
                'both_ok': both_ok,
            }
            rows.append(row)
            print('[budget] (cA=%5.1f,cB=%5.1f) -> '
                  'gA=%6.2f gB=%6.2f Mbps  '
                  'satA=%3.0f%% satB=%3.0f%%  both_ok=%s'
                  % (c_a, c_b, g_a, g_b, 100.0 * sat_a, 100.0 * sat_b,
                     both_ok),
                  flush=True)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    if rows:
        print_summary(rows, args)
    else:
        print('[budget] no rows collected')


if __name__ == '__main__':
    main()

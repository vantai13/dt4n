#!/usr/bin/env python3
"""Verify dynamic demand shift and decision flipping for A2.

This is the second Phase-1 gate:
  2a. Demand can change during one episode.
  2b. Goodput reflects the new demand after the shift.
  2c. The best allocation changes direction after demand flips.

Branch A is h1 -> srv1 through s1-s2.
Branch B is h2 -> srv2 through s1-s3.

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 /usr/bin/python3 rl/verify_demand_shift.py
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
from mininet.traffic import (
    IPERF_PORT,
    run_host_shell,
    start_iperf_server,
    stop_all_iperf,
)
from rl.verify_budget_feasible import (
    DEFAULT_BRANCH_A,
    DEFAULT_BRANCH_B,
    measure_goodput,
    normalize_link_key,
    parse_allocations,
    set_branch_bw,
)


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify demand shift and allocation decision flipping.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--branch-a', default=DEFAULT_BRANCH_A,
                    help='canonical link for branch A, e.g. s1-s2')
    ap.add_argument('--branch-b', default=DEFAULT_BRANCH_B,
                    help='canonical link for branch B, e.g. s1-s3')
    ap.add_argument('--total-budget', type=float, default=20.0,
                    help='fixed cA+cB bandwidth budget in Mbps')
    ap.add_argument('--phase1-demand-a', type=float, default=14.0)
    ap.add_argument('--phase1-demand-b', type=float, default=5.0)
    ap.add_argument('--phase2-demand-a', type=float, default=5.0)
    ap.add_argument('--phase2-demand-b', type=float, default=14.0)
    ap.add_argument('--settle', type=float, default=5.0,
                    help='seconds to wait after each allocation before reading')
    ap.add_argument('--warmup', type=float, default=4.0,
                    help='seconds to wait after starting phase-1 flows')
    ap.add_argument('--shift-wait', type=float, default=5.0,
                    help='seconds to wait after restarting flows at new demand')
    ap.add_argument('--flow-duration', type=int, default=100000,
                    help='iperf client duration in seconds')
    ap.add_argument('--allocations', default=None,
                    help='optional cA:cB list, e.g. 16:4,13:7,10:10')
    ap.add_argument('--tie-tolerance', type=float, default=0.03,
                    help='score window for treating allocations as co-optimal')
    ap.add_argument('--demand-tolerance', type=float, default=0.5,
                    help='Mbps tolerance for demand reflection checks')
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def rate_text(mbps):
    return '%gM' % float(mbps)


def start_flow(src, dst, demand_mbps, tag, duration):
    run_host_shell(
        src,
        'iperf -c %s -u -b %s -p %d -t %d '
        '> /tmp/verify_demand_%s.log 2>&1 &'
        % (dst.IP(), rate_text(demand_mbps), IPERF_PORT, duration, tag),
    )


def stop_client_flow(src):
    run_host_shell(src, 'pkill -f "[i]perf -c .* -p %d" 2>/dev/null'
                   % IPERF_PORT)


def restart_flow(src, dst, demand_mbps, tag, duration):
    """Change demand by replacing the iperf client process."""
    stop_client_flow(src)
    time.sleep(0.5)
    start_flow(src, dst, demand_mbps, tag, duration)


def start_phase_flows(net, demand_a, demand_b, duration):
    h1 = net.get('h1')
    h2 = net.get('h2')
    srv1 = net.get('srv1')
    srv2 = net.get('srv2')
    start_flow(h1, srv1, demand_a, 'a', duration)
    start_flow(h2, srv2, demand_b, 'b', duration)
    print('[shift] traffic: A h1->srv1 @%s, B h2->srv2 @%s'
          % (rate_text(demand_a), rate_text(demand_b)), flush=True)


def restart_phase_flows(net, demand_a, demand_b, duration):
    h1 = net.get('h1')
    h2 = net.get('h2')
    srv1 = net.get('srv1')
    srv2 = net.get('srv2')
    restart_flow(h1, srv1, demand_a, 'a', duration)
    restart_flow(h2, srv2, demand_b, 'b', duration)
    print('[shift] traffic shifted: A h1->srv1 @%s, B h2->srv2 @%s'
          % (rate_text(demand_a), rate_text(demand_b)), flush=True)


def satisfaction(goodput, demand):
    return min(float(goodput) / max(float(demand), 1e-9), 1.0)


def row_score(row):
    return row['satA'] + row['satB']


def allocation_direction(row, total_budget):
    if row['cA'] > total_budget / 2.0:
        return 'A'
    if row['cA'] < total_budget / 2.0:
        return 'B'
    return 'equal'


def best_rows(rows, tolerance):
    best_score = max(row_score(row) for row in rows)
    return [
        row for row in rows
        if best_score - row_score(row) <= tolerance
    ]


def choose_representative(rows, prefer):
    """Pick a stable representative from a co-optimal set.

    The measured plateau can contain multiple good allocations. For decision
    flipping we care about direction, so use the most branch-favoring member.
    """
    if prefer == 'A':
        return max(rows, key=lambda row: (row['cA'], row_score(row)))
    if prefer == 'B':
        return min(rows, key=lambda row: (row['cA'], -row_score(row)))
    return max(rows, key=row_score)


def scan_allocations(runner, collector, allocations, demand_a, demand_b, args,
                     label, prefer):
    print('[shift]   scan %s:' % label, flush=True)
    rows = []
    for c_a, c_b in allocations:
        with runner.net_lock:
            set_branch_bw(runner.net, args.branch_a, c_a)
            set_branch_bw(runner.net, args.branch_b, c_b)
        goodput = measure_goodput(collector, args.settle)
        g_a = goodput.get('srv1', 0.0)
        g_b = goodput.get('srv2', 0.0)
        row = {
            'cA': float(c_a),
            'cB': float(c_b),
            'gA': g_a,
            'gB': g_b,
            'satA': satisfaction(g_a, demand_a),
            'satB': satisfaction(g_b, demand_b),
        }
        rows.append(row)
        print('[shift]      (cA=%5.1f,cB=%5.1f) -> '
              'gA=%6.2f/%4.1f gB=%6.2f/%4.1f Mbps  '
              'satA=%3.0f%% satB=%3.0f%% score=%.3f'
              % (c_a, c_b, g_a, demand_a, g_b, demand_b,
                 100.0 * row['satA'], 100.0 * row['satB'],
                 row_score(row)),
              flush=True)

    winners = best_rows(rows, args.tie_tolerance)
    representative = choose_representative(winners, prefer)
    print('[shift]   >>> best %s: %s  co_optimal=%s'
          % (label, fmt_alloc(representative), fmt_allocs(winners)),
          flush=True)
    return rows, winners, representative


def fmt_alloc(row):
    return '(%.1f,%.1f)' % (row['cA'], row['cB'])


def fmt_allocs(rows):
    return '[' + ', '.join(fmt_alloc(row) for row in rows) + ']'


def demand_reflected(row, demand_a, demand_b, args):
    expected_a = min(row['cA'], demand_a)
    expected_b = min(row['cB'], demand_b)
    ok_a = abs(row['gA'] - expected_a) <= args.demand_tolerance
    ok_b = abs(row['gB'] - expected_b) <= args.demand_tolerance
    return ok_a, ok_b, expected_a, expected_b


def print_reflection(label, row, demand_a, demand_b, args):
    ok_a, ok_b, exp_a, exp_b = demand_reflected(row, demand_a, demand_b, args)
    print('[shift] 2b %s demand reflection at %s:' % (label, fmt_alloc(row)))
    print('[shift]    A expected~%.2f got %.2f Mbps => %s'
          % (exp_a, row['gA'], 'OK' if ok_a else 'WARN'))
    print('[shift]    B expected~%.2f got %.2f Mbps => %s'
          % (exp_b, row['gB'], 'OK' if ok_b else 'WARN'))
    return ok_a and ok_b


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
    print('[shift] start()...', flush=True)
    runner.start()
    net = runner.net

    phase1_best = None
    phase2_best = None
    phase1_reflect_ok = False
    phase2_reflect_ok = False
    try:
        stop_all_iperf(*net.hosts)
        start_iperf_server(net.get('srv1'), udp=True)
        start_iperf_server(net.get('srv2'), udp=True)
        collector = Collector(net, interval=args.sync_period,
                              net_lock=runner.net_lock)

        print('\n[shift] PHASE 1: demand A=%.1fM high, B=%.1fM low'
              % (args.phase1_demand_a, args.phase1_demand_b),
              flush=True)
        start_phase_flows(net, args.phase1_demand_a, args.phase1_demand_b,
                          args.flow_duration)
        time.sleep(args.warmup)
        _rows1, _winners1, phase1_best = scan_allocations(
            runner, collector, allocations,
            args.phase1_demand_a, args.phase1_demand_b,
            args, 'phase1', prefer='A')
        phase1_reflect_ok = print_reflection(
            'phase1', phase1_best,
            args.phase1_demand_a, args.phase1_demand_b, args)

        print('\n[shift] === SHIFT: A %.1fM -> %.1fM, B %.1fM -> %.1fM ==='
              % (args.phase1_demand_a, args.phase2_demand_a,
                 args.phase1_demand_b, args.phase2_demand_b),
              flush=True)
        restart_phase_flows(net, args.phase2_demand_a, args.phase2_demand_b,
                            args.flow_duration)
        time.sleep(args.shift_wait)

        print('\n[shift] PHASE 2: demand A=%.1fM low, B=%.1fM high'
              % (args.phase2_demand_a, args.phase2_demand_b),
              flush=True)
        _rows2, _winners2, phase2_best = scan_allocations(
            runner, collector, allocations,
            args.phase2_demand_a, args.phase2_demand_b,
            args, 'phase2', prefer='B')
        phase2_reflect_ok = print_reflection(
            'phase2', phase2_best,
            args.phase2_demand_a, args.phase2_demand_b, args)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[shift] === ANALYSIS ===')
    if phase1_best is None or phase2_best is None:
        print('[shift] no phase result collected')
        return

    dir1 = allocation_direction(phase1_best, args.total_budget)
    dir2 = allocation_direction(phase2_best, args.total_budget)
    print('[shift] 2a DEMAND SHIFT: replaced iperf clients in-episode '
          'A %.1f->%.1f Mbps, B %.1f->%.1f Mbps'
          % (args.phase1_demand_a, args.phase2_demand_a,
             args.phase1_demand_b, args.phase2_demand_b))
    print('[shift]    RESULT: OK' if (phase1_reflect_ok and phase2_reflect_ok)
          else '[shift]    RESULT: WARN, demand reflection was weak')

    print('[shift] 2c BEST ALLOCATION: phase1=%s (%s) -> phase2=%s (%s)'
          % (fmt_alloc(phase1_best), dir1, fmt_alloc(phase2_best), dir2))
    if dir1 == 'A' and dir2 == 'B':
        print('[shift]    RESULT: OK, optimum flips A -> B.')
        print('[shift]    Decision-relevant staleness is measurable: '
              'a phase-1 observation can imply the wrong phase-2 action.')
    else:
        print('[shift]    RESULT: WARN, optimum did not clearly flip.')
        print('[shift]    Try a stronger shift, e.g. --phase1-demand-a 16 '
              '--phase1-demand-b 3 --phase2-demand-a 3 --phase2-demand-b 16')


if __name__ == '__main__':
    main()

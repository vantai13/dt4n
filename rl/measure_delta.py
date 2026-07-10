#!/usr/bin/env python3
"""Measure env step delay Delta for action consequences.

Measure two distinct times after a setBandwidth action sent through Ditto:
  t1: capacity.bwMbps changed in the twin (command acknowledged by observation)
  t2: traffic.rxRate/txRate stabilized at the new level (consequence visible)

Delta should be p95(t2) + margin, not p95(t1).
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

from bridge.ditto_common import make_thing_id_link
from bridge.ditto_reader import fetch_all_things, make_session
from measurements.measure_command_latency import send_command
from measurements.stats import percentile
from mininet.env_runner import EnvRunner


LINK = 's2-s3'
BW_LOW = 5.0
BW_HIGH = 15.0
SATURATION_PORT = 5004
POLL = 0.2
STABLE_N = 3
STABLE_TOL = 0.05
CHANGE_MIN = 0.10


def _link_read(session, thing_id):
    things, _meta = fetch_all_things(session, [thing_id])
    thing = things.get(thing_id, {})
    features = thing.get('features', {})
    cap = features.get('capacity', {}).get('properties', {}).get('bwMbps')
    traffic = features.get('traffic', {}).get('properties', {})
    meta = features.get('meta', {}).get('properties', {})
    tsource = meta.get('tSource')
    rate_bytes = max(traffic.get('rxRate') or 0.0,
                     traffic.get('txRate') or 0.0)
    return cap, float(rate_bytes) * 8.0 / 1e6, tsource


def _stable(values, tol):
    if len(values) < STABLE_N:
        return False
    high = max(values)
    low = min(values)
    return (high - low) / max(high, 0.01) < tol


def wait_rate_stable(session, thing_id, timeout=12.0, min_rate_mbps=0.1):
    hist = []
    last_ts = None
    t0 = time.monotonic()
    last = 0.0
    while time.monotonic() - t0 < timeout:
        _cap, rate, ts = _link_read(session, thing_id)
        last = rate
        if ts is not None and ts != last_ts:
            last_ts = ts
            hist.append(rate)
            hist = hist[-STABLE_N:]
            if rate >= min_rate_mbps and _stable(hist, STABLE_TOL):
                return True, rate
        time.sleep(POLL)
    return False, last


def measure_once(session, thing_id, bw_to, timeout=12.0):
    _cap_before, rate_before, _ts0 = _link_read(session, thing_id)
    t0 = send_command('setBandwidth', thing_id, {'bw': bw_to})
    t1 = None
    hist = []
    last_ts = None
    n_samples = 0

    while time.monotonic() - t0 < timeout:
        cap, rate, ts = _link_read(session, thing_id)
        now = time.monotonic()

        if t1 is None and cap is not None and abs(float(cap) - bw_to) < 0.01:
            t1 = now - t0

        if ts is not None and ts != last_ts:
            last_ts = ts
            n_samples += 1
            hist.append(rate)
            hist = hist[-STABLE_N:]

            if len(hist) == STABLE_N and rate_before > 0.1:
                changed = abs(rate - rate_before) / rate_before
                if _stable(hist, STABLE_TOL) and changed > CHANGE_MIN:
                    return {
                        't1_s': t1,
                        't2_s': now - t0,
                        'n_collector_samples': n_samples,
                        'rate_before_mbps': rate_before,
                        'rate_after_mbps': rate,
                    }
        time.sleep(POLL)

    return {
        't1_s': t1,
        't2_s': None,
        'n_collector_samples': n_samples,
        'rate_before_mbps': rate_before,
        'rate_after_mbps': hist[-1] if hist else None,
    }


def summarize(values):
    values = sorted([v for v in values if v is not None])
    if not values:
        return None
    return {
        'n': len(values),
        'mean_s': statistics.mean(values),
        'p50_s': statistics.median(values),
        'p95_s': percentile(values, 0.95),
        'max_s': max(values),
        'min_s': min(values),
    }


def start_saturation_traffic(net):
    srv1 = net.get('srv1')
    srv2 = net.get('srv2')
    for host in (srv1, srv2):
        host.cmd('pkill -f "iperf.*%d" 2>/dev/null' % SATURATION_PORT)
    srv2.cmd('iperf -s -p %d > /tmp/delta_iperf_srv2.log 2>&1 &' %
             SATURATION_PORT)
    time.sleep(0.5)
    srv1.cmd('iperf -c %s -p %d -t 100000 '
             '> /tmp/delta_iperf_srv1.log 2>&1 &' %
             (srv2.IP(), SATURATION_PORT))


def main():
    p = argparse.ArgumentParser(description='Measure DT4N env step Delta')
    p.add_argument('--trials', type=int, default=20)
    p.add_argument('--period', type=float, default=1.0)
    p.add_argument('--timeout', type=float, default=12.0)
    p.add_argument('--margin', type=float, default=0.3)
    p.add_argument('--out', default='docs/phase-4.5/delta.json')
    args = p.parse_args()

    session = make_session()
    thing_id = make_thing_id_link(*LINK.split('-', 1))
    runner = EnvRunner(sync_period=args.period, hard_every=0,
                       do_pingall=False, mininet_log_level='info')
    rows = []

    try:
        runner.start()
        send_command('setBandwidth', thing_id, {'bw': BW_LOW})
        start_saturation_traffic(runner.net)
        ok, rate = wait_rate_stable(session, thing_id, timeout=args.timeout,
                                    min_rate_mbps=1.0)
        print('baseline saturated=%s rate=%.2fMbps' % (ok, rate))
        if not ok or rate < 3.0:
            print('WARNING: s2-s3 may not be saturated; t2 can be invalid.')

        for idx in range(1, args.trials + 1):
            row = measure_once(session, thing_id, BW_HIGH,
                               timeout=args.timeout)
            rows.append(row)
            print('%02d t1=%s t2=%s samples=%d rate %.2f->%s Mbps' % (
                idx,
                '%.2fs' % row['t1_s'] if row['t1_s'] is not None else 'TIMEOUT',
                '%.2fs' % row['t2_s'] if row['t2_s'] is not None else 'TIMEOUT',
                row['n_collector_samples'],
                row['rate_before_mbps'],
                '%.2f' % row['rate_after_mbps']
                if row['rate_after_mbps'] is not None else 'NA',
            ))
            send_command('setBandwidth', thing_id, {'bw': BW_LOW})
            wait_rate_stable(session, thing_id, timeout=args.timeout,
                             min_rate_mbps=1.0)
    finally:
        try:
            send_command('setBandwidth', thing_id, {'bw': BW_LOW})
        except Exception:
            pass
        runner.close()

    t1_stats = summarize([row['t1_s'] for row in rows])
    t2_stats = summarize([row['t2_s'] for row in rows])
    delta = None
    if t2_stats is not None:
        delta = t2_stats['p95_s'] + args.margin

    result = {
        'measured': t2_stats is not None,
        'link': LINK,
        'bw_low_mbps': BW_LOW,
        'bw_high_mbps': BW_HIGH,
        'period_s': args.period,
        'poll_interval_s': POLL,
        'stable_n': STABLE_N,
        'stable_tol': STABLE_TOL,
        'change_min': CHANGE_MIN,
        'margin_s': args.margin,
        't2_resolution_note': (
            'The t2 measurement resolves the consequence only at collector '
            'sample boundaries (period=%.1fs), with poll granularity %.2fs. '
            'Reported t2 therefore has a systematic floor of STABLE_N*period.'
            % (args.period, POLL)
        ),
        't1': t1_stats,
        't2': t2_stats,
        'delta_s': delta,
        'rows': rows,
    }

    if t1_stats and t2_stats and t1_stats['p95_s'] > 0:
        result['t2_over_t1_p95'] = t2_stats['p95_s'] / t1_stats['p95_s']

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')

    print('\n=== RESULT ===')
    print('t1:', t1_stats)
    print('t2:', t2_stats)
    print('Delta:', delta)
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Run one loaded-AoI measurement with a temporary Mininet testbed.

This is intentionally a file, not a heredoc command: cleanup helpers use
``pkill -f iperf`` and must not see the measurement source text in argv.
"""

import argparse
import json
import os
import statistics
import time

import requests

from bridge.ditto_common import DITTO_AUTH, DITTO_BASE_URL, HTTP_TIMEOUT
from mininet.env_runner import EnvRunner
from mininet.traffic import (
    IPERF_PORT,
    run_host_shell,
    start_iperf_server,
    stop_all_iperf,
)


LINKS = ('org.dt4n:link-s1-s2', 'org.dt4n:link-s1-s3')


def thing_url(thing_id):
    return '%s/things/%s' % (DITTO_BASE_URL, thing_id)


def read_thing(session, thing_id):
    r = session.get(thing_url(thing_id), auth=DITTO_AUTH,
                    timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()


def t_source(thing):
    return (thing.get('features', {})
            .get('meta', {})
            .get('properties', {})
            .get('tSource'))


def traffic(thing):
    return (thing.get('features', {})
            .get('traffic', {})
            .get('properties', {}))


def mbps(bytes_per_s):
    try:
        return float(bytes_per_s) * 8.0 / 1e6
    except (TypeError, ValueError):
        return 0.0


def percentile(sorted_values, q):
    if not sorted_values:
        return None
    idx = int(q * (len(sorted_values) - 1))
    idx = max(0, min(idx, len(sorted_values) - 1))
    return sorted_values[idx]


def summarize(rows, polling):
    vals = [r['aoi_s'] for r in rows if r.get('ok')]
    ts_values = [r['t_source'] for r in rows if r.get('ok')]
    distinct = sorted(set(ts_values))
    if not vals:
        return {
            'verdict': 'NO_VALID_SAMPLE',
            'n_valid': 0,
            'n_total': len(rows),
            'distinct_t_source': len(distinct),
        }

    sorted_vals = sorted(vals)
    aoi_min = min(vals)
    aoi_mean = statistics.mean(vals)
    expected = aoi_min + polling / 2.0
    ratio = aoi_mean / expected if expected > 0 else 0.0
    if len(distinct) <= 2:
        verdict = 'INVALID_STALE_TSOURCE'
    elif ratio < 1.5:
        verdict = 'OK_LOADED_FRESH'
    else:
        verdict = 'WARN_HIGH_AOI'

    return {
        'verdict': verdict,
        'n_valid': len(vals),
        'n_total': len(rows),
        'distinct_t_source': len(distinct),
        't_source_span_s': (
            ts_values[-1] - ts_values[0] if len(ts_values) > 1 else 0.0
        ),
        'mean_s': aoi_mean,
        'p95_s': percentile(sorted_vals, 0.95),
        'min_s': aoi_min,
        'max_s': max(vals),
        'expected_mean_s': expected,
        'observed_over_expected_ratio': ratio,
    }


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--samples', type=int, default=120)
    ap.add_argument('--interval', type=float, default=0.2)
    ap.add_argument('--polling-period', type=float, default=0.5)
    ap.add_argument('--duration', type=int, default=100)
    ap.add_argument('--rate-a', default='14M')
    ap.add_argument('--rate-b', default='5M')
    ap.add_argument('--out', default='results/aoi/aoi_LOADED_A14_B5_codex_live.json')
    return ap.parse_args()


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    session = requests.Session()
    report = {
        'condition': 'LOADED_A%s_B%s' % (args.rate_a, args.rate_b),
        'polling_period_s': args.polling_period,
        'interval_s': args.interval,
        'samples': args.samples,
        'links': list(LINKS),
        'records': {link: [] for link in LINKS},
    }

    runner = EnvRunner(
        sync_period=args.polling_period,
        reconcile_every=30,
        ping_every=0,
        hard_every=0,
        do_pingall=False,
        mininet_log_level='warning',
    )

    print('== START TEMP TESTBED ==', flush=True)
    runner.start()
    try:
        net = runner.net
        print('sync_alive_after_start=%s' % runner._sync_thread.is_alive(),
              flush=True)

        stop_all_iperf(*net.hosts)
        start_iperf_server(net.get('srv1'), udp=True)
        start_iperf_server(net.get('srv2'), udp=True)
        run_host_shell(
            net.get('h1'),
            'iperf -c %s -u -b %s -p %d -t %d '
            '> /tmp/aoi_codex_h1_srv1.log 2>&1 &'
            % (net.get('srv1').IP(), args.rate_a, IPERF_PORT, args.duration),
        )
        run_host_shell(
            net.get('h2'),
            'iperf -c %s -u -b %s -p %d -t %d '
            '> /tmp/aoi_codex_h2_srv2.log 2>&1 &'
            % (net.get('srv2').IP(), args.rate_b, IPERF_PORT, args.duration),
        )
        print('traffic=A h1->srv1 %s, B h2->srv2 %s'
              % (args.rate_a, args.rate_b), flush=True)

        time.sleep(6.0)
        print('sync_alive_before_measure=%s'
              % runner._sync_thread.is_alive(), flush=True)

        for link in LINKS:
            thing = read_thing(session, link)
            tr = traffic(thing)
            print('precheck %-22s tSource=%s rx=%.2fMbps tx=%.2fMbps'
                  % (link, t_source(thing), mbps(tr.get('rxRate')),
                     mbps(tr.get('txRate'))),
                  flush=True)

        print('== SAMPLE AoI ==', flush=True)
        for i in range(1, args.samples + 1):
            now = time.time()
            for link in LINKS:
                try:
                    thing = read_thing(session, link)
                    ts = float(t_source(thing))
                    tr = traffic(thing)
                    rec = {
                        'i': i,
                        'ok': True,
                        't_source': ts,
                        'aoi_s': now - ts,
                        'rx_mbps': mbps(tr.get('rxRate')),
                        'tx_mbps': mbps(tr.get('txRate')),
                    }
                except Exception as exc:
                    rec = {'i': i, 'ok': False, 'error': str(exc)}
                report['records'][link].append(rec)

            if i <= 8 or i % 20 == 0 or i == args.samples:
                parts = []
                for link in LINKS:
                    rec = report['records'][link][-1]
                    if rec.get('ok'):
                        parts.append('%s AoI=%.3f tS=%.3f tx=%.2fM'
                                     % (link.rsplit(':', 1)[-1],
                                        rec['aoi_s'], rec['t_source'],
                                        rec.get('tx_mbps') or 0.0))
                    else:
                        parts.append('%s ERR=%s'
                                     % (link.rsplit(':', 1)[-1],
                                        rec.get('error')))
                print('%03d  %s' % (i, ' | '.join(parts)), flush=True)
            time.sleep(args.interval)

        report['summary'] = {
            link: summarize(report['records'][link], args.polling_period)
            for link in LINKS
        }
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, sort_keys=True)

        print('== SUMMARY ==', flush=True)
        for link, item in report['summary'].items():
            print(
                '%s: verdict=%s valid=%s/%s distinct_tSource=%s '
                'span=%.3fs mean=%.3fs p95=%.3fs min=%.3fs max=%.3fs '
                'ratio=%.2f'
                % (
                    link,
                    item.get('verdict'),
                    item.get('n_valid'),
                    item.get('n_total'),
                    item.get('distinct_t_source'),
                    item.get('t_source_span_s') or 0.0,
                    item.get('mean_s') or 0.0,
                    item.get('p95_s') or 0.0,
                    item.get('min_s') or 0.0,
                    item.get('max_s') or 0.0,
                    item.get('observed_over_expected_ratio') or 0.0,
                ),
                flush=True,
            )
        print('wrote %s' % args.out, flush=True)
    finally:
        print('== CLEANUP TEMP TESTBED ==', flush=True)
        runner.close(cleanup_mn=False)


if __name__ == '__main__':
    main()

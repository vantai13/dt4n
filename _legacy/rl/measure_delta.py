#!/usr/bin/env python3
"""Measure env step delay Delta for action consequences.

The important distinction:
  t1: capacity.bwMbps changed in the twin (command reflection)
  t2: traffic.rxRate/txRate stabilized at the new level (consequence reflection)

Delta should be p95(t2) + margin, not p95(t1). This script also decomposes t2
into command routing/execution, collector-sample delay, and sample-to-visible
delay using command_flow.log plus Ditto meta.tSource.
"""

import argparse
import csv
import datetime as dt
import json
import logging
import os
import re
import statistics
import sys
import threading
import time
import uuid

import requests


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_common import (  # noqa: E402
    DITTO_AUTH,
    DITTO_BASE_URL,
    HTTP_TIMEOUT,
    NAMESPACE,
    make_thing_id_link,
)
from bridge.ditto_reader import fetch_all_things, make_session  # noqa: E402
from bridge.flow_log import FLOW_LOG_PATH  # noqa: E402
from measurements.stats import percentile  # noqa: E402
from mininet.env_runner import EnvRunner  # noqa: E402
from mininet.traffic import run_host_shell  # noqa: E402


LINK = 's2-s3'
BW_LOW = 5.0
BW_HIGH = 15.0
SATURATION_PORT = 5004
POLL = 0.2
STABLE_N = 3
STABLE_TOL = 0.05
CHANGE_MIN = 0.10
CHANGE_FRAC = 0.50

CONTROLLER = '%s:controller' % NAMESPACE
FLOW_TS_RE = re.compile(r'^\[([\d-]+ [\d:.]+)\]')
FIELD_RE = re.compile(r'(?P<key>[A-Za-z_][\w-]*)=(?P<value>[^\s\]]*)')


def configure_logging(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    handler = logging.FileHandler(path, mode='w', encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def reset_file(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8'):
        pass
    try:
        os.chmod(path, 0o666)
    except OSError:
        pass


def _link_read(session, thing_id):
    things, meta = fetch_all_things(session, [thing_id])
    thing = things.get(thing_id, {})
    features = thing.get('features', {})
    cap = features.get('capacity', {}).get('properties', {}).get('bwMbps')
    traffic = features.get('traffic', {}).get('properties', {})
    tsource = (features.get('meta', {})
               .get('properties', {})
               .get('tSource'))
    rate_bytes = max(traffic.get('rxRate') or 0.0,
                     traffic.get('txRate') or 0.0)
    read_wall = meta.get('read_times', {}).get(thing_id, meta.get('t_read'))
    return {
        'cap': cap,
        'rate_mbps': float(rate_bytes) * 8.0 / 1e6,
        't_source_wall': float(tsource) if tsource is not None else None,
        'read_wall': read_wall,
        'fetch_ms': meta.get('fetch_ms'),
        'n_ok': meta.get('n_ok'),
        'n_fail': meta.get('n_fail'),
    }


def _stable(values, tol):
    if len(values) < STABLE_N:
        return False
    high = max(values)
    low = min(values)
    return (high - low) / max(high, 0.01) < tol


def wait_capacity(session, thing_id, bw, timeout=8.0):
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        sample = _link_read(session, thing_id)
        cap = sample.get('cap')
        if cap is not None and abs(float(cap) - bw) < 0.01:
            return True, sample
        time.sleep(POLL)
    return False, _link_read(session, thing_id)


def wait_rate_stable(session, thing_id, timeout=12.0, min_rate_mbps=0.1,
                     max_rate_mbps=None):
    hist = []
    last_ts = None
    started = time.monotonic()
    last = _link_read(session, thing_id)
    while time.monotonic() - started < timeout:
        sample = _link_read(session, thing_id)
        last = sample
        rate = sample['rate_mbps']
        ts = sample['t_source_wall']
        if ts is not None and ts != last_ts:
            last_ts = ts
            hist.append(rate)
            hist = hist[-STABLE_N:]
            within = rate >= min_rate_mbps
            if max_rate_mbps is not None:
                within = within and rate <= max_rate_mbps
            if within and _stable(hist, STABLE_TOL):
                return True, sample
        time.sleep(POLL)
    return False, last


def send_command_traced(subject, target, params=None):
    cid = str(uuid.uuid4())
    url = '%s/things/%s/inbox/messages/%s?timeout=0' % (
        DITTO_BASE_URL, CONTROLLER, subject)
    body = {
        'target': target,
        'clientCorrelationId': cid,
    }
    if params:
        body.update(params)
    headers = {
        'Content-Type': 'application/json',
        'correlation-id': cid,
    }

    click_mono = time.monotonic()
    click_wall = time.time()
    command = {
        'cid': cid,
        'click_mono': click_mono,
        'click_wall': click_wall,
        'post_ms': None,
        'http_status': None,
        'post_error': None,
    }
    done = threading.Event()

    def _post():
        post_started = time.monotonic()
        try:
            response = requests.post(url, json=body, headers=headers,
                                     auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
            command['http_status'] = response.status_code
        except requests.exceptions.RequestException as exc:
            command['post_error'] = '%s:%s' % (type(exc).__name__, exc)
        finally:
            command['post_ms'] = (time.monotonic() - post_started) * 1000.0
            done.set()

    thread = threading.Thread(target=_post,
                              name='delta-post-%s' % cid[:8],
                              daemon=True)
    command['_post_done'] = done
    command['_post_thread'] = thread
    thread.start()
    return command


def wait_command_post(command, timeout=0.0):
    done = command.get('_post_done')
    if done is not None:
        done.wait(timeout)


def parse_flow_timestamp(line):
    match = FLOW_TS_RE.match(line)
    if not match:
        return None
    parsed = dt.datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S.%f')
    return parsed.timestamp()


def parse_fields(line):
    return {m.group('key'): m.group('value') for m in FIELD_RE.finditer(line)}


def flow_timing_for_cid(cid, click_wall, flow_log=FLOW_LOG_PATH):
    timing = {
        'route_ms': None,
        'lock_wait_ms': None,
        'exec_ms': None,
        'command_done_ms': None,
        'execute_error': None,
    }
    if not os.path.exists(flow_log):
        return timing

    times = {}
    fields_by_event = {}
    with open(flow_log, encoding='utf-8', errors='ignore') as f:
        for line in f:
            if '[cid=%s]' % cid not in line:
                continue
            ts = parse_flow_timestamp(line)
            if ts is None:
                continue
            for event in ('RECEIVE', 'LOCK_WAIT', 'EXECUTE_DONE',
                          'EXECUTE_ERROR'):
                if event in line and event not in times:
                    times[event] = ts
                    fields_by_event[event] = parse_fields(line)

    if 'RECEIVE' in times:
        timing['route_ms'] = (times['RECEIVE'] - click_wall) * 1000.0
    if 'LOCK_WAIT' in fields_by_event:
        try:
            timing['lock_wait_ms'] = float(
                fields_by_event['LOCK_WAIT'].get('waitMs'))
        except (TypeError, ValueError):
            pass
    if 'RECEIVE' in times and 'EXECUTE_DONE' in times:
        timing['exec_ms'] = (times['EXECUTE_DONE'] - times['RECEIVE']) * 1000.0
    if 'EXECUTE_DONE' in times:
        timing['command_done_ms'] = (
            times['EXECUTE_DONE'] - click_wall) * 1000.0
        timing['exec_done_wall'] = times['EXECUTE_DONE']
    if 'EXECUTE_ERROR' in times:
        timing['execute_error'] = True
    return timing


def add_decomposition(row):
    click_wall = row.get('click_wall')
    exec_done = row.get('exec_done_wall')

    for prefix in ('t1', 't_change', 't2'):
        source = row.get('%s_source_wall' % prefix)
        seen = row.get('%s_seen_wall' % prefix)
        if source is not None and click_wall is not None:
            row['%s_command_to_sample_ms' % prefix] = (
                source - click_wall) * 1000.0
        else:
            row['%s_command_to_sample_ms' % prefix] = None
        if source is not None and seen is not None:
            row['%s_sample_to_seen_ms' % prefix] = (
                seen - source) * 1000.0
        else:
            row['%s_sample_to_seen_ms' % prefix] = None

    if exec_done is not None and row.get('t2_source_wall') is not None:
        row['metric_settle_after_exec_ms'] = (
            row['t2_source_wall'] - exec_done) * 1000.0
    else:
        row['metric_settle_after_exec_ms'] = None
    if exec_done is not None and row.get('t_change_source_wall') is not None:
        row['metric_change_after_exec_ms'] = (
            row['t_change_source_wall'] - exec_done) * 1000.0
    else:
        row['metric_change_after_exec_ms'] = None
    return row


def measure_once(session, thing_id, bw_to, timeout=12.0,
                 change_min=CHANGE_MIN, change_threshold_mbps=None,
                 change_frac=CHANGE_FRAC, sigma_rate_mbps=None):
    before = _link_read(session, thing_id)
    command = send_command_traced('setBandwidth', thing_id, {'bw': bw_to})
    t0 = command['click_mono']
    t1 = None
    t1_sample = None
    t_change = None
    t_change_sample = None
    t2_sample = None
    hist = []
    samples = []
    last_ts = None

    while time.monotonic() - t0 < timeout:
        sample = _link_read(session, thing_id)
        now_mono = time.monotonic()

        cap = sample.get('cap')
        if t1 is None and cap is not None and abs(float(cap) - bw_to) < 0.01:
            t1 = now_mono - t0
            t1_sample = dict(sample)
            t1_sample['seen_mono'] = now_mono

        ts = sample['t_source_wall']
        rate = sample['rate_mbps']
        if ts is not None and ts != last_ts:
            last_ts = ts
            enriched = dict(sample)
            enriched['seen_mono'] = now_mono
            samples.append(enriched)
            if t_change is None and before['rate_mbps'] > 0.1:
                abs_delta = abs(rate - before['rate_mbps'])
                rel_delta = abs_delta / before['rate_mbps']
                try:
                    expected_swing = abs(float(bw_to) - before['rate_mbps'])
                except (TypeError, ValueError):
                    expected_swing = before['rate_mbps']
                cap_before = before.get('cap')
                try:
                    expect_increase = float(bw_to) > float(cap_before)
                except (TypeError, ValueError):
                    expect_increase = True
                if expect_increase:
                    direction_ok = rate > before['rate_mbps']
                else:
                    direction_ok = rate < before['rate_mbps']
                enough_abs = (
                    change_threshold_mbps is not None
                    and abs_delta >= change_threshold_mbps
                )
                enough_rel = rel_delta > change_min
                if change_frac is not None:
                    enough_change = (
                        abs_delta >= change_frac * max(expected_swing, 0.01))
                    if sigma_rate_mbps is not None:
                        enough_change = (
                            enough_change
                            and abs_delta >= 3.0 * sigma_rate_mbps)
                    if change_threshold_mbps is not None:
                        enough_change = (
                            enough_change
                            and abs_delta >= change_threshold_mbps)
                else:
                    enough_change = enough_abs or enough_rel
                if direction_ok and enough_change:
                    t_change = now_mono - t0
                    t_change_sample = enriched
            hist.append(rate)
            hist = hist[-STABLE_N:]

            if len(hist) == STABLE_N and before['rate_mbps'] > 0.1:
                changed = abs(rate - before['rate_mbps']) / before['rate_mbps']
                if _stable(hist, STABLE_TOL) and changed > CHANGE_MIN:
                    t2_sample = enriched
                    break
        time.sleep(POLL)

    wait_command_post(command, timeout=0.2)
    flow = flow_timing_for_cid(command['cid'], command['click_wall'])
    row = {
        'cid': command['cid'],
        'http_status': command['http_status'],
        'post_error': command['post_error'],
        'post_ms': command['post_ms'],
        'click_wall': command['click_wall'],
        'route_ms': flow.get('route_ms'),
        'lock_wait_ms': flow.get('lock_wait_ms'),
        'exec_ms': flow.get('exec_ms'),
        'command_done_ms': flow.get('command_done_ms'),
        'exec_done_wall': flow.get('exec_done_wall'),
        'execute_error': flow.get('execute_error'),
        't1_s': t1,
        't_change_s': t_change,
        't2_s': ((t2_sample['seen_mono'] - t0) if t2_sample else None),
        'n_collector_samples': len(samples),
        'rate_before_mbps': before['rate_mbps'],
        'rate_change_mbps': (
            t_change_sample['rate_mbps'] if t_change_sample else None),
        'change_progress_frac': (
            abs(t_change_sample['rate_mbps'] - before['rate_mbps'])
            / max(abs(float(bw_to) - before['rate_mbps']), 0.01)
            if t_change_sample else None),
        'rate_after_mbps': t2_sample['rate_mbps'] if t2_sample else (
            samples[-1]['rate_mbps'] if samples else None),
        'cap_before_mbps': before['cap'],
        'cap_after_mbps': t1_sample['cap'] if t1_sample else None,
        't1_source_wall': t1_sample.get('t_source_wall') if t1_sample else None,
        't1_seen_wall': t1_sample.get('read_wall') if t1_sample else None,
        't1_fetch_ms': t1_sample.get('fetch_ms') if t1_sample else None,
        't_change_source_wall': (
            t_change_sample.get('t_source_wall') if t_change_sample else None),
        't_change_seen_wall': (
            t_change_sample.get('read_wall') if t_change_sample else None),
        't_change_fetch_ms': (
            t_change_sample.get('fetch_ms') if t_change_sample else None),
        't2_source_wall': t2_sample.get('t_source_wall') if t2_sample else None,
        't2_seen_wall': t2_sample.get('read_wall') if t2_sample else None,
        't2_fetch_ms': t2_sample.get('fetch_ms') if t2_sample else None,
        'collector_sample_rates_mbps': [
            round(sample['rate_mbps'], 3) for sample in samples
        ],
        'collector_sample_sources': [
            sample['t_source_wall'] for sample in samples
        ],
    }
    return add_decomposition(row)


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


def summarize_ms(rows, key):
    values = [row.get(key) / 1000.0 for row in rows
              if isinstance(row.get(key), (int, float))]
    return summarize(values)


def start_saturation_traffic(net, traffic='tcp', udp_rate_mbps=20.0):
    srv1 = net.get('srv1')
    srv2 = net.get('srv2')
    for host in (srv1, srv2):
        run_host_shell(
            host,
            'pkill -f "iperf.*%d" 2>/dev/null' % SATURATION_PORT,
        )
    udp = traffic == 'udp'
    run_host_shell(
        srv2,
        'iperf -s %s -p %d > /tmp/delta_iperf_srv2.log 2>&1 &'
        % ('-u' if udp else '', SATURATION_PORT),
    )
    time.sleep(0.5)
    if udp:
        command = (
            'iperf -c %s -u -b %gM -p %d -t 100000 '
            '> /tmp/delta_iperf_srv1.log 2>&1 &'
            % (srv2.IP(), udp_rate_mbps, SATURATION_PORT)
        )
    else:
        command = (
            'iperf -c %s -p %d -t 100000 '
            '> /tmp/delta_iperf_srv1.log 2>&1 &'
            % (srv2.IP(), SATURATION_PORT)
        )
    run_host_shell(
        srv1,
        command,
    )


def write_csv(path, rows):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    fields = [
        'trial',
        'cid',
        'post_ms',
        'route_ms',
        'lock_wait_ms',
        'exec_ms',
        'command_done_ms',
        't1_s',
        't1_command_to_sample_ms',
        't1_sample_to_seen_ms',
        't_change_s',
        't_change_command_to_sample_ms',
        'metric_change_after_exec_ms',
        't_change_sample_to_seen_ms',
        't2_s',
        't2_command_to_sample_ms',
        'metric_settle_after_exec_ms',
        't2_sample_to_seen_ms',
        't2_fetch_ms',
        'n_collector_samples',
        'rate_before_mbps',
        'rate_change_mbps',
        'change_progress_frac',
        'rate_after_mbps',
        'cap_before_mbps',
        'cap_after_mbps',
        'http_status',
        'post_error',
        'execute_error',
    ]
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for idx, row in enumerate(rows, 1):
            out = dict(row)
            out['trial'] = idx
            writer.writerow(out)


def main():
    p = argparse.ArgumentParser(description='Measure DT4N env step Delta')
    p.add_argument('--trials', type=int, default=20)
    p.add_argument('--period', type=float, default=1.0)
    p.add_argument('--timeout', type=float, default=12.0)
    p.add_argument('--margin', type=float, default=0.3)
    p.add_argument('--traffic', choices=('tcp', 'udp'), default='tcp')
    p.add_argument('--sat-mode', dest='traffic', choices=('tcp', 'udp'),
                   help='alias for --traffic')
    p.add_argument('--udp-rate-mbps', type=float, default=20.0)
    p.add_argument('--change-min', type=float, default=CHANGE_MIN,
                   help='relative threshold for t_change detection')
    p.add_argument('--change-frac', type=float, default=CHANGE_FRAC,
                   help='expected swing fraction for t_50 detection; '
                        'set negative to use legacy change-min logic')
    p.add_argument('--change-threshold-mbps', type=float, default=None,
                   help='optional absolute threshold for t_change detection')
    p.add_argument('--sigma-mbps', type=float, default=None,
                   help='robust rate sigma in Mbps; t_50 must exceed 3*sigma')
    p.add_argument('--sigma-json', default=None,
                   help='JSON with robust_sigma_mbps for t_50 noise gate')
    p.add_argument('--out', default='docs/phase-4.5/artifacts/delta.json')
    p.add_argument('--csv', default='docs/phase-4.5/artifacts/delta_components.csv')
    p.add_argument('--log-path', default='docs/phase-4.5/raw/delta_runtime.log')
    p.add_argument('--flow-log-copy',
                   default='docs/phase-4.5/raw/delta_command_flow.log')
    p.add_argument('--run-sync-log-copy',
                   default='docs/phase-4.5/raw/delta_run_sync.log')
    args = p.parse_args()
    if args.change_frac is not None and args.change_frac < 0:
        args.change_frac = None
    sigma_rate_mbps = args.sigma_mbps
    if args.sigma_json:
        with open(args.sigma_json, encoding='utf-8') as f:
            sigma_data = json.load(f)
        sigma_rate_mbps = sigma_data.get('robust_sigma_mbps', sigma_rate_mbps)

    configure_logging(args.log_path)
    reset_file(FLOW_LOG_PATH)
    if os.path.exists('logs/run_sync.log'):
        reset_file('logs/run_sync.log')

    session = make_session()
    thing_id = make_thing_id_link(*LINK.split('-', 1))
    runner = EnvRunner(sync_period=args.period, hard_every=0,
                       do_pingall=False, mininet_log_level='info',
                       ping_every=0, reconcile_every=30)
    rows = []
    baseline = {}

    try:
        runner.start()
        send_command_traced('setBandwidth', thing_id, {'bw': BW_LOW})
        wait_capacity(session, thing_id, BW_LOW, timeout=args.timeout)
        start_saturation_traffic(runner.net, traffic=args.traffic,
                                 udp_rate_mbps=args.udp_rate_mbps)
        ok, sample = wait_rate_stable(
            session, thing_id, timeout=args.timeout,
            min_rate_mbps=3.0, max_rate_mbps=8.5)
        baseline = {
            'saturated_low_ok': ok,
            'low_rate_mbps': sample['rate_mbps'],
            'low_capacity_mbps': sample['cap'],
            'traffic': args.traffic,
            'udp_rate_mbps': args.udp_rate_mbps if args.traffic == 'udp' else None,
        }
        print('baseline traffic=%s saturated=%s rate=%.2fMbps cap=%s' % (
            args.traffic, ok, sample['rate_mbps'], sample['cap']))
        if not ok:
            print('WARNING: s2-s3 is not stably saturated at low bandwidth; '
                  't2 can be invalid.')

        for idx in range(1, args.trials + 1):
            row = measure_once(session, thing_id, BW_HIGH,
                               timeout=args.timeout,
                               change_min=args.change_min,
                               change_threshold_mbps=args.change_threshold_mbps,
                               change_frac=args.change_frac,
                               sigma_rate_mbps=sigma_rate_mbps)
            rows.append(row)
            print('%02d t1=%s t_change=%s t2=%s cmd=%s change=%s '
                  'settle=%s sample_seen=%s samples=%d rate %.2f->%s->%s Mbps' % (
                      idx,
                      '%.2fs' % row['t1_s']
                      if row['t1_s'] is not None else 'TIMEOUT',
                      '%.2fs' % row['t_change_s']
                      if row['t_change_s'] is not None else 'TIMEOUT',
                      '%.2fs' % row['t2_s']
                      if row['t2_s'] is not None else 'TIMEOUT',
                      '%.0fms' % row['command_done_ms']
                      if row.get('command_done_ms') is not None else 'NA',
                      '%.0fms' % row['metric_change_after_exec_ms']
                      if row.get('metric_change_after_exec_ms') is not None else 'NA',
                      '%.0fms' % row['metric_settle_after_exec_ms']
                      if row.get('metric_settle_after_exec_ms') is not None else 'NA',
                      '%.0fms' % row['t2_sample_to_seen_ms']
                      if row.get('t2_sample_to_seen_ms') is not None else 'NA',
                      row['n_collector_samples'],
                      row['rate_before_mbps'],
                      '%.2f' % row['rate_change_mbps']
                      if row['rate_change_mbps'] is not None else 'NA',
                      '%.2f' % row['rate_after_mbps']
                      if row['rate_after_mbps'] is not None else 'NA',
                  ))

            send_command_traced('setBandwidth', thing_id, {'bw': BW_LOW})
            wait_capacity(session, thing_id, BW_LOW, timeout=args.timeout)
            wait_rate_stable(session, thing_id, timeout=args.timeout,
                             min_rate_mbps=3.0, max_rate_mbps=8.5)
    finally:
        try:
            send_command_traced('setBandwidth', thing_id, {'bw': BW_LOW})
        except Exception:
            pass
        runner.close()

    t1_stats = summarize([row['t1_s'] for row in rows])
    t_change_stats = summarize([row['t_change_s'] for row in rows])
    t2_stats = summarize([row['t2_s'] for row in rows])
    delta_change = (
        t_change_stats['p95_s'] + args.margin
        if t_change_stats is not None else None
    )
    delta = t2_stats['p95_s'] + args.margin if t2_stats is not None else None

    result = {
        'measured': t2_stats is not None,
        'link': LINK,
        'bw_low_mbps': BW_LOW,
        'bw_high_mbps': BW_HIGH,
        'period_s': args.period,
        'traffic': args.traffic,
        'udp_rate_mbps': args.udp_rate_mbps if args.traffic == 'udp' else None,
        'poll_interval_s': POLL,
        'stable_n': STABLE_N,
        'stable_tol': STABLE_TOL,
        'change_min': args.change_min,
        'change_frac': args.change_frac,
        'change_threshold_mbps': args.change_threshold_mbps,
        'sigma_rate_mbps': sigma_rate_mbps,
        'margin_s': args.margin,
        'delta_change_s': delta_change,
        'delta_s': delta,
        'baseline': baseline,
        'notes': [
            't1 is capacity reflection; t2 is traffic consequence reflection.',
            't_change is the first new collector sample whose rate changed past the configured threshold.',
            'When change_frac is set, t_change is t_50: direction-correct progress through the expected swing and above the noise gate.',
            't2 uses only new collector samples (meta.tSource changes).',
            'Delta recommendation is p95(t2_s) + margin_s.',
            'Delta_change candidate is p95(t_change_s) + margin_s.',
            'component metric_settle_after_exec_ms is exec_done -> t2 sample tSource.',
            'component metric_change_after_exec_ms is exec_done -> t_change sample tSource.',
            'component t2_sample_to_seen_ms is t2 tSource -> measurement GET saw it.',
        ],
        't1': t1_stats,
        't_change': t_change_stats,
        't2': t2_stats,
        'components': {
            'post': summarize_ms(rows, 'post_ms'),
            'route': summarize_ms(rows, 'route_ms'),
            'lock_wait': summarize_ms(rows, 'lock_wait_ms'),
            'exec': summarize_ms(rows, 'exec_ms'),
            'command_done': summarize_ms(rows, 'command_done_ms'),
            't1_command_to_sample': summarize_ms(rows, 't1_command_to_sample_ms'),
            't1_sample_to_seen': summarize_ms(rows, 't1_sample_to_seen_ms'),
            't_change_command_to_sample': summarize_ms(
                rows, 't_change_command_to_sample_ms'),
            'metric_change_after_exec': summarize_ms(
                rows, 'metric_change_after_exec_ms'),
            't_change_sample_to_seen': summarize_ms(
                rows, 't_change_sample_to_seen_ms'),
            't2_command_to_sample': summarize_ms(rows, 't2_command_to_sample_ms'),
            'metric_settle_after_exec': summarize_ms(
                rows, 'metric_settle_after_exec_ms'),
            't2_sample_to_seen': summarize_ms(rows, 't2_sample_to_seen_ms'),
            't2_fetch': summarize_ms(rows, 't2_fetch_ms'),
        },
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
    write_csv(args.csv, rows)

    for src, dst in (
            (FLOW_LOG_PATH, args.flow_log_copy),
            ('logs/run_sync.log', args.run_sync_log_copy)):
        if os.path.exists(src):
            parent = os.path.dirname(os.path.abspath(dst))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(src, encoding='utf-8', errors='ignore') as fsrc:
                data = fsrc.read()
            with open(dst, 'w', encoding='utf-8') as fdst:
                fdst.write(data)

    print('\n=== RESULT ===')
    print('t1:', t1_stats)
    print('t_change:', t_change_stats)
    print('t2:', t2_stats)
    print('Delta_change:', delta_change)
    print('Delta:', delta)
    print('components:', result['components'])
    print('Wrote %s' % args.out)
    print('Wrote %s' % args.csv)


if __name__ == '__main__':
    main()

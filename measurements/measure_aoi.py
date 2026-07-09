#!/usr/bin/env python3
"""Sample Age of Information for one Ditto Thing.

AoI = time.time() - features.meta.properties.tSource
"""

import argparse
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_common import DITTO_BASE_URL, DITTO_AUTH, HTTP_TIMEOUT, NAMESPACE


def thing_url(thing_id):
    return '%s/things/%s' % (DITTO_BASE_URL, thing_id)


def read_t_source(session, thing_id):
    r = session.get(thing_url(thing_id), auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    thing = r.json()
    return thing.get('features', {}).get('meta', {}).get('properties', {}).get('tSource')


def main():
    p = argparse.ArgumentParser(description='Measure AoI from Ditto meta.tSource')
    p.add_argument('--thing', default='%s:link-s2-s3' % NAMESPACE,
                   help='Thing id, default org.dt4n:link-s2-s3')
    p.add_argument('--interval', type=float, default=0.2,
                   help='seconds between GET requests')
    p.add_argument('--samples', type=int, default=50,
                   help='number of samples')
    args = p.parse_args()

    try:
        import requests
    except ImportError:
        raise SystemExit(
            'THIEU requests trong interpreter nay. Chay bang interpreter co '
            'requests, vi du: /usr/bin/python3 measurements/measure_aoi.py')

    session = requests.Session()
    values = []
    print('thing=%s interval=%.3fs samples=%d' %
          (args.thing, args.interval, args.samples))
    print('i  tSource          AoI_s')
    print('-' * 34)

    prev_wall = None
    prev_mono = None
    for i in range(1, args.samples + 1):
        try:
            t_source = read_t_source(session, args.thing)
            wall_now = time.time()
            mono_now = time.monotonic()
            clock_note = ''
            if prev_wall is not None:
                wall_delta = wall_now - prev_wall
                mono_delta = mono_now - prev_mono
                drift = wall_delta - mono_delta
                if abs(drift) > 0.5:
                    clock_note = '  WARNING local clock jump %+0.3fs' % drift
            prev_wall = wall_now
            prev_mono = mono_now
            if t_source is None:
                print('%-2d %-16s %s%s' %
                      (i, '-', 'missing meta.tSource', clock_note))
            else:
                aoi = wall_now - float(t_source)
                values.append(aoi)
                note = '  WARNING clock skew' if aoi < -0.05 else ''
                print('%-2d %-16.3f %.3f%s%s' %
                      (i, float(t_source), aoi, note, clock_note))
        except Exception as exc:
            print('%-2d ERROR %s' % (i, exc))
        time.sleep(args.interval)

    if values:
        print('-' * 34)
        print('mean=%.3fs p95=%.3fs min=%.3fs max=%.3fs' % (
            statistics.mean(values),
            sorted(values)[int(0.95 * (len(values) - 1))],
            min(values),
            max(values),
        ))


if __name__ == '__main__':
    main()

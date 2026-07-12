#!/usr/bin/env python3
"""Sample Age of Information for one Ditto Thing.

AoI = time.time() - features.meta.properties.tSource
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

from bridge.ditto_common import DITTO_BASE_URL, DITTO_AUTH, HTTP_TIMEOUT, NAMESPACE


def thing_url(thing_id):
    return '%s/things/%s' % (DITTO_BASE_URL, thing_id)


def ensure_parent_dir(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


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
    p.add_argument('--polling-period', type=float, default=1.0,
                   help='chu ky polling cua collector (giay), de doi chieu d+T/2')
    p.add_argument('--out',
                   help='ghi ket qua JSON sau khi do, vi du docs/phase-5/artifacts/aoi_check.json')
    args = p.parse_args()

    try:
        import requests
    except ImportError:
        raise SystemExit(
            'THIEU requests trong interpreter nay. Chay bang interpreter co '
            'requests, vi du: /usr/bin/python3 measurements/measure_aoi.py')

    session = requests.Session()
    values = []
    records = []
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
                records.append({
                    'i': i,
                    'ok': False,
                    't_source': None,
                    'aoi_s': None,
                    'error': 'missing meta.tSource',
                    'clock_note': clock_note.strip() or None,
                })
            else:
                aoi = wall_now - float(t_source)
                values.append(aoi)
                note = '  WARNING clock skew' if aoi < -0.05 else ''
                print('%-2d %-16.3f %.3f%s%s' %
                      (i, float(t_source), aoi, note, clock_note))
                records.append({
                    'i': i,
                    'ok': True,
                    't_source': float(t_source),
                    'aoi_s': aoi,
                    'error': None,
                    'clock_note': clock_note.strip() or None,
                    'clock_skew_warning': aoi < -0.05,
                })
        except Exception as exc:
            print('%-2d ERROR %s' % (i, exc))
            records.append({
                'i': i,
                'ok': False,
                't_source': None,
                'aoi_s': None,
                'error': str(exc),
                'clock_note': None,
            })
        time.sleep(args.interval)

    summary = None
    theory = None
    if values:
        # ---- Doi chieu cong thuc AoI ~ d + T/2 ----
        # T = polling interval cua collector (giay).
        # d = delay co dinh pipeline, uoc bang AoI toi thieu quan sat duoc:
        #     luc data vua duoc cap nhat xong thi tuoi con lai chu yeu la delay d.
        T = args.polling_period
        sorted_values = sorted(values)
        aoi_mean = statistics.mean(values)
        aoi_min = min(values)
        aoi_p95 = sorted_values[min(int(0.95 * (len(sorted_values) - 1)),
                                    len(sorted_values) - 1)]
        d_est = aoi_min
        expected_mean = d_est + T / 2.0
        ratio = aoi_mean / expected_mean if expected_mean > 0 else float('nan')
        verdict = (
            'OK (pipeline lanh)' if ratio < 1.5
            else 'CANH BAO: pipeline tut hau (AoI phu len)'
        )

        print('')
        print('== DOI CHIEU d + T/2 ==')
        print('  T (polling)      = %.2f s' % T)
        print('  d (uoc = AoI min)= %.3f s' % d_est)
        print('  AoI mean (do)    = %.3f s' % aoi_mean)
        print('  AoI p95 (do)     = %.3f s' % aoi_p95)
        print('  Ky vong d + T/2  = %.3f s' % expected_mean)
        print('  Ty le do/ky vong = %.2f  %s' % (ratio, verdict))

        summary = {
            'mean_s': aoi_mean,
            'p95_s': aoi_p95,
            'min_s': aoi_min,
            'max_s': max(values),
            'n_valid': len(values),
            'n_total': args.samples,
        }
        theory = {
            'polling_period_s': T,
            'd_est_s': d_est,
            'expected_mean_s': expected_mean,
            'observed_over_expected_ratio': ratio,
            'verdict': verdict,
        }

        print('-' * 34)
        print('mean=%.3fs p95=%.3fs min=%.3fs max=%.3fs' % (
            aoi_mean,
            aoi_p95,
            aoi_min,
            max(values),
        ))

    if args.out:
        report = {
            'thing': args.thing,
            'interval_s': args.interval,
            'samples_requested': args.samples,
            'polling_period_s': args.polling_period,
            'summary': summary,
            'theory_check': theory,
            'records': records,
        }
        ensure_parent_dir(args.out)
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print('wrote %s' % args.out)


if __name__ == '__main__':
    main()

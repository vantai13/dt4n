#!/usr/bin/env python3
"""sweep_sync.py — chay MA TRAN polling x tai, xuat CSV + bang chuan cho Phase 7.

Ma tran: polling {0.5, 1, 2, 5} x tai {thap, vua, cao}. Moi o:
  - dung EnvRunner(sync_period=polling)
  - bat traffic muc tai tuong ung
  - do AoI (mean, p95) + fidelity (error mean, dominant source) trong >= do_seconds
  - ghi 1 dong CSV

CANH BAO THOI GIAN: 12 o x do_seconds. Voi do_seconds=120 (2 phut, RUT GON de
test truoc) -> ~30 phut. Voi 600 (10 phut, chuan bao cao) -> ~2 gio. Chay ban
rut gon TRUOC de chac script dung, roi moi chay ban day du qua dem.
"""

import argparse
import csv
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

POLLING = [0.5, 1.0, 2.0, 5.0]
LOADS = {                     # ten tai -> rate Mbps traffic nen
    'thap': 1.0,
    'vua': 5.0,
    'cao': 15.0,              # gan bao hoa bottleneck 5Mbps + backbone 20
}


def measure_cell(polling, load_rate, do_seconds, link):
    """Do 1 o (polling, load): tra dict AoI + fidelity."""
    import statistics
    from mininet.env_runner import EnvRunner
    from bridge.ditto_reader import expected_thing_ids, make_session, fetch_snapshot
    from bridge.ditto_common import make_thing_id_link
    from mininet.topology_meta import load_spec
    from measurements.fidelity import measure_fidelity_live, analyze_fidelity

    spec = load_spec('ditto/topology_spec.json')
    thing_ids = expected_thing_ids(spec)
    a, b = link.split('-')
    tid = make_thing_id_link(a, b)

    runner = EnvRunner(sync_period=polling)     # <-- DAT POLLING O DAY
    runner.start()
    aoi_values = []
    fidelity = {}
    try:
        runner.start_server_background(rate_mbps=load_rate)
        time.sleep(max(3.0, polling * 3))       # cho steady theo polling

        # --- do AoI song song bang cach lay tSource lien tuc ---
        session = make_session()
        t_end = time.monotonic() + do_seconds
        while time.monotonic() < t_end:
            _things, meta = fetch_snapshot(session, thing_ids)
            aoi = (meta.get('aoi') or {}).get(tid)
            if aoi is not None and aoi >= 0:
                aoi_values.append(float(aoi))
            time.sleep(min(0.3, polling / 3.0))

        # --- do fidelity (dung lai ham Buoc 2) ---
        n_fid = min(200, max(50, int(do_seconds / 0.5)))
        samples = measure_fidelity_live(runner, thing_ids, link,
                                        samples=n_fid, interval=0.5)
        fidelity = analyze_fidelity(samples)
    finally:
        runner.close()

    T = polling
    d_est = min(aoi_values) if aoi_values else 0.0
    aoi_mean = statistics.mean(aoi_values) if aoi_values else 0.0
    aoi_p95 = (sorted(aoi_values)[min(int(0.95 * (len(aoi_values) - 1)),
               len(aoi_values) - 1)] if aoi_values else 0.0)
    expected = d_est + T / 2.0
    return {
        'polling': polling, 'load': load_rate,
        'aoi_mean': round(aoi_mean, 3), 'aoi_p95': round(aoi_p95, 3),
        'aoi_min_d_est': round(d_est, 3),
        'expected_d_plus_T2': round(expected, 3),
        'aoi_ratio': round(aoi_mean / expected, 2) if expected > 0 else 0,
        'fidelity_err_mean': round(fidelity.get('error_mean', 0), 4),
        'staleness_slope': round(fidelity.get('staleness_error_slope', 0), 4),
        'fidelity_intercept': round(fidelity.get('fidelity_error_intercept', 0), 4),
        'dominant_source': fidelity.get('dominant_source', '?'),
        'n_aoi': len(aoi_values),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seconds', type=int, default=120,
                   help='giay moi o (120=rut gon test, 600=chuan bao cao)')
    p.add_argument('--link', default='s2-s3')
    p.add_argument('--out', default='docs/phase-5/artifacts/sweep_sync.csv')
    args = p.parse_args()

    rows = []
    total = len(POLLING) * len(LOADS)
    i = 0
    for polling in POLLING:
        for load_name, load_rate in LOADS.items():
            i += 1
            print('\n[%d/%d] O: polling=%.1fs load=%s(%gMbps) seconds=%d'
                  % (i, total, polling, load_name, load_rate, args.seconds))
            cell = measure_cell(polling, load_rate, args.seconds, args.link)
            cell['load_name'] = load_name
            rows.append(cell)
            print('  -> AoI mean=%.3f p95=%.3f ratio=%.2f | fid_err=%.4f dominant=%s'
                  % (cell['aoi_mean'], cell['aoi_p95'], cell['aoi_ratio'],
                     cell['fidelity_err_mean'], cell['dominant_source']))

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print('\n== BANG CHUAN (12 o) ==')
    print('%-8s %-6s %8s %8s %6s %10s %-14s'
          % ('polling', 'load', 'AoI_mean', 'AoI_p95', 'ratio', 'fid_err', 'dominant'))
    for r in rows:
        print('%-8.1f %-6s %8.3f %8.3f %6.2f %10.4f %-14s'
              % (r['polling'], r['load_name'], r['aoi_mean'], r['aoi_p95'],
                 r['aoi_ratio'], r['fidelity_err_mean'], r['dominant_source']))
    print('\nWrote %s' % args.out)


if __name__ == '__main__':
    main()
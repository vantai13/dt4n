#!/usr/bin/env python3
"""Do FIDELITY twin vs Mininet + tach sai-vi-CU khoi sai-vi-LOI.

Y tuong (Lesson 5.6):
  - Doc KEP: gia tri THAT tu Mininet (/proc/net/dev counter -> rate) va
    gia tri TWIN tu Ditto (rxRate) tai (gan) cung thoi diem.
  - Voi moi mau: error = |twin - real|/real, kem AoI cua mau twin.
  - Cuoi: hoi quy error theo AoI:  error ~ intercept + slope * AoI
       intercept = sai-vi-LOI (sai khi tuoi hoan hao, AoI=0) -> loi collector
       slope     = sai-vi-CU  (moi giay cu them gay them bao nhieu sai) -> staleness

Trung thuc ve gioi han: "cung thoi diem" chi dung toi Delta_t_read (khe lech
giua 2 lan doc, ~100ms). Ghi ro Delta_t_read vao output.
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# =====================================================================
# PHAN PURE — logic tach sai-cu/sai-loi, test duoc khong can Mininet
# =====================================================================

def relative_error(twin_value, real_value, eps=1e-9):
    """Sai so tuong doi |twin - real| / max(|real|, eps)."""
    return abs(float(twin_value) - float(real_value)) / max(abs(float(real_value)), eps)


def linear_regression(xs, ys):
    """Hoi quy tuyen tinh y = intercept + slope*x (binh phuong toi thieu).

    Tra (intercept, slope, r2). Dung de tach:
        intercept = error khi AoI=0  -> sai-vi-LOI (fidelity error thuan)
        slope     = d(error)/d(AoI)  -> sai-vi-CU  (staleness error)
        r2        = ty le phuong sai error giai thich duoc boi AoI
                    (r2 cao -> sai chu yeu do CU; r2 thap -> sai chu yeu do LOI)
    """
    n = len(xs)
    if n < 2:
        return float('nan'), float('nan'), float('nan')
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        return my, 0.0, 0.0
    slope = sxy / sxx
    intercept = my - slope * mx
    # r^2
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return intercept, slope, r2


def analyze_fidelity(samples):
    """samples: list dict {aoi, error, twin, real, dt_read}. Tra bao cao tach nguon."""
    if not samples:
        return {'n': 0}
    aois = [s['aoi'] for s in samples]
    errs = [s['error'] for s in samples]
    intercept, slope, r2 = linear_regression(aois, errs)
    errs_sorted = sorted(errs)
    n = len(errs)
    return {
        'n': n,
        'error_mean': sum(errs) / n,
        'error_p95': errs_sorted[min(int(0.95 * (n - 1)), n - 1)],
        'error_max': max(errs),
        'aoi_mean': sum(aois) / n,
        'aoi_max': max(aois),
        # TACH NGUON SAI:
        'staleness_error_slope': slope,       # sai-vi-CU: error tang bao nhieu / giay AoI
        'fidelity_error_intercept': intercept, # sai-vi-LOI: error khi AoI=0
        'r2_aoi_explains_error': r2,          # >0.5: sai chu yeu do CU; <0.2: do LOI
        'dominant_source': ('staleness' if r2 > 0.5 else
                            'fidelity_bug' if r2 < 0.2 else 'mixed'),
    }


def ensure_parent_dir(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


# =====================================================================
# PHAN LIVE — can Mininet + Ditto (ban ghep vao chi tiet interface cua minh)
# =====================================================================

def measure_fidelity_live(runner, thing_ids, link_key, samples=200, interval=0.5,
                          min_real_mbps=0.01, progress_every=10):
    """Doc kep twin vs Mininet cho mot link, thu list mau {aoi, error, ...}.

    CHU Y: doc gia tri THAT phai tinh RATE giong cach twin tinh (counter 2 lan
    chia thoi gian), khong so counter tho voi rate.
    """
    from bridge.ditto_reader import fetch_snapshot, make_session
    from bridge.collector import read_intf_counters, link_side_a_intf
    from bridge.ditto_common import make_thing_id_link

    session = make_session()
    a, b = link_key.split('-')
    tid = make_thing_id_link(a, b)
    # tim doi tuong link Mininet tuong ung
    link_obj = _find_link(runner.net, a, b)
    intf = link_side_a_intf(link_obj)

    out = []
    prev = None  # (rx, tx, t) de tinh rate that
    for i in range(1, samples + 1):
        # --- doc THAT tu Mininet ---
        t_real = time.monotonic()
        counters = read_intf_counters(intf)
        real_rx_mbps = None
        real_tx_mbps = None
        real_rate = None
        if counters is not None:
            rx, tx = counters
            if prev is not None:
                dt = t_real - prev[2]
                if dt > 0:
                    real_rx_mbps = (rx - prev[0]) * 8.0 / 1e6 / dt
                    real_tx_mbps = (tx - prev[1]) * 8.0 / 1e6 / dt
                    real_rate = max(real_rx_mbps, real_tx_mbps)
            prev = (rx, tx, t_real)

        # --- doc TWIN tu Ditto ---
        things, meta = fetch_snapshot(session, thing_ids)
        t_ditto = time.monotonic()
        dt_read = t_ditto - t_real          # khe lech doc, ghi ro
        try:
            props = things[tid]['features']['traffic']['properties']
            # Ditto rxRate/txRate la bytes/s. Doi sang Mbps de so voi real.
            twin_rx_mbps = float(props.get('rxRate') or 0.0) * 8.0 / 1e6
            twin_tx_mbps = float(props.get('txRate') or 0.0) * 8.0 / 1e6
            twin_rate = max(twin_rx_mbps, twin_tx_mbps)
        except (KeyError, TypeError):
            twin_rate = None
            twin_rx_mbps = None
            twin_tx_mbps = None
        aoi = (meta.get('aoi') or {}).get(tid)

        if (real_rate is not None and twin_rate is not None and
                aoi is not None and real_rate >= min_real_mbps):
            out.append({
                'aoi': float(aoi),
                'error': relative_error(twin_rate, real_rate),
                'twin': twin_rate, 'real': real_rate,
                'twin_rx_mbps': twin_rx_mbps,
                'twin_tx_mbps': twin_tx_mbps,
                'real_rx_mbps': real_rx_mbps,
                'real_tx_mbps': real_tx_mbps,
                'dt_read': dt_read,
            })
        if i == 1 or i % progress_every == 0 or i == samples:
            print('%03d/%03d kept=%d real=%sMbps twin=%sMbps aoi=%s dt=%.0fms' % (
                i, samples, len(out),
                '-' if real_rate is None else '%.3f' % real_rate,
                '-' if twin_rate is None else '%.3f' % twin_rate,
                '-' if aoi is None else '%.3f' % float(aoi),
                dt_read * 1000.0,
            ))
        time.sleep(interval)
    return out


def _find_link(net, a, b):
    for link in net.links:
        na, nb = link.intf1.node.name, link.intf2.node.name
        if {na, nb} == {a, b}:
            return link
    raise ValueError('khong tim thay link %s-%s' % (a, b))


def main():
    p = argparse.ArgumentParser(
        description='Do fidelity twin vs Mininet va tach sai-vi-CU/sai-vi-LOI')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--link', default='s2-s3',
                   help='link can do, dang nodeA-nodeB')
    p.add_argument('--samples', type=int, default=200)
    p.add_argument('--interval', type=float, default=0.5)
    p.add_argument('--period', type=float, default=1.0,
                   help='chu ky sync collector/runner')
    p.add_argument('--server-bg-rate', type=float, default=2.0,
                   help='Mbps UDP nen srv1->srv2 qua s2-s3; 0 de tat')
    p.add_argument('--settle', type=float, default=3.0,
                   help='giay cho traffic/sync on dinh truoc khi lay mau')
    p.add_argument('--min-real-mbps', type=float, default=0.01,
                   help='bo mau co real throughput nho hon nguong nay')
    p.add_argument('--progress-every', type=int, default=10)
    p.add_argument('--out', default='docs/phase-5/artifacts/fidelity_s2-s3.json')
    args = p.parse_args()

    from bridge.ditto_reader import expected_thing_ids
    from mininet.env_runner import EnvRunner

    print('== FIDELITY twin vs Mininet ==')
    print('link=%s samples=%d interval=%.3fs period=%.3fs out=%s' %
          (args.link, args.samples, args.interval, args.period, args.out))
    print('Chu y: script nay TU DUNG EnvRunner/Mininet rieng; '
          'khong can mo mininet.run_sync o terminal khac.')

    runner = EnvRunner(spec_path=args.spec, sync_period=args.period,
                       hard_every=0)
    samples = []
    try:
        runner.start()
        if args.server_bg_rate > 0:
            runner.start_server_background(rate_mbps=args.server_bg_rate)
        if args.settle > 0:
            print('settle %.1fs cho collector va traffic on dinh...' %
                  args.settle)
            time.sleep(args.settle)
        thing_ids = expected_thing_ids(runner.spec)
        samples = measure_fidelity_live(
            runner, thing_ids, args.link, samples=args.samples,
            interval=args.interval, min_real_mbps=args.min_real_mbps,
            progress_every=max(1, args.progress_every),
        )
    finally:
        runner.close()

    analysis = analyze_fidelity(samples)
    dt_reads = [s['dt_read'] for s in samples]
    report = {
        'link': args.link,
        'samples_requested': args.samples,
        'samples_kept': len(samples),
        'interval_s': args.interval,
        'period_s': args.period,
        'server_bg_rate_mbps': args.server_bg_rate,
        'min_real_mbps': args.min_real_mbps,
        'units': {
            'twin': 'Mbps, converted from Ditto bytes/s',
            'real': 'Mbps, computed from Mininet counters',
            'compared_signal': 'max(rxRate, txRate) on canonical link side',
        },
        'analysis': analysis,
        'dt_read': {
            'mean_ms': (sum(dt_reads) / len(dt_reads) * 1000.0
                        if dt_reads else None),
            'max_ms': (max(dt_reads) * 1000.0 if dt_reads else None),
        },
        'samples': samples,
    }

    ensure_parent_dir(args.out)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print('\n== KET QUA FIDELITY ==')
    if analysis.get('n', 0) == 0:
        print('Khong co mau hop le. Kiem tra traffic tren link %s hoac '
              'tSource/traffic trong Ditto.' % args.link)
    else:
        print('n=%d kept/%d requested' %
              (analysis['n'], args.samples))
        print('error mean=%.4f p95=%.4f max=%.4f' %
              (analysis['error_mean'], analysis['error_p95'],
               analysis['error_max']))
        print('AoI mean=%.3fs max=%.3fs' %
              (analysis['aoi_mean'], analysis['aoi_max']))
        print('intercept(sai-vi-LOI)=%.4f slope(sai-vi-CU)=%.4f r2=%.3f' %
              (analysis['fidelity_error_intercept'],
               analysis['staleness_error_slope'],
               analysis['r2_aoi_explains_error']))
        print('dominant_source=%s' % analysis['dominant_source'])
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Do phan ra SYNC CYCLE — vi sao 'Cycle overran 1.5-3.2s' thay vi 0.5s?

Nguyen tac do-truoc-khi-sua. Log cho thay sync cycle qua tai, nhung chua biet
BUOC NAO nang: collect (doc Mininet) / diff / push (18 HTTP PATCH len Ditto)?
Nghi pham chinh: collect_all() giu net_lock trong khi goi node.cmd() cho 18
Thing — moi node.cmd la mot lenh shell qua namespace, cham, va con tranh lock
voi Command Agent.

Script nay chay Collector THAT (khong qua Sync Agent thread) va bam gio tung
buoc, KHONG co inject/command de do NEN sach truoc. Sau do ban co the them tai
de xem cycle gian bao nhieu.

    sudo python3 rl/bench_sync_cycle.py --cycles 40
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from bridge.adapter import collector_to_things
from bridge.differ import diff_snapshot, DEFAULT_TOL


def p95(xs):
    if not xs:
        return 0.0
    xs = sorted(xs)
    pos = 0.95 * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (pos - lo) * (xs[hi] - xs[lo])


def summarize(name, xs):
    import statistics
    return {
        'step': name,
        'mean_ms': round(1000 * statistics.mean(xs), 1),
        'p95_ms': round(1000 * p95(xs), 1),
        'max_ms': round(1000 * max(xs), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cycles', type=int, default=40)
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--out', default='docs/phase-6/artifacts/bench_sync_cycle.json')
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='ket thuc bang mn -c; se kill ca ryu-manager')
    args = ap.parse_args()

    runner = EnvRunner(spec_path=args.spec, sync_period=args.sync_period,
                       hard_every=0)
    print('[bench] start()...', flush=True)
    runner.start()

    # Lay collector ma Sync Agent da tao (gan vao net khi start)
    collector = getattr(runner.net, 'dt4n_collector', None)
    if collector is None:
        raise RuntimeError('khong tim thay collector tren net — Sync Agent chua chay?')

    # Khoi dong traffic nen de collect co so lieu that
    runner._start_episode_traffic()
    runner._wait_steady_state()

    t_collect, t_adapt, t_diff = [], [], []
    prev = None
    try:
        for i in range(args.cycles):
            # --- buoc 1: collect (doc Mininet, giu net_lock) ---
            t0 = time.monotonic()
            snapshot = collector.collect_all()
            t_collect.append(time.monotonic() - t0)

            # --- buoc 2: adapt (chuyen snapshot -> things dict) ---
            t0 = time.monotonic()
            things_now = collector_to_things(snapshot)
            t_adapt.append(time.monotonic() - t0)

            # --- buoc 3: diff (so voi prev) ---
            t0 = time.monotonic()
            _changes = diff_snapshot(things_now, prev, DEFAULT_TOL)
            t_diff.append(time.monotonic() - t0)
            prev = things_now

            total_ms = 1000 * (t_collect[-1] + t_adapt[-1] + t_diff[-1])
            print('[bench] cycle %2d: collect=%.0fms adapt=%.0fms diff=%.0fms '
                  '(chua tinh push HTTP)  total=%.0fms'
                  % (i + 1, 1000 * t_collect[-1], 1000 * t_adapt[-1],
                     1000 * t_diff[-1], total_ms), flush=True)
            time.sleep(max(0, args.sync_period))
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    steps = [summarize('collect', t_collect),
             summarize('adapt', t_adapt),
             summarize('diff', t_diff)]
    out = {'cycles': args.cycles, 'sync_period_s': args.sync_period,
           'note': 'push HTTP (18 PATCH len Ditto) CHUA duoc do o day; '
                   'neu collect da > period thi thu pham la collect',
           'steps': steps}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2)

    print('\n[bench] === PHAN RA CYCLE (chua tinh push HTTP) ===')
    for s in steps:
        print('[bench] %-8s mean=%6.1fms  p95=%6.1fms  max=%6.1fms'
              % (s['step'], s['mean_ms'], s['p95_ms'], s['max_ms']))
    collect_p95 = steps[0]['p95_ms']
    print('\n[bench] period = %.0fms' % (1000 * args.sync_period))
    if collect_p95 > 1000 * args.sync_period:
        print('[bench] >>> collect p95 (%.0fms) DA VUOT period -> collect la thu pham chinh'
              % collect_p95)
    else:
        print('[bench] collect trong tam period; thu pham co the o PUSH HTTP (18 PATCH)')


if __name__ == '__main__':
    main()

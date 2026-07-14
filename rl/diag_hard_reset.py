#!/usr/bin/env python3
"""Gate 1a — Chan doan hard_reset: mang-nen co chet ngau nhien khong?

Y tuong: CHI goi hard_reset() lap lai. KHONG train, KHONG inject scenario,
KHONG agent. Sau moi lan, do suc khoe mang-NEN (chua co su co):
    - throughput_norm : server nhan duoc bao nhieu (0 = mang khong thong)
    - pingall loss %  : bao nhieu goi khong toi (kiem tra tang thap hon iperf)

Neu mang-nen thinh thoang chet -> bug hard_reset duoc CHUNG MINH (tai hien
duoc theo yeu cau), khong con la nghi ngo tu doc log.

Chay tren may co Mininet + controller:
    sudo python3 rl/diag_hard_reset.py --iters 10
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


def measure_baseline_health(runner, settle_s=3.0):
    """Do suc khoe mang-NEN sau khi da co traffic nen chay on dinh.

    Tra ve dict: throughput_norm, pingall_loss_pct, thong tin phu.
    KHONG inject scenario — day la suc khoe cua mang KHOE (baseline).
    """
    # 1) Khoi dong traffic nen (giong soft_reset lam) + cho on dinh
    runner._start_episode_traffic()
    ok_steady, waited = runner._wait_steady_state()
    time.sleep(settle_s)  # them le an toan cho collector kip mot chu ky

    # 2) Doc throughput nen — DUNG ham env dung, khong phat minh cach do moi
    thr = runner._read_throughput_norm()

    # 3) pingall: kiem tra ket noi tang thap (doc lap voi iperf/collector)
    #    net.pingAll() tra ve % PACKET LOSS (0 = hoan hao, 100 = tach roi)
    with runner.net_lock:
        loss_pct = runner.net.pingAll(timeout='1')

    return {
        'throughput_norm': round(thr, 4),
        'pingall_loss_pct': round(loss_pct, 1),
        'steady_ok': bool(ok_steady),
        'steady_wait_s': round(waited, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=10,
                    help='so lan hard_reset de lap lai thi nghiem')
    ap.add_argument('--thr-dead', type=float, default=0.10,
                    help='duoi nguong nay coi la mang-nen CHET')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--out', default='docs/phase-6/artifacts/diag_hard_reset.json')
    args = ap.parse_args()

    runner = EnvRunner(spec_path=args.spec, sync_period=args.sync_period,
                       hard_every=0)  # tat auto-hard-reset; ta tu goi
    print('[diag] start()...', flush=True)
    runner.start()

    rows = []
    n_dead = 0
    try:
        # Lan 0: do suc khoe NGAY SAU start() (chua hard_reset lan nao)
        h0 = measure_baseline_health(runner)
        h0['iter'] = 0
        h0['phase'] = 'after_start'
        h0['dead'] = h0['throughput_norm'] < args.thr_dead
        rows.append(h0)
        print('[diag] iter 0 (after start): %s' % json.dumps(h0), flush=True)

        for i in range(1, args.iters + 1):
            dt = runner.hard_reset()          # <-- BIEN DUY NHAT ta dang thu
            h = measure_baseline_health(runner)
            h['iter'] = i
            h['phase'] = 'after_hard_reset'
            h['hard_reset_s'] = round(dt, 2)
            h['dead'] = h['throughput_norm'] < args.thr_dead
            if h['dead']:
                n_dead += 1
            rows.append(h)
            flag = '  <<< DEAD' if h['dead'] else ''
            print('[diag] iter %d: thr=%.3f loss=%.1f%% reset=%.1fs%s'
                  % (i, h['throughput_norm'], h['pingall_loss_pct'],
                     h['hard_reset_s'], flag), flush=True)
    finally:
        runner.close(cleanup_mn=True)  # ket thuc thi don SACH that su

    summary = {
        'n_iters': args.iters,
        'n_dead': n_dead,
        'dead_rate': round(n_dead / max(args.iters, 1), 3),
        'thr_dead_threshold': args.thr_dead,
        'verdict': ('BUG CONFIRMED: hard_reset sinh mang chet'
                    if n_dead > 0 else
                    'hard_reset ON DINH tren %d lan' % args.iters),
        'rows': rows,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('\n[diag] ' + summary['verdict'])
    print('[diag] dead_rate = %.1f%% (%d/%d)  -> %s'
          % (summary['dead_rate'] * 100, n_dead, args.iters, args.out))


if __name__ == '__main__':
    main()

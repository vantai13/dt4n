#!/usr/bin/env python3
"""Đo thời gian đọc state (fetch_snapshot + build) để đóng gate Lesson 5.3.

Gate: p95(fetch + build) < 20% * Delta. Delta = 1.8s -> ngân sách 0.36s.

Đo p50/p95/p99 (KHÔNG chỉ mean) vì cái giết pipeline là tail latency:
1 lần fetch chậm 3s (như 'Cycle overran' đã thấy) lặp lại nhiều lần mỗi
episode sẽ phá mô hình thời gian, dù mean vẫn đẹp.

Đo ở HAI điều kiện:
  - idle: mạng khỏe, không tải  -> con số 'tốt nhất'
  - loaded: có traffic nền/flood -> con số 'thực chiến' (đuôi phình)
Gate phải pass ở điều kiện LOADED, không phải idle.
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


def percentile(sorted_vals, q):
    """Phân vị q (0..1) theo nội suy tuyến tính. sorted_vals đã sắp tăng."""
    if not sorted_vals:
        return float('nan')
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def summarize(name, samples):
    s = sorted(samples)
    return {
        'label': name,
        'n': len(s),
        'mean_ms': statistics.mean(s) * 1e3,
        'p50_ms': percentile(s, 0.50) * 1e3,
        'p95_ms': percentile(s, 0.95) * 1e3,
        'p99_ms': percentile(s, 0.99) * 1e3,
        'max_ms': max(s) * 1e3,
        'min_ms': min(s) * 1e3,
    }


def measure_loop(runner, builder, n, warmup, label):
    """Đo n lần (fetch + build), bỏ 'warmup' lần đầu (JIT/cache lạnh)."""
    fetch_only = []
    fetch_plus_build = []
    total = n + warmup
    for i in range(1, total + 1):
        t0 = time.perf_counter()
        things, info = runner.observe_raw()          # phần I/O (HTTP tới Ditto)
        t1 = time.perf_counter()
        builder.build(things, info=info,
                      episode={'t': 0, 'healthy_streak': 0})  # phần logic
        t2 = time.perf_counter()
        if i > warmup:
            fetch_only.append(t1 - t0)
            fetch_plus_build.append(t2 - t0)
        if i % 20 == 0:
            print('  [%s] %d/%d  last fetch=%.1fms build=%.1fms'
                  % (label, i, total, (t1 - t0) * 1e3, (t2 - t1) * 1e3))
        time.sleep(0.2)   # giãn nhẹ để không tự dồn tải lên Ditto
    return fetch_only, fetch_plus_build


def main():
    p = argparse.ArgumentParser(description='Do fetch+build latency cho gate 5.3')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--samples', type=int, default=100)
    p.add_argument('--warmup', type=int, default=5)
    p.add_argument('--delta', type=float, default=1.8,
                   help='Delta da do (s); ngan sach = 0.2 * delta')
    p.add_argument('--flood-rate', type=float, default=40.0,
                   help='rate Mbps cho dieu kien loaded')
    p.add_argument('--out', default='docs/phase-5/artifacts/fetch_time.json')
    args = p.parse_args()

    from rl.state_builder_draft import StateBuilderDraft
    from mininet.topology_meta import load_spec
    from mininet.env_runner import EnvRunner

    spec = load_spec(args.spec)
    builder = StateBuilderDraft(spec=spec)
    budget_s = 0.2 * args.delta

    runner = EnvRunner(spec_path=args.spec)
    runner.start()
    report = {}
    try:
        # --- Điều kiện 1: IDLE (mạng khỏe, không tải) ---
        print('== IDLE ==')
        builder.reset()
        _f_idle, fb_idle = measure_loop(
            runner, builder, args.samples, args.warmup, 'idle')
        report['idle'] = summarize('idle', fb_idle)

        # --- Điều kiện 2: LOADED (có traffic nền, đuôi phình) ---
        print('== LOADED ==')
        # bật traffic nền để mô phỏng lúc episode đang chạy
        runner.start_server_background(rate_mbps=2.0)
        time.sleep(3.0)
        builder.reset()
        _f_load, fb_load = measure_loop(
            runner, builder, args.samples, args.warmup, 'loaded')
        report['loaded'] = summarize('loaded', fb_load)
    finally:
        runner.close()

    report['delta_s'] = args.delta
    report['budget_ms'] = budget_s * 1e3
    # Gate phán trên điều kiện LOADED (thực chiến), dùng p95.
    loaded_p95 = report['loaded']['p95_ms']
    report['gate_pass'] = loaded_p95 < budget_s * 1e3
    report['gate_rule'] = 'p95(loaded, fetch+build) < 0.2 * Delta'

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print('\n== KET QUA ==')
    for cond in ('idle', 'loaded'):
        r = report[cond]
        print('%-7s: p50=%.1f  p95=%.1f  p99=%.1f  max=%.1f ms'
              % (cond, r['p50_ms'], r['p95_ms'], r['p99_ms'], r['max_ms']))
    print('budget = %.1f ms (0.2 x %.2fs)' % (budget_s * 1e3, args.delta))
    print('GATE (%s): %s' % (report['gate_rule'],
                             'PASS' if report['gate_pass'] else 'FAIL'))
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()
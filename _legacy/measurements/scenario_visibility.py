#!/usr/bin/env python3
"""Đo độ 'nhìn thấy được' của mỗi scenario trên state vector.

Câu hỏi script này trả lời (quyết định 45 vs 53 chiều):
  Với mỗi scenario sinh theo seed, có ÍT NHẤT một chiều state đổi > 3 sigma
  so với lúc mạng khỏe không? Nếu KHÔNG -> scenario đó là 'blind-spot':
  sự cố xảy ra nhưng agent hoàn toàn không thấy -> episode 'ma' -> phải thêm
  chiều state (path probe) hoặc ràng buộc scenario.

Thiết kế: tách PURE (so sánh, phán blind-spot — test được không cần Mininet)
khỏi LIVE (inject thật, đọc twin — cần testbed sống).
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
# PHẦN PURE — logic thuần, KHÔNG I/O, test được không cần Mininet/Ditto
# =====================================================================

def load_noise_thresholds(noise_path):
    """Đọc noise_std.json -> {dim_name: {'abs_delta_threshold', 'degenerate'}}.

    abs_delta_threshold = 3 * sigma_robust (đã tính sẵn trong measure_noise_std).
    """
    with open(noise_path, encoding='utf-8') as f:
        data = json.load(f)
    dim_order = data['dimension_order']
    dims = data['state_dims']
    thresholds = {}
    for name in dim_order:
        row = dims.get(name, {})
        thresholds[name] = {
            'abs_delta_threshold': float(row.get('abs_delta_threshold', 0.0)),
            'degenerate': bool(row.get('degenerate', True)),
            'sigma_robust': float(row.get('sigma_robust', 0.0)),
        }
    return dim_order, thresholds


def dimension_movements(baseline_vec, faulted_vec, dim_order, thresholds,
                        degenerate_eps=1e-6):
    """So từng chiều: chiều nào 'động' đủ mạnh để coi là nhìn thấy sự cố?

    Quy tắc:
      - Chiều KHÔNG degenerate: |delta| > 3*sigma_robust  -> nhìn thấy.
      - Chiều degenerate (sigma=0 lúc khỏe): |delta| > eps  -> nhìn thấy
        (vì bình thường nó bất động, động chút là bất thường).
    Trả list dict, mỗi chiều: tên, delta, ngưỡng, moved (bool).
    """
    out = []
    for idx, name in enumerate(dim_order):
        b = float(baseline_vec[idx])
        f = float(faulted_vec[idx])
        delta = f - b
        abs_delta = abs(delta)
        th = thresholds.get(name, {})
        if th.get('degenerate', True):
            moved = abs_delta > degenerate_eps
            threshold = degenerate_eps
        else:
            threshold = th['abs_delta_threshold']
            moved = abs_delta > threshold
        out.append({
            'dim': name,
            'baseline': b,
            'faulted': f,
            'abs_delta': abs_delta,
            'threshold': threshold,
            'moved': moved,
        })
    return out


def classify_scenario(movements):
    """Từ danh sách chiều -> phán scenario có nhìn thấy không.

    visible = có >= 1 chiều moved. blind_spot = ngược lại.
    Trả cả top chiều động mạnh nhất (theo bội số ngưỡng) để đọc cho dễ.
    """
    moved = [m for m in movements if m['moved']]
    # Sắp theo 'mạnh gấp mấy lần ngưỡng' để biết chiều nào phản ứng rõ nhất.
    def strength(m):
        th = m['threshold'] if m['threshold'] > 0 else 1e-9
        return m['abs_delta'] / th
    moved_sorted = sorted(moved, key=strength, reverse=True)
    return {
        'visible': len(moved) > 0,
        'blind_spot': len(moved) == 0,
        'n_moved': len(moved),
        'top_dims': [
            {'dim': m['dim'], 'abs_delta': m['abs_delta'],
             'threshold': m['threshold'],
             'x_over_threshold': strength(m)}
            for m in moved_sorted[:5]
        ],
    }


# =====================================================================
# PHẦN LIVE — cần Mininet + Ditto sống. Chạy trong môi trường testbed.
# =====================================================================

def measure_one_scenario(runner, builder, seed, spec,
                         settle_healthy_s=4.0, settle_fault_s=6.0):
    """Đo baseline (khỏe) rồi faulted (có sự cố) cho MỘT seed.

    Dùng đúng hạ tầng public của EnvRunner:
      - runner.injection: InjectionChannel được EnvRunner quản lý
      - runner.observe_raw(): đọc snapshot Ditto qua session/cache của runner

    Trả (baseline_vec, faulted_vec, scenario_desc).
    """
    from rl.scenarios import make_scenario

    # --- 1. Bảo đảm mạng ở trạng thái khỏe, ổn định ---
    runner.injection.revert_all()        # dọn mọi sự cố cũ (idempotent — an toàn)
    time.sleep(settle_healthy_s)         # chờ metrics ổn định

    builder.reset()                      # xóa lịch sử util_avg3 giữa các seed
    # warm-up vài mẫu để cửa sổ trượt util_avg3 đầy trước khi chốt baseline
    for _ in range(3):
        things, info = runner.observe_raw()
        builder.build(things, info=info, episode={'t': 0, 'healthy_streak': 0})
        time.sleep(1.0)
    things, info = runner.observe_raw()
    baseline_vec = builder.build(
        things, info=info, episode={'t': 0, 'healthy_streak': 0})

    # --- 2. Inject scenario theo seed qua BACK-DOOR (không qua Command Agent) ---
    scenario = make_scenario(seed, spec)
    runner.injection.apply(scenario)
    time.sleep(settle_fault_s)           # chờ sự cố ngấm + sync lên twin

    # warm-up để util_avg3 phản ánh trạng thái có-sự-cố, không lẫn baseline cũ
    for _ in range(3):
        things, info = runner.observe_raw()
        builder.build(things, info=info, episode={'t': 3, 'healthy_streak': 0})
        time.sleep(1.0)
    things, info = runner.observe_raw()
    faulted_vec = builder.build(
        things, info=info, episode={'t': 6, 'healthy_streak': 0})

    # --- 3. Dọn sự cố để seed sau bắt đầu sạch ---
    runner.injection.revert_all()
    time.sleep(2.0)

    return baseline_vec, faulted_vec, scenario.describe()


def main():
    p = argparse.ArgumentParser(
        description='Kiem tra blind-spot: scenario nao khong lam state doi >3sigma')
    p.add_argument('--noise', default='docs/phase-4.5/baseline/noise_std.json',
                   help='file noise_std.json tu measure_noise_std.py')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--seeds', type=int, default=30,
                   help='so seed (scenario) de kiem tra, 0..N-1')
    p.add_argument('--out', default='docs/phase-5/artifacts/scenario_visibility.json')
    args = p.parse_args()

    from mininet.topology_meta import load_spec
    from rl.state_builder_draft import StateBuilderDraft
    from mininet.env_runner import EnvRunner

    spec = load_spec(args.spec)
    dim_order, thresholds = load_noise_thresholds(args.noise)
    builder = StateBuilderDraft(spec=spec)

    runner = EnvRunner(spec_path=args.spec)
    runner.start()                       # dựng Mininet + Ditto + threads
    results = []
    blind_spots = []
    try:
        for seed in range(args.seeds):
            baseline, faulted, desc = measure_one_scenario(
                runner, builder, seed, spec)
            movements = dimension_movements(
                baseline, faulted, dim_order, thresholds)
            verdict = classify_scenario(movements)
            row = {'seed': seed, 'scenario': desc, **verdict}
            results.append(row)
            tag = 'BLIND-SPOT' if verdict['blind_spot'] else 'ok'
            top = verdict['top_dims'][0]['dim'] if verdict['top_dims'] else '-'
            print('seed=%02d %-14s %-12s n_moved=%d top=%s'
                  % (seed, desc.get('type'), tag, verdict['n_moved'], top))
            if verdict['blind_spot']:
                blind_spots.append(row)
    finally:
        runner.close()                   # dọn Mininet triệt để dù có lỗi

    summary = {
        'n_seeds': args.seeds,
        'n_blind_spots': len(blind_spots),
        'blind_spot_seeds': [r['seed'] for r in blind_spots],
        'decision_hint': (
            'State hien tai DU: khong can them chieu quan sat luc nay.'
            if not blind_spots else
            'CO blind-spot: can them path probe (Lua chon A) hoac rang buoc scenario.'
        ),
        'results': results,
    }
    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('\n== KET LUAN ==')
    print('blind-spot: %d/%d scenario' % (len(blind_spots), args.seeds))
    print(summary['decision_hint'])
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

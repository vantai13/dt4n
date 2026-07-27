#!/usr/bin/env python3
"""
check_snapshots.py — Kiểm tra file log snapshot SAU khi chạy runner.

Chạy ở MÁY THẬT (không cần Mininet, không cần root):
    python3 scenarios/check_snapshots.py logs/dt4n_snapshots.jsonl

Nó trả lời các câu trong Validation Gate Lesson 1.5:
  - Mỗi snapshot có đúng cấu trúc Thing (attributes/features)?
  - rxRate/txRate có > 0 ở giai đoạn có traffic? (số liệu BIẾN ĐỘNG đúng)
  - Có host/switch/path đầy đủ?
Đây là 'validation tự động' — thay vì mắt thường đọc JSON.
"""
import sys, json

def main(path):
    with open(path) as f:
        snaps = [json.loads(l) for l in f if l.strip()]
    if not snaps:
        print("✗ File rỗng:", path); sys.exit(1)

    print("== Đọc %d snapshot từ %s ==\n" % (len(snaps), path))

    # 1) cấu trúc
    s0 = snaps[0]
    assert 'timestamp' in s0 and 'things' in s0, "thiếu timestamp/things"
    print("✓ Có timestamp + things")

    # 2) phân loại thực thể
    kinds = {}
    for k, v in s0['things'].items():
        t = v.get('attributes', {}).get('type', '?')
        kinds[t] = kinds.get(t, 0) + 1
    print("✓ Thực thể trong snapshot đầu:", kinds)

    # 3) rate có biến động không? (gom max rxRate/txRate qua mọi host, mọi snapshot)
    max_rx = max_tx = 0.0
    for s in snaps:
        for k, v in s['things'].items():
            tr = v.get('features', {}).get('traffic')
            if tr:
                max_rx = max(max_rx, tr.get('rxRate') or 0)
                max_tx = max(max_tx, tr.get('txRate') or 0)
    print("✓ rxRate cao nhất quan sát được: %.0f bytes/s" % max_rx)
    print("✓ txRate cao nhất quan sát được: %.0f bytes/s" % max_tx)
    if max_rx == 0 and max_tx == 0:
        print("  ⚠ CẢNH BÁO: rate toàn 0 -> có thể bạn chạy scenario=idle,")
        print("    hoặc traffic không chạy song song với collector. Thử --scenario flood.")
    else:
        print("  -> Số liệu BIẾN ĐỘNG đúng (mạng có tải). Đạt Validation Gate 1.5.")

    # 4) latency (nếu có path)
    lat_vals = []
    for s in snaps:
        for k, v in s['things'].items():
            q = v.get('features', {}).get('quality')
            if q and q.get('latency_ms') is not None:
                lat_vals.append(q['latency_ms'])
    if lat_vals:
        print("✓ Latency đo được: min=%.2f avg=%.2f max=%.2f ms (n=%d)"
              % (min(lat_vals), sum(lat_vals)/len(lat_vals), max(lat_vals), len(lat_vals)))
    print("\n== Snapshot CUỐI (mẫu) ==")
    print(json.dumps(snaps[-1], indent=2)[:800])

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'logs/dt4n_snapshots.jsonl')

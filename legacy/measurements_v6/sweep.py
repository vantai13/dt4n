#!/usr/bin/env python3
"""
sweep.py — Tự động chạy BẢNG ĐO tham số (Lesson 2.4 Phần 5.5). Xuất CSV.

VÌ SAO TỰ ĐỘNG (Phần 7 gợi ý 3): đo tay 9 cấu hình = 1 buổi; script = 1 lệnh,
tái lập được, sửa code xong đo lại chỉ tốn vài phút. Đây là reproducibility.

LƯU Ý: file này KHUNG để bạn ghép. Việc dựng lại net với số host khác nhau cần
tắt/dựng Mininet mỗi cấu hình -> chạy ngoài CLI. Tham khảo cấu trúc, ghép với
run_sync.py của bạn. Cột CPU đo bằng psutil (Phần 5.6).
"""

import csv
import time
import os

# psutil là tùy chọn; nếu chưa cài, cột CPU để trống
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

from measurements.stats import summarize


# Các cấu hình cần quét (chu kỳ × quy mô) — Phần 5.5
PERIODS = [0.5, 1.0, 2.0]
SCALES  = [10, 30, 50]       # số client (-> số Thing tỉ lệ theo)


def run_one_config(build_net_fn, sync_run_fn, measure_fn,
                   period, clients, n_trials=20):
    """Chạy 1 cấu hình: dựng net -> bật sync nền -> đo -> tắt. Trả dict 1 dòng CSV.

    build_net_fn(clients) -> net (từ topology.build_net của bạn)
    sync_run_fn(net, period, max_cycles) -> chạy sync (gọi trong thread)
    measure_fn(net, n_trials) -> stats dict (từ measure_latency.main)
    """
    import threading
    net = build_net_fn(clients=clients)

    # sync chạy nền
    t = threading.Thread(target=sync_run_fn, args=(net,),
                         kwargs={'period': period}, daemon=True)
    t.start()
    time.sleep(period * 3)   # cho vài chu kỳ ổn định

    # đo CPU: khởi tạo trước (Phần 5.6 - lần đầu cpu_percent trả 0 nếu không init)
    proc = psutil.Process(os.getpid()) if _HAS_PSUTIL else None
    if proc:
        proc.cpu_percent(None)

    stats = measure_fn(net, n_trials=n_trials)
    cpu = proc.cpu_percent(None) if proc else None

    net.stop()

    row = {
        'period_s': period,
        'clients': clients,
        'n': stats['n'] if stats else 0,
        'mean_ms': round(stats['mean_ms'], 0) if stats else None,
        'p50_ms':  round(stats['p50_ms'], 0) if stats else None,
        'p95_ms':  round(stats['p95_ms'], 0) if stats else None,
        'max_ms':  round(stats['max_ms'], 0) if stats else None,
        'cpu_pct': round(cpu, 1) if cpu is not None else '',
    }
    return row


def write_csv(rows, path='measurements/sweep_results.csv'):
    """Ghi kết quả ra CSV để vẽ biểu đồ / đưa vào báo cáo."""
    if not rows:
        print('Không có dữ liệu.')
        return
    keys = list(rows[0].keys())
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print('✅ Ghi %d dòng -> %s' % (len(rows), path))
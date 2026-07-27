#!/usr/bin/env python3
"""
plot.py — Vẽ biểu đồ từ sweep_results.csv (Lesson 2.4 Phần 5.7). Cần matplotlib.
    pip3 install matplotlib
    python3 -m measurements.plot

VẼ 2 BIỂU ĐỒ tối thiểu lesson yêu cầu:
  1. line chart: p95 latency theo số Thing, mỗi chu kỳ một đường -> thấy điểm gãy.
  2. box-like (bar mean + đường target) -> so cấu hình.
"""

import csv
import matplotlib
matplotlib.use('Agg')          # backend không cần màn hình (lưu file PNG)
import matplotlib.pyplot as plt


def load(path='measurements/sweep_results.csv'):
    with open(path) as f:
        return list(csv.DictReader(f))


def plot_latency_vs_scale(rows, out='measurements/latency_vs_scale.png'):
    """Line chart: trục X = số client, trục Y = p95 latency, mỗi period 1 đường."""
    periods = sorted(set(float(r['period_s']) for r in rows))
    plt.figure(figsize=(8, 5))
    for p in periods:
        pts = sorted([(int(r['clients']), float(r['p95_ms']))
                      for r in rows if float(r['period_s']) == p])
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        plt.plot(xs, ys, marker='o', label='period=%.1fs' % p)
    plt.axhline(2000, color='red', linestyle='--', label='target 2s')
    plt.xlabel('Số client (quy mô)')
    plt.ylabel('p95 sync latency (ms)')
    plt.title('Sync latency p95 theo quy mô và chu kỳ')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(out, dpi=120, bbox_inches='tight')
    print('✅ Lưu', out)


def plot_mean_bars(rows, out='measurements/mean_latency_bars.png'):
    """Bar chart mean latency cho từng cấu hình."""
    labels = ['%.1fs/%s' % (float(r['period_s']), r['clients']) for r in rows]
    means = [float(r['mean_ms']) for r in rows]
    plt.figure(figsize=(10, 5))
    plt.bar(range(len(means)), means)
    plt.axhline(2000, color='red', linestyle='--', label='target 2s')
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.ylabel('mean sync latency (ms)')
    plt.title('Mean latency theo cấu hình (chu kỳ/số client)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches='tight')
    print('✅ Lưu', out)


if __name__ == '__main__':
    rows = load()
    plot_latency_vs_scale(rows)
    plot_mean_bars(rows)
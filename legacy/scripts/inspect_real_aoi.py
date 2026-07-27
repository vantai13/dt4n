#!/usr/bin/env python3
"""Summarize the real Ditto AoI calibration file."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, '.')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--path',
        default='results/aoi/aoi_a2_host_srv1.json',
        help='AoI JSON file produced by the real Ditto pipeline',
    )
    return parser.parse_args()


def _hist(values, bins=10):
    counts, edges = np.histogram(values, bins=bins)
    width = max(int(counts.max()), 1)
    rows = []
    for idx, count in enumerate(counts):
        bar = '#' * int(round(40 * count / width))
        rows.append(
            f'  [{edges[idx]:.3f},{edges[idx + 1]:.3f}) '
            f'{int(count):3d} {bar}'
        )
    return rows


def main():
    args = parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding='utf-8'))
    records = [r for r in data.get('records', []) if r.get('ok')]
    aoi = np.array([float(r['aoi_s']) for r in records], dtype=float)
    fetch_ms = np.array([float(r['fetch_ms']) for r in records], dtype=float)
    tsources = sorted({float(r['t_source']) for r in records})
    deltas = np.diff(tsources)

    print('=== REAL DITTO AOI CALIBRATION ===')
    print(f'file={path}')
    print(f'valid_samples={len(records)} host={data.get("host")}')
    print()
    print(
        f'AoI(s): mean={np.mean(aoi):.4f} std={np.std(aoi):.4f} '
        f'min={np.min(aoi):.4f} p50={np.percentile(aoi, 50):.4f} '
        f'p95={np.percentile(aoi, 95):.4f} max={np.max(aoi):.4f}'
    )
    print(f'fetch_ms_mean={np.mean(fetch_ms):.3f}')
    print(
        f'distinct_t_source={len(tsources)} '
        f'sync_period_mean={np.mean(deltas):.3f}s '
        f'sync_period_std={np.std(deltas):.6f}s'
    )
    print()
    print('AoI histogram:')
    for row in _hist(aoi):
        print(row)
    print()
    print('Interpretation: flat-ish histogram => sawtooth ageing over one sync cycle.')


if __name__ == '__main__':
    main()

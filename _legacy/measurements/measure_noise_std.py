#!/usr/bin/env python3
"""Measure baseline state-vector noise from Ditto Things.

Run while the network is healthy and episode-normal background traffic is
steady. The output calibrates scenario strength on the normalized 45D state
vector using robust MAD statistics, not raw feature standard deviation.
"""

import argparse
import json
import math
import os
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_reader import expected_thing_ids, fetch_snapshot, make_session  # noqa: E402
from mininet.topology_meta import load_spec  # noqa: E402
from rl.state_builder_draft import StateBuilderDraft  # noqa: E402


MAD_TO_SIGMA = 1.4826


def median_abs_deviation(values, median):
    return statistics.median([abs(value - median) for value in values])


def summarize_state_vectors(vectors, dim_names):
    out = {}
    for idx, name in enumerate(dim_names):
        values = [
            float(vector[idx]) for vector in vectors
            if idx < len(vector) and math.isfinite(float(vector[idx]))
        ]
        if not values:
            out[name] = {
                'n': 0,
                'degenerate': True,
            }
            continue
        median = statistics.median(values)
        mad = median_abs_deviation(values, median)
        sigma_robust = MAD_TO_SIGMA * mad
        if len(values) < 2:
            std = 0.0
        else:
            std = statistics.stdev(values)
        threshold = 3.0 * sigma_robust
        out[name] = {
            'n': len(values),
            'mean': statistics.mean(values),
            'median': median,
            'mad': mad,
            'sigma_robust': sigma_robust,
            'three_sigma_robust': threshold,
            'abs_delta_threshold': threshold,
            'lower_threshold': median - threshold,
            'upper_threshold': median + threshold,
            'degenerate': sigma_robust == 0.0,
            'std_reference_only': std,
            'three_sigma_std_reference_only': 3.0 * std,
            'min': min(values),
            'max': max(values),
        }
    return out


def main():
    p = argparse.ArgumentParser(
        description='Measure DT4N normalized state-vector baseline noise')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--samples', type=int, default=300)
    p.add_argument('--warmup', type=int, default=3,
                   help='initial observations to discard while state history warms up')
    p.add_argument('--interval', type=float, default=1.0)
    p.add_argument('--out', default='docs/phase-4.5/baseline/noise_std.json')
    p.add_argument('--condition', default='episode_normal_background',
                   help='label for the live baseline condition being measured')
    args = p.parse_args()

    spec = load_spec(args.spec)
    thing_ids = expected_thing_ids(spec)
    session = make_session()
    builder = StateBuilderDraft(spec=spec)
    vectors = []

    total = args.samples + max(0, args.warmup)
    for idx in range(1, total + 1):
        things, info = fetch_snapshot(session, thing_ids)
        vector = builder.build(
            things,
            info=info,
            episode={'t': 0, 'healthy_streak': 0},
        )
        kept = idx > args.warmup
        if kept:
            vectors.append(vector)
        print('%03d/%03d kept=%s dim=%d fetch=%.1fms fresh=%.1f' %
              (idx, total, 'yes' if kept else 'warmup', len(vector),
               info.get('fetch_ms', 0.0), info.get('data_fresh', 0.0)))
        if idx < total:
            time.sleep(args.interval)

    state_dims = summarize_state_vectors(vectors, builder.dim_names)
    degenerate = sorted(
        name for name, row in state_dims.items()
        if row.get('degenerate')
    )
    result = {
        'measured': True,
        'samples': args.samples,
        'warmup': args.warmup,
        'interval_s': args.interval,
        'condition': args.condition,
        'generated_at_epoch': time.time(),
        'state_dim': len(builder.dim_names),
        'dimension_order': builder.dim_names,
        'degenerate_dimensions': degenerate,
        'notes': [
            'Measure while the network is healthy under episode-normal background traffic.',
            'Statistics are computed on the normalized StateBuilderDraft vector, not raw Thing features.',
            'Scenario visibility criterion: at least one non-degenerate dimension moves by >= abs_delta_threshold.',
            'abs_delta_threshold = 3 * sigma_robust; sigma_robust = 1.4826 * MAD.',
            'std fields are reference-only and must not drive the 3-sigma gate.',
        ],
        'state_dims': state_dims,
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

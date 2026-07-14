#!/usr/bin/env python3
"""Do nhieu nen cua state 9 chieu A2 (allocation-centric).

Khac voi measure_noise_std cu (45 chieu, mang-centric). Script nay do dung
state 9 chieu tu build_a2_state, tren dung Thing A2 dung (host-srv1/srv2),
trong dieu kien mang khoe + demand on dinh, khong inject su co.
"""

import argparse
import json
import math
import os
import random
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rl.a2.state_a2 import A2_DIM_NAMES, build_a2_state  # noqa: E402


MAD_TO_SIGMA = 1.4826


def median_abs_deviation(values, median):
    return statistics.median([abs(value - median) for value in values])


def summarize(vectors, dim_names):
    """Voi moi chieu: median, MAD, sigma_robust, nguong 3-sigma."""
    out = {}
    for idx, name in enumerate(dim_names):
        col = [
            float(vector[idx]) for vector in vectors
            if idx < len(vector) and math.isfinite(float(vector[idx]))
        ]
        if not col:
            out[name] = {
                'n': 0,
                'degenerate': True,
            }
            continue

        med = statistics.median(col)
        mad = median_abs_deviation(col, med)
        sigma = MAD_TO_SIGMA * mad
        std = statistics.stdev(col) if len(col) > 1 else 0.0
        threshold = 3.0 * sigma
        out[name] = {
            'n': len(col),
            'median': med,
            'mad': mad,
            'sigma_robust': sigma,
            'three_sigma': threshold,
            'lower': med - threshold,
            'upper': med + threshold,
            'min': min(col),
            'max': max(col),
            'degenerate': sigma == 0.0,
            'std_reference_only': std,
        }
    return out


def collect_a2_state_live(env, samples, interval, warmup):
    """Doc state 9 chieu tu A2 env dang chay khoe (khong su co)."""
    vectors = []
    total = samples + max(0, warmup)
    for idx in range(1, total + 1):
        obs = env._observe()
        kept = idx > warmup
        if kept:
            vectors.append(list(obs))
        print('%03d/%03d %s dim=%d' %
              (idx, total, 'keep' if kept else 'warmup', len(obs)))
        if idx < total:
            time.sleep(interval)
    return vectors


def make_self_test_vectors(samples):
    random.seed(0)
    vectors = []
    for _ in range(samples):
        vectors.append(build_a2_state(
            alloc_level_norm=0.5,
            goodput_A=8.0 + random.gauss(0.0, 0.2),
            goodput_B=6.0 + random.gauss(0.0, 0.2),
            demand_A=8.0,
            demand_B=6.0,
            c_total=20.0,
            step_progress=0.5,
            last_action=0,
        ))
    return vectors


def print_summary_table(state_dims):
    header = (
        '%-16s %4s %10s %10s %10s %10s %10s %5s' %
        ('dim', 'n', 'median', 'sigma', '3sigma', 'min', 'max', 'deg')
    )
    print(header)
    print('-' * len(header))
    for name in A2_DIM_NAMES:
        row = state_dims[name]
        print('%-16s %4d %10.6f %10.6f %10.6f %10.6f %10.6f %5s' %
              (name,
               row.get('n', 0),
               row.get('median', 0.0),
               row.get('sigma_robust', 0.0),
               row.get('three_sigma', 0.0),
               row.get('min', 0.0),
               row.get('max', 0.0),
               'YES' if row.get('degenerate') else 'no'))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Measure A2 9D state baseline noise with robust MAD stats')
    parser.add_argument('--samples', type=int, default=300)
    parser.add_argument('--warmup', type=int, default=3,
                        help='initial observations to discard')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='seconds between live observations')
    parser.add_argument('--out', default='results/noise/noise_a2.json')
    parser.add_argument('--condition', default='a2_healthy_stable_demand',
                        help='label for the live baseline condition')
    parser.add_argument('--self-test', action='store_true',
                        help='use synthetic vectors; does not need Mininet')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.self_test:
        vectors = make_self_test_vectors(args.samples)
        print('SELF-TEST: %d vector gia, dim=%d' %
              (len(vectors), len(vectors[0]) if vectors else 0))
    else:
        from mininet.env_runner import EnvRunner  # noqa: E402
        from rl.a2.twin_env_a2 import TwinEnvA2  # noqa: E402

        runner = EnvRunner()
        runner.start()
        try:
            env = TwinEnvA2(runner=runner)
            env.reset()
            vectors = collect_a2_state_live(
                env, args.samples, args.interval, args.warmup)
        finally:
            runner.close()

    state_dims = summarize(vectors, A2_DIM_NAMES)
    degenerate = sorted(
        name for name, row in state_dims.items()
        if row.get('degenerate')
    )
    result = {
        'measured': not args.self_test,
        'self_test': args.self_test,
        'samples': len(vectors),
        'warmup': args.warmup,
        'interval_s': args.interval,
        'condition': args.condition,
        'state_dim': len(A2_DIM_NAMES),
        'dimension_order': A2_DIM_NAMES,
        'degenerate_dimensions': degenerate,
        'generated_at_epoch': time.time(),
        'notes': [
            'Measure while the A2 network is healthy and no fault is injected.',
            'Statistics are computed on the normalized A2 9D state vector.',
            'Scenario visibility criterion: a real event should move at least one non-degenerate dimension beyond 3 sigma.',
            'three_sigma = 3 * sigma_robust; sigma_robust = 1.4826 * MAD.',
            'std_reference_only is for comparison only; do not use it as the gate.',
        ],
        'state_dims': state_dims,
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')

    print_summary_table(state_dims)
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

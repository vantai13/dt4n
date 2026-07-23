#!/usr/bin/env python3
"""Sweep calibrated routing-stage configs before training.

The goal is not to tune the link model. The measured physics is fixed. This
script only sweeps stage-design knobs: traffic ranges, and optionally a
what-if reward loss weight, so we can find configs that pass the oracle gate
without guessing one edit at a time.
"""

import argparse

from rl.routing_2path.oracle_gate import evaluate_config
from rl.routing_2path.reward_r import W_LOSS


DEFAULT_BASE_HIS = (0.90, 0.95)
DEFAULT_E_HIS = (1.00, 1.02, 1.05, 1.10)


def _parse_floats(text):
    return tuple(float(part.strip()) for part in text.split(',') if part.strip())


def _tag(row):
    return ' '.join(
        'G%d=%s' % (idx, 'Y' if row[key] else 'N')
        for idx, key in enumerate(('g1', 'g2', 'g3'), start=1)
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=50_000)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--base-lo', type=float, default=0.75)
    parser.add_argument('--e-lo', type=float, default=0.70)
    parser.add_argument('--base-his', default=','.join(map(str, DEFAULT_BASE_HIS)))
    parser.add_argument('--e-his', default=','.join(map(str, DEFAULT_E_HIS)))
    parser.add_argument('--drift-steps', type=int, default=2)
    parser.add_argument(
        '--std-seed-estimate',
        type=float,
        required=True,
        help='measured std_agent from the current model 5-seed run',
    )
    parser.add_argument(
        '--w-losses',
        default=str(W_LOSS),
        help='comma-separated what-if W_LOSS values; default keeps reward fixed',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    base_his = _parse_floats(args.base_his)
    e_his = _parse_floats(args.e_his)
    w_losses = _parse_floats(args.w_losses)

    print(
        '%-18s %-18s %-7s | %6s %6s %6s %7s %7s | gate'
        % ('base_load', 'e_load', 'W_LOSS', 'P(E)', 'SNR', 'asym', 'regF', 'regE')
    )
    print('-' * 98)

    passing = []
    total = 0
    for base_hi in base_his:
        for e_hi in e_his:
            for w_loss in w_losses:
                total += 1
                row = evaluate_config(
                    base_load=(args.base_lo, base_hi),
                    e_load=(args.e_lo, e_hi),
                    w_loss=w_loss,
                    n=args.samples,
                    seed=args.seed,
                    std_seed_estimate=args.std_seed_estimate,
                    drift_steps=args.drift_steps,
                )
                print(
                    '%-18s %-18s %-7.2f | %6.3f %6.2f %6.2f %7.4f %7.4f | %s'
                    % (
                        '(%.2f,%.2f)' % (args.base_lo, base_hi),
                        '(%.2f,%.2f)' % (args.e_lo, e_hi),
                        w_loss,
                        row['p_e'],
                        row['snr'],
                        row['asym'],
                        row['regret_f'],
                        row['regret_e'],
                        _tag(row),
                    )
                )
                if row['ok']:
                    passing.append((row['snr'], base_hi, e_hi, w_loss, row))

    print()
    if not passing:
        print('NO PASS: widen the sweep or rebalance C/D->F base delay first.')
        return 1

    passing.sort(reverse=True)
    print('PASSING CONFIGS: %d/%d' % (len(passing), total))
    print('Best by SNR:')
    snr, base_hi, e_hi, w_loss, row = passing[0]
    print(
        '  base_load=(%.2f, %.2f)  e_load=(%.2f, %.2f)  W_LOSS=%.2f'
        % (args.base_lo, base_hi, args.e_lo, e_hi, w_loss)
    )
    print(
        '  P(E)=%.3f  SNR=%.2f  asym=%.2fx  regF=%.4f  regE=%.4f'
        % (row['p_e'], row['snr'], row['asym'], row['regret_f'], row['regret_e'])
    )
    if abs(w_loss - W_LOSS) > 1e-12:
        print('  NOTE: this changes reward design, not only stage traffic.')
    if len(passing) < 3:
        print('  WARNING: pass region is narrow; confirm with --samples 200000.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

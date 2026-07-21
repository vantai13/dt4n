#!/usr/bin/env python3
"""Diagnose why paired AoI/mask eval rows are identical.

This reads the debug columns written by ``scripts/eval_paired.py`` and reports
whether equality comes from broken z plumbing or from both policies choosing
the same action under the fixed-z observation.
"""

from __future__ import annotations

import argparse
import csv
import glob
from collections import Counter, defaultdict


def parse_values(value: str | None) -> list[float]:
    if not value:
        return []
    return [float(x) for x in str(value).split('|') if x]


def parse_labels(value: str | None) -> list[str]:
    if not value:
        return []
    return [x for x in str(value).split('|') if x]


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float('nan')


def rate(rows: list[dict], pred, ref) -> float:
    if not rows:
        return float('nan')
    return sum(pred(row) == ref(row) for row in rows) / len(rows)


def summarize(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['case'], int(row['z']))].append(row)

    out = []
    for (case, z), items in sorted(grouped.items()):
        seen_min_matches_target = []
        seen_min_matches_mask = []
        seen_low = []
        seen_gap = []
        aoi_margin = []
        mask_margin = []
        z_seen_values = []
        aoi_s_values = []

        for row in items:
            labels = parse_labels(row.get('aoi_decision_neighbors'))
            seen = parse_values(row.get('aoi_decision_seen_offered'))
            if len(labels) == len(seen) and seen:
                min_label = labels[min(range(len(seen)), key=lambda idx: seen[idx])]
                seen_min_matches_target.append(min_label == row['aoi_decision_target'])
                seen_min_matches_mask.append(min_label == row['mask_decision_choice'])
                seen_low.append(min(seen))
                seen_gap.append(abs(seen[0] - seen[1]) if len(seen) >= 2 else 0.0)

            for branch, store in (('aoi', aoi_margin), ('mask', mask_margin)):
                q_values = parse_values(row.get(f'{branch}_decision_q_values'))
                if len(q_values) >= 2:
                    store.append(abs(q_values[0] - q_values[1]))

            if row.get('aoi_z_steps_at_decision'):
                z_seen_values.append(float(row['aoi_z_steps_at_decision']))
            if row.get('aoi_at_decision_s'):
                aoi_s_values.append(float(row['aoi_at_decision_s']))

        out.append({
            'case': case,
            'z': z,
            'n': len(items),
            'z_seen_mean': mean(z_seen_values),
            'aoi_s_mean': mean(aoi_s_values),
            'aoi_eq_mask': rate(
                items,
                lambda row: row['aoi_decision_choice'],
                lambda row: row['mask_decision_choice'],
            ),
            'aoi_target': rate(
                items,
                lambda row: row['aoi_decision_choice'],
                lambda row: row['aoi_decision_target'],
            ),
            'mask_target': rate(
                items,
                lambda row: row['mask_decision_choice'],
                lambda row: row['mask_decision_target'],
            ),
            'seen_min_target': mean([float(x) for x in seen_min_matches_target]),
            'seen_min_mask': mean([float(x) for x in seen_min_matches_mask]),
            'seen_low_mean': mean(seen_low),
            'seen_gap_mean': mean(seen_gap),
            'aoi_q_margin_mean': mean(aoi_margin),
            'mask_q_margin_mean': mean(mask_margin),
            'target_counts': dict(Counter(row['aoi_decision_target'] for row in items)),
            'mask_counts': dict(Counter(row['mask_decision_choice'] for row in items)),
        })
    return out


def print_table(rows: list[dict]) -> None:
    print(
        f"{'case':>8} {'z':>3} {'n':>4} {'zSeen':>6} {'AoI_s':>6} "
        f"{'A=M':>6} {'A=T':>6} {'M=T':>6} {'min=T':>6} {'min=M':>6} "
        f"{'low':>7} {'gap':>7} {'qA':>7} {'qM':>7}"
    )
    for row in rows:
        print(
            f"{row['case']:>8} {row['z']:3d} {row['n']:4d} "
            f"{row['z_seen_mean']:6.1f} {row['aoi_s_mean']:6.2f} "
            f"{row['aoi_eq_mask']:6.3f} {row['aoi_target']:6.3f} "
            f"{row['mask_target']:6.3f} {row['seen_min_target']:6.3f} "
            f"{row['seen_min_mask']:6.3f} {row['seen_low_mean']:7.3f} "
            f"{row['seen_gap_mean']:7.3f} {row['aoi_q_margin_mean']:7.3f} "
            f"{row['mask_q_margin_mean']:7.3f}"
        )
    print('\nLegend: A=M AoI-policy equals mask-policy; A=T/M=T equal target;')
    print('min=T stale local min equals target; low/gap summarize stale offered values.')


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'csv_glob',
        nargs='?',
        default='results/huong_a/eval_paired_s*.csv',
        help='CSV glob from eval_paired.py',
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    paths = sorted(glob.glob(args.csv_glob))
    if not paths:
        raise SystemExit(f'no CSV files matched: {args.csv_glob}')

    rows = []
    for path in paths:
        with open(path, newline='') as handle:
            rows.extend(csv.DictReader(handle))
    print(f'Read {len(rows)} rows from {len(paths)} files.')
    print_table(summarize(rows))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

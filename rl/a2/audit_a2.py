#!/usr/bin/env python3
"""Audit A2 dynamic demand scenarios without starting Mininet.

This is a cheap pre-train check: do generated scenarios create scarcity, and
does the optimal allocation level move far enough after the demand flip?
"""

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rl.a2.demand_scenario import (  # noqa: E402
    _best_level_for,
    _best_score_for,
    _default_levels,
    make_dynamic_scenario,
)


def audit_seed(seed, c_total, t_max, min_level_gap):
    levels = _default_levels(c_total)
    scenario = make_dynamic_scenario(
        seed,
        c_total=c_total,
        t_max=t_max,
        levels=levels,
        min_level_gap=min_level_gap,
    )
    l1 = _best_level_for(scenario.demand_A_1, scenario.demand_B_1, levels)
    l2 = _best_level_for(scenario.demand_A_2, scenario.demand_B_2, levels)
    s1 = _best_score_for(scenario.demand_A_1, scenario.demand_B_1, levels)
    s2 = _best_score_for(scenario.demand_A_2, scenario.demand_B_2, levels)
    total1 = scenario.demand_A_1 + scenario.demand_B_1
    total2 = scenario.demand_A_2 + scenario.demand_B_2
    return {
        'seed': int(seed),
        'kind': scenario.kind,
        't_shift': int(scenario.t_shift),
        'phase1_demand': [scenario.demand_A_1, scenario.demand_B_1],
        'phase2_demand': [scenario.demand_A_2, scenario.demand_B_2],
        'phase1_total_demand': round(total1, 3),
        'phase2_total_demand': round(total2, 3),
        'phase1_total_over_capacity': round(total1 / c_total, 3),
        'phase2_total_over_capacity': round(total2 / c_total, 3),
        'phase1_best_level': int(l1),
        'phase2_best_level': int(l2),
        'level_gap': int(abs(l1 - l2)),
        'phase1_best_satisfaction': round(float(s1), 4),
        'phase2_best_satisfaction': round(float(s2), 4),
        'scarce_phase1': bool(total1 > c_total and s1 < 1.999),
        'scarce_phase2': bool(total2 > c_total and s2 < 1.999),
    }


def summarize(rows, min_level_gap):
    if not rows:
        return {}
    gaps = [row['level_gap'] for row in rows]
    scores = [
        row['phase1_best_satisfaction'] for row in rows
    ] + [
        row['phase2_best_satisfaction'] for row in rows
    ]
    return {
        'n': len(rows),
        'min_level_gap_required': min_level_gap,
        'level_gap_min': min(gaps),
        'level_gap_mean': sum(gaps) / len(gaps),
        'level_gap_ok_n': sum(1 for gap in gaps if gap >= min_level_gap),
        'best_satisfaction_mean': sum(scores) / len(scores),
        'best_satisfaction_max': max(scores),
        'scarce_all_phases': all(
            row['scarce_phase1'] and row['scarce_phase2'] for row in rows
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser(description='Audit hard A2 demand scenarios')
    parser.add_argument('--seed-start', type=int, default=500)
    parser.add_argument('--seeds', type=int, default=20)
    parser.add_argument('--c-total', type=float, default=20.0)
    parser.add_argument('--t-max', type=int, default=8)
    parser.add_argument('--min-level-gap', type=int, default=2)
    parser.add_argument('--out', default='results/baseline/a2_dynamic_demand_audit.json')
    return parser.parse_args()


def main():
    args = parse_args()
    rows = [
        audit_seed(seed, args.c_total, args.t_max, args.min_level_gap)
        for seed in range(args.seed_start, args.seed_start + args.seeds)
    ]
    summary = summarize(rows, args.min_level_gap)
    report = {
        'args': vars(args),
        'levels': _default_levels(args.c_total),
        'summary': summary,
        'rows': rows,
    }

    print('seed kind          shift  ph1(A,B)       ph2(A,B)       gap  best_sat')
    for row in rows:
        print('%4d %-13s %5d  %-13s  %-13s  %3d  %.3f/%.3f'
              % (
                  row['seed'],
                  row['kind'],
                  row['t_shift'],
                  tuple(row['phase1_demand']),
                  tuple(row['phase2_demand']),
                  row['level_gap'],
                  row['phase1_best_satisfaction'],
                  row['phase2_best_satisfaction'],
              ))

    print('\nsummary:', summary)
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

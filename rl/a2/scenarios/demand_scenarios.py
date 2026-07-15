#!/usr/bin/env python3
"""Named A2 demand scenarios for train/eval.

The original generator creates anonymous random scenarios.  This module keeps
the same DemandScenario/DynamicDemandScenario API, but gives each case a stable
name so evaluation can say which behavior was tested.
"""

import numpy as np

from rl.a2.demand_scenario import DemandScenario, DynamicDemandScenario


DEFAULT_LEVELS = [
    (16.0, 4.0),
    (13.0, 7.0),
    (10.0, 10.0),
    (7.0, 13.0),
    (4.0, 16.0),
]

SCENARIO_NAMES = [
    'S1_easy_balanced',
    'S2_static_skew',
    'S3_flip_near',
    'S4_flip_far',
    'S5_scarce_flip',
]

SCENARIO_DESC = {
    'S1_easy_balanced': 'Static, near-budget, balanced. Easy control case.',
    'S2_static_skew': 'Static, over-budget, strongly skewed to one branch.',
    'S3_flip_near': 'Dynamic flip with a one-level optimal move.',
    'S4_flip_far': 'Dynamic flip with a far optimal move.',
    'S5_scarce_flip': 'Dynamic flip under heavier scarcity.',
}


def best_level_for(demand_A, demand_B, levels=None):
    """Return the allocation level with highest total satisfaction."""
    levels = levels or DEFAULT_LEVELS
    best_level = 0
    best_score = -1.0

    for level, (c_a, c_b) in enumerate(levels):
        sat_a = min(c_a / demand_A, 1.0) if demand_A > 1e-6 else 1.0
        sat_b = min(c_b / demand_B, 1.0) if demand_B > 1e-6 else 1.0
        score = sat_a + sat_b
        if score > best_score:
            best_level = level
            best_score = score

    return best_level, best_score


def _skewed_pair(rng, c_total, total_frac_lo, total_frac_hi, to_a):
    """Generate a demand pair with total demand as a fraction of capacity."""
    total = rng.uniform(total_frac_lo, total_frac_hi) * c_total
    frac_a = rng.uniform(0.62, 0.78) if to_a else rng.uniform(0.22, 0.38)
    return round(total * frac_a, 1), round(total * (1.0 - frac_a), 1)


def _t_shift(rng, t_max):
    lo = max(1, int(t_max) // 3)
    hi = max(lo + 1, 2 * int(t_max) // 3 + 1)
    return int(rng.integers(lo, hi))


def make_scenario(name, seed, c_total=20.0, t_max=8, levels=None):
    """Create one named scenario from a name and seed."""
    levels = levels or DEFAULT_LEVELS
    rng = np.random.default_rng(seed)

    if name == 'S1_easy_balanced':
        total = rng.uniform(0.95, 1.02) * c_total
        demand_a = round(total * rng.uniform(0.45, 0.55), 1)
        return DemandScenario(
            demand_A=demand_a,
            demand_B=round(total - demand_a, 1),
            kind='S1_easy_balanced',
        )

    if name == 'S2_static_skew':
        to_a = rng.random() < 0.5
        demand_a, demand_b = _skewed_pair(rng, c_total, 1.05, 1.20, to_a)
        return DemandScenario(
            demand_A=demand_a,
            demand_B=demand_b,
            kind='S2_static_skew',
        )

    if name in ('S3_flip_near', 'S4_flip_far', 'S5_scarce_flip'):
        if name == 'S3_flip_near':
            lo_f, hi_f, gap_min, gap_max = 1.05, 1.20, 1, 1
        elif name == 'S4_flip_far':
            lo_f, hi_f, gap_min, gap_max = 1.05, 1.20, 3, 4
        else:
            lo_f, hi_f, gap_min, gap_max = 1.20, 1.30, 2, 4

        to_a_first = rng.random() < 0.5
        demand_a_1 = demand_b_1 = demand_a_2 = demand_b_2 = None
        for _ in range(60):
            demand_a_1, demand_b_1 = _skewed_pair(
                rng, c_total, lo_f, hi_f, to_a_first
            )
            demand_a_2, demand_b_2 = _skewed_pair(
                rng, c_total, lo_f, hi_f, not to_a_first
            )
            gap = abs(
                best_level_for(demand_a_1, demand_b_1, levels)[0]
                - best_level_for(demand_a_2, demand_b_2, levels)[0]
            )
            if gap_min <= gap <= gap_max:
                break

        return DynamicDemandScenario(
            demand_A_1=demand_a_1,
            demand_B_1=demand_b_1,
            demand_A_2=demand_a_2,
            demand_B_2=demand_b_2,
            t_shift=_t_shift(rng, t_max),
            kind=name,
        )

    raise ValueError(
        'unknown scenario: %r (known: %s)' % (
            name,
            ', '.join(SCENARIO_NAMES),
        )
    )


def train_seeds(n, start=1000):
    """Return training seeds, kept separate from evaluation seeds."""
    return list(range(start, start + n))


def eval_seeds(n, start=500):
    """Return evaluation seeds, kept separate from training seeds."""
    return list(range(start, start + n))

#!/usr/bin/env python3
"""A2 — Demand scenario: cau hinh demand 2 branch theo seed.

Scenario A2 KHONG phai link fault, ma la CAU HINH DEMAND (moi branch can
bao nhieu). Nghiem toi uu phu thuoc demand -> agent phai doc demand de phan bo.

Nguyen tac: tong demand > C_total de LUON khan hiem (co danh doi).
3 loai: lech A, lech B, can bang — de agent thay du dang tinh huong.
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class DemandScenario:
    demand_A: float      # Mbps branch A can
    demand_B: float      # Mbps branch B can
    kind: str            # 'skew_A' | 'skew_B' | 'balanced'

    def describe(self):
        return {'demand_A': self.demand_A, 'demand_B': self.demand_B,
                'kind': self.kind}


@dataclass
class DynamicDemandScenario:
    """Demand flips at t_shift, creating the decision-flip A2 needs."""

    demand_A_1: float
    demand_B_1: float
    demand_A_2: float
    demand_B_2: float
    t_shift: int
    kind: str

    def demand_at(self, t):
        if int(t) < self.t_shift:
            return self.demand_A_1, self.demand_B_1
        return self.demand_A_2, self.demand_B_2

    def describe(self):
        return {
            't_shift': self.t_shift,
            'kind': self.kind,
            'phase1': (self.demand_A_1, self.demand_B_1),
            'phase2': (self.demand_A_2, self.demand_B_2),
        }


def make_demand_scenario(seed, c_total=20.0):
    """Sinh scenario demand theo seed. Tong demand > c_total (khan hiem)."""
    rng = np.random.default_rng(seed)
    kind = rng.choice(['skew_A', 'skew_B', 'balanced'])

    # bien do de tong ~ 1.2-1.5 x c_total (khan hiem vua phai)
    high = rng.uniform(0.65, 0.85) * c_total    # branch "dong" can nhieu
    low = rng.uniform(0.15, 0.35) * c_total     # branch "thua" can it
    mid = rng.uniform(0.55, 0.70) * c_total     # can bang: ca hai can vua

    if kind == 'skew_A':
        dA, dB = high, low
    elif kind == 'skew_B':
        dA, dB = low, high
    else:  # balanced — ca hai can nhieu, tong > budget -> khan hiem gat
        dA, dB = mid, mid

    return DemandScenario(demand_A=round(float(dA), 1),
                          demand_B=round(float(dB), 1),
                          kind=str(kind))


def _default_levels(c_total=20.0, n_levels=5):
    """Allocation levels matching AllocationSpace without importing it here."""
    hi, lo = 0.8, 0.2
    levels = []
    for idx in range(n_levels):
        frac = hi - (hi - lo) * idx / (n_levels - 1)
        c_a = round(float(c_total) * frac, 1)
        levels.append((c_a, round(float(c_total) - c_a, 1)))
    return levels


def _best_level_for(demand_A, demand_B, levels):
    """Return the level with highest total satisfaction for one demand pair."""
    best_level = 0
    best_score = -1.0
    for level, (c_a, c_b) in enumerate(levels):
        sat_a = min(c_a / demand_A, 1.0) if demand_A > 1e-6 else 1.0
        sat_b = min(c_b / demand_B, 1.0) if demand_B > 1e-6 else 1.0
        score = sat_a + sat_b
        if score > best_score:
            best_level = level
            best_score = score
    return best_level


def _best_score_for(demand_A, demand_B, levels):
    best = 0.0
    for c_a, c_b in levels:
        sat_a = min(c_a / demand_A, 1.0) if demand_A > 1e-6 else 1.0
        sat_b = min(c_b / demand_B, 1.0) if demand_B > 1e-6 else 1.0
        best = max(best, sat_a + sat_b)
    return best


def make_dynamic_scenario(seed, c_total=20.0, t_max=8, levels=None,
                          min_level_gap=2):
    """Generate a harder two-phase demand flip around mid-episode.

    The dynamic scenario is the future AoI stage: demand flips while the agent
    is making sequential relative actions. Keep two properties true:

    - total demand is 1.05-1.25x capacity, so there is always scarcity;
    - the best allocation levels before/after the flip are far enough apart
      that the relative-action agent must plan through several steps.
    """
    rng = np.random.default_rng(seed)
    levels = levels or _default_levels(c_total)

    def demand_pair(skew_to_a):
        total = rng.uniform(1.05, 1.25) * c_total
        frac_a = (
            rng.uniform(0.62, 0.78)
            if skew_to_a else
            rng.uniform(0.22, 0.38)
        )
        return (
            round(float(total * frac_a), 1),
            round(float(total * (1.0 - frac_a)), 1),
        )

    a_first = rng.random() < 0.5
    dA1 = dB1 = dA2 = dB2 = None
    l1 = l2 = 0
    for _ in range(20):
        dA1, dB1 = demand_pair(a_first)
        dA2, dB2 = demand_pair(not a_first)
        l1 = _best_level_for(dA1, dB1, levels)
        l2 = _best_level_for(dA2, dB2, levels)
        if abs(l1 - l2) >= min_level_gap:
            break

    lo = max(1, int(t_max) // 3)
    hi = max(lo + 1, 2 * int(t_max) // 3 + 1)
    t_shift = int(rng.integers(lo, hi))
    kind = 'hard_A_to_B' if a_first else 'hard_B_to_A'

    return DynamicDemandScenario(
        demand_A_1=dA1,
        demand_B_1=dB1,
        demand_A_2=dA2,
        demand_B_2=dB2,
        t_shift=t_shift,
        kind=kind,
    )

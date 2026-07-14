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


def make_dynamic_scenario(seed, c_total=20.0, t_max=8):
    """Generate a demand scenario that flips direction around mid-episode."""
    rng = np.random.default_rng(seed)
    high = rng.uniform(0.70, 0.85) * c_total
    low = rng.uniform(0.15, 0.30) * c_total

    lo = max(1, int(t_max) // 3)
    hi = max(lo + 1, 2 * int(t_max) // 3 + 1)
    t_shift = int(rng.integers(lo, hi))

    if rng.random() < 0.5:
        dA1, dB1, dA2, dB2 = high, low, low, high
        kind = 'A_to_B'
    else:
        dA1, dB1, dA2, dB2 = low, high, high, low
        kind = 'B_to_A'

    return DynamicDemandScenario(
        demand_A_1=round(float(dA1), 1),
        demand_B_1=round(float(dB1), 1),
        demand_A_2=round(float(dA2), 1),
        demand_B_2=round(float(dB2), 1),
        t_shift=t_shift,
        kind=kind,
    )

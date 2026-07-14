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
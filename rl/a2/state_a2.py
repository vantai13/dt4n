#!/usr/bin/env python3
"""A2 — State builder allocation-centric (~9 chieu).

Khac han state 51 chieu mang-centric: gon, tap trung vao PHAN BO tai nguyen.
Trung tam la DEMAND (branch dang can bao nhieu) — day la thu AoI se lam cu.
"""

import numpy as np


A2_DIM_NAMES = [
    'alloc_level',      # muc phan bo hien tai (0-1)
    'goodput_A',        # goodput branch A / c_total
    'goodput_B',        # goodput branch B / c_total
    'demand_A',         # demand branch A / c_total  ★ (AoI lam cu cai nay)
    'demand_B',         # demand branch B / c_total  ★
    'sat_A',            # min(goodput_A/demand_A, 1) — A no chua
    'sat_B',            # min(goodput_B/demand_B, 1) — B no chua
    'step_progress',    # t / t_max
    'last_action',      # action vua roi (chuan hoa)
]
A2_STATE_DIM = len(A2_DIM_NAMES)


def build_a2_state(alloc_level_norm, goodput_A, goodput_B,
                   demand_A, demand_B, c_total,
                   step_progress, last_action, n_actions=3):
    """Dung state vector A2 tu cac dai luong da do.

    Moi dai luong chuan hoa ve [0,1] cho on dinh training.
    """
    def clip01(x):
        return float(max(0.0, min(1.0, x)))

    gA = clip01(goodput_A / c_total)
    gB = clip01(goodput_B / c_total)
    dA = clip01(demand_A / c_total)
    dB = clip01(demand_B / c_total)
    satA = clip01(goodput_A / demand_A) if demand_A > 1e-6 else 1.0
    satB = clip01(goodput_B / demand_B) if demand_B > 1e-6 else 1.0

    vec = [
        clip01(alloc_level_norm),
        gA, gB,
        dA, dB,
        satA, satB,
        clip01(step_progress),
        clip01(last_action / max(n_actions - 1, 1)),
    ]
    return np.array(vec, dtype=np.float32)
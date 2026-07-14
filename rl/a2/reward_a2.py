#!/usr/bin/env python3
"""A2 — Reward (a): weighted satisfaction + fairness penalty + switch cost.

r = w_A·sat_A + w_B·sat_B − λ_fair·|sat_A−sat_B| − c_switch·shift − c_step

Trong do sat_i = min(goodput_i/demand_i, 1) — do no cua branch (no roi thi
them bw vo ich -> chong lang phi budget).

Nguyen tac can bang he so: LOI (sat) ap dao, cac phat la dieu chinh NHO.
- Efficiency vs fairness: lambda_fair NHO luc dau (gia vi, khong phai mon chinh)
- Switch cost: chong thrashing + nen cua hanh vi AoI-aware (nghi ngo thi giu)
"""

from dataclasses import dataclass


@dataclass
class RewardA2Config:
    w_A: float = 1.0          # trong so branch A
    w_B: float = 1.0          # trong so branch B
    lambda_fair: float = 0.3  # phat bat cong bang (NHO — gia vi)
    c_switch: float = 0.05    # chi phi moi lan shift (chong thrashing)
    c_step: float = 0.02      # chi phi thoi gian (giai nhanh)


@dataclass
class RewardA2Breakdown:
    """Phan ra tung thanh phan — de audit component_sums, bat reward-hacking."""
    serve_A: float
    serve_B: float
    fairness_pen: float
    switch_pen: float
    step_pen: float
    total: float


def satisfaction(goodput, demand):
    """sat = min(goodput/demand, 1). demand~0 -> coi nhu no (=1)."""
    if demand <= 1e-6:
        return 1.0
    return max(0.0, min(goodput / demand, 1.0))


def compute_reward_a2(goodput_A, demand_A, goodput_B, demand_B,
                      action, cfg):
    """Tinh reward A2 + breakdown.

    action: 0=no-op, 1/2 = shift (co switch cost).
    """
    satA = satisfaction(goodput_A, demand_A)
    satB = satisfaction(goodput_B, demand_B)

    serve_A = cfg.w_A * satA
    serve_B = cfg.w_B * satB
    fairness_pen = -cfg.lambda_fair * abs(satA - satB)
    switch_pen = -cfg.c_switch if action in (1, 2) else 0.0
    step_pen = -cfg.c_step

    total = serve_A + serve_B + fairness_pen + switch_pen + step_pen
    return RewardA2Breakdown(serve_A, serve_B, fairness_pen,
                             switch_pen, step_pen, total)
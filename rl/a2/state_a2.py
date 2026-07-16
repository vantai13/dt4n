#!/usr/bin/env python3
"""A2 state builder with demand AoI features.

The A2 state stays compact and allocation-centric.  Demand can now be stale:
goodput is fresh, demand may be old, and satisfaction is computed from those
two observed quantities.  That creates the intended "satiety illusion" when an
agent divides fresh goodput by stale demand.
"""

import numpy as np


A2_DIM_NAMES = [
    'alloc_level',
    'goodput_A',
    'goodput_B',
    'demand_A',
    'demand_B',
    'sat_A',
    'sat_B',
    'step_progress',
    'last_action',
    'aoi_norm',
    'data_fresh',
]
A2_STATE_DIM = len(A2_DIM_NAMES)

AOI_DIMS = (9, 10)
AOI_NORM_DIVISOR_S = 6.0
FRESH_THRESHOLD_S = 1.0


def aoi_features(aoi_s):
    """Return normalized AoI and a binary freshness indicator."""
    aoi_s = float(max(0.0, aoi_s))
    aoi_norm = min(aoi_s / AOI_NORM_DIVISOR_S, 1.0)
    data_fresh = 1.0 if aoi_s < FRESH_THRESHOLD_S else 0.0
    return aoi_norm, data_fresh


def build_a2_state(alloc_level_norm, goodput_A, goodput_B,
                   demand_A, demand_B, c_total,
                   step_progress, last_action, n_actions=3,
                   aoi_s=0.0):
    """Build the normalized A2 state vector.

    ``demand_A`` and ``demand_B`` are the demand values observed by the agent.
    They may be stale.  Reward and diagnostics still use true demand in the env.
    """
    def clip01(x):
        return float(max(0.0, min(1.0, x)))

    gA = clip01(goodput_A / c_total)
    gB = clip01(goodput_B / c_total)
    dA = clip01(demand_A / c_total)
    dB = clip01(demand_B / c_total)
    satA = clip01(goodput_A / demand_A) if demand_A > 1e-6 else 1.0
    satB = clip01(goodput_B / demand_B) if demand_B > 1e-6 else 1.0
    aoi_norm, data_fresh = aoi_features(aoi_s)

    vec = [
        clip01(alloc_level_norm),
        gA, gB,
        dA, dB,
        satA, satB,
        clip01(step_progress),
        clip01(last_action / max(n_actions - 1, 1)),
        aoi_norm,
        data_fresh,
    ]
    return np.array(vec, dtype=np.float32)


def mask_aoi(state_vec):
    """Zero out AoI dimensions without changing state dimensionality."""
    masked = np.array(state_vec, dtype=np.float32, copy=True)
    for dim in AOI_DIMS:
        masked[dim] = 0.0
    return masked

#!/usr/bin/env python3
"""RouteEnv state builder, intentionally compact for AoI ablation.

State is 7-D. Two dimensions are AoI features, so a Phase-11 ablation hides
2/7 = 28.6% of the input. Keeping the state small is part of the experiment:
it prevents the AoI signal from being diluted by unrelated routing features.
"""

import numpy as np


MAX_NEIGHBORS = 2

R_DIM_NAMES = [
    'current_node',
    'hop_progress',
    'util_n0',
    'util_n1',
    'valid_n1',
    'aoi_norm',
    'data_fresh',
]
R_STATE_DIM = len(R_DIM_NAMES)

AOI_DIMS = (5, 6)
UTIL_DIMS = (2, 3)

AOI_NORM_DIVISOR_S = 6.0
FRESH_THRESHOLD_S = 1.0


def aoi_features(aoi_s):
    """Return normalized AoI and a binary freshness indicator."""
    aoi_s = float(max(0.0, aoi_s))
    aoi_norm = min(aoi_s / AOI_NORM_DIVISOR_S, 1.0)
    data_fresh = 1.0 if aoi_s < FRESH_THRESHOLD_S else 0.0
    return aoi_norm, data_fresh


def build_route_state(current_idx, n_nodes,
                      step, max_steps,
                      neighbor_utils, neighbor_valid,
                      aoi_s=0.0):
    """Build the 7-D normalized RouteEnv state vector.

    ``neighbor_utils`` are what the agent observes. A later staleness wrapper
    may pass older values here. Reward must still be computed from true values
    inside the environment.
    """
    def clip01(x):
        return float(max(0.0, min(1.0, x)))

    denom = max(int(n_nodes) - 1, 1)
    utils = list(neighbor_utils) + [0.0] * MAX_NEIGHBORS
    valid = list(neighbor_valid) + [0.0] * MAX_NEIGHBORS
    aoi_norm, data_fresh = aoi_features(aoi_s)

    vec = [
        clip01(float(current_idx) / denom),
        clip01(float(step) / max(int(max_steps), 1)),
        clip01(utils[0]),
        clip01(utils[1]),
        clip01(valid[1]),
        aoi_norm,
        data_fresh,
    ]
    return np.array(vec, dtype=np.float32)


def mask_aoi(state_vec):
    """Zero AoI dimensions without changing dimensionality."""
    masked = np.array(state_vec, dtype=np.float32, copy=True)
    for dim in AOI_DIMS:
        masked[dim] = 0.0
    return masked

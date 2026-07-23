#!/usr/bin/env python3
"""RouteEnv state builder, intentionally compact for AoI ablation.

State is 9-D. ``util`` carries delivered throughput and clips at 1.0, while
``loss`` carries the overload information that remains visible after the link
has saturated. Two dimensions are AoI features, so a Phase-11 ablation hides a
large enough part of the input to stay measurable without diluting the routing
signal with unrelated features.
"""

import numpy as np


MAX_NEIGHBORS = 2

R_DIM_NAMES = [
    'current_node',
    'hop_progress',
    'util_n0',
    'util_n1',
    'loss_n0',
    'loss_n1',
    'valid_n1',
    'aoi_norm',
    'data_fresh',
]
R_STATE_DIM = len(R_DIM_NAMES)

AOI_DIMS = (7, 8)
UTIL_DIMS = (2, 3)
LOSS_DIMS = (4, 5)

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
                      neighbor_losses=None,
                      aoi_s=0.0):
    """Build the normalized RouteEnv state vector.

    ``neighbor_utils`` are what the agent observes. A later staleness wrapper
    may pass older values here. ``neighbor_losses`` follows the same observed
    snapshot. Reward must still be computed from true values inside the
    environment.
    """
    def clip01(x):
        return float(max(0.0, min(1.0, x)))

    denom = max(int(n_nodes) - 1, 1)
    utils = list(neighbor_utils) + [0.0] * MAX_NEIGHBORS
    if neighbor_losses is None:
        neighbor_losses = [0.0] * MAX_NEIGHBORS
    losses = list(neighbor_losses) + [0.0] * MAX_NEIGHBORS
    valid = list(neighbor_valid) + [0.0] * MAX_NEIGHBORS
    aoi_norm, data_fresh = aoi_features(aoi_s)

    vec = [
        clip01(float(current_idx) / denom),
        clip01(float(step) / max(int(max_steps), 1)),
        clip01(utils[0]),
        clip01(utils[1]),
        clip01(losses[0]),
        clip01(losses[1]),
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

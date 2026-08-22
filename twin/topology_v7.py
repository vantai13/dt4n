#!/usr/bin/env python3
"""Topology v7: 2x2 butterfly, K=4, with proper-subset shared links.

This replaces the old symmetric three-path stage for Phase 20. The topology is
a small leaf-spine/Clos fragment: every shared link is used by a proper subset
of paths, so link errors can affect rankings instead of adding a common
constant to every action.

Calibration constraint: link bandwidths stay in {4, 6, 8} Mbps, the measured
bandwidths used by ``results/SUPERSEDED/calib/density_bw{4,6,8}_*.csv``.
"""

from __future__ import annotations

import numpy as np

from twin.link_model import (
    CLIFF_RHO_OFFERED,
    CRITICAL_TO_FULL_RHO_OFFERED,
    LOW_TO_CRITICAL_RHO_OFFERED,
    loss_rate,
    total_delay_ms,
)


NODES = ("SRC", "A", "B", "C", "D", "DST")

# link_name: (bw_mbps, base_delay_ms, queue_pkts)
LINKS = {
    "uA": (8.0, 2.0, 18),   # SRC->A, edge, shared by {P1,P2}
    "uB": (6.0, 2.0, 13),   # SRC->B, edge, shared by {P3,P4}
    "ac": (6.0, 3.0, 13),   # A->C, core, P1
    "ad": (4.0, 3.0, 10),   # A->D, core, P2
    "bc": (6.0, 4.0, 13),   # B->C, core, P3
    "bd": (6.0, 3.0, 13),   # B->D, core, P4
    "vC": (8.0, 2.0, 18),   # C->DST, edge, shared by {P1,P3}
    "vD": (6.0, 2.5, 13),   # D->DST, edge, shared by {P2,P4}
}
LINK_NAMES = tuple(LINKS)

PATHS = {
    "P1": ("uA", "ac", "vC"),
    "P2": ("uA", "ad", "vD"),
    "P3": ("uB", "bc", "vC"),
    "P4": ("uB", "bd", "vD"),
}
PATH_NAMES = tuple(PATHS)
K = len(PATH_NAMES)

# Jump thresholds of the calibrated staircase link model. Phase 20 uses
# distance to these steps, not a local derivative, as the main stability radius.
JUMPS = (LOW_TO_CRITICAL_RHO_OFFERED, CRITICAL_TO_FULL_RHO_OFFERED)
CLIFF = CLIFF_RHO_OFFERED

# Q8 stage target: edge links idle, core links cross the measured cliff. These
# are targets for traffic generation, not hand-tuned results from the main run.
LOAD_MEAN = {
    "uA": 0.80,
    "uB": 0.82,
    "ac": 0.920,
    "ad": 0.930,
    "bc": 0.915,
    "bd": 0.925,
    "vC": 0.80,
    "vD": 0.83,
}
LOAD_SIGMA_TARGET = 0.010
LOAD_TAU_TARGET_STEPS = 8.0

W_LOSS_DEFAULT = 2500.0
EPS = 1e-9


def path_delay_loss(rho, path):
    """Return ``(end_to_end_delay_ms, end_to_end_loss)`` for one path."""
    delay = 0.0
    keep = 1.0
    for link in PATHS[path]:
        bw, base_delay, queue_pkts = LINKS[link]
        delay += total_delay_ms(
            base_delay,
            rho[link],
            bw_mbps=bw,
            queue_pkts=queue_pkts,
        )
        keep *= 1.0 - loss_rate(rho[link])
    return delay, 1.0 - keep


def path_cost(rho, path, w_loss=W_LOSS_DEFAULT):
    """Return SLA-aligned path cost: delay plus loss penalty."""
    delay, loss = path_delay_loss(rho, path)
    return delay + w_loss * loss


def decide(rho, w_loss=W_LOSS_DEFAULT):
    """Return ``(best_index, costs, has_tie)`` with deterministic tie-breaking."""
    costs = np.array([path_cost(rho, p, w_loss) for p in PATH_NAMES])
    best = costs.min()
    has_tie = int(np.sum(costs - best < EPS)) > 1
    return int(np.argmin(costs)), costs, has_tie


def r_jump(rho):
    """Distance from the current link loads to the nearest staircase jump."""
    return min(abs(rho[link] - jump) for link in LINK_NAMES for jump in JUMPS)


def r_smooth(rho, w_loss=W_LOSS_DEFAULT, slope_ms_per_rho=3.2):
    """Smooth-region decision stability radius."""
    costs = np.sort([path_cost(rho, p, w_loss) for p in PATH_NAMES])
    return (costs[1] - costs[0]) / (2.0 * slope_ms_per_rho)


def r_stability(rho, w_loss=W_LOSS_DEFAULT):
    """Decision stability radius used by Phase 20 diagnostics."""
    return min(r_jump(rho), r_smooth(rho, w_loss))


def sharing_matrix():
    """Return link -> paths and assert every link is used by a proper subset."""
    out = {}
    for link in LINK_NAMES:
        users = tuple(path for path in PATH_NAMES if link in PATHS[path])
        if not (0 < len(users) < K):
            raise AssertionError(
                "link %s is used by %d/%d paths; a link shared by every "
                "path does not change argmin" % (link, len(users), K)
            )
        out[link] = users
    return out


if __name__ == "__main__":
    for link, users in sharing_matrix().items():
        print("%s: used by %s" % (link, users))

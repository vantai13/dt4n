#!/usr/bin/env python3
"""Locked 8-node routing topology for Phase 8-12.

V2 is calibrated to the real Mininet testbed's small-machine link budget:
4-8 Mbps rather than the old simulator-only 50-100 Mbps. The structure stays
8-node and compact so the state/action design from Lesson 8.2 remains valid.

Structure:
    SRC -> {A,B} -> {C,D} -> {E narrow-fast | F wide-slow} -> F -> DST

The E/F choice is the point: E is narrow-fast, F is wide-slow. Their ordering
flips as E utilization crosses the decision boundary.
"""

TOPO_V2 = {
    'nodes': ['SRC', 'A', 'B', 'C', 'D', 'E', 'F', 'DST'],
    # [from, to, base_delay_ms, base_bw_mbps]
    'edges': [
        ['SRC', 'A', 2.0, 8.0],
        ['SRC', 'B', 2.5, 8.0],
        ['A', 'C', 3.0, 6.0],
        ['A', 'D', 4.0, 6.0],
        ['B', 'C', 4.0, 6.0],
        ['B', 'D', 3.0, 6.0],
        ['C', 'E', 2.0, 4.0],
        ['D', 'E', 2.0, 4.0],
        ['E', 'F', 1.0, 8.0],
        ['C', 'F', 6.0, 8.0],
        ['D', 'F', 5.5, 8.0],
        ['F', 'DST', 1.5, 8.0],
    ],
    'source': 'SRC',
    'destination': 'DST',
}

# Backward-compatible name used by the Lesson 8.2/8.3 code.
TOPO = TOPO_V2

# Named slices of the same continuous load axis. Use these for demo or Phase 12
# storytelling, not for the main AoI curve where ``e_load`` is swept.
LOAD_PRESETS = {
    'normal': {
        'base_load': (0.25, 0.40),
        'e_load': (0.30, 0.50),
    },
    'borderline': {
        'base_load': (0.25, 0.40),
        'e_load': (0.70, 0.85),
    },
    'bottleneck_E': {
        'base_load': (0.25, 0.40),
        'e_load': (0.88, 0.95),
    },
}

LOAD_CFG_V1 = {
    'base_load': (0.25, 0.40),
    'e_load': (0.80, 0.97),
    'drift_sigma': 0.15,
}

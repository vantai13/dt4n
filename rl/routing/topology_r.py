#!/usr/bin/env python3
"""Locked 8-node routing topology for Phase 8-12.

V2 is the 8-node topology inherited from the routing-sdn lineage, scaled down
to the small-machine Mininet budget and updated after Lesson 9.0 calibration.
The E/F choice is deliberately close under low load; the measured finite-queue
cliff on C/D->E makes the decision flip when offered load crosses saturation.

Structure:
    SRC -> {A,B} -> {C,D} -> {E narrow-fast | F wide-slow} -> F -> DST

The E/F choice is the point: E is narrow-fast, F is wide-slow. Their ordering
flips when E offered load crosses the measured saturation cliff.
"""

TOPO_V2 = {
    'nodes': ['SRC', 'A', 'B', 'C', 'D', 'E', 'F', 'DST'],
    # [from, to, base_delay_ms, base_bw_mbps]
    'default_queue_pkts': 13,
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
        ['D', 'F', 6.0, 8.0],
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

# [9.3] Training load, intentionally separate from LOAD_CFG_V1.
#
# LOAD_CFG_TRAIN is tuned only after the measured link model is fixed. It keeps
# the E/F decision alive while staying inside the measured offered-load range.
LOAD_CFG_TRAIN = {
    'base_load': (0.75, 0.95),
    'e_load': (0.70, 1.00),
    'drift_sigma': 0.15,
}

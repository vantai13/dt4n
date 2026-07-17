#!/usr/bin/env python3
"""[9.3] Guardrails for the routing training load configuration."""

import sys

sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')

from diag_decision_balance import frac_E_better
from rl.routing.metrics_r import evaluate_z_range
from rl.routing.topology_r import LOAD_CFG_TRAIN, LOAD_CFG_V1


def test_load_cfg_v1_is_static_policy_risk_for_agent_training():
    """V1 stays useful for Dijkstra sweep, but is too one-sided for DQN train."""
    assert frac_E_better(LOAD_CFG_V1, n=200) < 0.05


def test_load_cfg_train_keeps_decision_alive():
    """Training load must keep the optimal E/F decision from freezing."""
    frac = frac_E_better(LOAD_CFG_TRAIN, n=200)
    assert 0.20 <= frac <= 0.80


def test_load_cfg_train_keeps_aoi_signal_measurable():
    """The balanced train load should still have a measurable AoI effect."""
    rows = evaluate_z_range(
        z_values=(0, 1, 3, 5, 8, 12),
        seeds=range(100),
        load_cfg=LOAD_CFG_TRAIN,
    )
    costs = [row['cost_of_blindness'] for row in rows]
    assert max(costs) > 0.30

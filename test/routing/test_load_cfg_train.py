#!/usr/bin/env python3
"""[9.3] Guardrails for the routing training load configuration."""

import sys

sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')

from diag_decision_balance import frac_E_better
from rl.routing.metrics_r import evaluate_z_range
from rl.routing.oracle_gate import evaluate_oracle_gate
from rl.routing.topology_r import LOAD_CFG_TRAIN, LOAD_CFG_V1


def test_load_cfg_v1_is_usable_but_less_balanced_than_train():
    """After calibration V1 is usable, while TRAIN is the tighter balance."""
    frac = frac_E_better(LOAD_CFG_V1, n=200)
    assert 0.65 <= frac <= 0.90


def test_load_cfg_train_keeps_decision_alive():
    """Training load must keep the post-drift E/F decision from freezing."""
    result = evaluate_oracle_gate(n_samples=20_000, seed=0)
    assert 0.35 <= result.p_e_optimal <= 0.65


def test_load_cfg_train_passes_pretrain_oracle_gate():
    result = evaluate_oracle_gate(n_samples=20_000, seed=0)
    assert result.ok


def test_load_cfg_train_keeps_aoi_signal_measurable():
    """The balanced train load should still have a measurable AoI effect."""
    rows = evaluate_z_range(
        z_values=(0, 1, 3, 5, 8, 12),
        seeds=range(100),
        load_cfg=LOAD_CFG_TRAIN,
    )
    costs = [row['cost_of_blindness'] for row in rows]
    assert max(costs) > 0.30


def _run_as_script():
    tests = [
        test_load_cfg_v1_is_usable_but_less_balanced_than_train,
        test_load_cfg_train_keeps_decision_alive,
        test_load_cfg_train_passes_pretrain_oracle_gate,
        test_load_cfg_train_keeps_aoi_signal_measurable,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f'  PASS  {test.__name__}')
    print(f'\n{passed}/{len(tests)} passed')


if __name__ == '__main__':
    _run_as_script()

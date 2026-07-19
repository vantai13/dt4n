#!/usr/bin/env python3
"""[9.3] Guardrails for the routing training load configuration."""

import sys

sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')

from diag_decision_balance import frac_E_better
from rl.routing.oracle_gate import evaluate_oracle_gate
from rl.routing.topology_r import (
    LOAD_CFG_TRAIN,
    LOAD_CFG_SWEEP,
    LOAD_CFG_V1,
    SCENARIOS_TRAIN,
    SCENARIOS_SWEEP,
    TRAIN_SCENARIO_MIX,
    resolve_load_scenario,
)


REV5_STD_AGENT = 0.07988327839856281


def test_load_cfg_v1_is_usable_but_less_balanced_than_train():
    """After calibration V1 is usable, while TRAIN is the tighter balance."""
    frac = frac_E_better(LOAD_CFG_V1, n=200)
    assert 0.65 <= frac <= 0.90


def test_load_cfg_train_keeps_decision_alive():
    """Training load must keep the post-drift E/F decision from freezing."""
    result = evaluate_oracle_gate(
        n_samples=20_000,
        seed=0,
        std_seed_estimate=REV5_STD_AGENT,
    )
    assert 0.35 <= result.p_e_optimal <= 0.65


def test_load_cfg_train_passes_current_std_snr_gate():
    result = evaluate_oracle_gate(
        n_samples=20_000,
        seed=0,
        std_seed_estimate=REV5_STD_AGENT,
    )
    assert result.g1_balance
    assert result.g3_symmetry
    assert result.g2_snr
    assert result.ok


def test_load_cfg_train_uses_corrected_static_scenario_mix():
    """Train on corrected C/D->E vs C/D->F scenarios; dynamic drift is later."""
    assert LOAD_CFG_TRAIN['scenario_mix'] == TRAIN_SCENARIO_MIX
    assert LOAD_CFG_TRAIN['scenarios'] == SCENARIOS_TRAIN
    assert all(
        SCENARIOS_TRAIN[name]['drift_sigma'] == 0.0
        for name in TRAIN_SCENARIO_MIX
    )


def test_load_cfg_sweep_keeps_parent_drift_alive():
    """Phase-10 sweep must not let child scenarios shadow parent drift."""
    assert LOAD_CFG_SWEEP['scenario_mix'] == tuple(SCENARIOS_SWEEP)
    assert LOAD_CFG_SWEEP['drift_sigma'] == 0.15
    assert all('drift_sigma' not in scenario
               for scenario in SCENARIOS_SWEEP.values())

    for name in LOAD_CFG_SWEEP['scenario_mix']:
        resolved, resolved_name = resolve_load_scenario(LOAD_CFG_SWEEP, name)
        assert resolved_name == name
        assert resolved['drift_sigma'] == LOAD_CFG_SWEEP['drift_sigma']


def _run_as_script():
    tests = [
        test_load_cfg_v1_is_usable_but_less_balanced_than_train,
        test_load_cfg_train_keeps_decision_alive,
        test_load_cfg_train_passes_current_std_snr_gate,
        test_load_cfg_train_uses_corrected_static_scenario_mix,
        test_load_cfg_sweep_keeps_parent_drift_alive,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print(f'  PASS  {test.__name__}')
    print(f'\n{passed}/{len(tests)} passed')


if __name__ == '__main__':
    _run_as_script()

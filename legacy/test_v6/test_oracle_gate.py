#!/usr/bin/env python3
"""Tests for the calibrated routing pre-train oracle gate."""

import sys

sys.path.insert(0, '.')

from rl.routing_2path.oracle_gate import evaluate_oracle_gate


REV5_STD_AGENT = 0.07988327839856281


def test_oracle_gate_requires_current_std_agent():
    try:
        evaluate_oracle_gate(n_samples=1_000, seed=0)
    except ValueError as exc:
        assert 'std_seed_estimate is required' in str(exc)
    else:
        raise AssertionError('gate must not use a stale default std estimate')


def test_oracle_gate_allows_scenario_training_stage_with_rev5_std():
    result = evaluate_oracle_gate(
        n_samples=20_000,
        seed=0,
        std_seed_estimate=REV5_STD_AGENT,
    )
    assert result.g1_balance
    assert result.g3_symmetry
    assert result.g2_snr
    assert result.ok


def _run_as_script():
    tests = [
        test_oracle_gate_requires_current_std_agent,
        test_oracle_gate_allows_scenario_training_stage_with_rev5_std,
    ]
    for test in tests:
        test()
        print('  PASS  %s' % test.__name__)
    print('\n%d/%d passed' % (len(tests), len(tests)))


if __name__ == '__main__':
    _run_as_script()

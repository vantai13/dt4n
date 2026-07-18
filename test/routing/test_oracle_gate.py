#!/usr/bin/env python3
"""Tests for the calibrated routing pre-train oracle gate."""

import sys

sys.path.insert(0, '.')

from rl.routing.oracle_gate import evaluate_oracle_gate


def test_oracle_gate_allows_current_training_stage():
    result = evaluate_oracle_gate(n_samples=20_000, seed=0)
    assert result.g1_balance
    assert result.g2_snr
    assert result.g3_symmetry
    assert result.ok


def _run_as_script():
    tests = [
        test_oracle_gate_allows_current_training_stage,
    ]
    for test in tests:
        test()
        print('  PASS  %s' % test.__name__)
    print('\n%d/%d passed' % (len(tests), len(tests)))


if __name__ == '__main__':
    _run_as_script()

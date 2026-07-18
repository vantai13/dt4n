#!/usr/bin/env python3
"""Negative controls for the calibrated routing oracle gate.

A useful gate must reject at least one known-bad stage. The Phase-8-style
traffic range was static-policy-prone, so the calibrated gate must not mark it
as train-ready.
"""

import sys

sys.path.insert(0, '.')

from rl.routing.oracle_gate import evaluate_config


REV5_STD_AGENT = 0.07988327839856281


def test_gate_rejects_phase8_style_config():
    row = evaluate_config(
        base_load=(0.25, 0.40),
        e_load=(0.60, 0.97),
        n=50_000,
        seed=0,
        std_seed_estimate=REV5_STD_AGENT,
    )
    print(
        'Phase8-style config: P(E)=%.3f SNR=%.2f asym=%.2f gates=%s%s%s'
        % (
            row['p_e'],
            row['snr'],
            row['asym'],
            'Y' if row['g1'] else 'N',
            'Y' if row['g2'] else 'N',
            'Y' if row['g3'] else 'N',
        )
    )
    assert not row['ok'], (
        'GATE BROKEN: it allowed the Phase-8-style static-policy-risk config.'
    )


def test_gate_rejects_obvious_static_e_config():
    row = evaluate_config(
        base_load=(0.25, 0.40),
        e_load=(0.30, 0.50),
        n=20_000,
        seed=0,
        std_seed_estimate=REV5_STD_AGENT,
    )
    print(
        'Always-E config: P(E)=%.3f SNR=%.2f asym=%.2f gates=%s%s%s'
        % (
            row['p_e'],
            row['snr'],
            row['asym'],
            'Y' if row['g1'] else 'N',
            'Y' if row['g2'] else 'N',
            'Y' if row['g3'] else 'N',
        )
    )
    assert not row['ok'], (
        'GATE BROKEN: it allowed an obvious always-E static-policy config.'
    )


def _run_as_script():
    tests = [
        test_gate_rejects_phase8_style_config,
        test_gate_rejects_obvious_static_e_config,
    ]
    passed = 0
    for test in tests:
        test()
        passed += 1
        print('  PASS  %s' % test.__name__)
    print('\n%d/%d passed' % (passed, len(tests)))


if __name__ == '__main__':
    _run_as_script()

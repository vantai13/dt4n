#!/usr/bin/env python3
"""Pure tests for robust state-vector noise calibration."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from measurements.measure_noise_std import summarize_state_vectors  # noqa: E402


def test_robust_sigma_uses_mad_not_std():
    summary = summarize_state_vectors(
        [
            [1.0, 0.0],
            [2.0, 0.0],
            [3.0, 10.0],
        ],
        ['smooth', 'bursty'],
    )

    smooth = summary['smooth']
    assert smooth['median'] == 2.0
    assert abs(smooth['mad'] - 1.0) < 1e-12
    assert abs(smooth['sigma_robust'] - 1.4826) < 1e-12
    assert abs(smooth['abs_delta_threshold'] - 4.4478) < 1e-12
    assert smooth['degenerate'] is False

    bursty = summary['bursty']
    assert bursty['median'] == 0.0
    assert bursty['mad'] == 0.0
    assert bursty['sigma_robust'] == 0.0
    assert bursty['degenerate'] is True
    assert bursty['std_reference_only'] > 0.0


if __name__ == '__main__':
    tests = [
        test_robust_sigma_uses_mad_not_std,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('noise std tests passed')

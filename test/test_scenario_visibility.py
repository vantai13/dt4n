#!/usr/bin/env python3
"""Test thuan cho logic phan dinh blind-spot (khong can Mininet/Ditto)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from measurements.scenario_visibility import (  # noqa: E402
    dimension_movements,
    classify_scenario,
)


DIM_ORDER = ['util:s2-s3', 'link_up:s1-s2', 'delay_mm1:s2-s3']
THRESHOLDS = {
    'util:s2-s3':          {'abs_delta_threshold': 0.05, 'degenerate': False,
                            'sigma_robust': 0.0167},
    'link_up:s1-s2':       {'abs_delta_threshold': 0.0,  'degenerate': True,
                            'sigma_robust': 0.0},
    'delay_mm1:s2-s3':     {'abs_delta_threshold': 0.02, 'degenerate': False,
                            'sigma_robust': 0.0067},
}


def test_visible_when_one_dim_exceeds_threshold():
    # util nhay tu 0.30 -> 0.62: delta 0.32 >> nguong 0.05 -> nhin thay
    baseline = [0.30, 1.0, 0.01]
    faulted  = [0.62, 1.0, 0.01]
    movements = dimension_movements(baseline, faulted, DIM_ORDER, THRESHOLDS)
    verdict = classify_scenario(movements)
    assert verdict['visible'] is True
    assert verdict['blind_spot'] is False
    assert verdict['top_dims'][0]['dim'] == 'util:s2-s3'


def test_blind_spot_when_nothing_moves_enough():
    # moi chieu chi rung trong nguong -> khong nhin thay -> blind-spot
    baseline = [0.30, 1.0, 0.010]
    faulted  = [0.33, 1.0, 0.015]   # util +0.03 < 0.05; delay +0.005 < 0.02
    movements = dimension_movements(baseline, faulted, DIM_ORDER, THRESHOLDS)
    verdict = classify_scenario(movements)
    assert verdict['blind_spot'] is True
    assert verdict['n_moved'] == 0


def test_degenerate_dim_moves_on_any_change():
    # link_up (degenerate) lat tu 1 -> 0: du delta nho van tinh nhin thay
    baseline = [0.30, 1.0, 0.010]
    faulted  = [0.31, 0.0, 0.011]   # util & delay trong nguong; chi link_up lat
    movements = dimension_movements(baseline, faulted, DIM_ORDER, THRESHOLDS)
    verdict = classify_scenario(movements)
    assert verdict['visible'] is True
    moved_dims = [m['dim'] for m in movements if m['moved']]
    assert moved_dims == ['link_up:s1-s2']


if __name__ == '__main__':
    for t in (test_visible_when_one_dim_exceeds_threshold,
              test_blind_spot_when_nothing_moves_enough,
              test_degenerate_dim_moves_on_any_change):
        t()
        print('PASS %s' % t.__name__)
    print('scenario_visibility pure tests passed')

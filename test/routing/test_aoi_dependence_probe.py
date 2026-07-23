#!/usr/bin/env python3
"""Tests for the AoI-dependence gap probe."""

import sys

import numpy as np

sys.path.insert(0, ".")

from measurements.probe_aoi_dependence import (  # noqa: E402
    ACTION_DIRECT_F,
    ACTION_VIA_E,
    aware_action,
    drift_forward,
    fresh_action,
    measure_gap,
)
from rl.routing.topology_r import LOAD_CFG_TRAIN, TOPO_V2  # noqa: E402


def _rho_snapshot(base=0.30, e_load=0.90, f_load=0.30):
    rho = {(src, dst): float(base) for src, dst, *_rest in TOPO_V2["edges"]}
    rho[("C", "E")] = float(e_load)
    rho[("D", "E")] = float(e_load)
    rho[("C", "F")] = float(f_load)
    rho[("D", "F")] = float(f_load)
    return rho


def test_zero_staleness_gap_is_zero():
    result = measure_gap(
        LOAD_CFG_TRAIN,
        z_steps=0,
        drift_sigma=0.0,
        n_cases=40,
        seed=0,
        mc_samples=5,
    )

    assert result["gap"] == 0.0
    assert result["f_rate_fresh"] == result["f_rate_aware"]


def test_drift_forward_matches_route_env_trend_and_cap():
    rho_obs = _rho_snapshot(base=0.30, e_load=1.55, f_load=0.40)

    rho_true = drift_forward(
        rho_obs,
        z_steps=2,
        drift_sigma=0.0,
        rng=np.random.default_rng(0),
        offered_max=1.60,
        trend_per_step=0.10,
        trend_links=(("C", "E"), ("D", "E")),
    )

    assert rho_true[("C", "E")] == 1.60
    assert rho_true[("D", "E")] == 1.60
    assert rho_true[("C", "F")] == 0.40
    assert rho_true[("E", "F")] == 0.30


def test_aware_action_can_depart_from_fresh_under_known_trend():
    rho_obs = _rho_snapshot(base=0.30, e_load=0.90, f_load=0.30)

    assert fresh_action(rho_obs) == ACTION_VIA_E
    assert aware_action(
        rho_obs,
        z_steps=1,
        drift_sigma=0.0,
        rng=np.random.default_rng(0),
        offered_max=1.60,
        n_samples=500,
        trend_scale=0.15,
    ) == ACTION_DIRECT_F


def _run_as_script():
    tests = [
        test_zero_staleness_gap_is_zero,
        test_drift_forward_matches_route_env_trend_and_cap,
        test_aware_action_can_depart_from_fresh_under_known_trend,
    ]
    for test in tests:
        test()
        print("  PASS  %s" % test.__name__)
    print("\n%d/%d passed" % (len(tests), len(tests)))


if __name__ == "__main__":
    _run_as_script()

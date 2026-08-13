"""Golden tests for cert.tau_sweep -- Phase 22 Lesson 22.6."""

import json
import os

import numpy as np
import pytest

import cert.tau_sweep as TS


MAIN = "results/phase-22/tau_sweep_poisson_0.925.json"
pytestmark = pytest.mark.skipif(not os.path.exists(MAIN), reason="thieu tau_sweep result")


def _q(row, group):
    return row["qhat_margin"][str(group)]


@pytest.fixture(scope="module")
def res():
    with open(MAIN, encoding="utf-8") as f:
        return json.load(f)


def test_GT1_tau_grid_and_preregistered_bands_are_locked(res):
    assert tuple(res["tau_grid"]) == TS.TAU_GRID
    assert res["z_rep"] == [TS.Z0_REP, TS.Z3_REP]
    assert set(map(float, res["preregistered_ratio_bands"])) == set(TS.PREREG_RATIO_BANDS)


def test_GT2_block_length_tracks_tau():
    for tau in TS.TAU_GRID:
        assert TS.block_len_for_tau(tau) * TS.V3.DT == pytest.approx(5.0 * tau, rel=1e-9)
    with pytest.raises(ValueError):
        TS.block_len_for_tau(0.0)


def test_GT3_every_tau_has_enough_calibration_blocks(res):
    expected = {0.5: 1000, 1.0: 500, 2.0: 250, 2.87: 175, 5.0: 100}
    for row in res["rows"]:
        tau = row["tau"]
        assert row["block_s"] == pytest.approx(5.0 * tau)
        assert row["min_calib_blocks"] == expected[tau]
        assert row["min_calib_blocks"] >= TS.MIN_BLOCKS
        assert row["enough_blocks"]


def test_GT4_A_is_tau_independent(res):
    A = np.array([r["ar1_fit"]["A"] for r in res["rows"]])
    assert (A.max() - A.min()) / A.mean() < 0.02
    for r in res["rows"]:
        assert r["ar1_fit"]["A_spread_pct"] < 3.0, r["tau"]


def test_GT5_c_and_model_floor_are_tau_independent(res):
    c = np.array([r["ar1_fit"]["c"] for r in res["rows"]])
    em = np.array([r["ar1_fit"]["rms_e_model"] for r in res["rows"]])
    assert (c.max() - c.min()) / abs(c.mean()) < 0.02
    assert (em.max() - em.min()) / em.mean() < 0.02
    assert np.all(c < 1.0)


def test_GT6_ar1_model_fits_rms_total_within_two_percent(res):
    for r in res["rows"]:
        assert r["ar1_fit"]["max_rel_err_vs_measured"] < 0.02, r["tau"]


def test_GT7_ratio_is_a_hump_not_monotone(res):
    ratios = [r["ratio_measured"] for r in res["rows"]]
    assert not all(a <= b for a, b in zip(ratios, ratios[1:]))
    assert not all(a >= b for a, b in zip(ratios, ratios[1:]))
    peak = int(np.argmax(ratios))
    assert 0 < peak < len(ratios) - 1


def test_GT8_ratio_matches_the_preregistered_bands(res):
    bands = {0.5: (1.77, 2.16), 1.0: (1.87, 2.29), 2.0: (1.88, 2.30), 2.87: (1.86, 2.27), 5.0: (1.77, 2.17)}
    for r in res["rows"]:
        lo, hi = bands[r["tau"]]
        assert lo <= r["ratio_measured"] <= hi, (r["tau"], r["ratio_measured"])


def test_GT9_finite_theory_matches_measured_ratios(res):
    for r in res["rows"]:
        assert r["ratio_measured"] / r["ratio_pred_finite"] == pytest.approx(1.0, abs=0.03)
    one = next(r for r in res["rows"] if r["tau"] == pytest.approx(1.0))
    assert one["ratio_pred_saturated"] == pytest.approx(2.1614, abs=5e-4)


def test_GT10_saturated_bound_is_above_and_monotone(res):
    sat = [r["ratio_pred_saturated"] for r in res["rows"]]
    assert all(a < b for a, b in zip(sat, sat[1:]))
    for r in res["rows"]:
        assert r["ratio_pred_saturated"] > r["ratio_measured"], r["tau"]


def test_GT11_qhat_B0_decreases_as_tau_gets_slower(res):
    q0 = [_q(r, 0) for r in res["rows"]]
    assert all(a > b for a, b in zip(q0, q0[1:]))


def test_GT12_coverage_drift_is_the_finite_sample_level(res):
    from cert.conformal_v2 import conformal_level

    for r in res["rows"]:
        lvl = conformal_level(r["min_calib_blocks"], 0.10)
        cov = float(np.mean(list(r["coverage"].values())))
        assert lvl - 0.005 <= cov <= lvl + 0.020, (r["tau"], lvl, cov)


def test_GT13_tau1_reproduces_the_21R_anchor_numbers(res):
    one = next(r for r in res["rows"] if r["tau"] == pytest.approx(1.0))
    assert one["ratio_measured"] == pytest.approx(2.0990, abs=2e-3)
    assert _q(one, 0) == pytest.approx(11.5878, abs=2e-3)
    assert one["ar1_fit"]["rms_e_model"] == pytest.approx(2.140, abs=0.02)
    assert one["ar1_fit"]["A_over_em"] > 10.0
    assert res["gates"]["G22_10_preregistered_ratio_bands"]
    assert res["gates"]["G22_11_A_independent_of_tau"]

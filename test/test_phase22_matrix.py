"""Golden tests for cert.config_matrix -- Phase 22 Lesson 22.5."""

import os

import numpy as np
import pandas as pd
import pytest

import cert.config_matrix as CM
from cert.simultaneous_score import ALPHA


CALIB = "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.925.parquet"
pytestmark = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu calib_set_v3")


def _row(rows, kappa):
    return next(r for r in rows if r["kappa"] == pytest.approx(float(kappa)))


def _risk_at(rows, target):
    return CM.risk_at_acceptance(rows, target)


@pytest.fixture(scope="module")
def matrix():
    df = pd.read_parquet(CALIB)
    return df, CM.run_matrix(df)


def test_GM1_four_corners_two_axes():
    assert set(CM.CONFIGS) == {"C0", "C1", "C2", "C3"}
    assert CM.CONFIGS["C0"] == {"simultaneous": False, "post": "none", "label": "21R baseline"}
    assert CM.CONFIGS["C3"]["simultaneous"] and CM.CONFIGS["C3"]["post"] == "mondrian"
    assert sum(c["simultaneous"] for c in CM.CONFIGS.values()) == 2
    assert sum(c["post"] != "none" for c in CM.CONFIGS.values()) == 2


def test_GM2_kappa0_returns_the_anchor_for_all_four_configs(matrix):
    _df, res = matrix
    anchor = res["anchor_err_on_test"]
    assert anchor == pytest.approx(0.222399, abs=2e-3)
    for cfg in CM.CONFIGS:
        r = _row(res["configs"][cfg]["rows"], 0.0)
        assert r["acceptance"] == 1.0
        assert r["err_given_accept"] == pytest.approx(anchor, abs=1e-12)
        assert r["lose_any_given_accept"] == pytest.approx(anchor, abs=1e-12)


def test_GM3_C0_kappa1_reproduces_21R_operating_point(matrix):
    _df, res = matrix
    r = _row(res["configs"]["C0"]["rows"], 1.0)
    assert r["acceptance"] == pytest.approx(0.2835, abs=2e-3)
    assert r["err_given_accept"] == pytest.approx(0.0330, abs=2e-3)
    assert r["violation_given_accept"] == pytest.approx(0.1214, abs=2e-3)
    assert not r["pass_coverage"]


def test_GM4_curves_are_monotone_in_acceptance_and_risk(matrix):
    _df, res = matrix
    for cfg in CM.CONFIGS:
        mono = res["configs"][cfg]["monotone"]
        assert mono["acceptance_nonincreasing"], cfg
        assert mono["risk_nonincreasing"], cfg


def test_GM5_H22_7_passes_only_when_the_new_coverage_condition_is_met(matrix):
    _df, res = matrix
    assert not res["configs"]["C0"]["H22_7"]["pass"]
    assert res["configs"]["C0"]["H22_7_without_coverage"]["pass"]
    for cfg in ("C1", "C2", "C3"):
        assert res["configs"][cfg]["H22_7"]["pass"], cfg
    h = res["configs"]["C3"]["H22_7"]
    assert h["kappa"] == pytest.approx(0.5)
    assert h["acceptance"] == pytest.approx(0.4911, abs=2e-3)
    assert h["risk_ratio"] == pytest.approx(0.364, abs=0.01)


def test_GM6_C3_keeps_post_selection_coverage_on_the_useful_range(matrix):
    _df, res = matrix
    c3 = res["configs"]["C3"]["rows"]
    for kappa in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0):
        assert _row(c3, kappa)["pass_coverage"], kappa
    c2 = res["configs"]["C2"]["rows"]
    assert not _row(c2, 1.5)["pass_coverage"]
    assert not _row(c2, 2.0)["pass_coverage"]


def test_GM7_full_claim_headline_numbers(matrix):
    _df, res = matrix
    r = _row(res["configs"]["C3"]["rows"], 0.5)
    assert r["acceptance"] == pytest.approx(0.4911, abs=2e-3)
    assert r["err_given_accept"] == pytest.approx(0.0809, abs=2e-3)
    assert r["risk_ratio"] == pytest.approx(0.364, abs=0.01)
    assert r["violation_given_accept"] == pytest.approx(0.0794, abs=2e-3)
    assert r["pass_coverage"]


def test_GM8_the_frontier_is_unchanged_by_the_corrections(matrix):
    _df, res = matrix
    base = res["configs"]["C0"]["rows"]
    for cfg in ("C1", "C2", "C3"):
        rows = res["configs"][cfg]["rows"]
        for target in (0.70, 0.50, 0.30):
            r0, r1 = _risk_at(base, target), _risk_at(rows, target)
            assert abs(r1 / r0 - 1.0) < 0.08, (cfg, target, r0, r1)
    for cfg in ("C1", "C2", "C3"):
        assert abs(res["configs"][cfg]["aurc"] / res["configs"]["C0"]["aurc"] - 1.0) < 0.02


def test_GM9_fcr_is_the_only_variant_that_degrades_the_frontier(matrix):
    _df, res = matrix
    variants = res["C3_post_variants"]
    base = res["configs"]["C0"]["aurc"]
    assert variants["fcr"]["aurc"] / base > 1.10
    for pv in ("none", "mondrian", "selective"):
        assert variants[pv]["aurc"] / base < 1.02, pv
    fcr1 = _row(variants["fcr"]["rows"], 1.0)
    assert fcr1["acceptance"] == 0.0
    assert fcr1["degenerate"]


def test_GM10_simultaneous_correction_is_almost_a_kappa_reparameterization(matrix):
    _df, res = matrix
    c0_acc = np.interp(0.655, [0.5, 0.75], [
        _row(res["configs"]["C0"]["rows"], 0.5)["acceptance"],
        _row(res["configs"]["C0"]["rows"], 0.75)["acceptance"],
    ])
    c1_acc = _row(res["configs"]["C1"]["rows"], 0.5)["acceptance"]
    assert abs(c1_acc - c0_acc) / c0_acc < 0.03


def test_GM11_every_row_reports_both_violation_quantities(matrix):
    _df, res = matrix
    for cfg in res["configs"].values():
        for row in cfg["rows"]:
            assert {"violation_given_accept", "err_given_accept", "lose_any_given_accept"} <= set(row)
            assert {"scale", "level", "rowset"} <= set(row)


def test_GM12_gates_are_serialized_in_the_report(matrix):
    _df, res = matrix
    assert res["gates"]["G22_8_H22_7_C3_full_claim"]
    assert res["gates"]["G22_9_acceptance_and_risk_monotone"]
    assert res["gates"]["G22_13_two_violation_quantities_reported"]
    assert res["gates"]["frontier_unchanged_C3_vs_C0_within_8pct"]
    assert res["gates"]["frontier_not_degraded_C3_vs_C0_within_8pct"]
    assert res["gates"]["FCR_only_variant_degrades_frontier"]

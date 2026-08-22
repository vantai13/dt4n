"""Golden tests for cert.conformal_simultaneous -- Phase 22 Lesson 22.3."""

import os

import numpy as np
import pandas as pd
import pytest

import cert.conformal_simultaneous as CS
from cert.simultaneous_score import ALPHA


CALIB = "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.925.parquet"
pytestmark = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu artifact phase-22 v3")


@pytest.fixture(scope="module")
def data():
    df = pd.read_parquet(CALIB)
    return df, df["is_calib"].to_numpy(bool)


@pytest.fixture(scope="module")
def fits(data):
    df, ic = data
    return {p: CS.fit_eval_simultaneous(df, ic, p) for p in CS.PROCEDURES}


def test_GQ1_alpha_each_and_validation():
    assert CS.alpha_each("uncorrected", ALPHA, 3) == pytest.approx(ALPHA)
    assert CS.alpha_each("maxscore", ALPHA, 3) == pytest.approx(ALPHA)
    assert CS.alpha_each("bonferroni", ALPHA, 3) == pytest.approx(ALPHA / 3.0)
    assert CS.alpha_each("sidak", ALPHA, 3) > CS.alpha_each("bonferroni", ALPHA, 3)
    with pytest.raises(ValueError):
        CS.alpha_each("pooled", ALPHA, 3)


def test_GQ2_maxscore_broadcasts_one_qhat_per_bin(fits):
    for q in fits["maxscore"]["qhat"].values():
        assert len({round(x, 6) for x in q}) == 1


def test_GQ3_corrected_widens_vs_uncorrected_and_sidak_le_bonf(fits):
    for z in fits["uncorrected"]["qhat"]:
        unc = np.asarray(fits["uncorrected"]["qhat"][z])
        bonf = np.asarray(fits["bonferroni"]["qhat"][z])
        sidak = np.asarray(fits["sidak"]["qhat"][z])
        assert (bonf > unc).all()
        assert (sidak > unc).all()
        assert (sidak <= bonf + 1e-9).all()


def test_GQ4_corrected_simultaneous_coverage_gate(fits):
    for p in ("bonferroni", "sidak", "maxscore"):
        assert fits[p]["coverage_marginal"] >= 1.0 - ALPHA - CS.COV_TOL
        assert min(fits[p]["coverage_simultaneous"].values()) >= 1.0 - ALPHA - CS.COV_TOL


def test_GQ5_maxscore_is_least_conservative_corrected_procedure(fits):
    cov_max = fits["maxscore"]["coverage_marginal"]
    cov_sid = fits["sidak"]["coverage_marginal"]
    cov_bonf = fits["bonferroni"]["coverage_marginal"]
    assert abs(cov_max - (1.0 - ALPHA)) < 0.015
    assert cov_max < cov_sid < cov_bonf


def test_GQ6_negative_control_collapses_but_pointwise_is_21R_like(fits):
    u = fits["uncorrected"]["coverage_marginal"]
    assert 0.74 <= u <= 0.80
    assert u > 0.9 ** 3 - 0.02
    assert fits["bonferroni"]["coverage_marginal"] - u > 0.10
    pw = np.asarray(fits["uncorrected"]["coverage_pointwise_marginal"])
    assert np.abs(pw - 0.9).max() <= 0.02


def test_GQ7_slot1_reproduces_21R_exactly(data):
    df, ic = data
    out = CS.reproduce_21R(df, ic)
    assert out["max_abs_diff"] == 0.0
    assert out["pass_V22_6"]


def test_GQ8_uncorrected_slot1_qhat_matches_expected_21R_values(fits):
    expected = {0: 11.5878, 1: 15.6348, 2: 19.6461, 3: 24.3222}
    for z, q in expected.items():
        assert fits["uncorrected"]["qhat"][z][0] == pytest.approx(q, abs=1e-3)


def test_GQ9_halfnormal_bridge_is_stable_ratio_not_absolute_prediction(data, fits):
    df, _ic = data
    b = CS.bridge_to_rms(df, fits["maxscore"])
    ratios = [row["ratio"] for row in b["per_bin"]]
    assert all(0.88 <= r <= 0.94 for r in ratios)
    assert max(ratios) - min(ratios) < 0.01


def test_GQ10_seed_validation_holds_for_confirmatory_corrected_procedures(data):
    df, _ic = data
    for p in ("bonferroni", "maxscore"):
        out = CS.seed_validation(df, p)
        assert out["coverage_marginal"] >= 1.0 - ALPHA - CS.COV_TOL


def test_GQ11_variant_C_is_conservative_vs_B_for_maxscore(data, fits):
    df, ic = data
    c = CS.fit_eval_simultaneous(df, ic, "maxscore", variant="C")
    for z in fits["maxscore"]["qhat"]:
        assert c["qhat"][z][0] > fits["maxscore"]["qhat"][z][0]


@pytest.mark.slow
def test_GQ12_PC22_3_variance_positive_control_collapses(data):
    df, _ic = data
    out = CS.v3_variance_control(df, "maxscore", repeats=8)
    assert out["sd_ratio_row_over_block"] < CS.V3_SD_RATIO_MAX
    assert out["coverage_mean_diff_max"] < 0.01


def test_GQ13_slot1_is_operationally_binding(data, fits):
    df, ic = data
    for p in ("bonferroni", "maxscore"):
        out = CS.acceptance_diagnostics(df, ic, fits[p])
        assert out["slot1_decides_share"] > 0.999

"""Gates for Phase 23 Lesson 23.3 baselines."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import baselines as BL
from cert import fallback as FB
from cert import threshold_families as TF


ARTIFACT = "results/phase-22/calib_set_v3.parquet"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 baselines: %s" % ARTIFACT)
    raw = pd.read_parquet(ARTIFACT)
    return FB.sort_for_stateful(raw[~raw["is_calib"]])


def test_PC23_1_random_baseline_reproduces_anchor_on_accept_branch(df: pd.DataFrame) -> None:
    """B1 has no information, so err|accept should stay near the twin anchor."""
    anchor = float(FB.loss_of(df, df["a_twin"].to_numpy(np.int64), "err").mean())
    score = BL.score_B1_random(df)
    sweep = BL.sweep_ranking(df, score, [0.30, 0.50, 0.78], label="B1")
    for _, row in sweep.iterrows():
        assert abs(float(row["err_accept"]) - anchor) < 0.01, row.to_dict()


def test_G23_10b_B4_is_identical_to_B3(df: pd.DataFrame) -> None:
    """B4 variance proxy is a monotone reparameterization of B3 AoI."""
    s3 = BL.score_B3_aoi(df)
    s4 = BL.score_B4_variance_proxy(df)
    for coverage in (0.20, 0.50, 0.78, 0.95):
        a3 = BL._accept_at_coverage(s3, coverage)
        a4 = BL._accept_at_coverage(s4, coverage)
        assert np.array_equal(a3, a4), coverage


def test_G23_12c_B6sys_matches_closed_form(df: pd.DataFrame) -> None:
    """Measured B6-sys curve must match the three-segment closed form."""
    n = len(df)
    a_twin = df["a_twin"].to_numpy(np.int64)
    a_p1 = np.full(n, FB.path_static_shortest(), dtype=np.int64)
    loss_twin = FB.loss_of(df, a_twin, "err")
    loss_p1 = FB.loss_of(df, a_p1, "err")

    anchor = float(loss_twin.mean())
    p1_wrong = float(loss_p1.mean())
    both_wrong = float(np.minimum(loss_twin, loss_p1).mean())
    closed = BL.b6sys_closed_form(anchor, p1_wrong, both_wrong)

    score = BL.score_B6sys_system_oracle(df, "static", "err")
    sweep = BL.sweep_ranking(df, score, [c for c, _err in closed["knees"]], label="B6-sys")
    for (coverage_expected, err_expected), (_, row) in zip(closed["knees"], sweep.iterrows()):
        assert float(row["coverage"]) == pytest.approx(coverage_expected, abs=1e-6)
        assert float(row["err_system"]) == pytest.approx(err_expected, abs=1e-9)


def test_paired_ranking_delta_reports_block_ci(df: pd.DataFrame) -> None:
    """Generic paired ranking CI returns the fields used by the C3-vs-B2 audit."""
    out = BL.paired_ranking_delta_at_coverage(
        df,
        BL.score_B2_constant_gap(df),
        BL.score_B3_aoi(df),
        0.50,
        "B2",
        "B3",
        scale="err",
        n_boot=5,
    )
    assert out["coverage_a"] == pytest.approx(0.50, abs=1e-5)
    assert out["coverage_b"] == pytest.approx(0.50, abs=1e-5)
    assert len(out["delta_ci95"]) == 2
    assert out["n_boot"] == 5
    assert out["n_blocks"] == df["block_id"].nunique()


def test_L20_intervention_rate_check_reports_actionable_gap(df: pd.DataFrame) -> None:
    """Matched coverage audit must expose true intervention-rate comparability."""
    accept_a = BL._accept_at_coverage(BL.score_B2_constant_gap(df), 0.78)
    accept_b = BL._accept_at_coverage(BL.score_B3_aoi(df), 0.78)
    out = BL._intervention_rate_check(df, accept_a, accept_b)
    assert out["intervention_rate_a"] >= 0.0
    assert out["intervention_rate_b"] >= 0.0
    assert out["abs_gap"] == pytest.approx(abs(out["gap_a_minus_b"]))
    assert out["tolerance"] == pytest.approx(0.01)
    assert isinstance(out["comparable_at_matched_coverage"], bool)


def test_argmin_information_report_uses_chance_agreement(df: pd.DataFrame) -> None:
    """Argmin mechanism audit must use subset marginals, not a fixed 0.5 baseline."""
    out = BL.argmin_information_report(
        df,
        {
            "B1": BL.score_B1_random(df),
            "B2": BL.score_B2_constant_gap(df),
        },
        coverage=0.78,
    )
    assert out["star_col"] == "a_star"
    assert out["n_actions"] == FB.K_ACTIONS
    assert len(out["rows"]) == 2
    for row in out["rows"]:
        for branch in ("accept", "reject"):
            stats = row[branch]
            assert 0.0 <= stats["agreement_independent"] <= 1.0
            assert stats["excess_agreement"] == pytest.approx(
                stats["agreement"] - stats["agreement_independent"]
            )
            assert 0.0 <= stats["p_a_star_eq_p1"] <= 1.0
            assert len(stats["a_twin_distribution"]) == FB.K_ACTIONS
            assert len(stats["a_star_distribution"]) == FB.K_ACTIONS


def test_G23_21_break_even_identity_reconstructs_delta(df: pd.DataFrame) -> None:
    """Static-fallback err delta must be reconstructed from reject argmin rates."""
    raw = pd.read_parquet(ARTIFACT)
    _calib, test, qhat_rows, _fit, _q_by_age, _qbar = TF.fit_c3_inputs(raw, config="C3")
    out = BL.break_even_identity_report(
        test,
        {
            "B1_random": BL.score_B1_random(test),
            "B3_aoi": BL.score_B3_aoi(test),
            "B2_constant_gap": BL.score_B2_constant_gap(test),
            "C3_conformal": BL.score_C3(test, qhat_rows),
        },
        coverage=0.78,
        policy="static",
    )
    assert out["gate"] == "G23-21"
    assert out["pass"] is True
    for row in out["rows"]:
        assert row["abs_identity_error"] <= 1e-9
        assert row["delta_vs_anchor"] == pytest.approx(row["delta_reconstructed"], abs=1e-9)


def test_G23_21b_gamma_closure_adjudicates_b2_b3_claim(df: pd.DataFrame) -> None:
    """C3(gamma) is not a pure B2-to-B3 interpolation under C3 Mondrian keys."""
    raw = pd.read_parquet(ARTIFACT)
    _calib, test, qhat_rows, fit, _q_by_age, _qbar = TF.fit_c3_inputs(raw, config="C3")
    out = BL.gamma_closure_report(
        test,
        qhat_rows,
        fit,
        gammas=(0.0, 0.5, 1.0, 2.0, 3.0, 20.0, 100.0),
        coverage=0.78,
        policy="static",
        n_boot=3,
    )
    assert out["gate"] == "G23-21b"
    assert out["qhat_monotonicity"]["n_score_slots"] == len(TF.MHAT_COLS)
    assert out["qhat_monotonicity"]["all_cell_level_monotone_by_z_bin"] is True
    assert out["qhat_monotonicity"]["all_row_level_monotone_by_z_s"] is False
    assert out["checks"]["b2_to_b3_interpolation_supported"] is False
    assert out["checks"]["no_gamma_gt2_beats_gamma1"] is True
    assert len(out["paired_gamma0p5_minus_gamma1"]["delta_ci95"]) == 2


def test_tie_break_sensitivity_is_small_for_baseline_conclusions(df: pd.DataFrame) -> None:
    """Stable top-k tie handling must not drive the C3-vs-B3 conclusion."""
    raw = pd.read_parquet(ARTIFACT)
    _calib, test, qhat_rows, _fit, _q_by_age, _qbar = TF.fit_c3_inputs(raw, config="C3")
    out = BL.tie_break_sensitivity_report(
        test,
        {
            "B3_aoi": BL.score_B3_aoi(test),
            "B2_constant_gap": BL.score_B2_constant_gap(test),
            "C3_conformal": BL.score_C3(test, qhat_rows),
        },
        coverage=0.78,
        policy="static",
    )
    spreads = {row["selector"]: row["spread"] for row in out["rows"]}
    assert spreads["B3_aoi"] < 0.001
    assert spreads["B2_constant_gap"] < 0.001
    assert spreads["C3_conformal"] < 0.001


def test_c3_b2_audit_includes_overlap_and_argmin_info(df: pd.DataFrame) -> None:
    """The C3-vs-B2 audit records the mechanism checks needed to close 23.3."""
    raw = pd.read_parquet(ARTIFACT)
    out = BL.run_c3_b2_audit(raw, coverages=[0.78], scales=["err"], n_boot=3)
    assert "argmin_information_at_078" in out
    assert "break_even_identity_at_078" in out
    assert out["break_even_identity_at_078"]["pass"] is True
    assert "gamma_sweep_at_078" in out
    assert out["gamma_sweep_at_078"]["gamma0_matches_B2"]["accept_bitwise_identical"] is True
    assert "gamma_closure_G23_21b_at_078" in out
    assert out["gamma_closure_G23_21b_at_078"]["checks"]["b2_to_b3_interpolation_supported"] is False
    assert "tie_break_sensitivity_at_078" in out
    assert "accept_overlap_at_078" in out
    assert out["accept_overlap_at_078"]["C3_B2"]["coverage_target"] == pytest.approx(0.78)
    assert out["accept_overlap_at_078"]["C3_B3"]["coverage_target"] == pytest.approx(0.78)

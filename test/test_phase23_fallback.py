"""Gates for Phase 23 Lesson 23.1 fallback semantics."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import fallback as FB


ARTIFACT = "results/SUPERSEDED/phase-22/calib_set_v3.parquet"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 fallback: %s" % ARTIFACT)
    return FB.sort_for_stateful(pd.read_parquet(ARTIFACT))


@pytest.fixture(scope="module")
def accept(df: pd.DataFrame) -> np.ndarray:
    rng = np.random.default_rng(23100)
    return rng.random(len(df)) < 0.4911


def test_NC23_5_fallback_equals_twin_reproduces_anchor(df: pd.DataFrame) -> None:
    """If chosen actions equal twin actions, measured system risk is the anchor."""
    acc = np.zeros(len(df), bool)
    res = {"a_chosen": df["a_twin"].to_numpy(np.int64)}
    out = FB.risk_decomposition(df, acc, res)
    assert abs(out["err_system"] - 0.2208351459330263) < 1e-9
    assert abs(out["sla_system"] - df["viol_twin"].mean()) < 1e-12


def test_NC23_1_accept_all_uses_no_fallback(df: pd.DataFrame) -> None:
    acc = np.ones(len(df), bool)
    for policy in FB.POLICIES:
        out = FB.risk_decomposition(df, acc, FB.apply_fallback(df, acc, policy))
        assert abs(out["err_system"] - 0.2208351459330263) < 1e-9, policy


def test_regret_reconstruction_matches_stored_column(df: pd.DataFrame) -> None:
    got = FB.loss_of(df, df["a_twin"].to_numpy(), "regret")
    assert np.abs(got - df["regret"].to_numpy(np.float64)).max() < 1e-4


def test_G23_1_every_row_has_exactly_one_action(df: pd.DataFrame, accept: np.ndarray) -> None:
    for policy in FB.POLICIES:
        a = FB.apply_fallback(df, accept, policy)["a_chosen"]
        assert a.shape == (len(df),)
        assert np.isfinite(a).all()
        assert a.min() >= 0 and a.max() < FB.K_ACTIONS


def test_G23_2_static_is_a_pure_function(df: pd.DataFrame, accept: np.ndarray) -> None:
    perm = np.random.default_rng(1).permutation(len(df))
    a1 = FB.fallback_static(df, accept)
    a2 = FB.fallback_static(df.iloc[perm].reset_index(drop=True), accept[perm])
    assert np.array_equal(a1[perm], a2)


def test_G23_3_sticky_resets_at_block_start_and_is_deterministic(
    df: pd.DataFrame,
    accept: np.ndarray,
) -> None:
    a1 = FB.fallback_sticky(df, accept)
    a2 = FB.fallback_sticky(df, accept)
    assert np.array_equal(a1, a2)

    p = FB.path_static_shortest()
    first = df.groupby("block_id", sort=False).head(1).index.to_numpy()
    rej_first = first[~accept[first]]
    assert np.all(a1[rej_first] == p)


def test_G23_3b_sticky_rejects_unsorted_input(df: pd.DataFrame, accept: np.ndarray) -> None:
    perm = np.random.default_rng(2).permutation(len(df))
    with pytest.raises(ValueError):
        FB.fallback_sticky(df.iloc[perm].reset_index(drop=True), accept[perm])


def test_G23_4_total_probability_identity(df: pd.DataFrame, accept: np.ndarray) -> None:
    for policy in FB.POLICIES:
        out = FB.risk_decomposition(df, accept, FB.apply_fallback(df, accept, policy))
        for scale in FB.SCALES:
            assert out["%s_identity_residual" % scale] < 1e-9, (policy, scale)


def test_G23_4b_break_even_is_twin_risk_given_reject(
    df: pd.DataFrame,
    accept: np.ndarray,
) -> None:
    """Break-even fallback loss equals twin loss on the same reject rows."""
    twin = FB.loss_of(df, df["a_twin"].to_numpy(np.int64), "err")
    acc = np.asarray(accept, bool)
    p_acc = float(acc.mean())
    p_rej = 1.0 - p_acc

    break_even = (float(twin.mean()) - p_acc * float(twin[acc].mean())) / p_rej
    assert abs(break_even - float(twin[~acc].mean())) < 1e-12


def test_G23_5_decision_delay_profile(df: pd.DataFrame, accept: np.ndarray) -> None:
    res = FB.apply_fallback(df, accept, "wait")
    out = FB.risk_decomposition(df, accept, res)

    z = df["z_s"].to_numpy(np.float64)
    expect = (FB.Z_MAX - z) + FB.DT
    rej = ~accept
    got = res["wait_s"]
    mask = rej & (got > 0)
    assert np.abs(got[mask] - expect[mask]).max() < 1e-9

    assert 0.0 < out["decision_delay_ms_mean_given_reject"] < 252.5
    assert out["decision_delay_ms_max"] <= (FB.T_SYNC + FB.DT) * 1e3 + 1e-9


def test_G23_5d_wait_availability_reported(df: pd.DataFrame, accept: np.ndarray) -> None:
    res = FB.apply_fallback(df, accept, "wait")
    share = res["n_no_refresh_in_block"] / max(res["n_reject"], 1)
    assert 0.0 <= share < 0.20


def test_G23_14b_paired_delta_zeroes_accept_branch() -> None:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 fallback: %s" % ARTIFACT)
    raw = pd.read_parquet(ARTIFACT)
    test, acc, _fit = FB.fit_accept_mask(raw, config="C3", kappa=0.25)

    out = FB.paired_block_bootstrap_delta(test, acc, "static", "err", n_boot=20, seed=7)
    dec = FB.risk_decomposition(test, acc, FB.apply_fallback(test, acc, "static"))
    assert out["nonzero_diff_on_accept"] == 0
    assert out["delta_point"] == pytest.approx(dec["err_system"] - out["risk_anchor"])
    assert out["n_blocks"] == test["block_id"].nunique()


def test_G23_14c_matched_random_control_reports_value_of_information() -> None:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 fallback: %s" % ARTIFACT)
    raw = pd.read_parquet(ARTIFACT)
    test, acc, _fit = FB.fit_accept_mask(raw, config="C3", kappa=0.25)

    out = FB.matched_coverage_control(test, acc, "static", "err", n_rep=20, seed=8)
    assert out["coverage"] == pytest.approx(float(acc.mean()))
    assert out["risk_random_mean"] > out["risk_anchor"]
    assert out["value_of_information"] > 0.0


def test_oracle_switch_bound_is_below_twin_and_static(df: pd.DataFrame) -> None:
    for scale in FB.SCALES:
        out = FB.oracle_switch_bound(df, scale)
        assert out["oracle_switch"] <= out["anchor_twin"] + 1e-12
        assert out["oracle_switch"] <= out["always_p1"] + 1e-12
        total = out["share_switch_to_p1"] + out["share_twin_better"] + out["share_tie"]
        assert total == pytest.approx(1.0)


def test_truth_persistence_reports_lagged_agreement(df: pd.DataFrame) -> None:
    out = FB.truth_persistence_at_lag(df, lags_ms=(50, 300, 500))
    probs = df["a_star"].value_counts(normalize=True)
    assert 0.0 < out["p_infinity"] < 1.0
    assert out["p_infinity"] == pytest.approx(float((probs**2).sum()))
    assert len(out["points"]) == 3
    assert out["agree_50ms"] >= out["agree_500ms"]
    assert out["tau_a_s_exp_fit"] > 0.0
    assert out["exp_fit_intercept"] == 0.0
    assert out["tau_a_s_free_intercept_fit"] > out["tau_a_s_exp_fit"]

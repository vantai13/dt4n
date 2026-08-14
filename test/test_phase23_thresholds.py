"""Gates for Phase 23 Lesson 23.2 threshold families."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import fallback as FB
from cert import threshold_families as TF


ARTIFACT = "results/phase-22/calib_set_v3.parquet"


@pytest.fixture(scope="module")
def raw() -> pd.DataFrame:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 thresholds: %s" % ARTIFACT)
    return pd.read_parquet(ARTIFACT)


@pytest.fixture(scope="module")
def inputs(raw: pd.DataFrame):
    return TF.fit_c3_inputs(raw)


@pytest.fixture(scope="module")
def test_df(inputs) -> pd.DataFrame:
    return inputs[1]


@pytest.fixture(scope="module")
def qrows(inputs) -> np.ndarray:
    return inputs[2]


@pytest.fixture(scope="module")
def qhat_by_bin(inputs) -> dict[int, float]:
    return inputs[4]


def test_V23_4_additive_at_delta0_equals_multiplicative_at_kappa1(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
) -> None:
    """eps = 0 gives m >= q, identical to multiplicative kappa = 1."""
    m = test_df[list(TF.MHAT_COLS)].to_numpy(np.float64)
    assert np.array_equal(
        TF.accept_additive(m, qrows, 0.0),
        TF.accept_multiplicative(m, qrows, 1.0),
    )


def test_G23_6b_regret_family_is_algebraically_additive(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
    qhat_by_bin: dict[int, float],
) -> None:
    """REGRET is an interpretation of additive, not a third family."""
    m = test_df[list(TF.MHAT_COLS)].to_numpy(np.float64)
    qbar = TF.qbar_from_age_bins(qhat_by_bin)
    for delta in TF.DELTA_GRID:
        eps = float(delta) * qbar
        assert np.array_equal(
            TF.accept_additive(m, qrows, eps),
            TF.accept_regret(m, qrows, eps),
        ), delta


def test_accept_sets_are_nested_within_each_family(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
    qhat_by_bin: dict[int, float],
) -> None:
    """Nested accept sets are structural assertions for both families."""
    m = test_df[list(TF.MHAT_COLS)].to_numpy(np.float64)

    prev = None
    for kappa in sorted(TF.KAPPA_GRID):
        acc = TF.accept_multiplicative(m, qrows, kappa)
        if prev is not None:
            assert np.all(acc <= prev), kappa
        prev = acc

    prev = None
    qbar = TF.qbar_from_age_bins(qhat_by_bin)
    for eps in sorted(TF.eps_grid_from_delta(qbar)):
        acc = TF.accept_additive(m, qrows, eps)
        if prev is not None:
            assert np.all(prev <= acc), eps
        prev = acc


def test_G23_7_additive_degenerates_on_an_interval(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
    qhat_by_bin: dict[int, float],
) -> None:
    """Additive reaches full coverage for every eps beyond the sufficient bound."""
    m = test_df[list(TF.MHAT_COLS)].to_numpy(np.float64)
    q_max = float(max(qhat_by_bin.values()))
    for eps in (q_max, q_max * 1.5, q_max * 3.0):
        assert TF.accept_additive(m, qrows, eps).all(), eps


def test_G23_8_all_families_reduce_to_anchor_at_full_coverage(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
) -> None:
    """At full coverage, no fallback is used and system risk is the twin anchor."""
    m = test_df[list(TF.MHAT_COLS)].to_numpy(np.float64)
    anchor = float(FB.loss_of(test_df, test_df["a_twin"].to_numpy(np.int64), "err").mean())
    for acc in (
        TF.accept_multiplicative(m, qrows, 0.0),
        TF.accept_additive(m, qrows, 1e9),
    ):
        assert acc.all()
        out = FB.risk_decomposition(test_df, acc, FB.apply_fallback(test_df, acc, "static"))
        assert out["err_system"] == pytest.approx(anchor)


def test_T5_T6_age_conditioning_ratio_moves_as_predicted(qhat_by_bin: dict[int, float]) -> None:
    """Multiplicative keeps shape fixed; additive moves from flat to steep."""
    r_mul = TF.age_conditioning_ratio(qhat_by_bin, "multiplicative", 1.0)
    for kappa in (0.2, 0.5, 1.0, 4.0):
        assert TF.age_conditioning_ratio(qhat_by_bin, "multiplicative", kappa) == pytest.approx(r_mul)

    q0 = qhat_by_bin[min(qhat_by_bin)]
    r_lo = TF.age_conditioning_ratio(qhat_by_bin, "additive", -3.0 * q0)
    r_hi = TF.age_conditioning_ratio(qhat_by_bin, "additive", 0.5 * q0)
    assert r_lo < r_mul < r_hi
    assert 1.2 <= r_lo <= 1.8
    assert r_hi > 2.5

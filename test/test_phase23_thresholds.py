"""Gates for Phase 23 Lesson 23.2 threshold families."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import fallback as FB
from cert import threshold_families as TF


ARTIFACT = "results/SUPERSEDED/phase-22/calib_set_v3.parquet"


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


def test_G23_7b_additive_local_degeneracy_cascade_is_reported(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
    qhat_by_bin: dict[int, float],
) -> None:
    """The shift family starts degenerating before the full-coverage interval."""
    m = test_df[list(TF.MHAT_COLS)].to_numpy(np.float64)
    eps_operating = 21.14238882667379
    out = TF.additive_local_degeneracy_report(m, qrows, qhat_by_bin, eps_operating)

    assert out["first_local_degeneracy_epsilon"] == pytest.approx(min(qhat_by_bin.values()))
    assert out["first_local_degeneracy_coverage"] < out["operating_coverage"] < 1.0
    assert out["operating_degenerate_age_bins"] == 2
    assert out["degenerate_bin_count_monotone"] is True


def test_G23_9_scale_agreement_self_check_passes(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
    qhat_by_bin: dict[int, float],
) -> None:
    """G23-9 Spearman values must pass an independent rank recomputation."""
    qbar = TF.qbar_from_age_bins(qhat_by_bin)
    sweeps = [
        TF.sweep_family(test_df, qrows, "multiplicative", TF.KAPPA_GRID),
        TF.sweep_family(test_df, qrows, "additive", TF.eps_grid_from_delta(qbar)),
    ]
    for sweep in sweeps:
        out = TF.scale_agreement_self_check(sweep)
        assert out["pass"] is True
        assert out["max_abs_diff_vs_pandas_rank_check"] < 1e-12


def test_G23_9b_pareto_front_considers_combined_sweeps(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
    qhat_by_bin: dict[int, float],
) -> None:
    """A one-family Pareto front is a result only after both families are considered."""
    qbar = TF.qbar_from_age_bins(qhat_by_bin)
    mul = TF.sweep_family(test_df, qrows, "multiplicative", TF.KAPPA_GRID)
    add = TF.sweep_family(test_df, qrows, "additive", TF.eps_grid_from_delta(qbar))
    combined = pd.concat([mul, add], ignore_index=True, sort=False)
    front = TF.pareto_front(combined)
    audit = TF.pareto_audit(combined, front)

    assert audit["n_candidates_considered"] == len(TF.KAPPA_GRID) + len(TF.DELTA_GRID)
    assert audit["candidate_family_counts"] == {
        "additive": len(TF.DELTA_GRID),
        "multiplicative": len(TF.KAPPA_GRID),
    }
    assert audit["survivor_family_counts"] == {"multiplicative": 2}
    assert audit["single_family_complete_dominance_on_grid"] is True


def test_aurc_system_and_reject_risk_summaries_are_reported(
    test_df: pd.DataFrame,
    qrows: np.ndarray,
) -> None:
    """AURC summarizes the ranking, while reject risk is a branch diagnostic."""
    sweep = TF.sweep_family(test_df, qrows, "multiplicative", TF.KAPPA_GRID)
    aurc = TF.aurc_system_by_scale(sweep)
    reject = TF.reject_risk_summary(sweep, "err")

    assert set(aurc) == set(FB.SCALES)
    assert all(np.isfinite(v) and v > 0.0 for v in aurc.values())
    assert reject["global_min"]["param"] in (6.0, 8.0)
    assert reject["operational_range_min"]["param"] == 0.5


def test_run_report_preserves_cell_label_and_input_provenance(raw: pd.DataFrame) -> None:
    """Cross-cell sweeps must not silently stamp every artifact as the main cell."""
    out = TF.run_report(
        raw,
        cell_label="unit@test",
        input_path="results/SUPERSEDED/phase-22/unit.parquet",
        n_boot=3,
    )
    assert out["cell"] == "unit@test"
    assert out["provenance"]["input"] == "results/SUPERSEDED/phase-22/unit.parquet"

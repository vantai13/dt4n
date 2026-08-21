"""Golden and leakage controls for Lesson 23.14."""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest

from cert import fallback_sweep as F


def _toy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "seed": [101, 101, 102, 102, 103, 103],
            "a_star": [0, 0, 1, 1, 2, 3],
            "a_twin": [1, 1, 0, 0, 2, 2],
            "a_rank_1": [0, 0, 1, 1, 3, 3],
            "z_bin": [0, 0, 1, 1, 1, 1],
            "m_hat_bin": [0, 0, 0, 0, 1, 1],
        }
    )


def test_NC_A_fallback_fit_chi_nhin_allowed_indices():
    df = _toy_df()
    allowed = np.asarray([0, 1, 2, 3])
    fit = F.fit_policy("F6", df, allowed)
    scoring = {4, 5}
    assert fit.indices_seen.issubset(set(allowed))
    assert fit.indices_seen.isdisjoint(scoring)
    assert fit.seeds_seen == frozenset({101, 102})
    assert 103 not in fit.seeds_seen


def test_NC_B_F6_scoring_chi_can_hai_bin():
    fit = F.fit_policy("F6", _toy_df(), np.asarray([0, 1, 2, 3]))
    actions = F.score_f6(np.asarray([0, 1]), np.asarray([0, 0]), fit)
    assert actions.tolist() == [0, 1]


def test_F5_la_expected_mixture_khong_co_MC_noise():
    df = _toy_df()
    fit = F.fit_policy("F5", df, np.asarray([], dtype=np.int64))
    probs = F.policy_probabilities(fit, df, np.arange(len(df)))
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert np.all((probs == 0.0) | (probs == 0.5))
    assert np.array_equal(probs, F.policy_probabilities(fit, df, np.arange(len(df))))


def test_tie_break_constant_chon_path_nho_nhat():
    assert F._best_constant(np.asarray([2, 2, 1, 1])) == 1


@pytest.mark.skipif(not os.path.exists(F.OUTPUT), reason="chua chay fallback sweep")
def test_NC_C_F2_tai_lap_ba_delta_legacy():
    with open(F.OUTPUT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    for cell, expected in F.LEGACY_DELTA.items():
        row = report["cells"][cell]
        assert row["families"]["F2"]["delta_system_vs_neo"] == pytest.approx(
            expected, abs=1e-12
        )
        assert row["controls"]["NC_C_F2_reproduced_at_1e_12"] is True


@pytest.mark.skipif(not os.path.exists(F.OUTPUT), reason="chua chay fallback sweep")
def test_all_crossfit_folds_are_row_and_seed_disjoint():
    with open(F.OUTPUT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    for cell in F.CELL_SPECS:
        for fold in report["cells"][cell]["folds"]:
            assert fold["row_disjoint"] is True
            assert fold["seed_disjoint"] is True
            assert fold["scoring_seed"] not in fold["selection_seeds"]

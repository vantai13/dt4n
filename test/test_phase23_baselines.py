"""Gates for Phase 23 Lesson 23.3 baselines."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import baselines as BL
from cert import fallback as FB


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

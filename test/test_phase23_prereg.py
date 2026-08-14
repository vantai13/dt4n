"""Phase 23 preregistration controls.

These tests do not run a Phase 23 experiment.  They check the measurement
device needed before fallback policies can be trusted.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from twin import topology_v7 as T7


ARTIFACT = "results/phase-22/calib_set_v3.parquet"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 prereg: %s" % ARTIFACT)
    return pd.read_parquet(ARTIFACT)


def relcost_matrix(frame: pd.DataFrame, k: int = 4) -> np.ndarray:
    """True cost relative to a1 for every path, shape (n, k)."""
    n = len(frame)
    out = np.full((n, k), np.nan, dtype=np.float64)
    rows = np.arange(n)

    out[rows, frame["a1"].to_numpy(np.int64)] = 0.0
    for slot in range(1, k):
        act = frame["a_rank_%d" % slot].to_numpy(np.int64)
        out[rows, act] = frame["m_true_%d" % slot].to_numpy(np.float64)

    assert not np.isnan(out).any(), "a1/a_rank_* khong phu het K action"
    return out


def regret_of(frame: pd.DataFrame, a_chosen: np.ndarray, k: int = 4) -> np.ndarray:
    rel = relcost_matrix(frame, k)
    rows = np.arange(len(frame))
    return rel[rows, np.asarray(a_chosen, dtype=np.int64)] - rel.min(axis=1)


def test_per_path_sla_columns_exist(df: pd.DataFrame) -> None:
    """Phase 23 cannot compute fallback sla_rate without these columns."""
    for j in range(len(T7.PATH_NAMES)):
        assert "sla_viol_p%d" % j in df.columns, "thieu sla_viol_p%d" % j


def test_per_path_sla_agrees_with_twin_and_star(df: pd.DataFrame) -> None:
    """Positive control: new columns must reproduce twin/star SLA flags."""
    k = len(T7.PATH_NAMES)
    mat = np.column_stack([df["sla_viol_p%d" % j].to_numpy(bool) for j in range(k)])
    rows = np.arange(len(df))

    got_twin = mat[rows, df["a_twin"].to_numpy(np.int64)]
    got_star = mat[rows, df["a_star"].to_numpy(np.int64)]

    assert np.array_equal(got_twin, df["viol_twin"].to_numpy(bool))
    assert np.array_equal(got_star, df["viol_star"].to_numpy(bool))


def test_d_sla_anchor_reproduced(df: pd.DataFrame) -> None:
    """Reproduce the inherited 21R d_sla anchor."""
    d_sla = float(df["viol_twin"].mean() - df["viol_star"].mean())
    assert abs(d_sla - 0.060125306891879) < 1e-6, d_sla


def test_regret_reconstruction_matches_stored_column(df: pd.DataFrame) -> None:
    """Positive control for arbitrary-action regret reconstruction."""
    got = regret_of(df, df["a_twin"].to_numpy())
    want = df["regret"].to_numpy(np.float64)
    assert np.abs(got - want).max() < 1e-4, np.abs(got - want).max()

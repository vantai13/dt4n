"""Audit F3-a: distinct policy or F1 plus look-ahead leakage?"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import fallback as FB


ARTIFACT = "results/SUPERSEDED/phase-22/calib_set_v3.parquet"


@pytest.fixture(scope="module")
def fitted() -> tuple[pd.DataFrame, np.ndarray]:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 fallback: %s" % ARTIFACT)
    df = pd.read_parquet(ARTIFACT)
    test, accept, _fit = FB.fit_accept_mask(df, config="C3", kappa=0.5)
    return test, accept


@pytest.fixture(scope="module")
def df(fitted: tuple[pd.DataFrame, np.ndarray]) -> pd.DataFrame:
    return fitted[0]


@pytest.fixture(scope="module")
def accept(fitted: tuple[pd.DataFrame, np.ndarray]) -> np.ndarray:
    return fitted[1]


def installed_path_rowlevel(df: pd.DataFrame, accept: np.ndarray, policy: str) -> np.ndarray:
    """Installed path at every row, the physically accountable action."""
    if policy == "static":
        return FB.fallback_static(df, accept)
    if policy in ("sticky", "wait_a"):
        # F3-a: while waiting, the installed route is unchanged; at refresh,
        # the same policy is applied again, so the row-level path is F1.
        return FB.fallback_sticky(df, accept)
    raise ValueError(policy)


def test_F3a_is_structurally_identical_to_F1(
    df: pd.DataFrame,
    accept: np.ndarray,
) -> None:
    a_wait = FB.apply_fallback(df, accept, "wait")["a_chosen"]
    a_stky = installed_path_rowlevel(df, accept, "wait_a")
    assert np.array_equal(a_wait, a_stky)


def test_measure_lookahead_horizon(df: pd.DataFrame, accept: np.ndarray) -> None:
    z = df["z_s"].to_numpy(np.float64)
    nxt = FB._next_refresh_index(df)
    rej = ~np.asarray(accept, bool)
    can_wait = rej & (nxt >= 0)
    horizon = 0.500 - z[can_wait]
    assert horizon.size > 0

    share_future = float((horizon > 0).mean())
    print("\nti le hang reject co the dung thong tin TUONG LAI: %.4f" % share_future)
    print("horizon trung binh: %+.1f ms" % (horizon.mean() * 1e3))
    print("horizon lon nhat  : %+.1f ms" % (horizon.max() * 1e3))


def test_ground_truth_drift_over_wait(df: pd.DataFrame, accept: np.ndarray) -> None:
    nxt = FB._next_refresh_index(df)
    rej = ~np.asarray(accept, bool)
    ok = rej & (nxt >= 0)
    assert ok.any()

    a_star = df["a_star"].to_numpy(np.int64)
    agree = float((a_star[ok] == a_star[nxt[ok]]).mean())
    print("\nP(a*(t) == a*(t')) tren hang reject co the cho: %.4f" % agree)

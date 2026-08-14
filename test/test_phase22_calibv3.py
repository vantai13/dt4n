"""Golden tests for cert.build_calib_set_v3 -- Phase 22 Lesson 22.2."""

import os

import numpy as np
import pandas as pd
import pytest

import cert.build_calib_set_v3 as V3
from measurements.decision_error_v2 import (
    DT,
    TAU,
    TRUTH_TABLE,
    TruthTable,
    _cell_arrays,
    rho_matrix_from_cell,
)
from twin import cost_v2 as C
from twin import topology_v7 as T7


CELL_MODE, CELL_RHO = "poisson", 0.925
V2_PARQUET = V3.V2_TEMPLATE % (CELL_MODE, CELL_RHO)
N_SMALL = 20_000


@pytest.fixture(scope="module")
def small():
    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = V3._load_cell(CELL_MODE, CELL_RHO)
    arr = _cell_arrays(tt, cv, cell, seed=101, n=N_SMALL, sigma_override=V3.SIGMA)
    cur, old, _ = V3._valid_rows(N_SMALL, DT)
    keep = old >= 200
    rho = rho_matrix_from_cell(CELL_MODE, CELL_RHO, V3.SIGMA, 101, tau=TAU, n=N_SMALL, dt=DT)
    return {
        "cv": cv,
        "arr": arr,
        "cur": cur[keep],
        "old": old[keep],
        "rho": rho,
        "w_loss": float(arr["w_loss"]),
    }


def test_GC1_profiles_locked():
    assert sorted(V3.AOI_PROFILES) == ["PC4", "U0", "U1", "U2"]
    for name, ms in V3.AOI_PROFILES.items():
        assert len(ms) == len(T7.LINK_NAMES), name
        assert min(ms) == 0.0, name
    assert V3.AOI_PROFILES["U0"] == (0.0,) * 8
    with pytest.raises(ValueError):
        V3.offset_steps("U9")


def test_GC1b_cell_cli_alias_is_parseable():
    assert V3.parse_cell_arg("poisson_0.925") == ("poisson", 0.925)
    assert V3.parse_cell_arg("h2_0.700") == ("h2", 0.700)
    with pytest.raises(ValueError):
        V3.parse_cell_arg("poisson")


def test_GC2_offset_quantisation_is_reported_not_hidden():
    steps = V3.offset_steps("U1", DT)
    realised_ms = steps * DT * 1000.0
    nominal_ms = np.asarray(V3.AOI_PROFILES["U1"])
    assert (np.abs(realised_ms - nominal_ms) <= 1000.0 * DT / 2 + 1e-9).all()
    assert abs(realised_ms.mean() - nominal_ms.mean()) <= 1000.0 * DT / 2


def test_GC3_stale_rho_shape_and_index():
    rho = np.arange(60, dtype=float).reshape(10, 6)
    rho = np.concatenate([rho, rho[:, :2]], axis=1)
    old = np.array([5, 6, 7])
    off = np.array([0, 1, 2, 0, 1, 2, 0, 1])
    out = V3.stale_rho(rho, old, off)
    assert out.shape == (3, 8)
    for i, t in enumerate(old):
        for l in range(8):
            assert out[i, l] == rho[t - off[l], l]
    with pytest.raises(ValueError):
        V3.stale_rho(rho, np.array([0]), np.array([1, 0, 0, 0, 0, 0, 0, 0]))


def test_GC4_paths_identical_at_zero_offset(small):
    a = V3.y_hat_row_shift(small["arr"]["c_fresh"], small["old"])
    b = V3.y_hat_rho_shift(
        small["cv"], small["rho"], small["old"], V3.offset_steps("U0"), CELL_MODE, small["w_loss"]
    )
    assert np.array_equal(a, b)


def test_GC5_paths_differ_at_nonzero_offset(small):
    a = V3.y_hat_row_shift(small["arr"]["c_fresh"], small["old"])
    for profile in ("U1", "U2", "PC4"):
        b = V3.y_hat_rho_shift(
            small["cv"], small["rho"], small["old"], V3.offset_steps(profile), CELL_MODE, small["w_loss"]
        )
        assert np.abs(a - b).max() > 1.0, profile


def test_GC5b_shifting_by_the_mean_is_not_the_same_as_shifting_per_link(small):
    off = V3.offset_steps("U1")
    right = small["cv"].tables_batch(
        V3.stale_rho(small["rho"], small["old"], off), CELL_MODE, small["w_loss"]
    )[2]
    wrong = small["cv"].tables_batch(
        V3.stale_rho(small["rho"], small["old"], np.full(8, int(round(off.mean())))),
        CELL_MODE,
        small["w_loss"],
    )[2]
    assert np.abs(right - wrong).max() > 1.0


def test_GC6_mhat_edges_use_calib_rows_only():
    df = pd.DataFrame(
        {
            "m_hat": np.concatenate([np.arange(100.0), np.arange(1000.0, 1100.0)]),
            "is_calib": np.concatenate([np.ones(100, bool), np.zeros(100, bool)]),
        }
    )
    edges = V3.mhat_bin_edges(df, 4)
    assert (edges < 100.0).all()


def test_GC7_mhat_bins_are_equal_sized_on_calib():
    rng = np.random.default_rng(0)
    m = rng.lognormal(0.0, 1.0, size=40000)
    df = pd.DataFrame({"m_hat": m, "is_calib": rng.random(40000) < 0.5})
    edges = V3.mhat_bin_edges(df, 4)
    b = V3.assign_mhat_bin(df.loc[df.is_calib, "m_hat"].to_numpy(), edges)
    share = np.bincount(b, minlength=4) / b.size
    assert np.abs(share - 0.25).max() < 0.01


def test_GC8_mhat_bins_are_scale_free():
    rng = np.random.default_rng(1)
    m = rng.lognormal(0.0, 1.0, size=20000)
    df = pd.DataFrame({"m_hat": m, "is_calib": np.ones(20000, bool)})
    b1 = V3.assign_mhat_bin(m, V3.mhat_bin_edges(df, 4))
    df80 = pd.DataFrame({"m_hat": 80.0 * m, "is_calib": np.ones(20000, bool)})
    b2 = V3.assign_mhat_bin(80.0 * m, V3.mhat_bin_edges(df80, 4))
    assert np.array_equal(b1, b2)


@pytest.mark.skipif(not os.path.exists(V2_PARQUET), reason="thieu artifact 21R")
def test_GC9_full_build_reproduces_21R_and_passes_V22():
    df, _meta = V3.build_cell(CELL_MODE, CELL_RHO, aoi_profile="U0")
    report = V3.validate_v3(df, V2_PARQUET)
    assert report["V22_1_worst"] == 0.0
    assert report["V22_2_max_abs_diff"] <= 1e-6
    assert report["V22_3_max_abs_diff"] <= 1e-6
    assert report["V22_5_min"] >= V3.MIN_BLOCKS_PER_CELL
    assert report["fail"] == []
    assert report["pair_ok_rate"] == pytest.approx(0.98757, abs=1e-4)
    assert set(report["a_star_rank_share"]) <= {1, 2, 3, 4}

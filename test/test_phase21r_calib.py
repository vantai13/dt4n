import numpy as np
import pandas as pd
import pytest

from cert import build_calib_set_v2 as B


def test_C1_bin_edges_cover_realized_aoi():
    from measurements.decision_error import sawtooth_age_steps

    z = np.unique(sawtooth_age_steps(200_000, 0.005) * 0.005)
    assert z.min() == pytest.approx(0.055)
    assert z.max() == pytest.approx(0.550)
    assert len(z) == 100
    for edges, k in ((B.Z_EDGES_PRIMARY, 4), (B.Z_EDGES_SECONDARY, 5)):
        bins = B.assign_bin(z, edges)
        assert set(np.unique(bins)) == set(range(k))


def test_C2_bin_rejects_out_of_range():
    with pytest.raises(ValueError):
        B.assign_bin(np.array([0.90]), B.Z_EDGES_PRIMARY)


def test_C3_block_split_never_cuts_a_block():
    df = pd.DataFrame({"block_id": np.repeat(np.arange(200), 50)})
    out = B.split_by_block(df, seed_split=7000)
    per = out.groupby("block_id")["is_calib"].nunique()
    assert (per == 1).all()
    assert 0.4 < out.groupby("block_id")["is_calib"].first().mean() < 0.6


def test_C4_V3_control_does_cut_blocks():
    df = pd.DataFrame({"block_id": np.repeat(np.arange(200), 50)})
    out = B.split_by_sample_V3(df, seed_split=7000)
    assert (out.groupby("block_id")["is_calib"].nunique() == 2).mean() > 0.9


def test_C5_block_len():
    assert B.block_len() == 1000


def test_C6_validate_catches_broken_identity():
    n = 100
    df = pd.DataFrame(
        {
            "block_id": np.arange(n) // 10,
            "z_bin": np.zeros(n, np.int8),
            "z_bin2": np.zeros(n, np.int8),
            "m_hat": np.ones(n),
            "m_true": np.ones(n),
            "m_mid": np.ones(n),
            "s_margin": np.zeros(n),
            "s_signed": np.zeros(n),
            "s_vs_a1": np.zeros(n),
            "s_maxabs": np.zeros(n),
            "regret": np.zeros(n),
            "wrong": np.zeros(n, bool),
            "viol_twin": np.zeros(n, bool),
            "viol_star": np.zeros(n, bool),
            "pair_ok": np.ones(n, bool),
        }
    )
    B.validate(df)
    bad = df.copy()
    bad.loc[0, "m_hat"] = -1.0
    with pytest.raises(AssertionError):
        B.validate(bad)

import numpy as np
import pandas as pd
import pytest

from cert import error_vs_age_v2 as E


def _synth(n_block=120, per_block=60, scales=(1.0, 1.5, 2.0, 2.5), seed=0):
    """Four age bins with known increasing half-normal scale."""
    rng = np.random.default_rng(seed)
    rows = []
    base_m = rng.uniform(0.0, 30.0, (n_block, per_block))
    for block in range(n_block):
        for group, scale in enumerate(scales):
            s = np.abs(rng.normal(0.0, scale, per_block))
            rows.append(
                pd.DataFrame(
                    {
                        "block_id": block,
                        "z_bin": group,
                        "z_bin2": group,
                        "z_s": 0.055 + 0.10 * group,
                        "s_margin": s,
                        "s_signed": s,
                        "s_vs_a1": s * 1.3,
                        "s_maxabs": s * 1.1,
                        "m_hat": base_m[block],
                        "m_true": base_m[block] - s,
                        "m_mid": base_m[block] - 0.5 * s,
                    }
                )
            )
    return pd.concat(rows, ignore_index=True)


def test_E1_monotone_detected():
    result = E.analyse(_synth(), n_boot=200, eta_boot=100)
    assert result["monotonicity"]["pass_G1_monotone"]
    assert result["monotonicity"]["n_positive"] == 3


def test_E2_flat_not_detected():
    """Negative control: flat s(z) must not pass the monotonicity gate."""
    result = E.analyse(_synth(scales=(1.0, 1.0, 1.0, 1.0), seed=2), n_boot=200, eta_boot=100)
    assert not result["monotonicity"]["pass_G1_monotone"]
    assert result["eta_squared"] < 0.01


def test_E3_ratio_matches_scale():
    result = E.analyse(_synth(scales=(1.0, 1.0, 1.0, 3.0), seed=3), n_boot=200, eta_boot=100)
    assert result["ratio"]["ratio_mean"] == pytest.approx(3.0, rel=0.15)
    assert result["ratio"]["pass_H2"]


def test_E4_eta_squared_bounds():
    df = _synth(seed=4)
    eta = E.eta_squared(df)
    assert 0.0 <= eta <= 1.0
    same = df.copy()
    same["s_margin"] = 1.0
    assert np.isnan(E.eta_squared(same)) or E.eta_squared(same) == 0.0


def test_E5_pooled_vs_block_quantile_differ():
    stats = E.bin_stats(_synth(seed=5))
    assert not np.allclose(stats["q_pooled"], stats["q_of_block_q"], rtol=1e-6)


def test_E6_mondrian_value_shows_miscoverage():
    value = E.marginal_vs_conditional(_synth(seed=6))
    assert value["max_over_coverage"] > 0.03
    assert value["max_under_coverage"] < -0.03


def test_E7_half_normal_recognised():
    stats = E.bin_stats(_synth(n_block=300, per_block=120, seed=7))
    half = E.sanity_half_normal(stats)
    assert half["consistent"]
    assert np.allclose(stats["q_over_rms"], 1.64485, rtol=0.04)


def test_E8_m_hat_invariance_control():
    ok = _synth(seed=8)
    assert E.sanity_m_hat_invariant(ok)["pass"]
    bad = ok.copy()
    bad.loc[bad.z_bin == 3, "m_hat"] *= 2.0
    assert not E.sanity_m_hat_invariant(bad)["pass"]


def test_E9_bootstrap_resamples_blocks_not_rows():
    df = _synth(n_block=50, seed=9)
    boot = E.block_bootstrap_quantiles(df, n_boot=200)
    assert boot.shape == (200, 4)
    assert boot.std(axis=0).min() > 0.0


def test_E10_missing_block_bin_cell_raises():
    df = _synth(n_block=20, seed=10)
    df = df[~((df.block_id == 0) & (df.z_bin == 2))]
    with pytest.raises(AssertionError):
        E.block_bootstrap_quantiles(df, n_boot=10)

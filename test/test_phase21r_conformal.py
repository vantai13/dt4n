import numpy as np
import pandas as pd
import pytest

from cert import conformal_v2 as CF


def _synth(n_block=400, per_block=100, scales=(1.0, 2.0), seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for block in range(n_block):
        for group, scale in enumerate(scales):
            rows.append(
                pd.DataFrame(
                    {
                        "block_id": block,
                        "seed": 101 + (block % 5),
                        "z_bin": group,
                        "z_bin2": group,
                        "s_margin": np.abs(rng.normal(0.0, scale, per_block)),
                        "s_signed": rng.normal(0.0, scale, per_block),
                        "s_vs_a1": np.abs(rng.normal(0.0, scale, per_block)) * 1.3,
                        "s_maxabs": np.abs(rng.normal(0.0, scale, per_block)) * 1.1,
                        "m_hat": rng.uniform(0.0, 10.0, per_block),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True)


def _synth_block_effect(n_block=200, per_block=60, scales=(1.0, 2.0), seed=13):
    rng = np.random.default_rng(seed)
    rows = []
    for block in range(n_block):
        block_scale = rng.lognormal(0.0, 0.6)
        for group, scale in enumerate(scales):
            sc = scale * block_scale
            rows.append(
                pd.DataFrame(
                    {
                        "block_id": block,
                        "seed": 101 + (block % 5),
                        "z_bin": group,
                        "z_bin2": group,
                        "s_margin": np.abs(rng.normal(0.0, sc, per_block)),
                        "s_signed": rng.normal(0.0, sc, per_block),
                        "s_vs_a1": np.abs(rng.normal(0.0, sc, per_block)) * 1.3,
                        "s_maxabs": np.abs(rng.normal(0.0, sc, per_block)) * 1.1,
                        "m_hat": rng.uniform(0.0, 10.0, per_block),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True)


def test_F1_level_formula():
    assert CF.conformal_level(500, 0.10) == pytest.approx(451 / 500)
    assert CF.conformal_level(9, 0.10) == pytest.approx(9 / 9)
    assert CF.conformal_level(8, 0.10) is None
    assert CF.conformal_level(0, 0.10) is None


def test_F2_level_is_above_nominal():
    for n in (10, 50, 100, 500, 5000):
        assert CF.conformal_level(n, 0.10) > 0.90


def test_F3_qhat_is_a_real_sample_point():
    values = np.array([1.0, 2.0, 3.0, 10.0])
    qhat = CF.empirical_qhat(values, 0.80)
    assert qhat in set(values.tolist())
    assert CF.empirical_qhat(values, 0.0) == 1.0
    assert CF.empirical_qhat(values, 1.0) == 10.0


def test_F4_higher_differs_from_linear():
    values = np.array([1.0, 2.0, 3.0, 100.0])
    assert CF.empirical_qhat(values, 0.90) != pytest.approx(np.percentile(values, 90))


def test_F5_block_split_is_pure():
    df = _synth(n_block=100, seed=5)
    mask = CF.split_blocks(df.block_id.to_numpy(), seed=7000)
    assert (df.assign(c=mask).groupby("block_id")["c"].nunique() == 1).all()


def test_F6_row_split_is_impure():
    df = _synth(n_block=100, seed=6)
    mask = CF.split_rows_V3(len(df), seed=7000)
    assert (df.assign(c=mask).groupby("block_id")["c"].nunique() == 2).mean() > 0.95


def test_F7_seed_split_is_disjoint():
    df = _synth(seed=7)
    mask = CF.split_by_seed(df.seed.to_numpy(), calib_seeds=(101, 102, 103))
    assert set(df[mask].seed.unique()).isdisjoint(set(df[~mask].seed.unique()))


def test_F8_coverage_near_nominal():
    df = _synth(n_block=600, seed=8)
    result = CF.fit_eval(df, CF.split_blocks(df.block_id.to_numpy()))
    assert result["pass_G3"] and result["pass_G4"]
    assert 0.88 <= result["coverage_marginal"] <= 0.95


def test_F9_qhat_scales_with_spread():
    df = _synth(scales=(1.0, 3.0), seed=9)
    result = CF.fit_eval(df, CF.split_blocks(df.block_id.to_numpy()))
    assert result["qhat"][1] / result["qhat"][0] == pytest.approx(3.0, rel=0.15)


def test_F10_alpha_over_K_increases_qhat():
    df = _synth(seed=10)
    mask = CF.split_blocks(df.block_id.to_numpy())
    q1 = CF.fit_eval(df, mask, alpha=0.10)["qhat"]
    q4 = CF.fit_eval(df, mask, alpha=0.025)["qhat"]
    assert all(q4[group] > q1[group] for group in q1)


def test_F11_tiny_group_gives_infinite_qhat():
    df = _synth(n_block=8, per_block=50, seed=11)
    result = CF.fit_eval(df, np.ones(len(df), bool))
    assert all(np.isinf(v) for v in result["qhat"].values())
    assert all(v == 1.0 for v in result["coverage"].values())


def test_F12_variant_ordering():
    df = _synth(n_block=600, seed=12)
    mask = CF.split_blocks(df.block_id.to_numpy())
    qa = CF.fit_eval(df, mask, variant="A")["qhat"]
    qb = CF.fit_eval(df, mask, variant="B")["qhat"]
    qc = CF.fit_eval(df, mask, variant="C")["qhat"]
    for group in qb:
        assert qc[group] > qb[group]
        assert abs(qa[group] - qb[group]) / qb[group] < 0.20


def test_F13_V3_detects_leakage_via_variance():
    df = _synth_block_effect()
    result = CF.v3_variance_control(df, repeats=8)
    assert result["sd_ratio_row_over_block"] < 1.0
    mb = np.mean(result["coverage_mean_block"])
    mr = np.mean(result["coverage_mean_row"])
    assert abs(mb - mr) < 0.02
    assert np.mean(result["coverage_sd_row"]) < np.mean(result["coverage_sd_block"])


def test_F14_bridge_half_normal():
    df = _synth(n_block=600, seed=14)
    mask = CF.split_blocks(df.block_id.to_numpy())
    qhat = CF.fit_eval(df, mask)["qhat"]
    assert CF.bridge_to_rms(df, qhat)["all_within_5pct"]


def test_F15_bridge_flags_wrong_qhat():
    df = _synth(n_block=600, seed=15)
    mask = CF.split_blocks(df.block_id.to_numpy())
    qhat = {group: 2.0 * value for group, value in CF.fit_eval(df, mask)["qhat"].items()}
    assert not CF.bridge_to_rms(df, qhat)["all_within_5pct"]

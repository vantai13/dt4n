"""Golden tests -- cert.studentized_score, Phase 23 Lesson 23.5[A]."""

import os

import numpy as np
import pandas as pd
import pytest

import cert.studentized_score as ST
from cert.simultaneous_score import ALPHA, conformal_level


CALIB = "results/phase-22/calib_set_v3_poisson_0.925.parquet"
needs_data = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu artifact phase-22 v3")


def _toy_frame(rng, n_blocks=80, per_block=40, n_bins=2):
    rows = []
    for block in range(n_blocks):
        base = rng.normal(0.0, 1.0)
        for _ in range(per_block):
            scores = np.abs(rng.normal(base, 1.0, size=3) * np.array([1.0, 1.5, 2.5]))
            rows.append(
                {
                    "block_id": block,
                    "z_bin": block % n_bins,
                    "s_pair_1": scores[0],
                    "s_pair_2": scores[1],
                    "s_pair_3": scores[2],
                    "s_sim": scores.max(),
                }
            )
    df = pd.DataFrame(rows)
    df["is_calib"] = df["block_id"] < n_blocks // 2
    return df


def test_T1_fold_split_whole_blocks_and_deterministic():
    bid = np.repeat(np.arange(40), 25)
    m1, m2 = ST.split_folds_by_block(bid, seed=7001, frac_fold1=0.5)
    assert not (m1 & m2).any()
    assert (m1 | m2).all()
    for block in np.unique(bid):
        rows = bid == block
        assert len(set(m1[rows].tolist())) == 1
    again, _ = ST.split_folds_by_block(bid, seed=7001)
    assert np.array_equal(m1, again)
    other, _ = ST.split_folds_by_block(bid, seed=7002)
    assert not np.array_equal(m1, other)


def test_T2_estimate_sigma_rms_is_exact():
    scores = np.array([[3.0, 0.0], [4.0, 0.0], [0.0, 5.0]])
    sigma = ST.estimate_sigma(scores, "rms")
    assert sigma[0] == pytest.approx(np.sqrt((9.0 + 16.0) / 3.0))
    assert sigma[1] == pytest.approx(np.sqrt(25.0 / 3.0))


def test_T3_sigma_floor_guards_degenerate_slot():
    scores = np.zeros((100, 3))
    scores[:, 1] = 2.0
    sigma = ST.estimate_sigma(scores, "rms")
    assert np.all(sigma > 0.0)
    assert sigma[0] == pytest.approx(ST.SIGMA_FLOOR)
    v = ST.s_studentized(scores, sigma)
    assert np.all(np.isfinite(v))


def test_T4_s_studentized_is_max_of_ratios():
    scores = np.array([[1.0, 4.0], [6.0, 2.0]])
    sigma = np.array([1.0, 2.0])
    assert np.allclose(ST.s_studentized(scores, sigma), [2.0, 6.0])


def test_T5_qhat_is_exactly_proportional_to_sigma():
    rng = np.random.default_rng(0)
    scale = np.array([1.0, 2.0, 4.0])
    f1 = np.abs(rng.normal(size=(4000, 3)) * scale)
    f2 = np.abs(rng.normal(size=(4000, 3)) * scale)
    out = ST.qhat_studentized(f1, f2, n_blocks_fold2=200)
    qhat = np.asarray(out["qhat"])
    sigma = np.asarray(out["sigma"])
    assert np.allclose(qhat / sigma, out["c"], rtol=1e-12)


def test_T6_studentization_reallocates_not_shrinks():
    rng = np.random.default_rng(1)
    scale = np.array([1.0, 2.0, 5.0])
    f1 = np.abs(rng.normal(size=(8000, 3)) * scale)
    f2 = np.abs(rng.normal(size=(8000, 3)) * scale)
    out = ST.qhat_studentized(f1, f2, n_blocks_fold2=400)
    qhat = np.asarray(out["qhat"])
    qmax = ST.maxscore_on_rows(f2.max(axis=1), 400, ALPHA, 3)
    assert qhat[0] < qmax[0]
    assert qhat[2] > qmax[2]
    assert out["sigma_ratio_max_over_min"] > 1.0


def test_T7_n_eff_uses_blocks_not_rows():
    assert conformal_level(250, 0.10) == pytest.approx(226 / 250)
    assert conformal_level(250, 0.10) > conformal_level(250_000, 0.10)


def test_T8_status_label_is_enforced():
    assert ST.STATUS == "EXPLORATORY"
    df = _toy_frame(np.random.default_rng(2))
    out = ST.fit_eval_studentized(df, df["is_calib"].to_numpy(bool))
    assert out["status"] == "EXPLORATORY"


def test_T9_raises_when_fold2_too_thin():
    scores = np.abs(np.random.default_rng(3).normal(size=(50, 3)))
    with pytest.raises(ValueError, match="block"):
        ST.qhat_studentized(scores, scores, n_blocks_fold2=4)


def test_T10_NC_S_1_uniform_sigma_equals_maxscore_on_fold2():
    df = _toy_frame(np.random.default_rng(4))
    out = ST.negative_control_uniform_sigma(df, df["is_calib"].to_numpy(bool))
    assert out["max_abs_diff"] <= 1e-9
    assert out["pass_G23_26"]


def test_T11_global_fold_split_no_block_in_both_folds_across_bins():
    df = _toy_frame(np.random.default_rng(5))
    ic = df["is_calib"].to_numpy(bool)
    bid = df["block_id"].to_numpy()
    pos = np.flatnonzero(ic)
    m1, _ = ST.split_folds_by_block(bid[pos], ST.SEED_FOLD, ST.FRAC_FOLD1)
    f1_blocks = set(bid[pos][m1].tolist())
    f2_blocks = set(bid[pos][~m1].tolist())
    assert f1_blocks.isdisjoint(f2_blocks)


def test_T12_sigma_never_computed_from_test_rows(monkeypatch):
    df = _toy_frame(np.random.default_rng(6))
    ic = df["is_calib"].to_numpy(bool)
    n_calib = int(ic.sum())
    seen = []
    original = ST.estimate_sigma

    def spy(arr, *args, **kwargs):
        seen.append(len(arr))
        return original(arr, *args, **kwargs)

    monkeypatch.setattr(ST, "estimate_sigma", spy)
    ST.fit_eval_studentized(df, ic)
    assert seen and max(seen) <= n_calib


@pytest.fixture(scope="module")
def real():
    df = pd.read_parquet(CALIB)
    return df, df["is_calib"].to_numpy(bool)


@needs_data
def test_T13_coverage_holds_on_real_data(real):
    df, ic = real
    out = ST.fit_eval_studentized(df, ic)
    assert out["coverage_marginal"] >= 1.0 - ALPHA - 0.02
    for group, coverage in out["coverage_simultaneous"].items():
        assert coverage >= 1.0 - ALPHA - 0.05, "bin %s vo: %.4f" % (group, coverage)


@needs_data
def test_T14_sigma_ratio_matches_committed_artifact(real):
    df, ic = real
    out = ST.fit_eval_studentized(df, ic)
    ratios = [v["sigma_ratio_max_over_min"] for v in out["per_bin"].values()]
    assert 1.0 < min(ratios) and max(ratios) < 1.6, ratios


@needs_data
def test_T15_PC_S_1_reports_and_does_not_silently_pass(real):
    df, ic = real
    full = ST.positive_control_sigma_leak(df, ic)
    assert abs(full["coverage_drop"]) < 0.02
    assert full["detectable"] is False

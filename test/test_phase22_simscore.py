"""Golden tests for cert.simultaneous_score -- Phase 22 Lesson 22.1."""

import inspect

import numpy as np
import pytest

from cert import margin_score as M
from cert import simultaneous_score as S
from twin import topology_v7 as T7


INCIDENCE = np.array(
    [[1.0 if link in T7.PATHS[path] else 0.0 for link in T7.LINK_NAMES] for path in T7.PATH_NAMES]
)

ALPHA = 0.10


def _independent(n=4000, K=4, seed=0, sd=1.5):
    """Twin errors independent across actions."""
    rng = np.random.default_rng(seed)
    y_hat = rng.uniform(10.0, 110.0, size=(n, K))
    y_true = y_hat + rng.normal(0.0, sd, size=(n, K))
    return y_true, y_hat


def _butterfly(n=4000, seed=0, sd_link=1.0):
    """Twin errors generated from the real topology_v7 link incidence."""
    rng = np.random.default_rng(seed)
    y_hat = rng.uniform(10.0, 110.0, size=(n, 4))
    e_link = rng.normal(0.0, sd_link, size=(n, 8))
    return y_hat + e_link @ INCIDENCE.T, y_hat


# --- GS-1 .. GS-5 : score algebra -----------------------------------------

def test_GS1_no_truth_leak_in_ranking():
    sig = inspect.signature(S.top_k_by_twin)
    assert list(sig.parameters) == ["y_hat", "k"]
    for name in sig.parameters:
        assert "true" not in name.lower()

    y_true, y_hat = _independent()
    perm = np.array([1, 0, 3, 2])
    assert np.array_equal(S.top_k_by_twin(y_hat), S.top_k_by_twin(y_hat))
    assert not np.allclose(S.s_simultaneous(y_true, y_hat), S.s_simultaneous(y_true[:, perm], y_hat))


def test_GS2_margin_le_sim_le_two_maxabs():
    for seed in range(4):
        y_true, y_hat = _independent(seed=seed)
        sm = S.s_margin(y_true, y_hat)
        ss = S.s_simultaneous(y_true, y_hat)
        sa = S.s_maxabs(y_true, y_hat)
        assert (sm <= ss + 1e-12).all()
        assert (ss <= 2.0 * sa + 1e-12).all()


def test_GS2b_identity_sim_is_max_of_pairs():
    y_true, y_hat = _butterfly(seed=11)
    pair = S.pair_scores(y_true, y_hat)
    assert np.allclose(S.s_simultaneous(y_true, y_hat), pair.max(axis=1), atol=1e-12)
    assert np.allclose(S.s_margin(y_true, y_hat), pair[:, 0], atol=1e-12)


def test_GS2c_agrees_with_phase21R_module():
    y_true, y_hat = _independent(seed=12)
    assert np.allclose(S.s_margin(y_true, y_hat), M.s_margin(y_true, y_hat), atol=1e-12)
    assert np.allclose(S.s_simultaneous(y_true, y_hat), M.s_vs_a1(y_true, y_hat), atol=1e-12)
    assert np.allclose(S.s_maxabs(y_true, y_hat), M.s_maxabs(y_true, y_hat), atol=1e-12)


def test_GS3_common_mode_invariance():
    y_true, y_hat = _independent(seed=3)
    base = S.s_simultaneous(y_true, y_hat)
    for c in (1.0, 1e3, 1e5):
        shifted = S.s_simultaneous(y_true + c, y_hat + c)
        assert np.allclose(base, shifted, atol=1e-6)
    for c in (1.0, 1e3):
        col = np.array([[c, c, c, c]])
        assert np.allclose(base, S.s_simultaneous(y_true + col, y_hat + col), atol=1e-6)


def test_GS4_perfect_twin_exact_zero():
    _y, y_hat = _independent(seed=4)
    assert np.array_equal(S.s_simultaneous(y_hat, y_hat), np.zeros(len(y_hat)))
    assert np.array_equal(S.pair_scores(y_hat, y_hat), np.zeros((len(y_hat), 3)))


def test_GS5_K2_degenerates_to_margin():
    y_true, y_hat = _independent(K=2, seed=5)
    assert S.n_comparisons(2) == 1
    assert np.allclose(S.s_simultaneous(y_true, y_hat), M.s_margin(y_true, y_hat), atol=1e-12)


def test_GS5b_margins_monotone_and_nonnegative():
    _y, y_hat = _independent(seed=6)
    mh = S.pair_margins_hat(y_hat)
    assert (mh >= -1e-12).all()
    assert (np.diff(mh, axis=1) >= -1e-12).all()


# --- GS-6 .. GS-8 : FWER procedures ---------------------------------------

def test_GS6_bonferroni_wider_than_uncorrected():
    y_true, y_hat = _independent(seed=7)
    pair = S.pair_scores(y_true, y_hat)
    q_unc = S.qhat_uncorrected(pair, ALPHA)
    q_bonf = S.qhat_bonferroni(pair, ALPHA)
    assert (q_bonf > q_unc).all()


def test_GS7_sidak_between_uncorrected_and_bonferroni():
    y_true, y_hat = _independent(seed=8)
    pair = S.pair_scores(y_true, y_hat)
    assert S.alpha_sidak(ALPHA, 3) > S.alpha_bonferroni(ALPHA, 3)
    q_sid = S.qhat_sidak(pair, ALPHA)
    q_bonf = S.qhat_bonferroni(pair, ALPHA)
    assert (q_sid <= q_bonf + 1e-9).all()


def test_GS8_maxscore_tighter_than_bonferroni_on_real_incidence():
    y_true, y_hat = _butterfly(n=200000, seed=9)
    pair = S.pair_scores(y_true, y_hat)
    q_max = S.qhat_maxscore(pair.max(axis=1), ALPHA)
    q_bonf = float(S.qhat_bonferroni(pair, ALPHA).max())
    assert q_max < q_bonf
    assert 0.93 <= q_max / q_bonf <= 0.99


def test_GS8b_maxscore_close_to_bonferroni_when_independent():
    y_true, y_hat = _independent(n=40000, seed=10)
    pair = S.pair_scores(y_true, y_hat)
    q_max = S.qhat_maxscore(pair.max(axis=1), ALPHA)
    q_bonf = float(S.qhat_bonferroni(pair, ALPHA).max())
    assert abs(q_max / q_bonf - 1.0) < 0.10


# --- GS-9 .. GS-10 : gate semantics ---------------------------------------

def test_GS9_certified_argmin_returns_none_when_gap_too_small():
    y_hat = np.array([[10.0, 10.1, 10.2, 10.3]])
    out = S.certified_argmin(y_hat, np.array([5.0, 5.0, 5.0]), kappa=1.0)
    assert out[0] == -1


def test_GS10_certified_argmin_returns_a1_when_gap_large():
    y_hat = np.array([[10.0, 60.0, 70.0, 80.0]])
    out = S.certified_argmin(y_hat, np.array([5.0, 5.0, 5.0]), kappa=1.0)
    assert out[0] == 0


def test_GS10b_accept_uses_all_rivals_not_just_the_runner_up():
    m_hat = np.array([[9.0, 9.5, 10.0]])
    assert S.accept_simultaneous(m_hat, np.array([5.0, 5.0, 5.0]))[0]
    assert not S.accept_simultaneous(m_hat, np.array([5.0, 5.0, 50.0]))[0]


def test_GS10c_maxscore_accept_equals_margin_vs_qhat():
    _y, y_hat = _independent(seed=13)
    mh = S.pair_margins_hat(y_hat)
    q = 7.0
    assert np.array_equal(S.accept_simultaneous(mh, q), mh[:, 0] >= q)


# --- GS-11 .. GS-12 : coverage and negative control ------------------------

def test_GS11_simultaneous_coverage_on_synthetic_data():
    for seed, gen in ((21, _independent), (22, _butterfly)):
        y_true, y_hat = gen(n=60000, seed=seed)
        pair = S.pair_scores(y_true, y_hat)
        cal, tst = pair[:30000], pair[30000:]
        for proc, fn in (("bonf", S.qhat_bonferroni), ("sidak", S.qhat_sidak)):
            cov = S.coverage_simultaneous(tst, fn(cal, ALPHA))
            assert 0.88 <= cov <= 0.92, (seed, proc, cov)
        cov_max = S.coverage_simultaneous(tst, S.qhat_maxscore(cal.max(axis=1), ALPHA))
        assert 0.88 <= cov_max <= 0.92, (seed, "maxscore", cov_max)


def test_GS12_negative_control_uncorrected_alpha_drops_coverage():
    y_true, y_hat = _independent(n=60000, seed=23)
    pair = S.pair_scores(y_true, y_hat)
    cal, tst = pair[:30000], pair[30000:]
    cov_unc = S.coverage_simultaneous(tst, S.qhat_uncorrected(cal, ALPHA))
    cov_bonf = S.coverage_simultaneous(tst, S.qhat_bonferroni(cal, ALPHA))
    assert cov_bonf - cov_unc > 0.05
    assert 0.70 <= cov_unc <= 0.78


def test_GS12b_pointwise_coverage_is_conservative_under_correction():
    y_true, y_hat = _independent(n=60000, seed=24)
    pair = S.pair_scores(y_true, y_hat)
    cal, tst = pair[:30000], pair[30000:]
    pw = S.coverage_pointwise(tst, S.qhat_bonferroni(cal, ALPHA))
    assert (pw > 0.94).all()


# --- GS-13 .. GS-16 : determinism, labels, and boundary behavior -----------

def test_GS13_deterministic_and_tie_rule():
    y_true, y_hat = _independent(seed=25)
    a = S.s_simultaneous(y_true, y_hat)
    b = S.s_simultaneous(y_true, y_hat)
    assert np.array_equal(a, b)
    tied = np.array([[5.0, 5.0, 5.0, 5.0]])
    assert np.array_equal(S.top_k_by_twin(tied)[0], np.array([0, 1, 2, 3]))


def test_GS14_three_label_rule():
    y_true, y_hat = _independent(seed=26)
    tags = S.labelled_scores(y_true, y_hat, rowset="synthetic-seed26")
    for name, lab in tags.items():
        d = lab.as_dict()
        assert {"scale", "level", "rowset"} <= set(d), name
    assert tags["s_sim"].level == "simultaneous"
    assert tags["s_margin"].level == "margin"

    pair = S.pair_scores(y_true, y_hat)
    q = S.labelled_qhat(pair, "bonferroni", ALPHA, rowset="synthetic-calib")
    assert q.extra["alpha_each"] == pytest.approx(ALPHA / 3)
    assert q.extra["m_comparisons"] == 3
    assert not q.extra["negative_control"]
    assert S.labelled_qhat(pair, "uncorrected", ALPHA, rowset="x").extra["negative_control"]

    with pytest.raises(ValueError):
        S.Labelled(1.0, "cost_ms", "margin", "")
    with pytest.raises(ValueError):
        S.Labelled(1.0, "furlongs", "margin", "rows")


def test_GS15_conformal_level_floor():
    assert S.conformal_level(8, 0.10) is None
    assert S.conformal_level(9, 0.10) == pytest.approx(9 / 9)
    assert S.conformal_level(99, 0.10) == pytest.approx(90 / 99)
    assert S.qhat_maxscore(np.arange(8.0), 0.10, n_eff=8) == float("inf")


def test_GS16_a_star_rank():
    y_hat = np.array([[10.0, 20.0, 30.0, 40.0]])
    assert S.a_star_rank_by_twin(np.array([[10.0, 20.0, 30.0, 40.0]]), y_hat)[0] == 1
    assert S.a_star_rank_by_twin(np.array([[10.0, 20.0, 30.0, 1.0]]), y_hat)[0] == 4

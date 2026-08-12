"""Golden tests for cert.margin_score -- Phase 21R Lesson 21R.1."""

import inspect

import numpy as np
import pytest

from cert import margin_score as M


def _rand(n=2000, K=4, seed=0, scale=100.0):
    rng = np.random.default_rng(seed)
    y_hat = rng.uniform(10.0, 10.0 + scale, size=(n, K))
    y_true = y_hat + rng.normal(0.0, 1.5, size=(n, K))
    return y_true, y_hat


def test_GM1_no_truth_leak():
    sig = inspect.signature(M.top_two_by_twin)
    assert list(sig.parameters) == ["y_hat"]
    for name in sig.parameters:
        assert "true" not in name.lower()

    y_true, y_hat = _rand()
    perm = np.array([1, 0, 3, 2])

    assert not np.allclose(M.s_margin(y_true, y_hat), M.s_margin(y_true[:, perm], y_hat))

    _a1, _a2, mh1, _ = M.margins(y_true, y_hat)
    _b1, _b2, mh2, _ = M.margins(y_true[:, perm], y_hat)
    assert np.array_equal(mh1, mh2)


def test_GM2_mhat_nonneg():
    y_true, y_hat = _rand(seed=2)
    _a1, _a2, m_hat, _m_true = M.margins(y_true, y_hat)
    assert (m_hat >= 0).all()


def test_GM3_mtrue_can_be_negative():
    y_hat = np.array([[10.0, 11.0, 50.0, 60.0]])
    y_true = np.array([[12.0, 11.0, 50.0, 60.0]])
    _a1, _a2, m_hat, m_true = M.margins(y_true, y_hat)
    assert m_hat[0] == pytest.approx(1.0)
    assert m_true[0] == pytest.approx(-1.0)
    assert M.s_margin(y_true, y_hat)[0] == pytest.approx(2.0)


def test_GM4_perfect_twin_zero():
    _y, y_hat = _rand(seed=4)
    score = M.s_margin(y_hat, y_hat)
    assert np.array_equal(score, np.zeros_like(score))


def test_GM5_common_mode_both():
    y_true, y_hat = _rand(seed=5)
    s0 = M.s_margin(y_true, y_hat)
    for c in (1.0, 1e3, 1e5):
        s1 = M.s_margin(y_true + c, y_hat + c)
        assert np.allclose(s0, s1, rtol=0, atol=1e-9 * max(1.0, c / 1e3))


def test_GM6_common_mode_yhat_only():
    y_true, y_hat = _rand(seed=6)
    assert np.allclose(M.s_margin(y_true, y_hat), M.s_margin(y_true, y_hat + 250.0), atol=1e-9)


def test_GM7_s_maxabs_not_invariant():
    y_true, y_hat = _rand(seed=7)
    assert not np.allclose(M.s_maxabs(y_true, y_hat), M.s_maxabs(y_true, y_hat + 250.0))


def test_GM8_accept_uses_one_qhat():
    m_hat = np.array([0.9, 1.0, 1.1, 2.1])
    qhat = np.full(4, 1.0)
    assert np.array_equal(M.accept_certified(m_hat, qhat), np.array([False, True, True, True]))
    assert np.array_equal(M.accept_kappa(m_hat, qhat, 1.0), M.accept_certified(m_hat, qhat))
    assert M.accept_kappa(m_hat, qhat, 2.0).sum() < M.accept_certified(m_hat, qhat).sum()


def test_GM9_K_values():
    for K in (2, 3, 4, 8):
        y_true, y_hat = _rand(n=50, K=K, seed=K)
        assert M.s_margin(y_true, y_hat).shape == (50,)
    with pytest.raises(ValueError):
        M.top_two_by_twin(np.zeros((5, 1)))


def test_GM10_two_formulas_agree():
    y_true, y_hat = _rand(seed=10, scale=1000.0)
    assert np.allclose(M.s_margin(y_true, y_hat), M.s_margin_via_errors(y_true, y_hat), atol=1e-10)


def test_GM11_score_ordering():
    y_true, y_hat = _rand(n=5000, seed=11)
    sm = M.s_margin(y_true, y_hat)
    sv = M.s_vs_a1(y_true, y_hat)
    sa = M.s_maxabs(y_true, y_hat)
    assert (sm <= sv + 1e-12).all()
    assert (sv <= 2 * sa + 1e-12).all()
    assert np.percentile(sm, 90) < np.percentile(sv, 90)


def test_GM12_regret_bound():
    m_hat = np.array([0.0, 1.0, 3.0, 10.0])
    qhat = np.full(4, 4.0)
    ub = M.regret_upper_bound(m_hat, qhat)
    assert np.allclose(ub, [4.0, 3.0, 1.0, 0.0])

    eps = 3.0
    kap = M.kappa_of_eps_regret(qhat, eps)
    assert np.array_equal(ub <= eps, M.accept_kappa(m_hat, qhat, float(kap[0])))

    qhat_small = np.array([2.0, 2.5])
    assert np.allclose(M.kappa_of_eps_regret(qhat_small, 3.2222), 0.0)


def test_GM13_signed_le_abs():
    y_true, y_hat = _rand(n=5000, seed=13)
    signed = M.s_margin_signed(y_true, y_hat)
    abs_score = M.s_margin(y_true, y_hat)
    assert (signed <= abs_score + 1e-12).all()
    assert np.percentile(signed, 90) <= np.percentile(abs_score, 90) + 1e-12


def test_GM14_tie_is_deterministic():
    y_hat = np.array([[5.0, 5.0, 5.0, 9.0]])
    for _ in range(5):
        a1, a2 = M.top_two_by_twin(y_hat)
        assert (a1[0], a2[0]) == (0, 1)


def test_GM15_contender_flag():
    y_hat = np.array([[1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0]])
    y_true = np.array([[1.0, 2.0, 3.0, 4.0], [9.0, 9.0, 0.5, 9.0]])
    flag = M.pair_is_true_contender(y_true, y_hat)
    assert flag[0] and (not flag[1])


def test_GM16_nan_rejected():
    with pytest.raises(ValueError):
        M.top_two_by_twin(np.array([[1.0, np.nan, 3.0]]))

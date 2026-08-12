import numpy as np
import pandas as pd
import pytest

from cert import decomposition as D


def _rand(n=3000, K=4, seed=0):
    rng = np.random.default_rng(seed)
    y_hat = rng.uniform(10.0, 110.0, (n, K))
    y_mid = y_hat + rng.normal(0.0, 2.0, (n, K))
    y_true = y_mid + rng.normal(0.0, 1.0, (n, K))
    return y_true, y_mid, y_hat


def test_D1_identity_margin():
    yt, ym, yh = _rand()
    em, es, total = D.decompose_margin(yt, ym, yh)
    assert np.allclose(em + es, total, atol=1e-12)


def test_D2_identity_path():
    yt, ym, yh = _rand()
    em, es, total = D.decompose_path(yt, ym, yh)
    assert np.allclose(em + es, total, atol=1e-12)


def test_D3_variance_identity():
    yt, ym, yh = _rand(seed=3)
    em, es, _total = D.decompose_margin(yt, ym, yh)
    m = D.moments(em, es)
    assert np.isclose(m["rms_total"] ** 2, m["rms_e_model"] ** 2 + m["rms_e_stale"] ** 2 + 2 * m["cov_e"])
    assert np.isclose(m["share_model"] + m["share_stale"] + m["share_cov"], 1.0)


def test_D4_NC1_zero_staleness():
    yt, ym, _yh = _rand(seed=4)
    em, es, total = D.decompose_margin(yt, ym, ym)
    assert np.array_equal(es, np.zeros_like(es))
    assert np.array_equal(em, total)


def test_D5_NC2_zero_model():
    _yt, ym, yh = _rand(seed=5)
    em, es, total = D.decompose_margin(ym, ym, yh)
    assert np.array_equal(em, np.zeros_like(em))
    assert np.array_equal(es, total)


def test_D6_pair_must_come_from_y_hat():
    yt, ym, yh = _rand(seed=6)
    em, _es, total = D.decompose_margin(yt, ym, yh)
    from cert import margin_score as MS

    b1, b2 = MS.top_two_by_twin(ym)
    rows = np.arange(len(ym))
    mm_bad = ym[rows, b2] - ym[rows, b1]
    _a1, _a2, m_hat, m_true = MS.margins(yt, yh)
    bad = (m_true - mm_bad) + (mm_bad - m_hat)
    assert np.allclose(bad, total)
    assert not np.allclose(m_true - mm_bad, em)


def test_D7_flatness_control():
    ok = pd.DataFrame({"z_s": [0.1, 0.2], "rms_e_model": [2.0, 2.001]})
    bad = pd.DataFrame({"z_s": [0.1, 0.2], "rms_e_model": [2.0, 3.0]})
    assert D.control_flatness(ok)["pass"]
    assert not D.control_flatness(bad)["pass"]


def test_D8_z_cross_interpolation():
    df = pd.DataFrame(
        {
            "z_s": [0.1, 0.2, 0.3],
            "rms_e_model": [2.0, 2.0, 2.0],
            "rms_e_stale": [1.0, 3.0, 4.0],
        }
    )
    result = D.find_z_cross(df)
    assert result["status"] == "interpolated"
    assert result["z_cross_s"] == pytest.approx(0.15)


def test_D9_z_cross_below_grid():
    df = pd.DataFrame(
        {
            "z_s": [0.05, 0.10],
            "rms_e_model": [2.0, 2.0],
            "rms_e_stale": [4.0, 6.0],
        }
    )
    result = D.find_z_cross(df)
    assert result["status"] == "below_grid_extrapolated_sqrt"
    assert result["z_cross_s"] == pytest.approx(0.05 * (2.0 / 4.0) ** 2)


def test_D10_cov_can_be_either_sign():
    rng = np.random.default_rng(10)
    x = rng.normal(0.0, 1.0, 5000)
    assert D.moments(x, -x + rng.normal(0.0, 0.1, 5000))["corr_e"] < 0
    assert D.moments(x, x + rng.normal(0.0, 0.1, 5000))["corr_e"] > 0

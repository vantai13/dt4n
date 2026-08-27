#!/usr/bin/env python3
"""Chan cau truc cho Lesson 23.23; khong test ket qua khoa hoc."""

import ast
import os

import numpy as np
import pandas as pd
import pytest

from cert import baselines_lit as BL
from cert import config_matrix as CM
from cert.transfer_matrix import POST_VARIANT


def test_k08_matches_analytic():
    assert BL.CV_MAX_FOLDED == pytest.approx(np.sqrt(np.pi / 2 - 1), abs=1e-15)
    assert BL.SQRT_2_OVER_PI == pytest.approx(np.sqrt(2 / np.pi), abs=1e-15)
    assert BL.CV_MAX_FOLDED == pytest.approx(
        np.sqrt(1.0 / BL.SQRT_2_OVER_PI**2 - 1.0), abs=1e-12
    )


def test_h_is_monotone_and_bounded():
    th = np.linspace(0.0, BL.THETA_HI, 200_001)
    h = BL._h(th)
    assert np.all(np.diff(h) >= -1e-15)
    assert h[0] == pytest.approx(BL.SQRT_2_OVER_PI, abs=1e-15)
    assert h[-1] < 1.0


@pytest.mark.parametrize(
    "mu,sigma", [(0.0, 1.0), (0.5, 1.0), (1.0, 3.0), (2.0, 1.0), (5.0, 1.0)]
)
def test_folded_roundtrip_on_qhat_not_on_params(mu, sigma):
    """Dao moment dieu kien xau o theta nho, nhung sai so khong lan sang q."""
    p = 1.0 - BL.ALPHA_EACH
    d = np.random.default_rng(3).normal(mu, sigma, 2_000_000)
    m, s, _ = BL.fit_folded_normal(np.abs(d))
    assert BL.folded_quantile(m, s, p) == pytest.approx(
        BL.folded_quantile(mu, sigma, p), rel=0.005
    )


def test_folded_quantile_wider_than_normal_quantile():
    q = BL.folded_quantile(0.0, 1.0, 1.0 - BL.ALPHA_EACH)
    assert q / BL.Z_BONF == pytest.approx(1.1604, abs=1e-3)


def test_folded_quantile_monotone():
    p = 1.0 - BL.ALPHA_EACH
    qs = [BL.folded_quantile(0.0, s, p) for s in (0.5, 1.0, 2.0, 4.0)]
    assert all(b > a for a, b in zip(qs, qs[1:]))
    ps = [BL.folded_quantile(1.0, 1.0, x) for x in (0.5, 0.8, 0.95, 0.99)]
    assert all(b > a for a, b in zip(ps, ps[1:]))


def test_alpha_each_matches_live_config():
    assert BL.N_MARGINS == len(CM.SIM_COLS) == 3
    assert BL.ALPHA_EACH == pytest.approx(0.10 / 3.0, abs=1e-15)
    assert BL.Z_BONF == pytest.approx(1.8339146358159146, abs=1e-12)


def test_baselines_lit_uses_live_config():
    assert BL.POST_VARIANT == POST_VARIANT == "selective"
    assert CM._keys(BL.POST_VARIANT) == ["z_bin"]


def test_b8_does_not_borrow_c3_qhat():
    src = os.path.join(os.path.dirname(BL.__file__), "baselines_lit.py")
    tree = ast.parse(open(src, encoding="utf-8").read())
    bad = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        if fn.name == "wiring_parity":
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Attribute) and node.attr == "fit_config":
                bad.append(fn.name)
    assert bad == [], "muon qhat cua C3 ngoai duong wiring: %r" % bad


def test_bisect_iters_is_a_constant_not_a_tolerance():
    src = os.path.join(os.path.dirname(BL.__file__), "baselines_lit.py")
    text = open(src, encoding="utf-8").read()
    assert "BISECT_ITERS = 200" in text
    assert "while" not in text.split("def _h")[0]


def test_naive_gaussian_is_documented_as_strawman():
    assert "MO TA" in BL.qhat_B8a_naive.__doc__


def test_qhat_conformal_can_refuse_but_b8_cannot():
    s = np.abs(np.random.default_rng(1).normal(0, 1, 20))
    assert BL.qhat_C3(s, n_eff=10) == float("inf")
    assert np.isfinite(BL.qhat_B8a_naive(s, n_eff=10))
    assert np.isfinite(BL.qhat_B8b_folded(s, n_eff=10))
    assert np.isfinite(BL.qhat_B8c_plugin(s, n_eff=10))


def test_b8_neff_counts_blocks(monkeypatch):
    seen = []

    def fake(s, n_eff):
        seen.append(n_eff)
        return 1.0

    monkeypatch.setitem(BL.PROCEDURES, "B8a", fake)
    frame = pd.DataFrame({
        "z_bin": [0] * 8 + [1] * 4,
        "block_id": [10] * 4 + [11] * 4 + [20] * 2 + [21] * 2,
        "s_pair_1": np.ones(12),
        "s_pair_2": np.ones(12),
        "s_pair_3": np.ones(12),
    })
    BL._raw_qhat_by_cell(frame, "B8a")
    assert seen == [2, 2, 2, 2, 2, 2]

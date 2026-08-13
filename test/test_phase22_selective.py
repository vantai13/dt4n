"""Golden tests for cert.selective_conformal -- Phase 22 Lesson 22.4."""

import os

import numpy as np
import pandas as pd
import pytest

import cert.selective_conformal as SC
from cert.simultaneous_score import ALPHA


CALIB = "results/phase-22/calib_set_v3_poisson_0.925.parquet"
pytestmark = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu calib_set_v3")


@pytest.fixture(scope="module")
def split():
    df = pd.read_parquet(CALIB)
    return df, df[df["is_calib"]], df[~df["is_calib"]]


@pytest.fixture(scope="module")
def at_kappa1(split):
    _df, cal, te = split
    return {
        p: (f, SC.evaluate(te, f, 1.0))
        for p in SC.PROCEDURES
        for f in [SC.FITTERS[p](cal, 1.0)]
    }


def test_GS4_1_kappa0_reduces_to_21R(split):
    _df, cal, te = split
    base = SC.evaluate(te, SC.fit_none(cal, 0.0), 0.0)
    assert base["acceptance"] == 1.0
    for proc in ("fcr", "selective"):
        r = SC.evaluate(te, SC.FITTERS[proc](cal, 0.0), 0.0)
        assert r["acceptance"] == 1.0, proc
        assert r["violation_given_accept"] == pytest.approx(base["violation_marginal"], abs=1e-9), proc
        assert r["inflation"] == pytest.approx(1.0, abs=1e-9), proc


def test_GS4_2_none_reproduces_the_21R_failure(at_kappa1):
    _fit, r = at_kappa1["none"]
    assert r["violation_marginal"] == pytest.approx(0.0913, abs=2e-3)
    assert r["violation_given_accept"] == pytest.approx(0.1214, abs=2e-3)
    assert r["inflation"] == pytest.approx(1.330, abs=0.02)
    assert not r["pass_post_selection"]
    assert r["decision_failure_given_accept"] < ALPHA


def test_GS4_3_all_three_procedures_restore_post_selection_validity(at_kappa1):
    for proc in ("fcr", "mondrian", "selective"):
        _fit, r = at_kappa1[proc]
        assert r["violation_given_accept"] <= ALPHA, (proc, r["violation_given_accept"])
        assert r["pass_post_selection"], proc


def test_GS4_4_fcr_one_shot_is_not_self_consistent(split):
    _df, cal, te = split
    p0 = SC.evaluate(te, SC.fit_none(cal, 1.0), 1.0)["acceptance"]
    one_shot = SC.fit_fcr(cal, 1.0, max_iter=2)
    converged = SC.fit_fcr(cal, 1.0)
    assert converged["converged"]
    for g in converged["qhat"]:
        assert converged["qhat"][g] > one_shot["qhat"][g]
    r = SC.evaluate(te, converged, 1.0)
    assert r["acceptance"] < p0 / 2.0


def test_GS4_5_fcr_per_bin_collapses_and_says_so(split):
    _df, cal, _te = split
    fit = SC.fit_fcr(cal, 1.0, p_scope="per_bin")
    assert fit["degenerate"]
    assert fit["collapsed_bins"] == [3]
    assert not np.isfinite(fit["qhat"][3])
    assert SC.fit_fcr(cal, 1.0, p_scope="global")["converged"]
    with pytest.raises(ValueError):
        SC.fit_fcr(cal, 1.0, p_scope="whatever")


def test_GS4_6_selective_terminates_on_a_limit_cycle(split):
    _df, cal, _te = split
    fit = SC.fit_selective(cal, 1.0)
    assert fit["converged"]
    assert fit["n_iter"] < SC.MAX_ITER
    assert fit["cycle_len"] >= 1
    if fit["cycle_len"] > 1:
        cyc = [t["qhat"] for t in fit["trace"][-fit["cycle_len"]:]]
        for g, v in fit["qhat"].items():
            assert v == pytest.approx(max(c[int(g)] for c in cyc))


def test_GS4_7_mondrian_widens_only_the_top_mhat_bin(at_kappa1, split):
    _df, cal, _te = split
    base = SC.fit_none(cal, 1.0)["qhat"]
    q = at_kappa1["mondrian"][0]["_qhat_raw"]
    for (zb, mb), v in q.items():
        ratio = v / base[zb]
        if mb == 3:
            assert ratio > 1.05, (zb, mb, ratio)
        else:
            assert ratio < 1.00, (zb, mb, ratio)


def test_GS4_8_mondrian_is_the_cheapest_valid_procedure(at_kappa1):
    acc = {p: at_kappa1[p][1]["acceptance"] for p in SC.PROCEDURES}
    assert acc["mondrian"] > acc["selective"] > acc["fcr"]
    assert acc["mondrian"] > 0.85 * acc["none"]


def test_GS4_9_mondrian_inflation_is_below_one(at_kappa1):
    assert at_kappa1["mondrian"][1]["inflation"] < 1.0
    assert at_kappa1["none"][1]["inflation"] > 1.3


def test_GS4_10_protection_degrades_at_large_kappa(split):
    df, _cal, _te = split
    res = SC.run_grid(df, procedures=("mondrian",), kappas=(0.5, 1.0, 2.0))
    v = {r["kappa"]: r["violation_given_accept"] for r in res["results"]["mondrian"]}
    assert v[0.5] <= ALPHA and v[1.0] <= ALPHA
    assert v[2.0] > ALPHA

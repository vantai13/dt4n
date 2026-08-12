import numpy as np
import pandas as pd
import pytest

from cert import usefulness_v2 as U
from cert.conformal_v2 import split_blocks


def _synth(n_block=300, per_block=100, informative=True, seed=0):
    """m_hat large means lower error. If uninformative, the gate is useless."""
    rng = np.random.default_rng(seed)
    rows = []
    for block in range(n_block):
        for group in (0, 1):
            m_hat = rng.uniform(0.0, 40.0, per_block)
            s_margin = np.abs(rng.normal(0.0, 5.0 * (group + 1), per_block))
            if informative:
                wrong = s_margin > m_hat
            else:
                wrong = rng.random(per_block) < 0.22
            m_true = m_hat - np.where(wrong, s_margin + 0.1, -s_margin)
            rows.append(
                pd.DataFrame(
                    {
                        "block_id": block,
                        "z_bin": group,
                        "m_hat": m_hat,
                        "s_margin": s_margin,
                        "s_signed": m_hat - m_true,
                        "m_true": m_true,
                        "wrong": wrong,
                        "regret": np.where(wrong, s_margin, 0.0),
                        "viol_twin": wrong,
                        "viol_star": np.zeros(per_block, bool),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True)


def _fit(df):
    mask = split_blocks(df.block_id.to_numpy())
    return U.fit_qhat(df, mask), df[~mask].copy()


def test_U1_kappa0_is_anchor():
    df = _synth(seed=1)
    qhat, test = _fit(df)
    curve = U.risk_coverage(test, qhat)
    row = curve[curve.kappa == 0.0].iloc[0]
    assert row.acceptance_rate == pytest.approx(1.0)
    assert row.err_given_accept == pytest.approx(test.wrong.mean())


def test_U2_acceptance_monotone_decreasing():
    df = _synth(seed=2)
    qhat, test = _fit(df)
    acceptance = U.risk_coverage(test, qhat)["acceptance_rate"].to_numpy()
    assert np.all(np.diff(acceptance) <= 1e-12)


def test_U3_risk_monotone_decreasing():
    df = _synth(seed=3)
    qhat, test = _fit(df)
    risk = U.risk_coverage(test, qhat)["err_given_accept"].dropna().to_numpy()
    assert np.all(np.diff(risk) <= 1e-9)


def test_U4_uninformative_gate_gives_flat_curve():
    df = _synth(informative=False, seed=4)
    qhat, test = _fit(df)
    curve = U.risk_coverage(test, qhat).dropna(subset=["err_given_accept"])
    assert curve.err_given_accept.std() < 0.02
    assert U.discrimination(curve, 1.0)["ratio_reject_over_accept"] == pytest.approx(1.0, abs=0.2)


def test_U5_informative_gate_discriminates():
    df = _synth(informative=True, seed=5)
    qhat, test = _fit(df)
    curve = U.risk_coverage(test, qhat)
    assert U.discrimination(curve, 1.0)["ratio_reject_over_accept"] > 2.0


def test_U6_H7_passes_on_informative():
    df = _synth(seed=6)
    qhat, test = _fit(df)
    curve = U.risk_coverage(test, qhat)
    assert U.evaluate_H7(curve, float(test.wrong.mean()))["pass"]


def test_U7_H7_fails_on_uninformative():
    df = _synth(informative=False, seed=7)
    qhat, test = _fit(df)
    curve = U.risk_coverage(test, qhat)
    assert not U.evaluate_H7(curve, float(test.wrong.mean()))["pass"]


def test_U8_H7_not_applicable_on_degenerate():
    df = _synth(seed=8)
    qhat, test = _fit(df)
    result = U.evaluate_H7(U.risk_coverage(test, qhat), anchor_err=0.0)
    assert result["pass"] is None
    assert "suy bien" in result["reason"]


def test_U8b_PC1_passes_on_degenerate_zero_error():
    curve = pd.DataFrame({"kappa": [1.0], "acceptance_rate": [1.0], "err_given_accept": [0.0]})
    assert U.evaluate_PC1(curve, anchor_err=0.0)["pass"]
    assert U.evaluate_PC1(curve, anchor_err=0.2)["pass"] is None


def test_U9_G12_flags_too_easy():
    df = _synth(seed=9)
    qhat, test = _fit(df)
    curve = U.risk_coverage(test, qhat)
    assert U.evaluate_G12(curve)["pass"]
    fake = curve.copy()
    fake.loc[fake.kappa == 1.0, "acceptance_rate"] = 0.99
    assert not U.evaluate_G12(fake)["pass"]


def test_U10_post_selection_reported():
    df = _synth(seed=10)
    qhat, test = _fit(df)
    result = U.post_selection_diagnostics(test, qhat)
    for key in (
        "violation_marginal",
        "violation_given_accept",
        "p_mtrue_neg_given_accept",
        "median_slack_given_accept",
    ):
        assert key in result and np.isfinite(result[key])
    assert result["median_slack_given_accept"] >= 0.0


def test_U11_aurc_lower_is_better():
    good = _synth(informative=True, seed=11)
    bad = _synth(informative=False, seed=11)
    q_good, test_good = _fit(good)
    q_bad, test_bad = _fit(bad)
    assert U.aurc(U.risk_coverage(test_good, q_good)) < U.aurc(U.risk_coverage(test_bad, q_bad))


def test_U12_C2_nonbinding_when_eps_exceeds_regret():
    qhat = {0: 11.0, 1: 24.0}
    curve = pd.DataFrame({"kappa": [1.0], "regret_given_accept": [0.18]})
    result = U.c2_mapping(qhat, 3.2222, curve)
    assert result["nonbinding_at_kappa1"]
    assert all(0.0 < v < 1.0 for v in result["kappa_C2_by_bin"].values())

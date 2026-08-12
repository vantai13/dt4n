import numpy as np
import pandas as pd
import pytest

from cert import gate_report as G


def _df(n_block=200, per_block=100, seed=0, corr=-0.4):
    rng = np.random.default_rng(seed)
    n = n_block * per_block
    e_model = rng.normal(0.0, 2.0, n)
    e_stale = corr * e_model * 3.0 + rng.normal(0.0, 6.0, n)
    return pd.DataFrame(
        {
            "block_id": np.repeat(np.arange(n_block), per_block),
            "z_bin": rng.integers(0, 4, n),
            "e_model": e_model,
            "e_stale": e_stale,
        }
    )


def test_G5_identity_and_ci():
    result = G.decomposition_ci(_df(), n_boot=200)["pooled"]
    assert result["identity_ok"]
    assert np.isclose(result["share_model"] + result["share_stale"] + result["share_cov"], 1.0)
    assert result["rms_e_model_ci95"][0] < result["rms_e_model"] < result["rms_e_model_ci95"][1]


def test_G5_derives_columns_from_calibration_frame():
    rng = np.random.default_rng(1)
    n = 1000
    m_hat = rng.normal(10.0, 2.0, n)
    e_stale = rng.normal(0.0, 3.0, n)
    e_model = rng.normal(0.0, 1.0, n)
    df = pd.DataFrame(
        {
            "block_id": np.repeat(np.arange(50), n // 50),
            "m_hat": m_hat,
            "m_mid": m_hat + e_stale,
            "m_true": m_hat + e_stale + e_model,
        }
    )
    result = G.decomposition_ci(df, n_boot=100, by_bin=False)["pooled"]
    assert result["identity_ok"]
    assert result["rms_e_model"] == pytest.approx(np.sqrt(np.mean(e_model**2)), rel=1e-6)


def test_G5_detects_negative_cov():
    result = G.decomposition_ci(_df(corr=-0.6), n_boot=300)["pooled"]
    assert result["cov_e"] < 0.0
    assert result["cov_excludes_zero"]


def test_G5_detects_positive_cov():
    result = G.decomposition_ci(_df(corr=0.6), n_boot=300)["pooled"]
    assert result["cov_e"] > 0.0
    assert result["cov_excludes_zero"]


def test_scorecard_counts_and_causes():
    observed = {
        "qhat_B1_ms": 11.588,
        "qhat_B4_ms": 24.322,
        "ratio_B4_over_B1": 2.151,
        "p_accept_kappa1": 0.2835,
        "z_cross_s": 0.0069,
        "err_anchor": 0.220835,
    }
    score = G.score_predictions(observed)
    assert score["n_hit"] == 0
    assert score["n_miss"] == 6
    assert score["n_distinct_root_causes"] == 3
    assert score["n_distinct_root_cause_families"] == 2


def test_scorecard_does_not_mutate_intervals():
    before = [(p["lo"], p["hi"]) for p in G.PREDICTIONS]
    G.score_predictions({"err_anchor": 0.22})
    assert [(p["lo"], p["hi"]) for p in G.PREDICTIONS] == before


def test_measurement_floor_loss_dominates():
    floor = G.measurement_floor("poisson", 0.925, 3222.2447)
    assert floor["floor_total_ms"] == pytest.approx(1.485, rel=0.05)
    assert floor["loss_over_delay"] > 5.0


def test_gate_status_has_three_levels():
    df = G.collect_gates(
        {
            "gates": [
                {"id": "G2", "value": 0.0730, "threshold": 0.05},
                {"id": "G3", "value": 0.02, "threshold": 0.00868},
                {"id": "G5", "status": "INCOMPLETE"},
            ]
        }
    )
    assert set(df["status"]) == {"PASS_MARGINAL", "PASS", "INCOMPLETE"}


def test_limitations_complete():
    ids = [limitation["id"] for limitation in G.LIMITATIONS]
    assert ids == ["L%d" % i for i in range(1, 11)]
    assert all(limitation["scope"] and limitation["resolved_by"] for limitation in G.LIMITATIONS)

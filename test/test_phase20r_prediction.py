"""Tests for Phase 20R.3 pre-campaign prediction helpers."""

import json

import numpy as np
import pytest

from measurements import predict_err_quick as P


def test_prediction_from_arrays_detects_stale_argmin_and_sla_delta():
    c_hat = np.array(
        [
            [0.0, 10.0],
            [0.0, 10.0],
            [10.0, 0.0],
            [10.0, 0.0],
        ]
    )
    c_true = np.array(
        [
            [0.0, 10.0],
            [10.0, 0.0],
            [10.0, 0.0],
            [0.0, 10.0],
        ]
    )
    viol = np.array(
        [
            [False, True],
            [True, False],
            [False, True],
            [False, True],
        ]
    )

    out = P.prediction_from_arrays(c_hat, c_true, viol, dt=1.0, z_values=(0.0, 1.0))

    assert out["0.000"]["err"] == pytest.approx(0.5)
    assert out["0.000"]["d_sla"] == pytest.approx(0.5)
    assert out["1.000"]["err"] == pytest.approx(1.0)
    assert out["1.000"]["d_sla"] == pytest.approx(1.0 / 3.0)


def test_zero_pc1_prediction_covers_all_declared_z_values():
    pred = P.zero_pc1_prediction({"mode": "cbr", "rho_bar": 0.925, "a": 0.9, "sigma_rho": 0.0})

    assert sorted(pred["per_z"]) == sorted(P.z_key(z) for z in P.Z_ALL)
    assert all(row["err"] == 0.0 and row["d_sla"] == 0.0 for row in pred["per_z"].values())
    assert pred["spearman"]["note"] == "constant curve"


def test_model_error_summary_matches_phase_l_artifact():
    fit = P.load_fit()
    summary = P.model_error_summary(fit)["by_mode"]

    assert summary["poisson"]["e_model_pure_min_ms"] == pytest.approx(0.0580, abs=0.0001)
    assert summary["poisson"]["e_model_pure_max_ms"] == pytest.approx(0.0784, abs=0.0001)
    assert summary["h2"]["e_model_pure_min_ms"] == pytest.approx(0.0474, abs=0.0001)
    assert summary["h2"]["e_model_pure_max_ms"] == pytest.approx(0.0800, abs=0.0001)
    assert summary["cbr"]["e_model_pure_min_ms"] == pytest.approx(4.9802, abs=0.0001)
    assert summary["cbr"]["e_model_pure_max_ms"] == pytest.approx(6.2159, abs=0.0001)
    assert summary["poisson"]["topology_mean_resid_sd_ms_per_link"] == pytest.approx(0.2556, abs=0.0001)


def test_written_prediction_json_is_complete_and_h6_passes():
    with open(P.OUT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["phase"] == "20R.3"
    assert report["config"]["n"] == 200_000
    assert len(report["main"]) == 12
    assert report["scaling_law"]["h6_pre_campaign_pass"] is True
    assert report["scaling_law"]["max_spread"] < report["scaling_law"]["pass_threshold"]
    assert all(row.get("prediction") is not None for row in report["main"].values())

#!/usr/bin/env python3
"""Phase L / L.7 -- tests for link_model_v2 fitting helpers."""

import json

import pytest

from measurements.l7_fit import build_links, fit_from_state, pava_non_decreasing, reich_workload_from_timestamps
from mininet.load_spec import FRAME_BG
from twin.link_model_v2 import LinkModelV2, MonotonePchip, kingman_ceiling


def test_pava_projects_small_wiggles_to_monotone_curve():
    y = [0.14, 0.13, 0.20, 0.19]
    out = pava_non_decreasing(y, [1, 1, 1, 1])
    assert out == pytest.approx([0.135, 0.135, 0.195, 0.195])
    assert all(a <= b for a, b in zip(out, out[1:]))


def test_pchip_monotone_interpolation_stays_inside_neighbor_values():
    f = MonotonePchip([0.5, 0.7, 0.9], [1.0, 2.0, 5.0])
    vals = [f(0.5 + i * 0.01) for i in range(41)]
    assert vals[0] == pytest.approx(1.0)
    assert vals[-1] == pytest.approx(5.0)
    assert all(a <= b + 1e-12 for a, b in zip(vals, vals[1:]))


def _row(mode, bw, q, rho, seed, value, block="A", probe=20.0):
    return {
        "mode": mode,
        "bw": bw,
        "q": q,
        "rho": rho,
        "seed": seed,
        "q_mean_ms": value,
        "loss": 0.0,
        "probe_pps": probe,
        "block": block,
    }


def test_build_links_uses_individual_runs_for_residual_band_and_excludes_controls():
    rows = []
    rhos = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 1.00, 1.02, 1.05]
    for rho in rhos:
        for seed, jitter in [(11, -0.2), (12, 0.0), (13, 0.2)]:
            rows.append(_row("poisson", 6.0, 13, rho, seed, 10.0 * rho + jitter))
        rows.append(_row("poisson", 6.0, 13, rho, 99, 999.0, block="D", probe=0.0))
    links, report = build_links(rows)
    link = links["poisson|6|13"]
    assert link["resid_n_cv"] == (len(rhos) - 2) * 3
    assert link["resid_n_cv_edge"] == 2 * 3
    assert link["sigma_train"][0] == pytest.approx(0.2)
    assert link["noise_rms_ms"] == pytest.approx(((len(rhos) - 2) * 0.08 / ((len(rhos) - 2) * 3 - 1)) ** 0.5)
    assert "0.9" in link["sigma_by_rho"]
    assert "subcritical_rho_le_0.95" in link["band_by_regime"]
    assert 1.05 in link["heldout_extrapolated_rho"]
    assert len(report) == 1


def test_build_links_residual_band_contains_loo_model_bias():
    rows = []
    rhos = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 1.00, 1.02, 1.05]
    for rho in rhos:
        for seed, jitter in [(11, -0.003), (12, 0.0), (13, 0.003)]:
            rows.append(_row("poisson", 6.0, 13, rho, seed, 100.0 * rho * rho + jitter))
    links, _report = build_links(rows)
    link = links["poisson|6|13"]
    assert link["bias_rms_interior_ms"] > 0.0
    assert link["resid_sd_cv_interior_ms"] > link["noise_rms_ms"]
    assert link["model_efficiency"] < 0.9999


def test_reich_workload_for_cbr_equals_one_service_time_after_arrival():
    bw = 6.0
    service_s = FRAME_BG * 8.0 / (bw * 1e6)
    timestamps = [i * service_s / 0.9 for i in range(100)]
    out = reich_workload_from_timestamps(timestamps, bw, warmup_s=0.0)
    assert out["mean_ms"] == pytest.approx(service_s * 1000.0)


def test_link_model_v2_runtime_api_rejects_outside_domain(tmp_path):
    fit = {
        "links": {
            "poisson|6|13": {
                "rho_train": [0.5, 0.8, 1.0],
                "delay_train": [1.0, 2.0, 4.0],
                "loss_train": [0.0, 0.0, 0.1],
                "sigma_train": [0.1, 0.2, 0.4],
                "domain": [0.5, 1.0],
                "kingman": {"K": 0.1, "w_max": 3.0, "floor": 0.0, "r2": 0.9},
                "sigma_schedule": 0.2,
                "resid_sd": 0.25,
                "unreliable_rho_ranges": [],
            },
            "cbr|6|13": {
                "rho_train": [0.5, 0.95, 1.0, 1.05],
                "delay_train": [0.1, 0.1, 1.0, 24.0],
                "loss_train": [0.0, 0.0, 0.05, 0.1],
                "sigma_train": [0.01, 0.01, 7.0, 0.05],
                "domain": [0.5, 1.05],
                "kingman": {"K": 0.1, "w_max": 3.0, "floor": 0.0, "r2": 0.9},
                "sigma_schedule": 0.2,
                "resid_sd": 0.25,
                "unreliable_rho_ranges": [[0.95, 1.05]],
            }
        }
    }
    path = tmp_path / "fit.json"
    path.write_text(json.dumps(fit), encoding="utf-8")
    model = LinkModelV2.load(str(path))
    assert model.predict_delay("poisson", 6, 13, 0.8) == pytest.approx(2.0)
    assert model.predict_loss("poisson", 6, 13, 1.0) == pytest.approx(0.1)
    assert model.sigma("poisson", 6, 13, 0.8) == pytest.approx(0.2)
    assert model.model_efficiency("poisson", 6, 13) == pytest.approx(0.8)
    assert model.is_reliable("poisson", 6, 13, 0.98) is True
    assert model.is_reliable("cbr", 6, 13, 0.95) is True
    assert model.is_reliable("cbr", 6, 13, 0.98) is False
    assert model.is_reliable("cbr", 6, 13, 1.05) is True
    assert model.explain("poisson", 6, 13, 2.0)["delay_ms"] == pytest.approx(3.0)
    with pytest.raises(ValueError):
        model.predict_delay("poisson", 6, 13, 1.1)


def test_fit_from_state_writes_model_and_report_without_reich(tmp_path):
    rhos = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 1.00, 1.02, 1.05]
    rows = []
    idx = 0
    for mode, scale in [("cbr", 0.0), ("poisson", 5.0), ("h2", 10.0), ("onoff", 7.0)]:
        for rho in rhos:
            for seed in [11, 12, 13, 14, 15]:
                rows.append(
                    {
                        **_row(mode, 6.0, 13, rho, seed, 0.1 + scale * rho + 0.01 * (seed - 13)),
                        "idx": idx,
                        "pid": "p%d" % idx,
                        "gate_fail": [],
                        "socket_drops": 0,
                        "n_foreign": 0,
                        "rate_ratio": 1.0,
                        "rho_actual": rho,
                        "ca_actual": 1.0,
                    }
                )
                idx += 1
    state = {
        "rows": rows,
        "done_idx": [r["idx"] for r in rows],
        "sentinels": [{"q_mean_ms": 1.0}, {"q_mean_ms": 1.01}, {"q_mean_ms": 0.99}],
    }
    state_path = tmp_path / "state.json"
    out_path = tmp_path / "fit.json"
    reich_path = tmp_path / "reich.json"
    report_path = tmp_path / "report.md"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    fit = fit_from_state(
        str(state_path),
        str(out_path),
        str(reich_path),
        str(report_path),
        compute_reich=False,
    )
    assert out_path.exists()
    assert report_path.exists()
    assert fit["gates"]["G-L7d_sigma_present_pass"] is True
    assert "poisson|6|13" in fit["links"]


def test_kingman_ceiling_caps_at_finite_queue():
    assert kingman_ceiling(2.0, 1.0, 7.0, 0.5) == pytest.approx(7.5)

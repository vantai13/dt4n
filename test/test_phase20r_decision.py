"""Golden tests for Phase 20R measured decision-error helpers."""

import json

import numpy as np
import pandas as pd
import pytest

from measurements import additivity_check as A
from measurements import decision_error_v2 as D
from measurements import h9_separability as H9
from measurements import plot_decision_error_v2 as P
from measurements import quasistatic_check as Q
from twin import cost_v2 as C
from twin import topology_v7 as T7


def _mini_truth(tmp_path):
    rows = []
    for mode in ("poisson", "h2", "cbr"):
        for bw, q in {(float(v[0]), int(v[2])) for v in T7.LINKS.values()}:
            for rho in (0.5, 0.6, 0.7):
                rows.append(
                    {
                        "mode": mode,
                        "bw": bw,
                        "q": q,
                        "rho": rho,
                        "delay_mean_ms": 10.0 * rho + bw + q * 0.01,
                        "loss": 0.001 * rho,
                        "se_mean_ms": 0.01,
                        "source": "test",
                        "n_seed": 5,
                    }
                )
    table = pd.DataFrame(rows)
    table.attrs["truth_field"] = "q_mean_ms"
    path = tmp_path / "truth.parquet"
    table.to_parquet(path, index=False)
    return path, table


def test_truth_table_delay_loss_returns_exact_grid_value_plus_static_terms(tmp_path):
    path, table = _mini_truth(tmp_path)
    tt = D.TruthTable(str(path))
    link = "uA"
    bw, base, q = T7.LINKS[link]
    rho = 0.6
    delay, loss = tt.delay_loss("poisson", link, np.array([rho]))
    expected = table[
        (table["mode"] == "poisson")
        & (table["bw"] == float(bw))
        & (table["q"] == int(q))
        & (table["rho"] == rho)
    ].iloc[0]

    assert delay[0] - float(base) - C.serialization_ms(bw) == pytest.approx(expected["delay_mean_ms"], abs=1e-9)
    assert loss[0] == pytest.approx(expected["loss"], abs=1e-12)


def test_truth_table_clip_fraction_records_out_of_domain_rate(tmp_path):
    path, _table = _mini_truth(tmp_path)
    tt = D.TruthTable(str(path))

    tt.delay_loss("poisson", "uA", np.array([0.4, 0.55, 0.8]))

    assert tt.clip_log["poisson|uA"] == pytest.approx(2.0 / 3.0)


def test_error_decomposition_is_exact_identity():
    d_true = np.array([[3.0, 5.0], [4.0, 6.0], [7.0, 9.0], [9.0, 10.0]])
    d_fresh = np.array([[2.5, 4.0], [3.5, 5.5], [6.0, 8.0], [8.0, 9.5]])

    e_model, e_stale, total = D._decomposition(d_true, d_fresh, k=1)

    assert np.allclose(e_model + e_stale, total, atol=1e-9)


def test_check_z_grid_rejects_duplicate_lags_at_dt_0p2():
    with pytest.raises(ValueError, match="AoI aliasing"):
        D.check_z_grid([0.05, 0.10, 0.20], 0.2, require_sawtooth_age=False)


def test_scaled_z_values_follow_tau_ratios():
    assert D.z_values_for(tau=2.0, scaled=True) == pytest.approx((0.20, 0.60, 1.10, 2.00))


def test_parse_float_list_accepts_empty_and_values():
    assert D.parse_float_list("") == ()
    assert D.parse_float_list("0.65, 0.78,0.88") == pytest.approx((0.65, 0.78, 0.88))


def test_cost_margin_stats_uses_best_second_best_gap():
    cost = np.array([[1.0, 3.0, 2.0], [4.0, 1.0, 2.0], [0.0, 10.0, 4.0]])
    stats = D.cost_margin_stats(cost)
    margins = np.array([1.0, 1.0, 4.0])

    assert stats["margin_mean_ms"] == pytest.approx(float(margins.mean()))
    assert stats["margin_sd_ms"] == pytest.approx(float(margins.std(ddof=0)))
    assert stats["margin_cv"] == pytest.approx(float(margins.std(ddof=0) / margins.mean()))


def test_a_override_sets_sigma_from_sigma_max():
    cell = {"sigma_max": 0.25, "sigma_rho": 0.9}

    sigma, source = D.resolve_sigma(cell, a_override=0.2)

    assert sigma == pytest.approx(0.05)
    assert source == "a_override"


def test_margin_cv_bootstrap_from_block_moments_reports_observed_value():
    values = np.array([1.0, 2.0, 3.0, 4.0])
    means, seconds = D._margin_block_moments(values, block_len=2)

    stats = D.bootstrap_margin_cv_from_blocks(means, seconds, n_boot=10, seed=1)

    assert stats["margin_mean_ms"] == pytest.approx(float(values.mean()))
    assert stats["margin_cv"] == pytest.approx(float(values.std(ddof=0) / values.mean()))


def test_seed_mean_margin_cv_bootstrap_matches_seed_average_estimator():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([2.0, 2.0, 2.0, 2.0])
    blocks = [D._margin_block_moments(a, 2), D._margin_block_moments(b, 2)]

    stats = D.bootstrap_seed_mean_margin_cv(blocks, n_boot=10, seed=2)

    expected = 0.5 * (float(a.std(ddof=0) / a.mean()) + 0.0)
    assert stats["margin_cv"] == pytest.approx(expected)


def test_additivity_plan_matches_preregistered_day2_budget():
    plan = A.build_plan()

    assert plan["counts"] == {"A_table_cells": 9, "B_live_runs": 30, "C_live_runs": 45}
    assert plan["branch_b_paths"] == ["P1"]


def test_tost_equivalence_uses_90ci_inside_delta():
    out = A.tost_equivalence([0.01, 0.02, 0.0, -0.01, 0.01], delta_ms=0.44)

    assert out["equiv_pass"]
    assert out["power_ok"]


def test_quasistatic_analyze_checks_max_window_difference():
    rows = [
        {"seed": 101, "window_idx": 0, "measured_cost_ms": 10.10, "table_cost_ms": 10.00},
        {"seed": 101, "window_idx": 1, "measured_cost_ms": 10.20, "table_cost_ms": 10.00},
        {"seed": 102, "window_idx": 0, "measured_cost_ms": 9.90, "table_cost_ms": 10.00},
    ]

    report = Q.analyze(rows, seeds=(101, 102))

    assert report["summary"]["evaluated"]
    assert report["summary"]["max_abs_diff_ms"] == pytest.approx(0.2)
    assert report["summary"]["pass"]


def test_spearman_helper_does_not_require_scipy():
    assert P._spearman_no_scipy(pd.Series([1.0, 2.0, 3.0]), pd.Series([10.0, 20.0, 30.0])) == pytest.approx(1.0)


def test_h9_gaussian_gap_fit_recovers_synthetic_parameters():
    r = np.array([0.25, 0.35, 0.50, 0.70, 0.90])
    y = 2.0 * H9.phi_neg_over_r(0.8, r)

    fit = H9.fit_gaussian_gap(r, y, c_free=True)

    assert fit["k"] == pytest.approx(0.8, abs=0.002)
    assert fit["c"] == pytest.approx(2.0, rel=0.002)
    assert fit["mae"] < 1e-4


def test_h9_threshold_report_is_strict_about_nonzero_boundary():
    df = pd.DataFrame(
        [
            {"set": "x", "mode": "h2", "rho_bar": 0.9, "z_key": "0.550", "z_over_tau": 0.55, "tau_rho": 1.0, "margin_cv": 0.29, "err_total": 0.0},
            {"set": "x", "mode": "h2", "rho_bar": 0.96, "z_key": "0.550", "z_over_tau": 0.55, "tau_rho": 1.0, "margin_cv": 0.299, "err_total": 0.001},
        ]
    )

    report = H9.threshold_report(df, threshold=0.30)

    assert not report["pass_strict_zero"]
    assert report["n_low_nonzero"] == 1

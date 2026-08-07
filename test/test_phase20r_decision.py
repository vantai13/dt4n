"""Golden tests for Phase 20R measured decision-error helpers."""

import json
import math

import numpy as np
import pandas as pd
import pytest

from measurements import additivity_check as A
from measurements import additivity_live as AL
from measurements import decision_error_v2 as D
from measurements import h9_separability as H9
from measurements import plot_decision_error_v2 as P
from measurements import quasistatic_check as Q
from measurements import sentinel_loss_recheck as SL
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

    assert plan["counts"] == {
        "A_table_cells": 12,
        "Aprime_live_runs": 30,
        "B_live_runs": 30,
        "C_live_runs": 20,
    }
    assert [row["link"] for row in plan["tandem_links"]] == ["L1", "L2", "L3"]


def test_additivity_live_branch_plans_match_reduced_budget():
    seeds = (101, 102, 103, 104, 105)

    assert len(AL.build_plan("Aprime", modes=("poisson", "h2"), rho_bars=(0.925,), seeds=seeds)) == 30
    assert len(AL.build_plan("B", modes=("poisson", "h2"), rho_bars=(0.925,), seeds=seeds)) == 30
    assert len(AL.build_plan("C", modes=("poisson", "h2"), rho_bars=(0.85, 0.925), seeds=seeds)) == 20


def test_additivity_probe_budget_uses_phase_l_defaults():
    args = type("Args", (), {"probe_rate": AL.DEFAULT_PROBE_RATE_PPS, "probe_size": AL.DEFAULT_PROBE_SIZE_BYTES})()

    assert AL.DEFAULT_PROBE_RATE_PPS == pytest.approx(20.0)
    assert AL.DEFAULT_PROBE_SIZE_BYTES == 64
    assert A.PROBE_INTRUSION_MAX == pytest.approx(0.005)
    assert AL.probe_load_share(3, args) == pytest.approx(0.00424)
    assert AL.probe_load_share(3, args) < A.PROBE_INTRUSION_MAX


def test_additivity_analyze_checks_c_minus_sum_b():
    rows = []
    for seed in A.SEEDS:
        for link, cost in zip(("L1", "L2", "L3"), (1.0, 2.0, 3.0)):
            rows.append(
                {
                    "branch": "B",
                    "mode": "poisson",
                    "rho_bar": 0.925,
                    "seed": seed,
                    "link": link,
                    "cost_ms": cost,
                    "delay_ms": cost,
                    "probe_delay_ms": cost,
                    "trajectory_digest": "traj-%d" % seed,
                    "probe_intrusion_ratio": 0.001,
                }
            )
        rows.append(
            {
                "branch": "C",
                "mode": "poisson",
                "rho_bar": 0.925,
                "seed": seed,
                "path": "T123",
                "cost_ms": 5.9,
                "delay_ms": 5.9,
                "trajectory_digest": "traj-%d" % seed,
                "probe_intrusion_ratio": 0.001,
            }
        )

    report = A.analyze(rows, modes=("poisson",))
    g6 = [row for row in report["checks"] if row["contrast"] == "C_minus_sumB"]

    assert report["summary"]["g6_evaluated"]
    assert report["summary"]["g6_pass"]
    assert report["summary"]["g6a_delay_pass"]
    assert report["summary"]["g6_primary_contrast"] == "G6a_delay_C_minus_sumB"
    assert report["paired_schedule"]["pass"]
    assert g6[0]["mean_ms"] == pytest.approx(-0.1)


def test_tost_equivalence_uses_90ci_inside_delta():
    out = A.tost_equivalence([0.01, 0.02, 0.0, -0.01, 0.01], delta_ms=0.44)

    assert out["equiv_pass"]
    assert out["power_ok"]
    assert out["verdict"] == "PASS"


def test_tost_verdict_separates_power_problem_from_established_bias():
    wide = A.tost_equivalence([-6.0, 6.0, -5.0, 5.0, 0.0], delta_ms=0.5)
    biased = A.tost_equivalence([-9.0, -9.1, -8.9, -9.05, -8.95], delta_ms=0.5)

    # CI straddles zero but is far wider than delta: underpowered, NOT a bias.
    assert wide["verdict"] == "INCONCLUSIVE"
    assert not wide["bias_detected"]
    assert not wide["power_ok"]

    # CI lies entirely outside +-delta: non-equivalence is established.
    assert biased["verdict"] == "FAIL"
    assert biased["bias_detected"]
    assert biased["power_ok"]


def test_tost_propagates_reference_standard_error():
    samples = [0.10, 0.12, 0.08, 0.11, 0.09]
    without = A.tost_equivalence(samples, delta_ms=0.44)
    with_ref = A.tost_equivalence(samples, delta_ms=0.44, ref_se=0.30, ref_df=4.0)

    assert with_ref["mean_ms"] == pytest.approx(without["mean_ms"])
    assert with_ref["se_ms"] == pytest.approx(math.hypot(without["se_sample_ms"], 0.30))
    # Ignoring branch-A uncertainty understates the interval (RC5).
    assert with_ref["ci90_hi_ms"] > without["ci90_hi_ms"]
    assert with_ref["equiv_pass"] is False and without["equiv_pass"] is True


def test_tcrit_fallback_is_conservative_for_untabulated_df():
    assert A.tcrit_95(22) >= A.tcrit_95(24)
    assert A.tcrit_95(200) == pytest.approx(1.644854)


def _aprime_rows(link_costs, seeds=A.SEEDS, mode="poisson"):
    rows = []
    for seed in seeds:
        for link, cost in zip(("L1", "L2", "L3"), link_costs):
            rows.append(
                {
                    "branch": "Aprime",
                    "mode": mode,
                    "rho_bar": 0.925,
                    "seed": seed,
                    "link": link,
                    "cost_ms": cost,
                    "delay_ms": cost,
                    "loss": 0.0,
                    "probe_intrusion_ratio": 0.001,
                }
            )
    return rows


def test_topology_transfer_primary_estimand_is_path_level():
    a = pd.DataFrame(A.branch_a_link_rows(modes=("poisson",), rho_bars=(0.925,)))
    a_costs = a.set_index("link")["cost_ms"]
    offset = 0.05
    rows = _aprime_rows([float(a_costs[link]) + offset for link in ("L1", "L2", "L3")])

    report = A.analyze(rows, modes=("poisson",))
    path = [row for row in report["checks"] if row["contrast"] == "Aprime_minus_A_path"]
    link = [row for row in report["checks"] if row["contrast"] == "Aprime_minus_A"]

    assert report["summary"]["topology_transfer_primary_contrast"] == "Aprime_minus_A_path"
    assert report["summary"]["topology_transfer_link_role"] == "diagnostic"
    assert all(row["role"] == "diagnostic" for row in link)
    assert len(path) == 1
    assert path[0]["role"] == "primary"
    # Path delta is the sum over the three links, tested against the path margin.
    assert path[0]["mean_ms"] == pytest.approx(3.0 * offset)
    assert path[0]["delta_ms"] == pytest.approx(A.N_LINKS_IN_PATH * link[0]["delta_ms"])
    # Path loss composes nonlinearly, so link SEs enter through the partials
    # d(path_loss)/d(l_i) = prod_{j != i}(1 - l_j), not as a plain RSS of costs.
    loss = a["loss"].to_numpy(float)
    partial = np.array([float(np.prod(np.delete(1.0 - loss, i))) for i in range(len(loss))])
    se_path_loss = math.sqrt(float(((partial * a["se_loss"].to_numpy(float)) ** 2).sum()))
    se_path_delay = math.sqrt(float((a["se_delay_ms"].to_numpy(float) ** 2).sum()))
    w_loss = float(a["w_loss"].iloc[0])
    assert path[0]["ref_se_ms"] == pytest.approx(
        math.hypot(se_path_delay, w_loss * se_path_loss), rel=1e-9
    )
    # The partials are < 1, so ignoring the composition overstates the reference SE.
    assert path[0]["ref_se_ms"] < math.sqrt(float((a["se_cost_ms"] ** 2).sum()))


def test_branch_a_cost_se_includes_the_loss_term():
    a = pd.DataFrame(A.branch_a_link_rows(modes=("h2",), rho_bars=(0.925,)))

    assert a["se_cost_includes_loss"].all()
    # w_loss is O(1e3), so the loss term dominates the branch-A cost uncertainty.
    assert (a["se_loss"] > 0).all()
    assert (a["se_cost_ms"] > a["se_delay_ms"]).all()
    for _idx, row in a.iterrows():
        assert row["se_cost_ms"] == pytest.approx(
            math.hypot(row["se_delay_ms"], row["w_loss"] * row["se_loss"])
        )


def test_truth_loss_se_returns_zero_when_campaign_state_is_absent(tmp_path):
    table = A.TruthLossSE(str(tmp_path / "nope.json"))

    assert not table.available
    assert table.se("h2", "uA", 0.9) == 0.0
    assert table.df("h2", "uA") == 0.0


def test_topology_transfer_path_drops_seeds_missing_a_link():
    rows = [row for row in _aprime_rows([5.0, 6.0, 7.0]) if not (row["seed"] == A.SEEDS[0] and row["link"] == "L3")]

    report = A.analyze(rows, modes=("poisson",))
    path = [row for row in report["checks"] if row["contrast"] == "Aprime_minus_A_path"]

    assert path[0]["n"] == len(A.SEEDS) - 1


def test_sentinel_drift_uses_the_two_sample_statistic():
    ref = {"mean": 10.868010, "sd": 0.014864, "se": 0.003410}
    today = [10.9111, 10.8886, 10.9199, 10.8967]

    out = SL.z_score(today, ref)

    # A mean-of-n divided by the sd of a SINGLE run understates the shift, so the
    # single-run reading must not be what decides drift.
    assert abs(out["z_mean"]) < SL.Z_ALERT
    assert abs(out["z_welch"]) > SL.Z_ALERT
    assert out["drift"] is True


def test_sentinel_summary_drops_gate_failed_replicates():
    ref = {"loss": {"mean": 0.063904, "sd": 0.000128, "se": 0.000029},
           "q_mean_ms": {"mean": 10.868010, "sd": 0.014864, "se": 0.003410}}
    rows = [
        {"loss": 0.063900, "q_mean_ms": 10.868, "gate_fail": [], "vl1g_run_pass": True, "direct_packets_delta": 0},
        {"loss": 0.063910, "q_mean_ms": 10.869, "gate_fail": [], "vl1g_run_pass": True, "direct_packets_delta": 0},
        {"loss": 0.090000, "q_mean_ms": 14.000, "gate_fail": ["late=0.0012"], "vl1g_run_pass": True, "direct_packets_delta": 0},
    ]

    summary = SL.summarize(rows, ref)

    assert summary["n_run"] == 3 and summary["n_clean"] == 2
    assert summary["loss"]["mean"] == pytest.approx(0.063905)
    assert summary["verdict"] == "STABLE"


def test_sentinel_summary_flags_a_runtime_direct_packet():
    ref = {"loss": {"mean": 0.063904, "sd": 0.000128, "se": 0.000029},
           "q_mean_ms": {"mean": 10.868010, "sd": 0.014864, "se": 0.003410}}
    rows = [{"loss": 0.0639, "q_mean_ms": 10.868, "gate_fail": [], "vl1g_run_pass": False, "direct_packets_delta": 1}]

    summary = SL.summarize(rows, ref)

    assert summary["n_clean"] == 0
    assert summary["max_direct_packets_delta"] == 1
    assert not summary["evaluated"]


def test_worst_verdict_ranks_fail_above_inconclusive():
    assert A.worst_verdict([{"verdict": "PASS"}, {"verdict": "INCONCLUSIVE"}]) == "INCONCLUSIVE"
    assert A.worst_verdict([{"verdict": "FAIL"}, {"verdict": "INCONCLUSIVE"}]) == "FAIL"
    assert A.worst_verdict([]) is None


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

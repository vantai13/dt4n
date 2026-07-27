#!/usr/bin/env python3
"""Pure tests for Phase 20 decision-error measurement helpers."""

import json

import numpy as np
import pytest

from measurements import decision_error as DE
from twin import topology_v7 as T7


def test_vectorized_cost_matches_topology_scalar_model():
    rho_row = {link: T7.LOAD_MEAN[link] for link in T7.LINK_NAMES}
    rho = np.array([[rho_row[link] for link in T7.LINK_NAMES]], dtype=float)

    delay, loss, cost = DE.build_cost_tables(rho, w_loss=1445.0)

    for a, path in enumerate(T7.PATH_NAMES):
        scalar_delay, scalar_loss = T7.path_delay_loss(rho_row, path)
        assert delay[0, a] == pytest.approx(scalar_delay)
        assert loss[0, a] == pytest.approx(scalar_loss)
        assert cost[0, a] == pytest.approx(T7.path_cost(rho_row, path, w_loss=1445.0))


def test_decide_uses_eps_tie_band_lowest_index():
    costs = np.array([
        [1.0 + 5e-10, 1.0, 2.0, 3.0],
        [3.0, 2.0, 1.0, 1.0 + 2e-9],
    ])

    actions, ties = DE.decide(costs)

    assert actions.tolist() == [0, 2]
    assert ties.tolist() == [True, False]


def test_sawtooth_age_steps_is_deterministic():
    age = DE.sawtooth_age_steps(6, dt_s=0.1, sync_period_s=0.5, d_sync_s=0.1)
    assert age.tolist() == [5, 1, 2, 3, 4, 5]


def test_reference_sawtooth_mean_age_matches_phase20_grid():
    assert DE.reference_sawtooth_mean_age_s(
        sync_period_s=0.5,
        d_sync_s=0.051,
        reference_dt_s=0.010,
    ) == pytest.approx(0.305)


def test_check_z_grid_rejects_duplicate_lags_on_coarse_measured_grid():
    with pytest.raises(ValueError, match="AoI aliasing"):
        DE.check_z_grid(
            [0.0, 0.05, 0.10, 0.20, 0.298],
            dt_s=0.200,
            require_sawtooth_age=False,
        )


def test_check_z_grid_rejects_sawtooth_on_coarse_measured_grid():
    with pytest.raises(ValueError, match="distinct sawtooth age levels"):
        DE.check_z_grid(
            [0.0, 0.2, 0.4, 0.6, 1.0],
            dt_s=0.200,
            sync_period_s=0.5,
            d_sync_s=0.051,
            require_sawtooth_age=True,
        )


def test_check_z_grid_allows_bracket_mode_on_representable_z_values():
    result = DE.check_z_grid(
        [0.0, 0.2, 0.4, 0.6, 1.0],
        dt_s=0.200,
        sync_period_s=0.5,
        d_sync_s=0.051,
        require_sawtooth_age=False,
    )

    assert result["z_steps"] == [0, 1, 2, 3, 5]
    assert result["sawtooth_age_levels"] < 10


def test_crossed_fixed_z_detects_threshold_side_change():
    rho = np.full((4, len(T7.LINK_NAMES)), 0.80)
    ac = T7.LINK_NAMES.index("ac")
    rho[0, ac] = T7.JUMPS[0] - 0.01
    rho[1, ac] = T7.JUMPS[0] + 0.01
    rho[2, ac] = T7.JUMPS[0] + 0.02
    rho[3, ac] = T7.JUMPS[0] - 0.02

    crossed = DE.crossed_fixed_z(rho, rows=np.array([1, 2, 3]), z_steps=1)

    assert crossed.tolist() == [True, False, True]


def test_block_bootstrap_uses_common_block_draws_for_pairwise_delta():
    a = np.r_[np.zeros(50), np.ones(50)]
    arrays = {
        "base_violation": np.zeros(100),
        "err:0.000": a,
        "err:0.100": a.copy(),
        "twin_violation:0.000": a,
        "twin_violation:0.100": a.copy(),
    }

    result = DE.block_bootstrap(arrays, tau_core_s=0.002, dt_s=0.01, n_boot=50, seed=0)

    delta = result["pairwise_err_delta"]["0.100-0.000"]
    assert delta["mean"] == pytest.approx(0.0)
    assert delta["ci_lo"] == pytest.approx(0.0)
    assert delta["ci_hi"] == pytest.approx(0.0)
    assert delta["ci_bonferroni"]["lo"] == pytest.approx(0.0)
    assert delta["ci_bonferroni"]["hi"] == pytest.approx(0.0)


def test_spearman_one_sided_exact_for_monotone_curve():
    result = DE.spearman_one_sided([0, 1, 2, 3], [0.0, 0.1, 0.2, 0.3])
    assert result["rho"] == pytest.approx(1.0)
    assert result["p_one_sided"] == pytest.approx(1.0 / 24.0)


def test_interpolate_per_z_metric_uses_effective_z_seconds():
    per_z = {
        "0.298": {"effective_z_s": 0.30, "err": 0.10, "d_sla": 0.05},
        "0.500": {"effective_z_s": 0.50, "err": 0.20, "d_sla": 0.09},
    }

    result = DE.interpolate_per_z_metric(per_z, "err", target_s=0.305)

    assert result["value"] == pytest.approx(0.1025)
    assert result["lo_key"] == "0.298"
    assert result["hi_key"] == "0.500"


def test_load_frozen_calibration_from_decision_error_output(tmp_path):
    path = tmp_path / "decision_error.json"
    path.write_text(
        json.dumps({"config": {"calibration": {"w_loss": 12, "t_delay_ms": 3.4, "t_loss": 0.01}}}),
        encoding="utf-8",
    )

    calibration = DE.load_frozen_calibration(str(path))

    assert calibration["w_loss"] == pytest.approx(12.0)
    assert calibration["t_delay_ms"] == pytest.approx(3.4)
    assert calibration["t_loss"] == pytest.approx(0.01)


def test_gate_g3_uses_pairwise_bonferroni_not_spearman_p_value():
    evaluation = {
        "per_z": {
            "0.000": {"z_s": 0.0, "err": 0.0},
            "0.100": {"z_s": 0.1, "err": 0.1},
        }
    }
    bootstrap = {
        "err": {"operational": {"ci_lo": 0.10, "ci_hi": 0.20}},
        "d_sla": {"operational": {"ci_lo": 0.04, "ci_hi": 0.08}},
        "pairwise_err_delta": {
            "0.100-0.000": {
                "mean": 0.1,
                "se": 0.01,
                "z_score": 10.0,
                "ci_lo": 0.08,
                "ci_hi": 0.12,
                "ci_bonferroni": {"lo": 0.07, "hi": 0.13, "alpha": 0.05, "level": 0.95},
            }
        },
    }

    gate = DE.gate_summary(
        evaluation,
        bootstrap,
        nc={"all_pass": True},
        mechanism={"operational": {"P3_prime_pass": True}},
    )

    assert gate["G3_pairwise_err_delta_bonferroni_positive"] is True
    assert "p_one_sided" not in gate["spearman_descriptive_only"]

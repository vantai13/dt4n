#!/usr/bin/env python3
"""Guard tests for Lesson 20R.7 mechanism estimands."""

from measurements import decision_error_v2 as D
from measurements import mechanism_map as M
from twin import cost_v2 as C
from twin import topology_v7 as T7
import pytest


def test_path_loss_sensitivity_uniform_p():
    loss = {link: 0.1 for link in T7.LINK_NAMES}

    for path in T7.PATH_NAMES:
        assert M.path_loss_sensitivity(loss, path) == pytest.approx(3.0 * (1.0 - 0.1) ** 2)


def test_gradient_includes_loss_term():
    tt = D.TruthTable()
    rho = C.rho_vector(0.925)

    g_full = M.grad_cost(tt, "poisson", "ad", rho["ad"], w_loss=3222.244681647411)
    g_delay_only = M.grad_cost(tt, "poisson", "ad", rho["ad"], w_loss=0.0)

    assert abs(g_full) > 2.0 * abs(g_delay_only)


def test_clipped_negative_common_mode_matches_scan_k4_bracket():
    report = M.build_report(rho_bar=0.925, modes=("poisson",))
    row = report["modes"][0]
    best = row["clipped_negative_loss_shift"][0]
    scan = row["scan_cascade_loss_common_mode"]["r_star_bracket"]

    assert best["pair"] == ["P1", "P3"]
    assert scan["r_star_lo"] <= best["first_r_star_path"] <= scan["r_star_hi"]


def test_unclipped_first_order_is_not_the_k4_mechanism_under_clipping():
    report = M.build_report(rho_bar=0.925, modes=("poisson",))
    row = report["modes"][0]
    best = row["first_order_unclipped"][0]

    assert best["pair"] != ["P1", "P3"]
    assert best["r_star_path"] > 1.0

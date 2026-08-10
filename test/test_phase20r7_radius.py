#!/usr/bin/env python3
"""Guard tests for the Lesson 20R.7 decision-margin radius (Amendment 17)."""

import numpy as np
import pytest

from measurements import decision_error_v2 as D
from measurements import margin_radius as MR
from measurements import mechanism_map as MM
from twin import cost_v2 as C
from twin import topology_v7 as T7


def test_slope_is_the_exact_segment_slope():
    tt = D.TruthTable()
    li = MR.LinkInterp(tt, "poisson", "uA")
    k = 15
    mid = 0.5 * (li.grid[k] + li.grid[k + 1])
    expected = (li.loss[k + 1] - li.loss[k]) / (li.grid[k + 1] - li.grid[k])

    _d, _l, _dd, dl = li.evaluate(np.array([mid]))

    assert dl[0] == pytest.approx(expected, rel=1e-12)


def test_values_match_the_truth_table_including_static_terms():
    tt = D.TruthTable()
    li = MR.LinkInterp(tt, "poisson", "ad")
    rho = np.array([0.72, 0.8375, 0.9875])

    delay, loss, _dd, _dl = li.evaluate(rho)
    ref_delay, ref_loss = tt.delay_loss("poisson", "ad", rho)

    assert np.allclose(delay, ref_delay, atol=1e-12)
    assert np.allclose(loss, ref_loss, atol=1e-12)


def test_outside_the_domain_the_slope_is_zero_and_counted():
    tt = D.TruthTable()
    li = MR.LinkInterp(tt, "poisson", "uA")

    _d, _l, dd, dl = li.evaluate(np.array([li.hi + 0.05]))

    assert dd[0] == 0.0 and dl[0] == 0.0
    assert li.report()["n_out_of_domain"] == 1


def _interps(mode="poisson"):
    tt = D.TruthTable()
    return tt, {link: MR.LinkInterp(tt, mode, link) for link in T7.LINK_NAMES}


def test_path_cost_matches_the_truth_table_path_tables():
    tt, interps = _interps()
    rho_mat = np.tile(np.array([C.rho_vector(0.925)[link] for link in T7.LINK_NAMES]), (4, 1))
    w_loss = MM.DEFAULT_W_LOSS["poisson"]

    cost, _grad, _diag = MR.path_cost_and_grad(interps, rho_mat, w_loss)
    _d, _l, ref = tt.path_tables("poisson", rho_mat, w_loss)

    assert np.allclose(cost, ref, atol=1e-10)


def test_gradient_is_zero_on_links_not_used_by_the_path():
    _tt, interps = _interps()
    rho_mat = np.tile(np.array([C.rho_vector(0.90)[link] for link in T7.LINK_NAMES]), (3, 1))

    _cost, grad, _diag = MR.path_cost_and_grad(interps, rho_mat, 3000.0)

    for a, path in enumerate(T7.PATH_NAMES):
        for i, link in enumerate(T7.LINK_NAMES):
            if link not in T7.PATHS[path]:
                assert np.all(grad[:, a, i] == 0.0)


def test_gradient_is_dominated_by_the_loss_channel_at_high_rho():
    _tt, interps = _interps()
    rho_mat = np.tile(np.array([C.rho_vector(0.925)[link] for link in T7.LINK_NAMES]), (2, 1))

    _c0, g0, _ = MR.path_cost_and_grad(interps, rho_mat, 0.0)
    _c1, g1, _ = MR.path_cost_and_grad(interps, rho_mat, MM.DEFAULT_W_LOSS["poisson"])

    assert np.linalg.norm(g1) > 5.0 * np.linalg.norm(g0)


def test_margin_is_non_negative_and_bound_radius_is_conservative():
    _tt, interps = _interps()
    rng = np.random.default_rng(7)
    rho_mat = 0.90 + 0.02 * rng.standard_normal((500, len(T7.LINK_NAMES)))

    cost, grad, _diag = MR.path_cost_and_grad(interps, rho_mat, 3222.24)
    out = MR.radius_series(cost, grad)

    assert np.all(out["margin_ms"] >= -1e-12)
    finite = np.isfinite(out["r_bound"]) & np.isfinite(out["r_exact"])
    assert np.all(out["r_bound"][finite] <= out["r_exact"][finite] + 1e-12)


def test_radius_uses_the_per_cell_w_loss_not_the_0925_constant():
    tt = D.TruthTable()
    cells = {(str(c["mode"]), float(c["rho_bar"])): c for c in D.measurement_cells()}
    cell = cells[("poisson", 0.7)]

    out = MR.cell_radius(tt, cell, seeds=(101,), n=2000)

    assert out["w_loss"] == pytest.approx(float(cell["w_loss"]))
    assert out["w_loss"] != pytest.approx(MM.DEFAULT_W_LOSS["poisson"])


def test_spearman_negative_detects_a_perfect_decreasing_relation():
    out = MR.spearman_negative([1.0, 2.0, 3.0, 4.0, 5.0], [9.0, 7.0, 5.0, 3.0, 1.0])

    assert out["rho"] == pytest.approx(-1.0)
    assert out["p_one_sided_negative"] == pytest.approx(1.0 / 120.0)


def test_spearman_negative_does_not_reward_the_wrong_direction():
    out = MR.spearman_negative([1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 3.0, 5.0, 7.0, 9.0])

    assert out["rho"] == pytest.approx(1.0)
    assert out["p_one_sided_negative"] > 0.9


def test_err_summary_has_the_eight_non_cbr_cells_at_the_operating_z():
    err = MR.load_err(z=MR.Z_OPERATING)

    assert len(err) == 8
    assert {mode for mode, _rho in err} == set(MR.MODES)

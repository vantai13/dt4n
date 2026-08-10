#!/usr/bin/env python3
"""Guard tests for the Lesson 20R.7 mechanism maps (Amendment 16).

The point of these tests is not that the code runs. It is that the estimator
cannot silently drift back into the grid-artifact regime that Amendment 16 was
written to close.
"""

import numpy as np
import pytest

from measurements import decision_error_v2 as D
from measurements import mechanism_map as MM
from measurements import mechanism_maps as M


def test_nonuniform_weights_reduce_to_uniform():
    h = 0.02
    w1 = M.d1_weights(h, h)
    w2 = M.d2_weights(h, h)

    assert w1 == pytest.approx((-1.0 / (2 * h), 0.0, 1.0 / (2 * h)))
    assert w2 == pytest.approx((1.0 / h**2, -2.0 / h**2, 1.0 / h**2))


def test_stencil_is_exact_on_a_quadratic_even_on_a_ragged_grid():
    # f(x) = 3x^2 - 5x + 7  ->  f' = 6x - 5, f'' = 6
    x = np.array([0.10, 0.34, 0.41])
    f = 3 * x**2 - 5 * x + 7
    hm, hp = float(x[1] - x[0]), float(x[2] - x[1])

    d1 = M.apply_weights(M.d1_weights(hm, hp), f)
    d2 = M.apply_weights(M.d2_weights(hm, hp), f)

    assert d1 == pytest.approx(6 * x[1] - 5)
    assert d2 == pytest.approx(6.0)


def test_second_derivative_of_a_straight_line_is_zero():
    x = np.array([0.5, 0.52, 0.54])
    f = 4.0 * x + 1.0
    hm, hp = float(x[1] - x[0]), float(x[2] - x[1])

    assert M.apply_weights(M.d2_weights(hm, hp), f) == pytest.approx(0.0, abs=1e-9)


def test_sub_grid_h_on_the_real_table_is_a_grid_artifact():
    """h < grid step turns d2 into a readout of knot placement."""
    curves = M.load_curves()
    curve = curves[("poisson", 8.0, 18)]
    grid, loss = curve["rho"], curve["loss"]
    step = M.grid_step(grid)
    assert step is not None

    h_bad = 0.5 * step
    f = lambda r: float(np.interp(r, grid, loss))

    def d2(r):
        return (f(r + h_bad) - 2 * f(r) + f(r - h_bad)) / h_bad**2

    midpoints = [float(a + 0.5 * step) for a in grid[8:-2]]
    knots = [float(a) for a in grid[9:-2]]

    assert all(abs(d2(r)) < 1e-9 for r in midpoints)
    assert any(abs(d2(r)) > 1e-3 for r in knots)


def test_node_evaluation_never_leaves_the_measured_domain():
    curves = M.load_curves()
    step = M.common_grid_step(curves)

    for stride in (1, 2):
        rows = M.build_rows(curves, stride=stride)
        for (mode, bw, q), curve in curves.items():
            cell = [r for r in rows if (r["mode"], r["bw"], r["q"]) == (mode, bw, q)]
            assert cell
            lo = float(curve["rho"].min()) + stride * step
            hi = float(curve["rho"].max()) - stride * step
            assert min(r["rho"] for r in cell) >= lo - 1e-12
            assert max(r["rho"] for r in cell) <= hi + 1e-12


def test_node_values_match_the_truth_table_exactly():
    curves = M.load_curves()
    out = M.crosscheck_truth_table(curves)

    assert out["n_nodes_checked"] > 0
    assert out["max_abs_diff"] == pytest.approx(0.0, abs=1e-12)


def test_cost_gradient_is_delay_plus_w_loss_times_loss():
    rows = M.build_rows(M.load_curves(), stride=1)

    for row in rows:
        expected = row["d1_delay_ms"] + row["w_loss"] * row["d1_loss"]
        assert row["d1_cost_ms"] == pytest.approx(expected, rel=1e-12, abs=1e-12)
        assert row["w_loss"] == pytest.approx(MM.DEFAULT_W_LOSS[row["mode"]])


def test_cbr_is_out_of_scope():
    rows = M.build_rows(M.load_curves(), stride=1)

    assert {r["mode"] for r in rows} <= set(M.MODES)
    assert "cbr" not in {r["mode"] for r in rows}
    assert "cbr" in M.excluded_modes()


def test_static_link_terms_do_not_enter_the_gradient():
    """base delay and serialization are constant in rho, so maps use queue delay."""
    tt = D.TruthTable()
    curves = M.load_curves()
    curve = curves[("poisson", 6.0, 13)]
    q_delay, _loss = tt.queue_delay_loss("poisson", 6.0, 13, curve["rho"])

    assert np.allclose(q_delay, curve["qdelay_ms"], atol=1e-12)


def test_zero_drop_cell_still_gets_a_positive_error_bar():
    out = M.loss_uncertainty(0.0, 60000.0)

    assert out["x_drop"] == 0.0
    assert out["se_wald"] == pytest.approx(0.0)
    assert out["se_ac"] > 0.0


def test_error_propagation_matches_the_weighted_quadrature():
    w = M.d2_weights(0.02, 0.02)
    se = (1e-4, 2e-4, 1e-4)
    expected = float(np.sqrt(sum((wi * si) ** 2 for wi, si in zip(w, se))))

    assert M.propagate_se(w, se) == pytest.approx(expected)


def test_significance_flag_uses_the_preregistered_threshold():
    rows = M.build_rows(M.load_curves(), stride=1)

    for row in rows:
        assert row["significant_d2_loss"] == (abs(row["d2_loss"]) > M.SIG_K * row["se_d2_loss"])

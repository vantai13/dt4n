#!/usr/bin/env python3
"""Guard tests for the Lesson 20R.7 prediction adjudication (Amendment 18)."""

import numpy as np
import pytest

from measurements import decision_error_v2 as D
from measurements import margin_radius as MR
from measurements import mechanism_predictions as P
from twin import cost_v2 as C
from twin import topology_v7 as T7


def test_link_curve_has_no_single_rho_bar_preimage():
    """Why P2 needed the path level: one (bw, q) curve serves many offsets."""
    sharing = [link for link in T7.LINK_NAMES if T7.LINKS[link][0] == 6.0 and T7.LINKS[link][2] == 13]
    offsets = {round(C.LINK_OFFSET[link], 6) for link in sharing}

    assert len(sharing) > 1
    assert len(offsets) > 1


def test_feasible_window_keeps_every_link_inside_its_domain():
    tt = D.TruthTable()
    h = 0.02
    lo, hi = P.feasible_rho_bar(tt, "poisson", h)

    for link in T7.LINK_NAMES:
        bw, _base, q = T7.LINKS[link]
        grid = tt.curves[("poisson", float(bw), int(q))][0]
        assert lo + C.LINK_OFFSET[link] - h >= float(grid.min()) - 1e-12
        assert hi + C.LINK_OFFSET[link] + h <= float(grid.max()) + 1e-12


def test_curvature_map_never_clips():
    tt = D.TruthTable()
    tt.reset_clip_log()
    P.path_curvature_map(tt, "poisson", h=0.02, step=0.02)

    assert max(tt.clip_log.values()) == pytest.approx(0.0)


def test_off_node_second_difference_interpolates_the_node_values():
    """For piecewise-linear f, D(knot + t*h) = (1-t)*D_k + t*D_{k+1}."""
    h = 0.02
    x = np.arange(0.50, 0.98 + 1e-12, h)
    y = np.array(
        [
            0.0,
            0.0,
            0.0,
            0.1,
            0.3,
            0.9,
            1.4,
            2.4,
            3.0,
            4.5,
            6.0,
            9.0,
            12.0,
            16.0,
            21.0,
            27.0,
            34.0,
            42.0,
            51.0,
            61.0,
            72.0,
            84.0,
            97.0,
            111.0,
            126.0,
        ]
    )[: x.size]
    f = lambda r: np.interp(r, x, y)

    def d2(r):
        return (f(r + h) - 2 * f(r) + f(r - h)) / h**2

    k = 10
    node_k = d2(x[k])
    node_k1 = d2(x[k + 1])
    for t in (0.25, 0.5, 0.75):
        assert d2(x[k] + t * h) == pytest.approx((1 - t) * node_k + t * node_k1, rel=1e-9)


def test_path_loss_matches_the_direct_composition():
    tt = D.TruthTable()
    rb = np.array([0.80, 0.90])
    got = P.path_loss_at(tt, "poisson", "P1", rb)

    keep = np.ones_like(rb)
    for link in T7.PATHS["P1"]:
        _d, loss = tt.delay_loss("poisson", link, rb + C.LINK_OFFSET[link])
        keep *= 1.0 - loss

    assert np.allclose(got, 1.0 - keep, atol=1e-12)


def test_edge_argmax_is_reported_as_not_identified():
    err = {
        ("poisson", 0.70): {"err_total": 0.9},
        ("poisson", 0.85): {"err_total": 0.5},
        ("poisson", 0.925): {"err_total": 0.2},
    }
    out = P.prediction_2(err, modes=("poisson",))

    assert out["by_mode"]["poisson"]["testable"] is False
    assert "edge" in out["by_mode"]["poisson"]["reason"]


def test_interior_argmax_is_testable():
    err = {
        ("poisson", 0.70): {"err_total": 0.2},
        ("poisson", 0.85): {"err_total": 0.9},
        ("poisson", 0.925): {"err_total": 0.4},
    }
    out = P.prediction_2(err, modes=("poisson",))

    assert out["by_mode"]["poisson"]["testable"] is True
    assert out["by_mode"]["poisson"]["argmax_rho_bar_err"] == pytest.approx(0.85)


def test_prediction_3_uses_only_significant_cells():
    out = P.prediction_3()
    maps = P.load_json(P.MAPS)
    expected = sum(1 for r in maps["rows"] if r["significant_d2_loss"])

    assert out["n_cells"] == expected
    assert out["n_cells"] > 0


def test_a_prediction_is_supported_only_when_every_relevant_cell_agrees():
    out = P.prediction_3()

    assert out["supported"] == (out["n_loss_dominates"] == out["n_cells"])


def test_operating_z_is_the_one_used_by_the_gate_decision():
    assert MR.Z_OPERATING == pytest.approx(0.55)
    assert len(MR.load_err(z=MR.Z_OPERATING)) == 8

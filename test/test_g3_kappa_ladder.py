"""Unit tests for the G-A014 analytic kappa ladder.

The ladder chooses a design parameter that multiplies campaign run time, so
its algebra, its selection rule, and its budget arithmetic are all machine
checked before the rule is signed.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

from tools.g3_dryrun import GATE_PC_FLIP_SPREAD, OMEGA_GRID
from tools.g3_kappa_ladder import (
    GATE_KAPPA1_FLAT,
    KAPPA_LADDER,
    SAFETY_FACTOR,
    TAU_LINK_S,
    campaign_budget,
    flip_curve,
    margin_weights,
    mixture_monotonicity_violation,
    omega_roundtrip,
)

A013_ARTIFACT = pathlib.Path("results/SMOKE/phase-G/g3_dryrun_a013.json")


def _spread(kappa: int) -> float:
    _c, path_variance, link_variance = margin_weights()
    _curve, spread = flip_curve(
        TAU_LINK_S * kappa, TAU_LINK_S, path_variance, link_variance
    )
    return spread


# --------------------------------------------------------------- algebra
def test_shared_link_cancels_from_the_pairwise_contrast():
    """DEC-0: uA is on both paths and must carry zero decision weight."""
    contrast_vector, path_variance, link_variance = margin_weights()
    assert contrast_vector[0] == 0.0
    assert path_variance > 0.0 and link_variance > 0.0


def test_kappa_one_makes_the_flip_curve_exactly_flat():
    """G-A010 in arithmetic: with one time scale, omega cancels from r(z)."""
    assert _spread(1) <= GATE_KAPPA1_FLAT


def test_flip_spread_increases_with_kappa():
    spreads = [_spread(kappa) for kappa in KAPPA_LADDER]
    assert spreads == sorted(spreads)


def test_kappa_ten_reproduces_the_signed_dry_d_pc_value():
    """The ladder must reproduce the signed artifact, not merely agree with it."""
    artifact = json.loads(A013_ARTIFACT.read_text(encoding="utf-8"))
    signed = next(
        check for check in artifact["checks"] if check["id"] == "DRY-D-PC"
    )
    assert _spread(10) == pytest.approx(signed["value"], rel=0.0, abs=1e-12)


# --------------------------------------------------------- selection rule
def test_selection_rule_picks_the_cheapest_admissible_kappa():
    threshold = SAFETY_FACTOR * GATE_PC_FLIP_SPREAD
    eligible = [kappa for kappa in KAPPA_LADDER if _spread(kappa) >= threshold]
    assert min(eligible) == 5


def test_kappa_four_is_excluded_by_the_stated_margin_not_by_rounding():
    """kappa=4 clears the inherited gate but misses the design margin."""
    threshold = SAFETY_FACTOR * GATE_PC_FLIP_SPREAD
    spread = _spread(4)
    assert spread >= GATE_PC_FLIP_SPREAD
    assert spread < threshold


# ---------------------------------------------------------------- budget
def test_budget_halves_between_kappa_ten_and_kappa_five():
    cheap = campaign_budget(5)["total_hours"]
    expensive = campaign_budget(10)["total_hours"]
    assert cheap < expensive
    assert expensive - cheap == pytest.approx(16.666, abs=0.01)


def test_budget_uses_the_slower_time_scale_in_every_regime():
    budget = campaign_budget(5)
    assert budget["t_run_pc_s"] == pytest.approx(3000.0)
    assert budget["t_run_symmetry_s"] == pytest.approx(3000.0)
    assert budget["t_run_nc_s"] == pytest.approx(600.0)


def test_budget_refuses_a_non_positive_kappa():
    with pytest.raises(ValueError):
        campaign_budget(0)


# ------------------------------------------------------------ diagnostics
def test_mixture_acf_is_monotone_at_the_selected_regime():
    assert mixture_monotonicity_violation(5.0 * TAU_LINK_S, TAU_LINK_S) == 0.0


def test_mixture_acf_monotonicity_detector_fires_on_the_inverse_regime():
    """The symmetry regime runs the mixture the other way; the check must see it."""
    assert mixture_monotonicity_violation(TAU_LINK_S, 5.0 * TAU_LINK_S) > 0.0


def test_omega_roundtrip_recovers_each_grid_point():
    """Wiring check at a short length; KAP-3 adjudicates at campaign length."""
    for omega in OMEGA_GRID:
        row = omega_roundtrip(omega, 15.0, TAU_LINK_S, 6000, 8, 20260910)
        assert abs(row["omega_hat_bias"]) <= 0.05


def test_omega_roundtrip_refuses_a_degenerate_length():
    with pytest.raises(ValueError):
        omega_roundtrip(0.5, 15.0, TAU_LINK_S, 1, 4, 20260910)

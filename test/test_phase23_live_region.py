"""Locked controls for Lesson 23.16."""

from __future__ import annotations

import json
import os

import pytest

from cert import live_region_sweep as L


def _load(path):
    if not os.path.exists(path):
        pytest.skip("artifact chua duoc sinh: %s" % path)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_preregistered_cells_va_thresholds_khoa():
    assert L.PRIMARY_CANDIDATES == (("poisson", 0.875), ("poisson", 0.900), ("h2", 0.650))
    assert L.H2_FALLBACK == ("h2", 0.675)
    assert L.DOMAIN_LIMIT == 1e-4
    assert L.LIVE_THRESHOLD == 0.05


def test_NC_H_domain_control_du_hai_sigma_va_nam_seed():
    report = _load(L.SLA_OUTPUT)
    lesson = [row for row in report["cells"] if row.get("lesson") == "23.16"]
    assert lesson
    for row in lesson:
        checks = row["domain_control"]["rows"]
        assert len(checks) == 2 * len(L.SEEDS)
        assert {item["sigma_source"] for item in checks} == {"sla_regime", "calib_builder"}
        assert {item["seed"] for item in checks} == set(L.SEEDS)
        assert row["domain_control"]["pass"] == all(item["worst_fraction"] < L.DOMAIN_LIMIT for item in checks)


def test_NC_K_fallback_chi_do_domain_quyet_dinh():
    report = _load(L.SLA_OUTPUT)
    h2 = {"%s@%.3f" % (r["mode"], r["rho_bar"]): r for r in report["cells"] if r.get("lesson") == "23.16" and r["mode"] == "h2"}
    assert report["fallback_triggered"] == (not h2["h2@0.650"]["domain_control"]["pass"])
    assert ("h2@0.675" in h2) == report["fallback_triggered"]


def test_NC_G_I_J_va_metric_keys():
    report = _load(L.OUTPUT)
    assert report["controls"]["NC_G_old_cell_max_gap"] <= 1e-12
    assert report["controls"]["NC_H_domain_checked_before_build"] is True
    assert report["controls"]["NC_I_identity_all_valid"] is True
    assert report["controls"]["NC_J_crossfit_all_valid"] is True
    assert set(report["verdict"]) == {
        "M_53_rho_hit_in_0_860_0_925",
        "M_54_poisson_sign_monotone",
        "M_55_poisson_err_neo_both_in_0_15_0_26",
        "M_56_h2_candidate_live",
        "M_57_h2_live_lift_minus_swing_negative",
        "M_47b_delta_nonpositive_all_live_heldout",
        "M_48b_twin_deg_spread_in_1_00_1_30",
    }


def test_M48b_tai_lap_readout_da_khoa():
    report = _load(L.OUTPUT)
    assert report["metrics"]["M_48b_twin_deg_spread"] == pytest.approx(1.059170016762354, abs=1e-12)

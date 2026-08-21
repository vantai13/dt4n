"""Locked controls for Lesson 23.15 eight-cell confirmation."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cert import eight_cell_sweep as E


def _artifact():
    if not os.path.exists(E.OUTPUT):
        pytest.skip("chua chay eight-cell sweep")
    with open(E.OUTPUT, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_NC_F_w_loss_lay_tu_artifact_khong_hardcode():
    src = Path("cert/eight_cell_sweep.py").read_text(encoding="utf-8")
    function = src.split("def w_loss_for_cell", 1)[1].split("def _decomposition_f2", 1)[0]
    assert "sla_calibration.json" in src
    assert "w_loss" in function
    for bad in ("1451.377", "3222.244", "2424.359", "2861.395"):
        assert bad not in function


def test_ratio_grid_va_tap_cell_khoa():
    assert E.RATIOS[0] == pytest.approx(0.50)
    assert E.RATIOS[-1] == pytest.approx(1.50)
    assert len(E.RATIOS) == 21
    assert len(E.SEEN_CELLS) == 3
    assert len(E.NEW_CELLS) == 5
    assert set(E.SEEN_CELLS).isdisjoint(E.NEW_CELLS)


def test_NC_D_ba_cell_cu_tai_lap_den_1e_12():
    out = _artifact()
    for cell, want in E.LEGACY_DELTA.items():
        got = out["cells"][cell]["F2"]["delta_system_vs_neo"]
        assert abs(got - want) < 1e-12, "%s lech %.3e" % (cell, got - want)
    assert out["controls"]["NC_D_max_absolute_gap"] <= 1e-12


def test_M50_dong_nhat_thuc_dai_so_phai_dung_8_tren_8():
    out = _artifact()
    for cell, row in out["cells"].items():
        d = row["lift_swing_F2"]
        lhs = d["delta_vs_anchor"]
        rhs = d["reject_share"] * (d["swing"] - d["lift"])
        assert abs(lhs - rhs) < 1e-12, "dong nhat thuc do o %s" % cell
    assert out["verdict"]["M_50_sign_identity_8_of_8"] is True


def test_NC_E_crossfit_va_objective_ratio_one():
    out = _artifact()
    assert out["controls"]["NC_E_all_leakage_controls"] is True
    for row in out["cells"].values():
        assert row["objective"]["ratio_one_selected_delta_gap"] <= 1e-12


def test_artifact_cham_du_M46_den_M52():
    out = _artifact()
    assert set(out["verdict"]) == {
        "M_46_r_cross_in_0_80_0_95",
        "M_47_delta_negative_all_new_at_confirm_ratio",
        "M_48_twin_deg_spread_in_1_00_1_30",
        "M_49_prior_deg_spread_gt_3",
        "M_50_sign_identity_8_of_8",
        "M_51_capacity_in_4_8",
        "M_52_selection_mean_not_worse",
    }

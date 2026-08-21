"""Test cho Lesson 23.7 [3b] -- conditioning va bom residual."""

from __future__ import annotations

import ast
import json
import os
import pathlib

import numpy as np
import pytest

from cert import conditioning_audit as A


MAIN_ARTIFACT = A.artifact_path(A.MAIN_CELL)
ALL_ARTIFACTS = tuple(A.artifact_path(cell) for cell in A.CELL_SPECS)
RELATIVE_ARTIFACTS = tuple(A.relative_artifact_path(cell) for cell in A.CELL_SPECS)


def _load(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_conditioning_audit_chi_import_xuong_module_nen():
    tree = ast.parse(pathlib.Path("cert/conditioning_audit.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("cert"):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names if a.name.startswith("cert"))
    assert not any("lesson23_7_" in name for name in imported)
    assert "cert.cell_matrices" in imported


def test_spread_tach_duoc_co_gap_bang_khong():
    z = np.asarray([1.0, 2.0])[:, None, None]
    m = np.asarray([1.0, 1.5, 3.0])[None, :, None]
    slot = np.asarray([1.0, 4.0])[None, None, :]
    out = A.spread_and_separability(z * m * slot)
    assert out["M_1_spread_m"] == pytest.approx(3.0)
    assert out["M_2_spread_z"] == pytest.approx(2.0)
    assert out["spread_slot"] == pytest.approx(4.0)
    assert out["M_3_spread_total"] == pytest.approx(24.0)
    assert out["M_9_separability_gap_rel"] == pytest.approx(0.0)


def test_M13_b_bang_0_duoc_hieu_la_ti_so_vo_han():
    y_hat = np.asarray([[1.0, 5.0, 4.0, 0.0], [2.0, 6.0, 5.0, 0.0]])
    base = {"y_hat": y_hat}
    prep = {"a_star_full": np.asarray([0, 0])}
    out = A.pruning_profitability(base, prep)
    assert out["n_fixable_a"] == 2
    assert out["n_broken_b"] == 0
    assert out["conditional_ratio_a_over_b"] is None
    assert out["conditional_ratio_is_infinite"] is True
    assert out["M_13_predicts_profitable"] is True
    assert out["profitable_exact"] is True
    assert out["M_13_prediction_correct"] is True


def test_M13_a_b_cung_bang_0_la_trung_tinh():
    y_hat = np.asarray([[0.0, 1.0, 2.0, 3.0], [0.0, 2.0, 3.0, 4.0]])
    out = A.pruning_profitability({"y_hat": y_hat}, {"a_star_full": np.asarray([0, 0])})
    assert out["n_fixable_a"] == 0
    assert out["n_broken_b"] == 0
    assert out["conditional_ratio_a_over_b"] is None
    assert out["conditional_ratio_is_infinite"] is False
    assert out["M_13_predicts_profitable"] is False
    assert out["profitable_exact"] is False
    assert out["M_13_evaluable"] is False
    assert out["M_13_prediction_correct"] is None


def test_flip_by_gate_giu_dong_nhat_thuc_co_trong_so():
    a0 = np.asarray([0, 0, 0, 0, 0, 0])
    a1 = np.asarray([1, 0, 1, 0, 0, 1])
    accept = np.asarray([True, True, False, False, False, False])
    out = A._flip_by_gate(a0, a1, accept)
    assert out["flip_all_rows"] == pytest.approx(0.5)
    assert out["flip_given_accept"] == pytest.approx(0.5)
    assert out["flip_given_reject"] == pytest.approx(0.5)
    assert out["identity_residual"] < 1e-12
    assert out["concentration_ratio"] == pytest.approx(1.0)


def test_nhanh_tuyet_doi_cu_van_co_diem_neo_da_ky():
    """Regression control; the superseded branch remains a reference point."""
    assert callable(A.conclusion_flip_absolute_superseded)
    old = A._absolute_superseded_reference(A.MAIN_CELL)
    assert old["status"] == "SUPERSEDED_BY_AMENDMENT_35"
    assert abs(old["point"]["perturbed"]["delta"] - 0.04487496174747532) < 1e-9


@pytest.mark.skipif(not os.path.exists(MAIN_ARTIFACT), reason="chua chay cell chinh")
def test_doi_chung_3_tai_lap_lesson_23_6():
    report = _load(MAIN_ARTIFACT)
    approval = report["C_astar_sensitivity"]["conclusion_flip"]["baseline_approval_23_6"]
    assert approval["matches_lesson_23_6"] is True
    assert max(approval["absolute_gaps"].values()) <= approval["tolerance"]


@pytest.mark.skipif(not os.path.exists(MAIN_ARTIFACT), reason="chua chay cell chinh")
def test_bom_khong_doi_yhat_va_tap_accept():
    report = _load(MAIN_ARTIFACT)
    conclusion = report["C_astar_sensitivity"]["conclusion_flip"]
    assert conclusion["control_y_hat_unchanged_all_three"] is True
    assert conclusion["control_accept_set_unchanged_all_three"] is True
    assert all(row["y_hat_unchanged"] for row in conclusion["points"])
    assert all(row["accept_set_unchanged"] for row in conclusion["points"])


@pytest.mark.skipif(not os.path.exists(MAIN_ARTIFACT), reason="chua chay cell chinh")
def test_M16_bat_buoc_bao_cao_cap_doi_chung():
    report = _load(MAIN_ARTIFACT)
    coverage = report["C_astar_sensitivity"]["coverage_under_misspec"]
    assert coverage["NC23v2_8_pert_pert"] >= coverage["nominal_coverage"]
    assert coverage["PC23v2_3_orig_pert"] < coverage["nominal_coverage"]
    assert coverage["control_pair_discriminates"] is True


@pytest.mark.skipif(
    not all(os.path.exists(path) for path in ALL_ARTIFACTS),
    reason="chua chay du ba cell",
)
def test_ky_luat_pham_vi_13_tren_hai_cell_giu_kin():
    reports = {cell: _load(A.artifact_path(cell)) for cell in A.CELL_SPECS}
    summary = A.summarize(reports)
    assert summary["predictions"]["M-12b"]["cells"] == [A.MAIN_CELL]
    assert summary["predictions"]["M-16"]["cells"] == [A.MAIN_CELL]
    for prediction in (
        "M-6", "M-6b", "M-6c", "M-9", "M-11", "M-13", "M-13b",
        "M-13c", "M-14", "M-15",
    ):
        assert summary["predictions"][prediction]["cells"] == list(A.HELD_OUT_CELLS)


@pytest.mark.skipif(not os.path.exists(A.SUMMARY_PATH), reason="chua tong hop")
def test_12_mechanisms_duoc_sinh_tu_summary():
    summary = _load(A.SUMMARY_PATH)
    with open(A.DOC_PATH, "r", encoding="utf-8") as handle:
        assert handle.read() == A.markdown_report(summary)


@pytest.mark.skipif(
    not all(os.path.exists(path) for path in RELATIVE_ARTIFACTS),
    reason="chua chay du ba cell 23.7-quater",
)
def test_M35_flip_tren_tap_chap_nhan_duoc_tach_khoi_tap_tu_choi():
    """Record the mechanism hypothesis without forcing its observed direction."""
    for cell in A.CELL_SPECS:
        out = _load(A.relative_artifact_path(cell))
        gate = out["relative_multiplicative"]["gate_split"]
        assert gate["concentration_ratio"] is not None
        assert gate["identity_residual"] < 1e-12
        # Do not assert reject > accept: a reversal is a reportable result.


@pytest.mark.skipif(
    not all(os.path.exists(path) for path in RELATIVE_ARTIFACTS),
    reason="chua chay du ba cell 23.7-quater",
)
def test_relative_branch_controls_and_accounting_are_explicit():
    for cell in A.CELL_SPECS:
        out = _load(A.relative_artifact_path(cell))
        rel = out["relative_estimand"]
        conclusion = out["relative_multiplicative"]
        assert rel["relative_point"] == rel["relative_point_mean_of_ratios"]
        assert "relative_point_ratio_of_means" in rel
        assert rel["M_28_estimand"] == "mean_of_seed_ratios"
        assert conclusion["controls"]["accept_set_unchanged"] is True
        assert conclusion["controls"]["y_hat_unchanged"] is True
        assert out["domain_control"]["clip_ratio"] == 0.0
        assert out["verdict"]["M_37_delta_still_negative"] is (
            conclusion["M_36_delta_relative"] < 0.0
        )

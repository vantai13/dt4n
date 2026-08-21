"""Golden tests cho S7. Khong xoa: moi loi cau truc can mot regression test."""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from cert import residual_level_audit as A
from measurements import decision_error_v2 as D
from twin import topology_v7 as T7


ARTIFACT = "results/phase-23/residual_level_audit_poisson_0.925.json"


@pytest.fixture(scope="module")
def poisson_record():
    return A._loss_record("poisson")


@pytest.fixture(scope="module")
def rho_small():
    cell = next(
        row
        for row in D.load_calibration()
        if row.get("feasible") and row["mode"] == "poisson" and row["rho_bar"] == 0.925
    )
    sigma, _source = D.resolve_sigma(cell)
    return D.rho_matrix_from_cell("poisson", 0.925, sigma, seed=101, n=2000)


def test_moi_duong_deu_co_dung_3_link():
    for path, links in T7.PATHS.items():
        assert len(links) == 3, "%s co %d link" % (path, len(links))


def test_residual_loss_cua_moi_mode_o_dung_tang():
    for mode in ("poisson", "h2"):
        rec = A._loss_record(mode)
        assert rec.mode == mode
        assert rec.channel == "loss"
        assert rec.level == "per_path"


def test_H_path_khong_lat_mot_hang_nao(rho_small, poisson_record):
    for r in A.endpoint_values(poisson_record).values():
        out = A.audit_rho_matrix(rho_small, "poisson", poisson_record, r, 3222.244681647411)
        assert out["all_rows"]["flip_fraction"]["H_path_correct_level"] == 0.0


def test_negative_control_shift_zero(rho_small, poisson_record):
    out = A.audit_rho_matrix(rho_small, "poisson", poisson_record, 0.0, 3222.244681647411)
    assert all(value == 0.0 for value in out["all_rows"]["flip_fraction"].values())


def test_clip_ratio_duoc_ghi_lai(rho_small, poisson_record):
    out = A.audit_rho_matrix(
        rho_small, "poisson", poisson_record, poisson_record.point, 3222.244681647411
    )
    diag = out["diagnostics"]["H_link_with_clip"]
    assert diag["eval_count"] > 0
    assert 0.0 <= diag["clip_ratio"] <= 1.0


def test_mode_mismatch_lam_do(rho_small):
    with pytest.raises(ValueError, match="khong khop"):
        A.audit_rho_matrix(rho_small, "poisson", A._loss_record("h2"), -0.01, 1.0)


def test_relative_point_khop_residual_cascade_va_ghi_diem_do():
    out = A.relative_point_from_raw(mode="poisson")
    assert out["matches_residual_cascade"]
    assert out["rho_bar_measured"] == 0.925
    assert -0.20 <= out["relative_point"] <= -0.12
    assert out["scale"] == "loss_fraction"


def test_estimand_loss_khong_con_ghi_chi_phi():
    rec = A._loss_record("poisson")
    assert "ton that" in rec.estimand.lower()
    assert "chi phi" not in rec.estimand.lower()
    assert rec.relative_point == pytest.approx(rec.point / rec.baseline_magnitude)


def test_M30_mo_hinh_tuong_doi_khong_cat_nguong(rho_small):
    rel = A.relative_point_from_raw(mode="poisson")["relative_point"]
    tt = A.RelativePathShiftTruthTable(rel, "poisson")
    _delay, loss, _cost = tt.path_tables("poisson", rho_small, 3222.244681647411)
    assert tt.clip_events == 0
    assert np.all((0.0 <= loss) & (loss <= 1.0))


@pytest.mark.skipif(not os.path.exists(ARTIFACT), reason="chua sinh artifact 23.7-bis")
def test_artifact_chinh_cham_dung_bon_dong_da_khoa():
    with open(ARTIFACT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    assert report["negative_control"]["NC23v2_10_pass"]
    verdict = report["verdict"]
    assert verdict["M_23_H_path_exact_zero"]
    assert verdict["M_24_H_link0_point_in_0_0_02"]
    assert verdict["M_25_clip_share_gt_0_90"]
    assert verdict["M_26_H_link1_reproduces_0_2130"]


@pytest.mark.skipif(not os.path.exists(ARTIFACT), reason="chua sinh artifact 23.7-bis")
def test_tong_flip_pairs_khop_n_flip():
    with open(ARTIFACT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    for endpoint in report["endpoints"].values():
        for scope in ("all_rows", "test_rows"):
            for branch, pairs in endpoint[scope]["flip_pairs"].items():
                assert sum(pairs.values()) == endpoint[scope]["n_flip"][branch]


@pytest.mark.parametrize("cell", ["poisson_0.850", "h2_0.700"])
def test_heldout_M24_M25_duoc_cham_va_M26_co_ly_do(cell):
    path = "results/phase-23/residual_level_audit_%s.json" % cell
    if not os.path.exists(path):
        pytest.skip("chua tai sinh held-out artifact")
    with open(path, "r", encoding="utf-8") as handle:
        verdict = json.load(handle)["verdict"]
    assert verdict["M_24_H_link0_point_in_0_0_02"] is True
    assert verdict["M_25_clip_share_gt_0_90"] is True
    assert verdict["M_26_H_link1_reproduces_0_2130"] is None
    assert verdict["M_26_reason"] == "main_cell_only_by_definition"

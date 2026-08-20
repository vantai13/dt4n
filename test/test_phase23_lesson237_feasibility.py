"""Test cho buoc [2a] Lesson 23.7 -- kiem kha thi va thang cat hanh dong.

Phan nhanh doc ARTIFACT da sinh; phan cham (dung lai 1M hang, bisection tren
ba muc cua thang) mang nhan `slow` theo `pytest.ini`.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from cert import lesson23_7_feasibility as F

ARTIFACT = "results/phase-23/lesson23_7_feasibility.json"

pytestmark = pytest.mark.skipif(
    not os.path.exists(ARTIFACT), reason="chua chay cert.lesson23_7_feasibility"
)


@pytest.fixture(scope="module")
def rep():
    with open(ARTIFACT, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# A1/A2/A3 -- ba mat xich kha thi
# ---------------------------------------------------------------------------

def test_A1_ba_input_20R_con_nguyen_ven(rep):
    chain = rep["A1_input_chain"]
    assert chain["all_match"], [r for r in chain["rows"] if not r["match"]]
    assert len(chain["rows"]) == 3


def test_A2_tai_lap_ranking_goc_va_cu_lat(rep):
    k4 = rep["A2_k4_reproduction"]
    assert k4["reproduces_published_base"]
    assert k4["reproduces_published_flip"]
    assert k4["bracket_consistent"]


def test_A2_cu_lat_la_MOT_CHIEU_chi_o_dau_am(rep):
    """Bom dau duong KHONG lat. Neu ca hai dau deu lat thi co che khac han."""
    for entry in rep["A2_k4_reproduction"]["endpoints"]:
        assert entry["signs"]["+1"]["K4_preserved"], entry["label"]


def test_A2_bracket_dung_thu_tu(rep):
    """r_star_lo giu K4; r_star va CI90 bien xau deu vo."""
    eps = rep["A2_k4_reproduction"]["endpoints"]
    assert eps[0]["variant_k4_holds"] is True
    assert eps[1]["variant_k4_holds"] is False
    assert eps[2]["variant_k4_holds"] is False
    assert eps[0]["endpoint"] < eps[1]["endpoint"] < eps[2]["endpoint"]


def test_A3_astar_tai_lap_tuyet_doi(rep):
    a = rep["A3_astar_reproduction"]
    assert a["same_length"]
    assert a["a_star_exact_match"]
    assert a["a_twin_exact_match"]
    assert a["block_id_exact_match"]


def test_ket_luan_kha_thi_la_hop_cua_ba_mat_xich(rep):
    """Co KY DUOC phai keo theo ca ba, khong duoc bat mot cai roi ket luan."""
    expected = (
        rep["A1_input_chain"]["all_match"]
        and rep["A2_k4_reproduction"]["reproduces_published_base"]
        and rep["A2_k4_reproduction"]["reproduces_published_flip"]
        and rep["A3_astar_reproduction"]["a_star_exact_match"]
    )
    assert rep["M12_M15_feasible"] == expected


# ---------------------------------------------------------------------------
# B -- do nhay a_star
# ---------------------------------------------------------------------------

def test_B_twin_khong_biet_residual(rep):
    """Bat bien kien truc: bom vao tt chi cham y_true, khong cham y_hat."""
    for s in rep["B_M15_sensitivity"].values():
        assert s["y_hat_unchanged_invariant"] is True


def test_B_bom_manh_hon_thi_lat_nhieu_hon(rep):
    a = rep["B_M15_sensitivity"]["at_r_star"]
    b = rep["B_M15_sensitivity"]["at_ci90_worst"]
    assert b["endpoint"] > a["endpoint"]
    assert b["M_15_flip_fraction"] > a["M_15_flip_fraction"]


def test_B_err_neo_tang_khi_bom(rep):
    """a* lech khoi twin -> err_neo phai TANG, khong the giam."""
    for s in rep["B_M15_sensitivity"].values():
        assert s["delta_err_neo"] > 0.0


def test_B_clip_dang_ke_nen_M15_la_can_duoi(rep):
    """20R ghi clip_ratio 43.2%. Neu clip bien mat, dinh nghia bom da doi."""
    clip = rep["B_M15_sensitivity"]["at_ci90_worst"]["clip"]
    assert clip["clip_ratio"] > 0.30
    assert clip["is_lower_bound"] is True


def test_B_tong_cac_cap_doi_khop_n_flip(rep):
    for s in rep["B_M15_sensitivity"].values():
        assert sum(s["flip_pairs"].values()) == s["n_flip"]


def test_B_phan_phoi_a_star_van_la_phan_phoi(rep):
    for s in rep["B_M15_sensitivity"].values():
        for key in ("a_star_dist_baseline", "a_star_dist_perturbed"):
            assert sum(s[key]) == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# C -- thang cat hanh dong
# ---------------------------------------------------------------------------

def test_C_S0_tai_lap_C3_da_commit(rep):
    """Doi chung goc: neu S0 lech C3 da commit thi ca thang vo nghia."""
    ap = rep["C_action_ladder"]["S0_approval_vs_committed_C3"]
    assert ap["matches"], ap


def test_C_thang_long_nhau_va_dung_thu_tu(rep):
    levels = rep["C_action_ladder"]["levels"]
    assert [r["level"] for r in levels] == ["S0", "S1", "S2"]
    prev: set = set()
    for r in levels:
        cur = set(r["pruned_paths"])
        assert prev <= cur, "thang phai LONG NHAU"
        prev = cur
    assert [r["K_eff"] for r in levels] == [4, 3, 2]
    assert [r["m_slots"] for r in levels] == [3, 2, 1]


def test_C_alpha_each_bang_alpha_chia_m(rep):
    for r in rep["C_action_ladder"]["levels"]:
        assert r["alpha_each"] == pytest.approx(F.ALPHA_FAMILY / r["m_slots"])


def test_C_san_loi_khong_giam_theo_thang(rep):
    floors = [r["error_floor_from_pruning"] for r in rep["C_action_ladder"]["levels"]]
    assert floors == sorted(floors)
    assert floors[0] == 0.0


def test_C_cat_P2_khong_doi_err_vi_twin_khong_bao_gio_chon_P2(rep):
    """P(a_twin = P2) = 0 nen S1 phai TRUNG KHOP S0 ve err toan bo."""
    s0, s1 = rep["C_action_ladder"]["levels"][:2]
    assert s1["err_system_all_rows"] == pytest.approx(s0["err_system_all_rows"], abs=1e-12)


def test_C_acceptance_tang_khi_ngan_sach_alpha_rong_ra(rep):
    """alpha_each lon hon -> q_hat hep hon -> chap nhan nhieu hon, tai cung kappa."""
    acc = [r["acceptance_at_kappa_0.50"] for r in rep["C_action_ladder"]["levels"]]
    assert acc[0] < acc[1] < acc[2]


def test_C_coverage_khop_muc_tieu_o_moi_bac(rep):
    for r in rep["C_action_ladder"]["levels"]:
        assert r["coverage_achieved"] == pytest.approx(F.GAMMA_OP, abs=2e-3)


def test_C_M13_ket_luan_khop_so_lieu(rep):
    m13 = rep["C_action_ladder"]["M_13_cutting_P4_profitable"]
    assert m13["profitable"] == (m13["delta_err_accept_S2_minus_S1"] < 0.0)


# ---------------------------------------------------------------------------
# D -- dai M-11
# ---------------------------------------------------------------------------

def test_D_dai_M11_bao_gia_tri_do_duoc_va_loai_tru_1(rep):
    d = rep["D_M11_band"]
    lo, hi = d["suggested_band_M11"]
    assert lo < d["one_sided_ratio_all_test"] < hi
    assert lo > 1.0
    assert d["band_excludes_1"] is True


def test_D_M14_duoi_1_tren_cell_chinh(rep):
    """M-14 se duoc CHAM tren hai cell con lai; day chi la neo cell chinh."""
    d = rep["D_M11_band"]
    assert d["M_14_ratio_accept_over_all"] == pytest.approx(
        d["one_sided_ratio_accept_only"] / d["one_sided_ratio_all_test"]
    )
    assert d["M_14_ratio_accept_over_all"] < 1.0


# ---------------------------------------------------------------------------
# Cau truc / hang so khoa
# ---------------------------------------------------------------------------

def test_thang_khoa_dung_ba_bac_va_dung_duong(rep):
    assert F.LADDER == (("S0", ()), ("S1", (1,)), ("S2", (1, 3)))


def test_script_khong_ky_gi(rep):
    assert rep["signs_nothing"] is True
    assert rep["cell"] == "poisson@0.925"


@pytest.mark.slow
def test_end_to_end_tai_lap_duoc(tmp_path):
    """Chay lai toan bo (~2 phut) va doi chieu cac truong quyet dinh."""
    out = F.build(str(tmp_path / "out.json"))
    assert out["M12_M15_feasible"] is True
    assert out["C_action_ladder"]["S0_approval_vs_committed_C3"]["matches"]
    assert out["A3_astar_reproduction"]["a_star_exact_match"]

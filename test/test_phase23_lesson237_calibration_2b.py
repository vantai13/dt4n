"""Test cho buoc [2b] Lesson 23.7 -- phan ra M-D11 va nguong M-D13."""

from __future__ import annotations

import json
import os

import pytest

from cert import lesson23_7_calibration_2b as C

ARTIFACT = "results/phase-23/lesson23_7_calibration_2b.json"
TABLES = "results/phase-23/lesson23_7_tables.md"

pytestmark = pytest.mark.skipif(
    not os.path.exists(ARTIFACT), reason="chua chay cert.lesson23_7_calibration_2b"
)


@pytest.fixture(scope="module")
def rep():
    with open(ARTIFACT, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# M-D11 -- phan ra ba nhanh
# ---------------------------------------------------------------------------

def test_MD11_co_du_hai_bac_S1_S2(rep):
    levels = rep["M_D11_decomposition"]["levels"]
    assert [r["level"] for r in levels] == ["S1", "S2"]


def test_MD11_ba_nhanh_gan_nhu_cong_duoc(rep):
    """d(iii) ~= d(i) + d(ii). Tuong tac lon => hai co che khong tach duoc."""
    for r in rep["M_D11_decomposition"]["levels"]:
        assert r["additive"] is True, r["level"]
        assert r["interaction_rel_to_total"] < 0.10


def test_MD11_moi_nhanh_deu_lam_TANG_acceptance(rep):
    """Bot rang buoc va noi alpha deu chi co the tang chap nhan."""
    for r in rep["M_D11_decomposition"]["levels"]:
        assert r["branch_i_constraint_only"]["delta_vs_S0"] > 0
        assert r["branch_ii_budget_only"]["delta_vs_S0"] > 0
        assert r["branch_iii_both"]["delta_vs_S0"] > 0


def test_MD11_nhanh_ii_giu_du_ba_slot(rep):
    """Nhanh NGAN SACH phai KHONG cat duong nao -- neu cat la confound lai."""
    for r in rep["M_D11_decomposition"]["levels"]:
        assert r["branch_ii_budget_only"]["pruned"] == []
        assert r["branch_ii_budget_only"]["n_slots"] == 3


def test_MD11_nhanh_i_giu_alpha_goc(rep):
    """Nhanh RANG BUOC phai giu alpha_each danh nghia."""
    nominal = rep["M_D11_decomposition"]["alpha_each_nominal"]
    for r in rep["M_D11_decomposition"]["levels"]:
        assert r["branch_i_constraint_only"]["alpha_each"] == pytest.approx(nominal)
        assert r["branch_i_constraint_only"]["n_slots"] == r["m_effective"]


def test_MD11_ngan_sach_chiem_phan_lon(rep):
    """Ket qua chinh cua [2b-i]: Delta chu yeu la ngan sach, khong phai rang buoc."""
    for r in rep["M_D11_decomposition"]["levels"]:
        assert r["M_6b_budget_share"] > 0.5


def test_MD11_cat_P2_gan_nhu_thuan_ngan_sach(rep):
    """P2 khong doi quyet dinh nao, nen phan rang buoc phai gan 0."""
    s1 = rep["M_D11_decomposition"]["levels"][0]
    assert s1["level"] == "S1"
    assert s1["constraint_share"] < 0.05


def test_MD11_dai_M6_bao_gia_tri_do_duoc(rep):
    d = rep["M_D11_decomposition"]
    total = d["levels"][-1]["M_6_delta_total"]
    lo, hi = d["M_6_band_from_S2"]
    assert lo < total < hi


# ---------------------------------------------------------------------------
# M-D13 -- nguong dan tu so lieu
# ---------------------------------------------------------------------------

def test_MD13_phan_hoach_a_cong_b(rep):
    """a + b phai bang so hang twin chon p -- neu khong, ke toan sai."""
    for r in rep["M_D13_r_crit"]["paths"]:
        assert r["partition_check_a_plus_b"] is True


def test_MD13_nguong_nhat_quan_voi_ke_toan_chinh_xac(rep):
    cc = rep["M_D13_r_crit"]["consistency_check"]
    assert cc["agree"] is True


def test_MD13_phac_thao_ban_dau_KHONG_khop(rep):
    """Doi chung: nguong phac thao tren ti so BIEN cho ket luan NGUOC.

    Test nay khoa lai LY DO phai sua dai so. Neu ai do doi lai cong thuc cu,
    test se do.
    """
    sk = rep["M_D13_r_crit"]["sketch_correction"]
    assert sk["sketch_agrees_with_exact"] is False
    assert sk["sketch_says_profitable"] is False
    assert sk["exact_says_profitable"] is True


def test_MD13_chi_phi_that_nho_hon_P_a_star(rep):
    """b < P(a*=p)*n: hang da sai san khong phai chi phi cua viec cam."""
    p4 = rep["M_D13_r_crit"]["paths"][0]
    assert p4["path"] == "P4"
    assert p4["n_broken_b"] < p4["P_a_star_eq_p"] * 999945


def test_MD13_r_cond_lon_hon_r_bien(rep):
    """Ti so co dieu kien phai LON hon ti so bien vi mau so nho hon."""
    p4 = rep["M_D13_r_crit"]["paths"][0]
    assert p4["conditional_ratio_a_over_b"] > p4["marginal_ratio_r"]


def test_MD13_P2_la_trung_tinh_khong_phai_khong_co_lai(rep):
    """P2: twin khong bao gio chon -> a = b = 0 -> cam no khong doi gi."""
    p2 = next(r for r in rep["M_D13_r_crit"]["paths"] if r["path"] == "P2")
    assert p2["neutral"] is True
    assert p2["n_fixable_a"] == 0 and p2["n_broken_b"] == 0
    assert p2["net_err_change"] == 0.0


def test_MD13_P_sua_duoc_la_mot_xac_suat(rep):
    for r in rep["M_D13_r_crit"]["paths"]:
        if r["P_sua_duoc"] is not None:
            assert 0.0 <= r["P_sua_duoc"] <= 1.0


# ---------------------------------------------------------------------------
# M-15 va ky luat pham vi
# ---------------------------------------------------------------------------

def test_M15_cham_tren_hai_cell_giu_kin(rep):
    m = rep["M_15_band"]
    assert m["scored_on"] == ["poisson@0.850", "h2@0.700"]
    assert m["is_lower_bound"] is True
    lo, hi = m["band_held_out"]
    assert lo < m["observed_main_cell"] < hi


def test_M16_khong_duoc_tinh_o_buoc_nay(rep):
    assert rep["M16_computed_here"] is False


def test_cell_chinh_la_phong_hieu_chuan(rep):
    assert rep["signs_nothing"] is True
    assert "HIEU CHUAN" in rep["cell_role"]
    assert rep["cell"] == "poisson@0.925"


# ---------------------------------------------------------------------------
# NT-v2-23 -- bang phai duoc SINH
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not os.path.exists(TABLES), reason="chua sinh bang")
def test_bang_markdown_duoc_sinh_tu_artifact(rep):
    """Bang phai khop artifact tung con so -- chong loi dan de cot (NT-v2-23)."""
    with open(TABLES, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert text == C.markdown_tables(rep)


def test_bang_chua_san_loi_dung_cua_S1(rep):
    """Loi da mac: cot san loi cua S1 bi dan de thanh 0.5256 thay vi 0.000007."""
    md = C.markdown_tables(rep)
    assert "0.525631" not in md.split("M-D13")[0].split("\n| S1")[1].split("\n")[0]

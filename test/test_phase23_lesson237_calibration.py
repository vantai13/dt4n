"""Test cho buoc hieu chuan dai Lesson 23.7.

`NT-v2-20`: ke cong cu chan mot loai loi phai duoc ap cho CHINH nguoi viet ra
no. Script hieu chuan tu dat mot quy tac ("chi doc cell chinh"), nen quy tac do
phai song trong mot test, khong phai trong dau nguoi viet.
"""

from __future__ import annotations

import numpy as np
import pytest

from cert import lesson23_7_range_calibration as L


# ---------------------------------------------------------------------------
# 1. Rao pham vi -- quy tac tu ap len chinh minh
# ---------------------------------------------------------------------------

def test_scope_guard_chi_cho_phep_cell_chinh():
    assert L.SCOPE_GUARD == ("poisson@0.925",)


@pytest.mark.parametrize(
    "cells",
    [
        ("poisson@0.925", "poisson@0.850"),
        ("poisson@0.850",),
        ("poisson@0.925", "h2@0.700"),
        (),
    ],
)
def test_build_tu_choi_moi_pham_vi_ngoai_cell_chinh(cells):
    """Hai cell con lai mang du doan TINH DIEM; cham vao chung la ro ri."""
    with pytest.raises(ValueError, match="TINH DIEM"):
        L.build("/tmp/khong-duoc-ghi.json", cells=cells)


def test_nguong_hanh_dong_chet_duoc_khoa_o_0_05():
    """M-D4: khoa TRUOC khi nhin phan phoi. Doi gia tri = doi du doan."""
    assert L.DEAD_ACTION_THRESHOLD == 0.05


def test_alpha_va_K_danh_nghia_khop_phase_22():
    from cert.simultaneous_score import ALPHA

    assert L.ALPHA_FAMILY == ALPHA == 0.10
    assert L.M_NOMINAL == L.K_NOMINAL - 1 == 3


# ---------------------------------------------------------------------------
# 2. M-D1 -- dinh nghia spread phai lay TB tren HAI truc con lai
# ---------------------------------------------------------------------------

def test_spread_axis_lay_trung_binh_tren_hai_truc_con_lai():
    """Truc 0 bien thien 1..2; hai truc kia chi them offset khong doi."""
    arr = np.zeros((2, 3, 4), dtype=np.float64)
    arr[0] = 1.0
    arr[1] = 2.0
    out = L._spread_axis(arr, 0)
    assert out["spread"] == pytest.approx(2.0)
    assert out["profile"] == pytest.approx([1.0, 2.0])
    assert (out["argmax"], out["argmin"]) == (1, 0)


def test_spread_axis_khong_bi_anh_huong_boi_truc_khac():
    rng = np.random.default_rng(0)
    base = rng.uniform(1.0, 2.0, size=(4, 4, 3))
    a = L._spread_axis(base, 1)["spread"]
    # Nhan mot he so KHONG DOI vao toan bo tensor: ti so bien phai giu nguyen.
    b = L._spread_axis(base * 7.5, 1)["spread"]
    assert a == pytest.approx(b)


def test_tensor_tach_duoc_hoan_toan_thi_khe_tach_duoc_bang_0():
    """Neu q = f(z) * g(m) * h(s) thi spread_total == tich ba spread bien."""
    f = np.array([1.0, 2.0, 3.0, 4.0])
    g = np.array([1.0, 1.1, 1.2, 1.3])
    h = np.array([1.0, 1.05, 1.10])
    arr = f[:, None, None] * g[None, :, None] * h[None, None, :]
    out = L.separability_audit(arr)
    assert out["separability_gap_rel"] == pytest.approx(0.0, abs=1e-12)
    assert out["M_3_spread_total"] == pytest.approx(
        out["product_of_marginal_spreads"], rel=1e-12
    )


def test_tensor_co_tuong_tac_thi_khe_tach_duoc_khac_0():
    """Doi chung am: them mot so hang tuong tac phai lam khe bat len."""
    f = np.array([1.0, 2.0, 3.0, 4.0])
    g = np.array([1.0, 1.1, 1.2, 1.3])
    h = np.array([1.0, 1.05, 1.10])
    arr = f[:, None, None] * g[None, :, None] * h[None, None, :]
    arr[3, 3, 2] *= 3.0                       # mot goc bi keo len
    out = L.separability_audit(arr)
    assert out["separability_gap_rel"] > 0.10


# ---------------------------------------------------------------------------
# 3. Khao co L10 -- ket luan phai doc tu artifact, khong hard-code
# ---------------------------------------------------------------------------

def test_khao_co_L10_khong_tim_thay_phat_bieu_dinh_luong():
    out = L.archaeology_L10()
    assert out["n_quantitative_statements_found"] == 0
    assert out["verdict"] == "(ii)"
    assert all(
        not v["quantitative"] for v in out["L10_text_in_repo"].values()
    )


def test_neo_20R_co_safety_duoi_1_va_K4_bi_lat():
    q = L.archaeology_L10()["quantitative_anchor_that_does_exist"]
    assert q["safety_lt_1"] is True
    assert q["safety_published"] == pytest.approx(0.868750, abs=1e-6)
    assert "K4_path_ranking_preserved" in q["first_broken"]
    assert "poisson@0.925" in q["first_broken_cell"]
    # Thu hang top-1 doi that su, khong chi mot co bi bat.
    det = q["k4_detail"]["poisson@0.925"]
    assert det["base"][0] != det["pert"][0]


def test_safety_published_la_ti_so_r_star_tren_residual_do_duoc():
    """Dong nhat thuc tai lap `safety_published` tu hai con so goc."""
    bs = L.archaeology_L10()["quantitative_anchor_that_does_exist"]["binding_scan_numbers"]
    assert bs["safety_identity_r_star_lo_over_ci90_worst"] == pytest.approx(
        0.868750, abs=1e-6
    )
    assert bs["residual_over_flip_threshold"] > 1.0


# ---------------------------------------------------------------------------
# 4. q_hat tensor doc tu artifact
# ---------------------------------------------------------------------------

def test_qhat_tensor_dung_hinh_dang_va_huu_han():
    arr = L.qhat_tensor()
    assert arr.shape == (4, 4, 3)
    assert np.isfinite(arr).all()
    assert (arr > 0).all()


def test_M1_M2_M3_khop_gia_tri_da_cong_bo():
    """[TAT DINH]: ba con so nay doc tu artifact da commit, phai on dinh."""
    out = L.separability_audit(L.qhat_tensor())
    assert out["M_1_spread_m"] == pytest.approx(1.1188, abs=5e-4)
    assert out["M_2_spread_z"] == pytest.approx(2.1232, abs=5e-4)
    assert out["M_3_spread_total"] == pytest.approx(2.6134, abs=5e-4)
    assert out["separability_gap_rel"] == pytest.approx(0.0156, abs=5e-4)


def test_M3_nam_NGOAI_dai_phac_1_2_den_2_0():
    """Dai M-3 mau thuan voi dai M-2: spread_z mot minh da vuot can tren M-3."""
    out = L.separability_audit(L.qhat_tensor())
    assert not (1.2 <= out["M_3_spread_total"] <= 2.0)
    assert out["M_2_spread_z"] > 2.0        # nguon cua mau thuan

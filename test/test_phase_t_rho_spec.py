"""Phase T / T.2 -- contract tests for pure rho(t) generation."""

import statistics as st

import pytest

from mininet.rho_spec import (
    RHO_MAX,
    RHO_MIN,
    expected_sigma_hat,
    measure_mean,
    measure_sigma,
    measure_tau,
    mminf_trajectory,
    ou_trajectory,
    sigma_from_a,
    sigma_max_feasible,
    sub_seed,
)


GRID_RHO_BAR = (0.70, 0.85, 0.925, 0.98)
GRID_A = (0.20, 0.90)
GRID_TAU = (0.2, 1.0, 5.0)


def test_vt0_cung_seed_cung_digest():
    a = ou_trajectory(0.85, 0.05, 1.0, 5000, 11)
    b = ou_trajectory(0.85, 0.05, 1.0, 5000, 11)
    assert a.digest() == b.digest()
    assert a.rho == b.rho


@pytest.mark.parametrize(
    "khac",
    [
        dict(seed=12),
        dict(tau_rho=2.0),
        dict(sigma_rho=0.06),
        dict(rho_bar=0.86),
        dict(dt=0.010),
    ],
)
def test_vt0_doi_bat_ky_tham_so_nao_thi_digest_doi(khac):
    goc = dict(rho_bar=0.85, sigma_rho=0.05, tau_rho=1.0, n_steps=5000, seed=11)
    moi = dict(goc)
    moi.update(khac)
    assert ou_trajectory(**goc).digest() != ou_trajectory(**moi).digest()


def test_sub_seed_tach_dong_theo_nhan():
    assert sub_seed(11, "rho_ou") != sub_seed(11, "rho_mminf")
    assert sub_seed(11, "rho_ou") != sub_seed(12, "rho_ou")
    assert sub_seed(11, "rho_ou") == sub_seed(11, "rho_ou")


@pytest.mark.parametrize(
    "sigma_rho,tau_rho",
    [(0.0054, 0.2), (0.0155, 1.0), (0.0436, 5.0), (0.0698, 1.0), (0.0698, 0.2)],
)
def test_vt1_sigma_bo_sinh_khop_thiet_ke_duoi_1_phan_tram(sigma_rho, tau_rho):
    t = ou_trajectory(
        0.75,
        sigma_rho,
        tau_rho,
        1_000_000,
        99,
        dt=tau_rho / 2.0,
        lo=-9.0,
        hi=9.0,
    )
    assert measure_sigma(t.rho) == pytest.approx(sigma_rho, rel=0.01)


@pytest.mark.parametrize(
    "sigma_rho,tau_rho",
    [(0.0054, 0.2), (0.0155, 1.0), (0.0436, 5.0), (0.0698, 1.0), (0.0698, 0.2)],
)
def test_vt2_tau_bo_sinh_khop_thiet_ke_duoi_2_phan_tram(sigma_rho, tau_rho):
    t = ou_trajectory(
        0.75,
        sigma_rho,
        tau_rho,
        1_000_000,
        99,
        dt=tau_rho / 2.0,
        lo=-9.0,
        hi=9.0,
    )
    assert measure_tau(t.rho, t.dt) == pytest.approx(tau_rho, rel=0.02)


@pytest.mark.parametrize("rho_bar", GRID_RHO_BAR)
@pytest.mark.parametrize("a", GRID_A)
def test_vt3_moi_o_luoi_co_ti_le_kep_duoi_1_phan_tram(rho_bar, a):
    t = ou_trajectory(rho_bar, sigma_from_a(rho_bar, a), 1.0, 200_000, 7)
    assert t.clamp_ratio < 0.01


@pytest.mark.parametrize("rho_bar", GRID_RHO_BAR)
@pytest.mark.parametrize("a", GRID_A)
def test_moi_gia_tri_rho_nam_trong_mien_cua_link_model_v2(rho_bar, a):
    t = ou_trajectory(rho_bar, sigma_from_a(rho_bar, a), 1.0, 50_000, 7)
    assert min(t.rho) >= RHO_MIN - 1e-12
    assert max(t.rho) <= RHO_MAX + 1e-12


def test_sigma_max_lay_min_cua_hai_phia_khong_phai_mot_phia():
    """Guard against the T.1 draft bug: only checking the upper boundary."""
    assert sigma_max_feasible(0.70) == pytest.approx(0.20 / 2.58, rel=1e-9)
    assert sigma_max_feasible(0.98) == pytest.approx(0.07 / 2.58, rel=1e-9)
    for rho_bar in GRID_RHO_BAR:
        assert sigma_max_feasible(rho_bar) <= (1.05 - rho_bar) / 2.58 + 1e-12


def test_vt5_sigma_bang_khong_cho_duong_hang_so():
    t = ou_trajectory(0.90, 0.0, 1.0, 1000, 11)
    assert t.kind == "const"
    assert t.n_clamped == 0
    assert set(t.rho) == {0.90}


def test_vt5_duong_hang_so_khong_phu_thuoc_seed_hay_tau():
    a = ou_trajectory(0.90, 0.0, 1.0, 1000, 11)
    b = ou_trajectory(0.90, 0.0, 999.0, 1000, 77)
    assert a.digest() == b.digest()


def test_bat_dau_o_trang_thai_dung_khong_phai_o_trung_binh():
    starts = [ou_trajectory(0.80, 0.05, 5.0, 10, s, lo=-9, hi=9).rho[0] for s in range(200)]
    assert st.pstdev(starts) == pytest.approx(0.05, rel=0.15)
    assert st.mean(starts) == pytest.approx(0.80, abs=0.02)


@pytest.mark.parametrize("tau_rho", GRID_TAU)
def test_cong_thuc_thien_lech_khop_monte_carlo_tren_cua_so_90s(tau_rho):
    sigma_rho = 0.0698
    n = int(round(90.0 / 0.005))
    mc = st.mean(
        measure_sigma(ou_trajectory(0.75, sigma_rho, tau_rho, n, s, lo=-9, hi=9).rho)
        for s in range(40)
    )
    assert mc == pytest.approx(expected_sigma_hat(sigma_rho, tau_rho, 90.0), rel=0.15)


def test_thien_lech_lon_dan_khi_tau_lon_dan():
    e = [expected_sigma_hat(0.05, tau, 90.0) for tau in GRID_TAU]
    assert e[0] > e[1] > e[2]
    assert e[2] / 0.05 < 0.96


@pytest.mark.parametrize(
    "rho_bar,sigma_rho,tau_rho",
    [(0.85, 0.0698, 1.0), (0.70, 0.0698, 5.0), (0.925, 0.0436, 1.0)],
)
def test_mminf_khop_ca_ba_tham_so_thiet_ke(rho_bar, sigma_rho, tau_rho):
    t = mminf_trajectory(
        rho_bar,
        sigma_rho,
        tau_rho,
        400_000,
        5,
        dt=tau_rho / 4.0,
        lo=-9.0,
        hi=9.0,
    )
    assert measure_mean(t.rho) == pytest.approx(rho_bar, rel=0.02)
    assert measure_sigma(t.rho) == pytest.approx(sigma_rho, rel=0.03)
    assert measure_tau(t.rho, t.dt) == pytest.approx(tau_rho, rel=0.03)


def test_mminf_va_ou_cho_cung_thong_ke_bac_hai():
    kw = dict(
        rho_bar=0.85,
        sigma_rho=0.0698,
        tau_rho=1.0,
        n_steps=400_000,
        seed=5,
        dt=0.25,
        lo=-9.0,
        hi=9.0,
    )
    a = ou_trajectory(**kw)
    b = mminf_trajectory(**kw)
    assert measure_sigma(a.rho) == pytest.approx(measure_sigma(b.rho), rel=0.05)
    assert measure_tau(a.rho, 0.25) == pytest.approx(measure_tau(b.rho, 0.25), rel=0.05)
    assert a.digest() != b.digest()


@pytest.mark.parametrize(
    "kw",
    [
        dict(rho_bar=0.85, sigma_rho=-0.01, tau_rho=1.0),
        dict(rho_bar=0.85, sigma_rho=0.05, tau_rho=0.0),
        dict(rho_bar=0.40, sigma_rho=0.05, tau_rho=1.0),
        dict(rho_bar=1.20, sigma_rho=0.05, tau_rho=1.0),
    ],
)
def test_tham_so_vo_ly_thi_bao_loi_som(kw):
    with pytest.raises(ValueError):
        ou_trajectory(n_steps=100, seed=1, **kw)


def test_n_steps_khong_duong_thi_bao_loi():
    with pytest.raises(ValueError):
        ou_trajectory(0.85, 0.05, 1.0, 0, 1)

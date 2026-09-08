"""T2.5 nhanh NHAY CAM -- u_cond (QD-1 cua prereg T2).

Bo test nay bao ve MOT QUAN HE, khong bao ve mot con so. Neu no do, cong
thuc hoi quy ve trung binh dang bi cai sai -- khong phai mang dang khac di.

`u` cu KHONG mat bao dam bao phu (Mondrian hop le voi moi taxonomy co dinh
truoc). Nhanh nay do MUC KEM HIEU QUA cua no, va do la mot phep do, khong
phai mot ban sua loi.
"""
from __future__ import annotations

import numpy as np
import pytest

from cert.build_calib_set import TAU_CORE_MEASURED_S, U_EDGES, _bin_with_edge_warnings

SIGMA = 0.010


def u_plain(rho, thr, sig_z):
    return abs(rho - thr) / sig_z


def u_conditional(rho, mu, thr, z, tau, sig_z):
    phi = np.exp(-z / tau)
    return abs(mu + phi * (rho - mu) - thr) / sig_z


def sig_z_of(z, tau=TAU_CORE_MEASURED_S, sigma=SIGMA):
    return sigma * np.sqrt(1.0 - np.exp(-2.0 * z / tau))


# --- BIEN THAI: quan he, khong phai gia tri -----------------------------

def test_u_cond_converges_to_u_as_z_goes_to_zero():
    """phi_z -> 1 thi mu + 1*(rho-mu) = rho, nen u_cond -> u.

    Bat sai dau trong (rho - mu) va nham mu voi nguong.
    """
    rho, mu, thr, tau = 0.93, 0.90, 0.95, TAU_CORE_MEASURED_S
    for z in (1e-6, 1e-5, 1e-4):
        s = sig_z_of(z)
        assert u_conditional(rho, mu, thr, z, tau, s) == pytest.approx(
            u_plain(rho, thr, s), rel=1e-3)


def test_u_cond_pulls_toward_the_mean_as_z_grows():
    """z lon thi du bao ve mu, nen TU SO tien den |mu - nguong|.

    Day la noi dung vat ly cua hoi quy ve trung binh.
    """
    rho, mu, thr, tau = 0.93, 0.90, 0.95, TAU_CORE_MEASURED_S
    z = 50.0 * tau
    s = sig_z_of(z)
    assert u_conditional(rho, mu, thr, z, tau, s) == pytest.approx(
        abs(mu - thr) / s, rel=1e-6)


def test_the_two_definitions_differ_where_the_prereg_says_they_do():
    """QD-1 do san: bo qua 4.9% o z/tau=0.05 va 63% o z/tau=1.00.

    Kiem chinh BANG SO da ghi trong prereg, khong phai mot so moi.
    """
    for z_over_tau, want in ((0.05, 0.049), (0.19, 0.17),
                             (1.00, 0.63), (2.50, 0.92)):
        assert 1.0 - np.exp(-z_over_tau) == pytest.approx(want, abs=0.005)


def test_u_cond_is_never_negative_and_stays_finite():
    tau = TAU_CORE_MEASURED_S
    for z in (0.05, 0.10, 0.30, 0.55):
        s = sig_z_of(z)
        for rho in (0.50, 0.70, 0.925, 1.05):
            v = u_conditional(rho, 0.90, 0.95, z, tau, s)
            assert np.isfinite(v) and v >= 0.0


def test_bin_edges_are_shared_between_the_two_arms():
    """CUNG U_EDGES: doi bien cho vua u_cond la chon bin SAU khi nhin du lieu.

    Neu phan bo u_cond lech khoi U_EDGES thi do CHINH LA phat hien.
    """
    tau = TAU_CORE_MEASURED_S
    z, s = 0.30, sig_z_of(0.30)
    rho = np.linspace(0.50, 1.05, 400)
    a, _ = _bin_with_edge_warnings(u_plain(rho, 0.95, s), U_EDGES)
    b, db = _bin_with_edge_warnings(
        u_conditional(rho, 0.90, 0.95, z, tau, s), U_EDGES)
    assert db["n_bins"] == len(U_EDGES) - 1
    # KHONG khang dinh chung khac nhau: muc khac biet la KET QUA cua T2.6,
    # khong phai mot dieu kien de test xanh.
    assert set(np.unique(b)) <= set(range(len(U_EDGES) - 1))
    assert a.dtype == b.dtype


# --- chan doan bin: mot o rong phai NHIN THAY DUOC ----------------------

def test_bin_diagnostics_expose_an_empty_bin():
    """Mot bin rong khong lam conformal SAI -- no lam q_hat = inf va
    coverage = 1.0 (cert/conformal_age.py). Chung chi VO DUNG ma bao cao
    HOAN HAO. Khong dem thi khong thay.
    """
    values = np.array([0.1, 0.5, 0.9, 1.2, 5.0, 5.5])
    _bins, diag = _bin_with_edge_warnings(values, U_EDGES)
    assert diag["n_per_bin"] == [3, 1, 0, 2]
    assert diag["n_min_bin"] == 0
    assert diag["empty_bins"] == [2]

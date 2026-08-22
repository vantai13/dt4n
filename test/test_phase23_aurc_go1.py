"""Golden tests -- cert.aurc_go1, Phase 23 Lesson 23.5[B].

Moi test tuong ung MOT bay da xac nhan trong Amendment 23-22/23.
Khong bao gio xoa test o day.
"""

import os

import numpy as np
import pandas as pd
import pytest

import cert.aurc_go1 as AG
from cert.config_matrix import DEGENERATE_ERR

CALIB = "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.925.parquet"
needs_data = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu artifact v3")


# --------------------------------------------------------------------------
# Nhom 1: kernel
# --------------------------------------------------------------------------

def test_A1_aurc_of_constant_curve_equals_the_constant():
    """Kiem tra don vi: R(gamma) = 0.2 khap noi -> AURC = 0.2 (khong phai 0.08)."""
    x = np.array([0.0, 0.5, 1.0]); y = np.array([0.2, 0.2, 0.2])
    assert AG.aurc_window(x, y)["aurc"] == pytest.approx(0.2, abs=1e-12)


def test_A2_aurc_of_linear_curve_equals_midpoint_value():
    """R(g) = g  ->  trung binh tren [0.6,1.0] = 0.8."""
    x = np.array([0.0, 1.0]); y = np.array([0.0, 1.0])
    assert AG.aurc_window(x, y)["aurc"] == pytest.approx(0.8, abs=1e-6)


def test_A3_extrapolation_raises_in_strict_mode():
    """B-D4: np.interp pad PHANG -- so bia. Phai no, khong duoc im lang."""
    x = np.array([0.0, 0.3, 0.5]); y = np.array([0.0, 0.1, 0.2])
    with pytest.raises(ValueError, match="khong phu cua so"):
        AG.aurc_window(x, y, strict=True)
    r = AG.aurc_window(x, y, strict=False)
    assert r["extrapolated"] and not np.isfinite(r["aurc"])


def test_A4_none_round_trip_does_not_crash():
    """Bay 7: err_given_accept -> JSON null -> float(None) TypeError."""
    assert np.isnan(AG.as_float_nan(None))
    x = np.array([0.5, 0.8, 1.0])
    y = np.array([AG.as_float_nan(v) for v in (None, 0.15, 0.22)])
    with pytest.raises(ValueError):          # chi con 2 diem, khong phu 0.6
        AG.aurc_window(x, y, strict=True)


def test_A5_require_refuses_silent_defaults():
    """Bay 2: .get(key, 0.0) bien 'khong tinh duoc' thanh gia tri TOT NHAT."""
    with pytest.raises(KeyError, match="partial"):
        AG.require({"beneficial": False}, "partial_aurc_060_100")


def test_A6_duplicate_acceptance_keeps_min_risk():
    """B-D9."""
    x = np.array([0.5, 0.8, 0.8, 1.0]); y = np.array([0.1, 0.30, 0.16, 0.22])
    ux, uy, d = AG.prepare_curve(x, y)
    assert d["n_duplicate_acceptance"] == 1
    assert uy[list(ux).index(0.8)] == pytest.approx(0.16)


def test_A7_no_monotonisation_violations_are_reported_not_fixed():
    """B-D11: khong sua, chi BAO CAO."""
    x = np.array([0.5, 0.8, 1.0]); y = np.array([0.20, 0.10, 0.22])
    _ux, uy, d = AG.prepare_curve(x, y)
    assert d["n_monotonicity_violations"] == 1
    assert not d["monotone_nondecreasing"]
    assert uy[1] == pytest.approx(0.10)          # KHONG bi nang len


def test_A8_common_grid_differs_from_own_grid_trapezoid():
    """Bay 3: hai duong lay mau o diem KHAC NHAU -> hai cach cho hai so.
    Test nay khoa SU TON TAI cua hieu ung, khong khoa dau cua no."""
    xa = np.array([0.586, 0.788, 1.0]); ya = np.array([0.1034, 0.1599, 0.2224])
    xb = np.array([0.491, 0.738, 1.0]); yb = np.array([0.0809, 0.1456, 0.2224])
    own = (np.trapezoid(ya, xa) / (xa.max() - xa.min())) / \
          (np.trapezoid(yb, xb) / (xb.max() - xb.min()))
    common = AG.aurc_window(xb, yb)["aurc"] / AG.aurc_window(xa, ya)["aurc"]
    assert abs(own - common) > 1e-3, "hieu ung luoi bien mat -> kiem lai"


def test_A9_block_sufficient_stats_reproduce_full_sample_exactly():
    """Xuong song bootstrap: picks=None phai bang mean() tren toan bo hang."""
    rng = np.random.default_rng(0)
    nb, per = 40, 25
    st = {
        "n_rows": np.full(nb, per, np.float64),
        "n_acc": rng.integers(0, per + 1, nb).astype(np.float64),
    }
    st["n_wrong_acc"] = np.array([rng.integers(0, a + 1) for a in st["n_acc"]], np.float64)
    acc, err = AG.curve_from_stats([st], picks=None)
    assert acc[0] == pytest.approx(st["n_acc"].sum() / st["n_rows"].sum())
    assert err[0] == pytest.approx(st["n_wrong_acc"].sum() / st["n_acc"].sum())


def test_A10_zero_accept_block_gives_nan_not_zero():
    """n_acc = 0 -> err|accept = nan. Tra 0.0 se lam AURC nho gia tao."""
    st = {"n_rows": np.array([10.0]), "n_acc": np.array([0.0]),
          "n_wrong_acc": np.array([0.0])}
    _acc, err = AG.curve_from_stats([st], picks=None)
    assert np.isnan(err[0])


# --------------------------------------------------------------------------
# Nhom 2: du lieu that
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real():
    return pd.read_parquet(CALIB)


@pytest.fixture(scope="module")
def real_stats(real):
    """Thong ke du tren luoi primary, dung chung cho cac test doi chung."""
    calib = real[real["is_calib"].to_numpy(bool)]
    test = real[~real["is_calib"].to_numpy(bool)]
    return (
        AG.build_stats(calib, test, AG.CONFIG_NUM, AG.KAPPA_PRIMARY),
        AG.build_stats(calib, test, AG.CONFIG_DEN, AG.KAPPA_PRIMARY),
    )


@pytest.fixture(scope="module")
def cell_result(real):
    return AG.run_cell(real, n_boot=50)


@needs_data
def test_A11_reproduces_the_audit_numbers(cell_result):
    """Kiem tra tai lap: luoi primary PHAI cho dung so da ghi o Amendment 23-22.
    Neu do nay: hoac code doi, hoac du lieu doi. Ca hai deu phai biet ngay."""
    assert cell_result["status"] == "EVALUABLE"
    assert cell_result["grid_primary"]["ratio_point"] == pytest.approx(1.002492, abs=5e-5)


@needs_data
def test_A12_primary_grid_has_only_three_effective_knots(cell_result):
    """Phat hien 8, khoa bang test: cua so [0.6,1] chi tua tren 3 knot."""
    p = cell_result["grid_primary"]
    for cfg in (AG.CONFIG_NUM, AG.CONFIG_DEN):
        assert p["aurc_%s" % cfg]["n_knots_in_window"] == 2
        assert p["aurc_%s" % cfg]["n_knots_effective"] == 3
        assert p["aurc_%s" % cfg]["widest_segment_in_window"] > 0.20
    assert not p["grid_adequacy"]["pass"]


@needs_data
def test_A13_refined_grid_actually_refines(cell_result):
    """B-D12/B-D14 phai LAM GI DO. Neu khong, luoi min la trang tri."""
    r = cell_result["grid_refined"]
    for cfg in (AG.CONFIG_NUM, AG.CONFIG_DEN):
        assert r["aurc_%s" % cfg]["n_knots_in_window"] >= AG.MIN_KNOTS_IN_WINDOW
        assert r["aurc_%s" % cfg]["widest_segment_in_window"] < AG.MAX_SEGMENT_IN_WINDOW
    assert r["grid_adequacy"]["pass"]


@needs_data
def test_A14_NC_A_1_paired_self_ratio_is_exactly_one(real_stats):
    """NC-A-1. Do rong CI > 0 <=> ghep cap HONG. Test re nhat, manh nhat."""
    _sn, sd = real_stats
    nc = AG.negative_control_self_ratio(sd, n_boot=100)
    assert nc["pass"], nc


@needs_data
def test_A15_PC_A_1_detects_a_ten_percent_shift(real_stats):
    """PC-A-1. Neu doi chung duong khong kich hoat, CI vo nghia."""
    sn, sd = real_stats
    pc = AG.positive_control_shift(sn, sd, shift=1.10, n_boot=300)
    assert pc["pass"], pc
    assert 1.05 < pc["ratio_mean"] < 1.15


@needs_data
def test_A16_pairing_is_not_cosmetic(real_stats):
    """Ghep cap phai LAM HEP CI thuc su, neu khong no chi la mot nhan."""
    sn, sd = real_stats
    paired = AG.paired_bootstrap_ratio(sn, sd, n_boot=300)
    assert paired["corr_num_den"] > 0.95, paired["corr_num_den"]
    assert paired["ci95_width"] > 0.0


@needs_data
def test_A17_degenerate_cell_is_flagged_not_scored():
    """B-D5/B-D6: poisson@0.700 co err_neo ~ 0 -> DEGENERATE, ratio None.
    aurc() cu tra 0.0 o day, tuc 'tot nhat co the' -> 0/0."""
    path = "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.700.parquet"
    if not os.path.exists(path):
        pytest.skip("thieu cell suy bien")
    res = AG.run_cell(pd.read_parquet(path), n_boot=10)
    assert res["status"] == "DEGENERATE"
    assert res["ratio"] is None
    assert res["err_neo"] < DEGENERATE_ERR


@needs_data
@pytest.mark.slow
def test_A18_mc_error_shrinks_as_one_over_sqrt_B_but_width_does_not(real_stats):
    """Hai menh de KHAC NHAU, va lan dau thiet ke da gop nham lam mot.

    Do rong CI hoi tu ve HANG SO (dinh boi so BLOCK). Thu co theo 1/sqrt(B) la
    SAI SO MONTE CARLO cua dau mut. Ap tieu chi "width ~ 1/sqrt(B)" se lam mot
    bootstrap DUNG bi FAIL.
    """
    sn, sd = real_stats
    mc = AG.mc_convergence(sn, sd, n_seeds=6)
    assert mc["pass_width_stabilises"], mc["ladder"]
    assert mc["pass_mc_error_shrinks"], mc["ladder"]

    widths = [r["ci95_width_mean"] for r in mc["ladder"]]
    # width KHONG duoc co theo 1/sqrt(B): B tang 10x thi width van gan nhu cu
    assert widths[-1] > 0.5 * widths[0], widths

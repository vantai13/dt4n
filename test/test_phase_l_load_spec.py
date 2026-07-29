#!/usr/bin/env python3
"""Phase L / L.4 -- tests for pure load schedule generation."""

import pytest

from mininet.load_spec import (
    FRAME_BG,
    FRAME_PROBE,
    MODES,
    PROBE_PPS,
    aggregate_ca,
    background_pps,
    build_schedule,
    cv,
    h2_params,
    merge_schedules,
    normalize_rate,
    rho_from_rates,
    schedule_digest,
)


BW = 6.0
RHO = 0.90
BG = background_pps(RHO, BW)
MG = 1.0 / BG
N = 30000


def test_rho_di_va_ve_khop_chinh_xac():
    assert rho_from_rates(BG, PROBE_PPS, BW) == pytest.approx(RHO, abs=1e-12)


def test_gia_tri_khoa_cho_cau_hinh_tham_chieu():
    assert BG == pytest.approx(445.0265, abs=1e-3)
    assert MG * 1e3 == pytest.approx(2.24706, abs=1e-4)
    assert (FRAME_BG, FRAME_PROBE) == (1512, 106)


def test_probe_duoc_tinh_vao_rho():
    assert background_pps(RHO, BW, probe_pps=0) > background_pps(RHO, BW, probe_pps=20)


@pytest.mark.parametrize(
    ("mode", "want", "tol"),
    [
        ("cbr", 0.0, 1e-12),
        ("poisson", 1.0, 0.05),
        ("h2", 2.0, 0.05),
    ],
)
def test_c_a_dat_dung_muc_tieu(mode, want, tol):
    assert cv(build_schedule(mode, N, MG, seed=1)) == pytest.approx(want, abs=tol)


def test_h2_on_dinh_giua_cac_seed_con_onoff_thi_khong():
    h2 = [cv(build_schedule("h2", N, MG, seed=s)) for s in range(5)]
    onoff = [cv(build_schedule("onoff", N, MG, seed=s)) for s in range(5)]

    def rel(values):
        return (max(values) - min(values)) / (sum(values) / len(values))

    assert rel(h2) < 0.05
    assert rel(onoff) > 0.15
    assert rel(onoff) > 3 * rel(h2)


def test_h2_tu_choi_c_a_nho_hon_1():
    with pytest.raises(ValueError):
        h2_params(MG, ca=0.5)


@pytest.mark.parametrize("mode", MODES)
def test_moi_che_do_dat_dung_toc_do_muc_tieu(mode):
    gaps = build_schedule(mode, N, MG, seed=3)
    assert (sum(gaps) / len(gaps)) == pytest.approx(MG, rel=1e-9)


def test_co_gian_thoi_gian_khong_doi_c_a():
    gaps = build_schedule("onoff", N, MG, seed=5)
    assert cv(normalize_rate(gaps, MG * 7.3)) == pytest.approx(cv(gaps), rel=1e-9)


@pytest.mark.parametrize("mode", MODES)
def test_cung_seed_cho_cung_digest(mode):
    a = schedule_digest(build_schedule(mode, 5000, MG, seed=42))
    b = schedule_digest(build_schedule(mode, 5000, MG, seed=42))
    assert a == b


@pytest.mark.parametrize("mode", ["poisson", "h2", "onoff"])
def test_mode_ngau_nhien_seed_khac_cho_digest_khac(mode):
    a = schedule_digest(build_schedule(mode, 5000, MG, seed=42))
    b = schedule_digest(build_schedule(mode, 5000, MG, seed=43))
    assert a != b


def test_cbr_khong_phu_thuoc_seed():
    a = schedule_digest(build_schedule("cbr", 5000, MG, seed=42))
    b = schedule_digest(build_schedule("cbr", 5000, MG, seed=43))
    assert a == b


def test_gop_lich_sap_xep_dung_va_du_so_luong():
    events = merge_schedules(
        build_schedule("cbr", 100, MG, 1),
        build_schedule("poisson", 10, 1 / PROBE_PPS, 2),
    )
    assert len(events) == 110
    assert all(events[i][0] <= events[i + 1][0] for i in range(len(events) - 1))
    assert sum(1 for _t, is_probe in events if is_probe) == 10


def test_probe_lam_c_a_tong_hop_khac_c_a_nen_o_che_do_cbr():
    bg = build_schedule("cbr", 20000, MG, 1)
    probe = build_schedule("poisson", 900, 1 / PROBE_PPS, 2)
    assert cv(bg) == pytest.approx(0.0, abs=1e-12)
    assert aggregate_ca(merge_schedules(bg, probe)) > 0.05


def test_mode_khong_hop_le_bi_tu_choi():
    with pytest.raises(ValueError):
        build_schedule("bursty", 100, MG, 1)

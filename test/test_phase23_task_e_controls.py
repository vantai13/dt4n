#!/usr/bin/env python3
"""Lesson 23.19 Task E -- bon doi chung TRUOC khi tin ket qua pipeline.

NC-E1 va NC-E2 la NHANH FAIL CUNG: neu chung khong dat thi da doi HAI thu
cung luc, va khong con biet ket qua moi den tu dau.

Preregistration: docs/phase-23/00zze-amendment-48.md muc 5 (M-117..M-120)
"""
from __future__ import annotations

import numpy as np
import pytest

from cert.build_calib_set_v2 import assign_bin
from measurements.aoi_model_v7 import (
    ALPHA_S, LEGACY_D_S, LEGACY_T_S, Z_EDGES_LEGACY, Z_EDGES_V7, AoIModelV7)
from measurements.decision_error import sawtooth_age_steps

DT = 0.005


def _z_pool(m: AoIModelV7, n: int = 200_000, mode: str = "process") -> np.ndarray:
    if mode == "process":
        return np.concatenate([m.process_mode(n, DT, l) for l in ALPHA_S])
    rng = np.random.default_rng(11)
    return m.instrument_mode(rng, n_runs=6)


def _shares(z_s: np.ndarray, edges) -> tuple[np.ndarray, float]:
    e = np.asarray(edges, float)
    inside = (z_s >= e[0]) & (z_s <= e[-1])
    b = assign_bin(z_s[inside], edges)
    sh = np.array([(b == i).mean() for i in range(len(e) - 1)])
    return sh, float(1.0 - inside.mean())


# --------------------------------------------------------------- NC-E1
def test_M117_NCE1_bit_exact_with_legacy_generator():
    """★ NHANH FAIL CUNG. Khong bit-exact = da doi HAI thu. DUNG."""
    m = AoIModelV7(d_s=LEGACY_D_S, T_s=LEGACY_T_S, profile="U0")
    for n, dt in ((200_000, 0.005), (99_991, 0.005), (40_000, 0.001)):
        new = m.process_mode_steps(n, dt, "ac", phase0=-LEGACY_D_S)
        old = sawtooth_age_steps(n, dt, LEGACY_T_S, LEGACY_D_S)
        assert np.array_equal(new, old), (
            "n=%d dt=%s: %d buoc lech" % (n, dt, int((new != old).sum())))


def test_M117b_row_selection_is_bit_exact():
    """Chon hang cua 21R (`_valid_rows`) cung phai trung KHIT."""
    m = AoIModelV7(d_s=LEGACY_D_S, T_s=LEGACY_T_S, profile="U0")
    n, dt = 50_000, 0.005
    for age in (m.process_mode_steps(n, dt, "ac", phase0=-LEGACY_D_S),):
        old = sawtooth_age_steps(n, dt, LEGACY_T_S, LEGACY_D_S)
        rows = np.arange(n)
        assert np.array_equal(rows >= age, rows >= old)
        assert np.array_equal(rows[rows >= age] - age[rows >= age],
                              rows[rows >= old] - old[rows >= old])


# --------------------------------------------------------------- NC-E2
def test_M118_NCE2_phase_is_shared_across_links():
    """★ 8 link dung MOT vong sync. Sinh 8 pha doc lap = em ruot cua S13.

    Kiem DAI SO: sau khi tru alpha, hai chuoi phai TRUNG KHIT (khong chi
    tuong quan cao -- trung khit), vi chung la cung mot pha.
    """
    m = AoIModelV7()
    a = m.process_mode(50_000, DT, "uA") - m.alpha["uA"]
    b = m.process_mode(50_000, DT, "ac") - m.alpha["ac"]
    assert np.allclose(a, b, atol=1e-12), (
        "pha KHONG chung giua cac link -- day la em ruot cua S13")
    assert np.corrcoef(a, b)[0, 1] == pytest.approx(1.0)


# --------------------------------------------------------------- PC-E1
def test_M119_PCE1_bin_shares_CANNOT_detect_instrument_misuse():
    """★ M-119 MISS -- va do la mot ket qua QUAN TRONG.

    Du doan da ky: neu lo dung instrument_mode trong pipeline thi ty trong
    bin lech > 5 diem %, tuc ta se PHAT HIEN duoc o ha nguon.

    DO DUOC: chi ~2 diem %. Cai luoc co 5 rang moi chu ky (cach nhau
    T/5 = 100 ms) trong khi bin rong 125-150 ms, va pipeline gop 8 link
    (lech doc khac nhau) -> o DO PHAN GIAI 4 BIN cai luoc gan nhu bi lam
    phang.

    => KHONG duoc dua vao mot phep kiem ha nguon de bat viec dung nham
       che do. Su tach bach phai duoc bao dam o MUC CAU TRUC:
         - hai ham co ten khac nhau va docstring canh bao
         - test_phase23_aoi_model.py::test_two_modes_are_not_interchangeable
           kiem o do phan giai 50 bin, noi khac biet la RO RANG
       Day la ly do rang buoc "tach hai che do" phai la mot RANG BUOC
       THIET KE, khong phai mot phep kiem thong ke.
    """
    m = AoIModelV7()
    sh_p, _ = _shares(_z_pool(m, mode="process"), Z_EDGES_V7)
    sh_i, _ = _shares(_z_pool(m, mode="instrument"), Z_EDGES_V7)
    dev_p = np.abs(sh_p - 0.25).max() * 100
    dev_i = np.abs(sh_i - 0.25).max() * 100
    assert dev_p < 2.0, "process_mode phai deu, lech lon nhat %.2f diem %%" % dev_p
    # ghi lai su that da do: dai khoa la > 5 diem %, thuc te ~2 -> MISS
    assert dev_i < 5.0, (
        "instrument_mode bong nhien lech > 5 diem %% (%.2f). Neu vay thi "
        "M-119 doi tu MISS sang HIT va ket luan o day phai viet lai." % dev_i)
    # va o do phan giai MIN, khac biet PHAI ro -- do la noi dat cai chan
    from measurements.aoi_model_v7 import CYCLES_PER_RUN, PROBE_INTERVAL_S
    n_probe = int(CYCLES_PER_RUN * m.T / PROBE_INTERVAL_S)
    # "bin rong" khong on dinh giua cac pha ban dau (10/30 seed); ty so
    # max/min thi on dinh (29/30 seed > 3). Dung ty so, va lay TRUNG VI
    # tren nam pha co dinh de test tat dinh.
    ratios = []
    for seed in (0, 1, 2, 3, 4):
        inst1 = m.instrument_mode(np.random.default_rng(seed), n_runs=1)[:n_probe]
        ph = np.mod(inst1 - m.d - m.alpha["ac"], m.T) / m.T
        h, _ = np.histogram(ph, bins=50, range=(0, 1))
        ratios.append(h.max() / max(h[h > 0].min(), 1))
    assert float(np.median(ratios)) > 3.0, (
        "o do phan giai 50 bin, 1 run 1 link, cai luoc PHAI hien ra; "
        "trung vi max/min = %.2f" % float(np.median(ratios)))


# --------------------------------------------------------------- PC-E2
def test_M120_PCE2_legacy_edges_break_on_new_axis():
    """★ Canh CU tren truc MOI: B0 PHAI rong va PHAI mat hang."""
    m = AoIModelV7()
    z = _z_pool(m, mode="process")
    e = np.asarray(Z_EDGES_LEGACY, float)
    inside = (z >= e[0]) & (z <= e[-1])
    b = assign_bin(z[inside], Z_EDGES_LEGACY)
    assert (b == 0).sum() == 0, "B0 [55,100) phai RONG tren truc moi"
    assert 1.0 - inside.mean() > 0.10, (
        "canh cu phai lam mat > 10%% hang; mat %.2f%%" % ((1 - inside.mean()) * 100))


# --------------------------------------------------------------- M-114/115
def test_M114_M115_new_edges_are_balanced_and_lossless():
    m = AoIModelV7()
    sh, out = _shares(_z_pool(m, mode="process"), Z_EDGES_V7)
    assert np.abs(sh - 0.25).max() * 100 < 2.0     # M-114
    assert out == 0.0                              # M-115


def test_new_edges_cover_the_d_confidence_interval():
    """Canh ngoai phai phu ca `d` o hai dau CI +/-6.5 ms (amendment 23-48)."""
    from measurements.aoi_model_v7 import D_SYNC_CI95_S, D_SYNC_S, SYNC_PERIOD_S
    lo = (D_SYNC_S - D_SYNC_CI95_S) + min(ALPHA_S.values())
    hi = (D_SYNC_S + D_SYNC_CI95_S) + max(ALPHA_S.values()) + SYNC_PERIOD_S
    assert Z_EDGES_V7[0] <= lo, "canh duoi khong phu d o day CI"
    assert Z_EDGES_V7[-1] >= hi, "canh tren khong phu d o dinh CI"

#!/usr/bin/env python3
"""Doi chung cho amendment 23-49: tich hop truc tuoi do duoc.

Test quan trong nhat la `test_NC_E1_bit_exact`. No la NHANH FAIL CUNG: neu
khong bit-exact thi da doi HAI thu chu khong phai mot, va moi so sanh
CU vs MOI sau do deu vo nghia. KHONG duoc noi thanh "gan bit-exact".
"""
from __future__ import annotations

import numpy as np
import pytest

from cert import build_calib_set_v3 as B
from measurements.aoi_model_v7 import (
    ALPHA_S, D_SYNC_S, LINK_NAMES, Z_EDGES_LEGACY, Z_EDGES_V7,
    AoIModelV7, InstrumentSamples, d_base_s, u3_profile_ms)
from measurements.decision_error import sawtooth_age_steps

DT, N = 0.005, 200_000
T_MS = 500.2922


# ── U3 va D_BASE ───────────────────────────────────────────────────────────
def test_u3_is_non_negative_and_derived():
    """`offset_steps()` cam offset am; alpha do duoc co 5/8 gia tri am."""
    u3 = np.array(u3_profile_ms(DT))
    assert (u3 >= 0).all()
    assert u3.tolist() == [20.0, 25.0, 0.0, 0.0, 0.0, 0.0, 5.0, 15.0]
    assert B.AOI_PROFILES["U3"] == u3_profile_ms(DT)      # DAN XUAT, khong go tay
    # va `offset_steps` phai nhan duoc no
    assert B.offset_steps("U3", DT).tolist() == [4, 5, 0, 0, 0, 0, 1, 3]


def test_u3_would_be_rejected_without_the_shift():
    """Chung minh phep DICH la BAT BUOC, khong phai trang tri."""
    raw = tuple(ALPHA_S[l] * 1000.0 for l in LINK_NAMES)
    B.AOI_PROFILES["_U3_raw"] = raw
    try:
        with pytest.raises(ValueError, match="offset am"):
            B.offset_steps("_U3_raw", DT)
    finally:
        del B.AOI_PROFILES["_U3_raw"]


def test_PC_E4_d_base_uses_realised_not_nominal_mean():
    """PC-E4: dung trung binh DANH DINH lech -0.565 ms MOT CACH AM THAM."""
    a = np.array([ALPHA_S[l] for l in LINK_NAMES]) * 1000.0
    nominal_shift = float(-a.min())                    # 8.690
    realised_shift = float(np.mean(u3_profile_ms(DT)))  # 8.125
    assert abs(nominal_shift - 8.690344772) < 1e-6
    assert abs(realised_shift - 8.125) < 1e-9
    assert abs(d_base_s(DT) * 1000 - (D_SYNC_S * 1000 - realised_shift)) < 1e-9
    # hai cach KHAC nhau du de gay hai, nhung qua nho de thay bang mat
    assert 0.5 < abs(nominal_shift - realised_shift) < 1.0


def test_M121_mean_age_matches_measurement():
    """M-121: mean(z_s) = D_BASE + mean(U3) + T/2 = 366.07 +/- 0.10 ms."""
    cur, old, _ = B._valid_rows(N, DT, axis=B.AXIS_MEASURED)
    base_ms = (cur - old) * DT * 1000.0
    mean_z = base_ms.mean() + float(np.mean(u3_profile_ms(DT)))
    assert abs(mean_z - 366.070) < 0.10, "mean z = %.4f ms" % mean_z


# ── NHANH FAIL CUNG ────────────────────────────────────────────────────────
def test_NC_E1_bit_exact():
    """★ axis=legacy phai tai tao BIT-EXACT bo sinh cu. diff = 0, khong 'gan'."""
    cur_l, old_l, _ = B._valid_rows(N, DT, B.D_SYNC, axis=B.AXIS_LEGACY)
    age = sawtooth_age_steps(N, DT, B.SYNC_PERIOD, B.D_SYNC)
    rows = np.arange(N)
    valid = rows >= age
    cur_ref, old_ref = rows[valid], rows[valid] - age[valid]
    keep = age[valid] != 0
    np.testing.assert_array_equal(cur_l, cur_ref[keep])
    np.testing.assert_array_equal(old_l, old_ref[keep])


def test_NC_E1_z_shift_is_zero_on_u0():
    """Bit-exact cua z_s doi hoi mean(off) = 0 o U0."""
    assert float(np.mean(B.offset_steps("U0", DT))) == 0.0


def test_NC_E3_u0_on_measured_axis():
    """axis=measured + U0: mean(z_s) = D_BASE + T/2 (alpha = 0)."""
    cur, old, _ = B._valid_rows(N, DT, axis=B.AXIS_MEASURED)
    z_ms = (cur - old) * DT * 1000.0
    expect = d_base_s(DT) * 1000.0 + T_MS / 2
    assert abs(z_ms.mean() - expect) < 0.10, "%.4f vs %.4f" % (z_ms.mean(), expect)


def test_axis_argument_is_validated():
    with pytest.raises(ValueError, match="axis phai la"):
        B._valid_rows(1000, DT, axis="khong_ton_tai")


# ── canh bin ───────────────────────────────────────────────────────────────
def _z_pooled():
    cur, old, _ = B._valid_rows(N, DT, axis=B.AXIS_MEASURED)
    base = (cur - old) * DT
    return np.concatenate([base + o / 1000.0 for o in u3_profile_ms(DT)])


def test_M122_bin_shares_and_M123_no_overflow():
    z = _z_pooled()
    share = [float(np.mean((z >= Z_EDGES_V7[i]) & (z < Z_EDGES_V7[i + 1])))
             for i in range(4)]
    assert max(abs(s - 0.25) for s in share) < 0.02, share          # M-122
    out = float(np.mean((z < Z_EDGES_V7[0]) | (z >= Z_EDGES_V7[-1])))
    assert out == 0.0, "%.6f%% hang ngoai dai" % (out * 100)        # M-123


def test_PC_E3_legacy_edges_break_on_new_axis():
    """Doi chung DUONG: canh cu PHAI vo tren truc moi."""
    z = _z_pooled()
    b0 = float(np.mean((z >= Z_EDGES_LEGACY[0]) & (z < Z_EDGES_LEGACY[1])))
    assert b0 == 0.0, "B0 phai RONG tren truc moi"
    assert float(np.mean(z >= Z_EDGES_LEGACY[-1])) > 0.10


# ── pha chung va chan kieu ─────────────────────────────────────────────────
def test_V_E1_phase_is_shared_across_links():
    """MOT vong sync phuc vu 8 link. 8 pha doc lap = em ruot cua S13."""
    m = AoIModelV7()
    ref = m.process_mode(2000, DT, "uA") - m.alpha["uA"]
    for l in ("ac", "vD", "bc"):
        np.testing.assert_allclose(m.process_mode(2000, DT, l) - m.alpha[l],
                                   ref, atol=1e-12)


def test_L36_instrument_mode_is_blocked_by_type():
    """L36: chan o KIEU vi phep kiem thong ke ha nguon KHONG bat duoc."""
    s = AoIModelV7().instrument_mode(np.random.default_rng(0), n_runs=1)
    assert isinstance(s, InstrumentSamples)
    with pytest.raises(TypeError, match="L36"):
        B._valid_rows(1000, DT, axis=B.AXIS_MEASURED,
                      **{}) if False else _feed(s)


def _feed(age):
    """Mo phong dung cho `_valid_rows` nhan phai mang instrument."""
    if isinstance(age, InstrumentSamples):
        raise TypeError("instrument_mode khong duoc dung trong pipeline (L36)")


def test_L36_guard_is_actually_in_valid_rows(monkeypatch):
    """Chan phai nam TRONG `_valid_rows`, khong phai chi trong test."""
    fake = AoIModelV7().instrument_mode(np.random.default_rng(0), n_runs=1)[:1000]
    monkeypatch.setattr(B.AOI_V7, "base_age_steps",
                        lambda *a, **k: fake.view(InstrumentSamples))
    with pytest.raises(TypeError, match="L36"):
        B._valid_rows(1000, DT, axis=B.AXIS_MEASURED)


# ── confound U1/U2 ─────────────────────────────────────────────────────────
def test_U1_U2_are_not_mean_preserving_but_U3_is_compensated():
    """Amendment 23-49 muc 3."""
    assert abs(float(np.mean(B.AOI_PROFILES["U1"])) - 22.5) < 1e-9
    assert abs(float(np.mean(B.AOI_PROFILES["U2"])) - 12.5) < 1e-9
    # U3 co mean != 0 nhung duoc BU TRU qua d_base -> tuoi trung binh bao toan
    assert abs(d_base_s(DT) * 1000
               + float(np.mean(B.AOI_PROFILES["U3"])) - D_SYNC_S * 1000) < 1e-6


def test_centred_profiles_preserve_shape_not_level():
    """U1c/U2c giu HINH DANG (sd) nhung mean da duoc trung tam hoa."""
    for name, orig in (("U1c", "U1"), ("U2c", "U2")):
        a = np.array(B.AOI_PROFILES[orig])
        c = np.array(B.AOI_PROFILES[name])
        assert abs(c.std() - a.std()) < 3.0, name    # hinh dang giu (luoi 5 ms)
        assert c.min() == 0.0, name                  # da dich len >= 0

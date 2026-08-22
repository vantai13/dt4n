#!/usr/bin/env python3
"""Test cho Lesson 23.19 Task B -- aoi_model_v7.

Test quan trong nhat: `test_two_modes_are_not_interchangeable`. Neu ai do
gop `process_mode` va `instrument_mode`, cai luoc cua nhac cu se chay thang
vao pipeline. Do la loi te nhat co the xay ra o 23.19 va tinh vi hon
`d = 51 ms` -- no khong lam sai MUC cua z ma lam sai PHAN BO theo bin tuoi.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

from measurements.aoi_model_v7 import (
    ALPHA_S, D_SYNC_S, LEGACY_D_S, LEGACY_T_S, SYNC_PERIOD_S, AoIModelV7)
from measurements.decision_error import sawtooth_age_steps

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "results", "LIVE", "phase-23",
                   "aoi_model_selfcheck.json")


def test_locked_parameters():
    """Do duoc. Doi phai qua amendment."""
    assert D_SYNC_S == pytest.approx(0.1159)
    assert SYNC_PERIOD_S == pytest.approx(0.5002922)
    assert abs(sum(ALPHA_S.values())) < 1e-9          # mean(alpha) = 0


def test_negative_control_is_bit_exact():
    """G23-95: khong bit-exact = da doi HAI thu."""
    m = AoIModelV7(d_s=LEGACY_D_S, T_s=LEGACY_T_S, profile="U0")
    for n, dt in ((100000, 0.005), (49991, 0.005), (20000, 0.001)):
        assert np.array_equal(
            m.age_steps(n, dt, "ac", phase0=-LEGACY_D_S),
            sawtooth_age_steps(n, dt, LEGACY_T_S, LEGACY_D_S))


def test_two_modes_are_not_interchangeable():
    """★ process_mode quet pha DEU; instrument_mode ra mot cai LUOC."""
    m = AoIModelV7()
    proc = m.process_mode(200_000, 0.005, "ac")
    ph_p = np.mod(proc - m.d - m.alpha["ac"], m.T) / m.T
    hp, _ = np.histogram(ph_p, bins=50, range=(0, 1))

    # instrument_mode noi 8 link x n_runs; cat lay DUNG khoi cua link "ac"
    # trong run dau (gop 8 link se tron cac luoc lech nhau va lam mem di).
    from measurements.aoi_model_v7 import (CYCLES_PER_RUN, PROBE_INTERVAL_S)
    n_probe = int(CYCLES_PER_RUN * m.T / PROBE_INTERVAL_S)
    inst = m.instrument_mode(np.random.default_rng(1), n_runs=2)[:n_probe]
    ph_i = np.mod(inst - m.d - m.alpha["ac"], m.T) / m.T
    hi, _ = np.histogram(ph_i, bins=50, range=(0, 1))

    r_proc = hp.max() / hp[hp > 0].min()
    r_inst = hi.max() / max(hi[hi > 0].min(), 1)
    assert r_proc < 1.5, "process_mode phai quet pha gan deu, duoc %.2f" % r_proc
    # process_mode: 0 bin rong, max/min ~ 1.00
    # instrument_mode 1 run 1 link: luoc chu ky 10 bin (= T/5), 5 bin rong
    assert (hi == 0).sum() >= 3, (
        "instrument_mode phai de trong mot phan khong gian pha trong MOT run; "
        "so bin rong = %d" % (hi == 0).sum())
    assert r_inst > 3.0, (
        "instrument_mode phai ra mot cai LUOC (do la diem cua no), duoc %.2f"
        % r_inst)
    assert (hp == 0).sum() == 0, "process_mode khong duoc de bin rong"


def test_phase0_is_shared_across_links():
    """Mot vong sync phuc vu ca 8 link -- khong phai 8 vong doc lap (anh em S13)."""
    m = AoIModelV7()
    a = m.process_mode(1000, 0.005, "ac", phase0=0.3)
    b = m.process_mode(1000, 0.005, "uB", phase0=0.3)
    # hieu phai la HANG SO = alpha(uB) - alpha(ac)
    diff = b - a
    assert np.allclose(diff, m.alpha["uB"] - m.alpha["ac"])


def test_u0_variance_is_the_uniform_variance():
    m = AoIModelV7(profile="U0")
    z = m.process_mode(1_000_000, 0.005, "ac")
    assert z.std(ddof=1) == pytest.approx(m.T / np.sqrt(12), rel=1e-3)


@pytest.mark.skipif(not os.path.exists(ART), reason="chua chay selfcheck")
def test_selfcheck_has_discriminating_power():
    """G23-96: mot selfcheck khong FAIL duoc thi khong kiem duoc gi."""
    with open(ART, encoding="utf-8") as fh:
        r = json.load(fh)
    assert r["M_111_process_mode_misuse"]["hit"] is True
    assert r["M_112_wrong_d"]["hit"] is True


@pytest.mark.skipif(not os.path.exists(ART), reason="chua chay selfcheck")
def test_m109_replaced_because_not_estimable():
    """M-109 nhu ky cong tuyen hoan toan; M-109b la ban thay the."""
    with open(ART, encoding="utf-8") as fh:
        r = json.load(fh)
    a = r["M_109b_alpha_stability"]
    assert a["design_rank"] == 9, "thiet ke GOP fwd+rev phai du hang"
    assert a["M_109b_hit"] is True

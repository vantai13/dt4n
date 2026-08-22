#!/usr/bin/env python3
"""Test cho Lesson 23.19 Task A -- chan doan lay mau probe.

Test quan trong nhat: `test_verdict_blocks_task_b`. Task A la mot CHAN.
Neu phan xu la H7 thi Task B khong duoc dung phan bo thuc nghiem lam muc
tieu selfcheck -- va test nay giu cho ket luan do khong bi quen.
"""
from __future__ import annotations

import json
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(REPO, "results", "LIVE", "phase-23",
                    "aoi_sampling_diagnostic.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(DIAG),
    reason="chua chay measurements/aoi_sampling_diagnostic.py")


def _load():
    with open(DIAG, encoding="utf-8") as fh:
        return json.load(fh)


def test_verdict_is_computed_from_the_locked_thresholds():
    d = _load()
    m100 = d["M_100_ks_within_run"]["max"] < 0.05
    m103 = d["M_103_hist_ratio"]["max"] < 3.0
    m101 = d["M_101_ks_pooled"]["max"] < 0.02
    expect = ("H6_UNBIASED" if m100 and m103
              else "H7_POOLING_SUFFICES" if m101
              else "H7_BIASED_MUST_CORRECT")
    assert d["verdict"] == expect


def test_verdict_blocks_task_b():
    """Neu H7 thi phan bo do duoc KHONG duoc dung lam muc tieu selfcheck."""
    d = _load()
    if d["verdict"].startswith("H7"):
        assert "KHONG khop phan bo thuc nghiem" in d["action"] or \
               "khong dung mot run le" in d["action"]


def test_commensurate_lock_is_the_mechanism():
    """T/probe gan mot so nguyen, va jitter qua nho de tron pha."""
    d = _load()
    T = d["H8_equilibrium"]["E_T_ms"]
    P = d["M_104_probe_interval"]["mean_ms"]
    ratio = T / P
    assert abs(ratio - round(ratio)) < 0.01, (
        "ty so T/probe = %.6f khong con gan so nguyen -- co che da doi" % ratio)
    assert d["M_104_probe_interval"]["sd_ms"] < 1.0, (
        "jitter probe da tang; ket luan ve khoa pha phai duoc tinh lai")


def test_inspection_paradox_is_insufficient():
    """H8 chi giai thich mot phan nho cua lech trung vi."""
    d = _load()
    eq = d["H8_equilibrium"]
    shift_h8 = eq["equilibrium_quantiles_ms"]["50"] - eq["uniform_median_ms"]
    assert abs(shift_h8) < 1.0, "T_eff van rat on dinh (CV nho)"
    assert abs(d["M_107_median"]["delta_ms"]) > 3.0, (
        "neu H8 bong nhien du de giai thich thi ket luan Task A phai viet lai")


def test_d_uncertainty_is_larger_than_the_estimator_spread():
    """Cac uoc luong d chenh nhau ~2 ms; sai so lay mau lon hon nhieu."""
    dec = os.path.join(REPO, "results", "LIVE", "phase-23",
                       "aoi_decomposition.json")
    if not os.path.exists(dec):
        pytest.skip("chua co aoi_decomposition.json")
    with open(dec, encoding="utf-8") as fh:
        ind = json.load(fh)["T4_d_estimate"]["independent_of_debias"]
    # trai giua cac estimator (khong ke duong phu thuoc bias)
    vals = [v for k, v in ind["estimates_ms"].items() if "decomposition" not in k]
    assert max(vals) - min(vals) < 6.5, (
        "trai giua cac estimator da vuot sai so lay mau -- phai xem lai")


def test_artifact_declares_measures_role():
    v = _load()["validity"]
    assert v["axis_role"] == "measures_axis"
    assert v["instrument"]["source_sha256"]

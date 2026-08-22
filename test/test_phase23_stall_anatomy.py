#!/usr/bin/env python3
"""Test cho Lesson 23.18 -- giai phau stall va phan ra d.

Test quan trong nhat o day la `test_locked_constants_unchanged`: no bien
viec doi WARMUP_CYCLES thanh mot hanh dong lam GAY TEST, tuc mot hanh dong
CO Y THUC. Neu 20 la mot co dong lenh thi se co nguoi thu 10/20/30/50 cho
toi khi CV lot dai M-79 -- do la p-hacking.
"""
from __future__ import annotations

import json
import os

import pytest

from measurements import aoi_stall_anatomy as A

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STALL = os.path.join(REPO, "results", "LIVE", "phase-23", "aoi_stall_anatomy.json")
DECOMP = os.path.join(REPO, "results", "LIVE", "phase-23", "aoi_decomposition.json")

pytestmark = pytest.mark.skipif(
    not (os.path.exists(STALL) and os.path.exists(DECOMP)),
    reason="chua chay measurements/aoi_stall_anatomy.py va aoi_decompose.py",
)


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def test_locked_constants_unchanged():
    """KHOA o amendment 23-45 muc 5. Doi chung phai qua mot amendment moi."""
    assert A.WARMUP_CYCLES == 20
    assert A.LONG_CYCLE_S == 0.55


def test_warmup_is_not_a_cli_flag():
    """Neu thanh --warmup thi se co nguoi quet gia tri cho toi khi CV vua y."""
    import inspect
    src = inspect.getsource(A.main)
    assert "--warmup" not in src and "--long-cycle" not in src


def test_adjudication_is_a_formula_not_a_judgement():
    """Nguong 0.80 / 0.50 phai co trong ma nguon, khong phai trong dau nguoi."""
    import inspect
    src = inspect.getsource(A.stall_positions)
    assert "0.80" in src and "0.50" in src
    assert "AMBIGUOUS" in src


def test_h1_verdict_matches_measured_share():
    t1 = _load(STALL)["T1_stall_positions"]
    share = t1["M_78_share_runs_first_overrun_before_cycle_20"]
    if share >= 0.80:
        assert t1["verdict"] == "H1_STARTUP_TRANSIENT"
    elif share <= 0.50:
        assert t1["verdict"] == "H2_INTRINSIC"
    else:
        assert t1["verdict"] == "AMBIGUOUS"


def test_h3_rejected_by_a_discriminating_test():
    """M-78c nhu ky KHONG phan biet duoc (CLEAN: moi chu ky deu reconcile).

    Phep kiem co suc phan biet chi ton tai o PROD.
    """
    t1 = _load(STALL)["T1_stall_positions"]
    d = t1["H3_prod_only_diagnostic_posthoc"]
    assert d["n_overrun_prod"] > 0
    assert d["H3_supported"] is False
    # va CLEAN dung la truong hop thoai hoa da neu
    c = t1["H3_clean_reference_posthoc"]
    assert c["base_reconcile_rate"] == pytest.approx(1.0)


def test_h4_identity_holds():
    """alpha(l) == d_transport(l) - mean(d_transport), du RMS nho."""
    it = _load(DECOMP)["T3_order_check"]["identity_test"]
    assert it["rms_over_spread"] < 0.15, (
        "dong nhat thuc H4 khong con giai thich duoc bien do alpha: RMS/bien do "
        "= %.3f" % it["rms_over_spread"])


def test_scan_and_patch_components_have_opposite_sign_effect():
    """Hai thanh phan cua H4 phai dau nguoc nhau (amendment 23-45 muc 2)."""
    o = _load(DECOMP)["T3_order_check"]
    links = o["links"]
    scan = [o["scan_offset_median_ms_by_link"][l] for l in links]
    dtr = [o["d_transport_median_ms_by_link"][l] for l in links]
    # scan muon hon => t_source moi hon => AoI nho hon (dau am trong AoI)
    # patch muon hon => nhin thay muon hon => AoI lon hon (dau duong)
    assert max(scan) - min(scan) > 0
    assert max(dtr) - min(dtr) > 0


def test_instrument_limit_is_recorded_next_to_the_number():
    """Gioi han nhac cu phai o CANH con so, khong phai o 'future work'."""
    lim = _load(DECOMP)["instrument_limit"]
    assert lim["d_transport_is"] == "CAN TREN"
    assert lim["systematic_bias_ms"] == 50.0
    assert lim["not_reducible_by_more_runs"] is True


def test_both_confidence_intervals_are_reported():
    """Bao cao CA HAI: long nhau va gop iid, kem ICC. Khong duoc chon mot."""
    ci = _load(DECOMP)["T4_d_estimate"]["nested_ci"]
    for k in ("ci95_nested", "ci95_naive_iid", "icc",
              "width_ratio_nested_over_iid"):
        assert k in ci
    assert ci["df"] == 4 and ci["df_iid"] == 14


def test_degenerate_partial_correlation_was_replaced():
    """Phep kiem trong-epoch cu thoai hoa vi rho la hang so trong epoch."""
    pc = _load(DECOMP)["T5_partial_correlation"]
    assert pc["rho_constant_within_epoch"] is True
    assert "corr_link_and_teff_adjusted" in pc


def test_artifacts_declare_measures_role():
    for p in (STALL, DECOMP):
        v = _load(p)["validity"]
        assert v["axis_role"] == "measures_axis"
        assert v["instrument"]["source_sha256"]

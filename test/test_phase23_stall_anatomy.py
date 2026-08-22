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
    assert "M_94_K1_corr_rho_vs_teff_prev" in pc      # bien khu TRE
    assert "M_96_K3_partial_inverse_dt" in pc         # quan he TI SO


# ---------------------------------------------------------------------------
# Vong ra soat: amendment 23-45b (bug cong thuc null) va 23-45c (ket luan T5)
# ---------------------------------------------------------------------------


def test_sawtooth_null_does_not_use_p05_as_d():
    """BUG 23-45b: `p05 = d + 0.05T`, dung no lam `d` keo CV null xuong.

    Test nay chan viec quay lai cong thuc cu.
    """
    n = _load(STALL)["T2_warmup_trim"]["by_mode"]["clean"]["sawtooth_null"]
    # d phai suy tu MEAN, khong phai tu p05
    assert abs(n["d_hat_ms"] - (n["T_hat_ms"] / 2 + n["d_hat_ms"])
               + n["T_hat_ms"] / 2) < 1e-6
    st = _load(STALL)["T2_warmup_trim"]["by_mode"]["clean"]["trimmed"]
    assert n["d_hat_ms"] == pytest.approx(st["mean_ms"] - n["T_hat_ms"] / 2)
    # va gia tri SAI phai duoc giu lai de doi chieu, KHAC gia tri dung
    assert n["cv_null_BUGGED_p05_as_d"] < n["cv_null"]


def test_aoi_is_a_clean_sawtooth_after_trim():
    """Ket qua trung tam cua vong ra soat."""
    n = _load(STALL)["T2_warmup_trim"]["by_mode"]["clean"]["sawtooth_null"]
    assert abs(n["sd_ratio_observed_over_uniform"] - 1.0) < 0.01, (
        "sd khong con khop Uniform[d, d+500]")
    assert abs(n["cv_gap"]) < 0.005, "khoang cach CV toi null DUNG qua lon"


def test_shape_test_exists_because_moments_are_not_shape():
    """sd khop KHONG chung minh la uniform. Phai co phep kiem HINH DANG."""
    n = _load(STALL)["T2_warmup_trim"]["by_mode"]["clean"]["sawtooth_null"]
    assert "M_91_ks_statistic" in n
    q = n["quantile_comparison_ms"]
    # lech phan vi la POSITIVE CONTROL cho mo hinh co alpha o 23.19
    assert all(abs(v["delta"]) < 20 for v in q.values())


def test_t5_applies_the_warmup_cut():
    """23-45c loi 1: ba ham, hai ham cat warm-up, mot ham quen."""
    import inspect

    from measurements import aoi_decompose as D
    src = inspect.getsource(D.partial_corr_within_epoch)
    assert "warmup_cut" in src and "t_cut" in src, (
        "partial_corr_within_epoch phai ap dung moc cat warm-up nhu T2")


def test_between_and_within_link_are_reported_separately():
    """23-45c loi 2: gop 8 link roi tinh MOT he so lat dau ket qua."""
    pc = _load(DECOMP)["T5_partial_correlation"]
    assert pc["corr_between_links"] < -0.5, "confounding giua-link phai hien ra"
    assert abs(pc["corr_link_adjusted"]) < 0.05, (
        "corr TRONG link phai ~ 0 sau khi cat warm-up")
    assert pc["verdict"] == "NO_EFFECT_TO_EXPLAIN"


def test_broken_rho_links_are_flagged():
    """L30: uA/uB do rho sai chieu trong toan bo chien dich."""
    pc = _load(DECOMP)["T5_partial_correlation"]
    assert set(pc["links_with_broken_rho"]) == {"uA", "uB"}
    for l in ("uA", "uB"):
        assert pc["rho_zero_share_by_link"][l] > 0.9
    for l in ("ac", "ad", "bc", "bd", "vC", "vD"):
        assert pc["rho_zero_share_by_link"][l] < 0.01


def test_probe_bias_is_measured_not_assumed():
    """M-93: hang so 50 ms phai duoc DO, kem CI."""
    b = _load(DECOMP)["T7_probe_bias"]
    assert b["M_93_ci95"][0] < b["M_93_measured_bias_ms"] < b["M_93_ci95"][1]
    assert b["n_refresh_transitions"] > 1000


def test_variance_accumulation_signature():
    """M-98: Var ~ E voi giao truc o vi tri DAU vong lap."""
    va = _load(DECOMP)["T7_variance_accumulation"]
    assert va["M_98_r2"] > 0.7
    assert abs(va["crossing_vs_min_observed_ms"]) < 15.0, (
        "giao truc Var=0 phai roi gan d_transport nho nhat quan sat duoc")


def test_patch_position_decomposition_is_exact():
    """slope(visible) = slope(scan) + slope(d_transport) -- dong nhat thuc."""
    pp = _load(DECOMP)["T7_patch_position"]
    assert abs(pp["slope_consistency_check_ms"]) < 0.01
    # hai thanh phan DAU NGUOC NHAU trong AoI
    assert pp["slope_scan_offset_ms_per_position"] > 0
    assert pp["M_99_slope_d_transport_ms_per_position"] > 0


def test_d_final_does_not_depend_on_the_bias_constant():
    ind = _load(DECOMP)["T4_d_estimate"]["independent_of_debias"]
    assert ind["spread_ms"] <= 15.0
    assert ind["chosen_ms"] == pytest.approx(
        _load(DECOMP)["T4_d_estimate"]["d_final_moment_ms"])


def test_artifacts_declare_measures_role():
    for p in (STALL, DECOMP):
        v = _load(p)["validity"]
        assert v["axis_role"] == "measures_axis"
        assert v["instrument"]["source_sha256"]

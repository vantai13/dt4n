"""Lesson 23.25b -- test cho khoi `T7_null_audit` va phep phan xu H1/H2.

Bao gom `PC-25b-1`/`PC-25b-2` (doi chung DUONG cho `null_homogeneity`) va
`NC-25b-2` (`T0`..`T6` khong doi).
"""
import inspect
import json
import os

import numpy as np
import pytest

from measurements import link_corr_matrix as A
from measurements import link_pair_stability as S

ART = "results/LIVE/phase-23/link_corr_matrix.json"
STAB = "results/LIVE/phase-23/link_pair_stability.json"
TAU = {"ac": 2.75, "ad": 4.17, "bc": 2.74, "bd": 2.76,
       "uA": 20.03, "uB": 27.35, "vC": 20.03, "vD": 27.67}


# ------------------------------------------- V3: rang buoc CAU TRUC
def test_no_structured_pair_is_fast_fast():
    """★ `L142` -- hat nhan cua ca Lesson 23.25b.

    `k_lm > 0` doi hai link chung duong. Moi link LOI thuoc DUNG MOT duong,
    nen hai link loi khac nhau KHONG BAO GIO chung duong. Vay moi cap co cau
    truc phai chua it nhat mot link BIEN, va `n_eff` cua `omega_hat` bi `tau`
    bien chi phoi -- KHONG the sua bang tinh toan.
    """
    fast = {l for l in A.LINKS if TAU[l] < A.TIMESCALE_SLOW_S}
    assert fast == {"ac", "ad", "bc", "bd"}
    ff = [(a, b) for a, b in A.S_PAIRS if a in fast and b in fast]
    assert ff == [], "co cap nhanh-nhanh co k>0 -> lap luan `L142` sai"
    # va cap loi-loi bat ky deu that su co k = 0
    assert A.K_PAIR[("ac", "ad")] == 0.0
    assert A.K_PAIR[("bc", "bd")] == 0.0


def test_neff_is_dominated_by_the_slow_link():
    ne = A.neff_pair("uA", "ac", TAU, n_samples=599, n_runs=15)
    assert ne == pytest.approx(15 * 599 * 0.2 / (2 * 20.03), rel=1e-9)
    # cap co link cham nhat cho `n_eff` nho nhat
    assert (A.neff_pair("uB", "vD", TAU, 599, 15)
            < A.neff_pair("uA", "ac", TAU, 599, 15))


def test_weighted_sd_is_much_wider_than_bootstrap():
    """`sd` dung phai RONG HON bootstrap dang ke -- do la ca van de."""
    R = A.structured_matrix(0.0)
    w = A.omega_hat_weighted(R, TAU, n_samples=599, n_runs=15)
    assert w["n_pairs_fast_fast"] == 0
    assert w["sum_weight_k2"] == pytest.approx(175.70, abs=0.5)
    assert w["sd_omega_hat_correct"] == pytest.approx(0.0754, abs=0.002)
    assert 30.0 < w["n_eff_min"] < w["n_eff_max"] < 50.0


# ------------------------------------------- PC-25b-1 / PC-25b-2
def _null_matrix(values: dict, base: float = 0.05, seed: int = 0):
    """Ma tran voi cap NULL dat theo `values`, con lai `base` + nhieu nho."""
    rng = np.random.default_rng(seed)
    R = np.eye(len(A.LINKS))
    for a, b in A.NULL_PAIRS:
        v = values.get(frozenset((a, b)), base + rng.normal(0, 0.01))
        R[A.IDX[a], A.IDX[b]] = R[A.IDX[b], A.IDX[a]] = v
    for a, b in A.S_PAIRS:
        R[A.IDX[a], A.IDX[b]] = R[A.IDX[b], A.IDX[a]] = 0.05
    return R


def test_PC_25b_1_homogeneous_null_is_not_flagged():
    """★ `PC-25b-1`: tap NULL DONG NHAT -> `heterogeneous = False`."""
    R = _null_matrix({})
    h = A.null_homogeneity(R, TAU)
    assert h["_verdict_null_set_heterogeneous"] is False
    assert h["_null_outliers"] == []


def test_PC_25b_2_two_inflated_null_pairs_are_caught():
    """★ `PC-25b-2`: bom DUNG hai cap NULL len +0.6 -> phai bat DUNG hai cap."""
    R = _null_matrix({frozenset(("uA", "uB")): 0.60,
                      frozenset(("vC", "vD")): 0.62})
    h = A.null_homogeneity(R, TAU)
    assert h["_verdict_null_set_heterogeneous"] is True
    assert set(h["_null_outliers"]) == {"uA-uB", "vC-vD"}
    assert h["slow-slow"]["mean_r"] > 0.55
    assert h["fast-fast"]["mean_r"] < 0.10


def test_null_homogeneity_discriminates():
    """Cai chan phai PHAN BIET, khong chi 'luon bao co'."""
    assert A.null_homogeneity(_null_matrix({}), TAU)[
        "_verdict_null_set_heterogeneous"] is False
    assert A.null_homogeneity(_null_matrix(
        {frozenset(("uA", "uB")): 0.60,
         frozenset(("vC", "vD")): 0.62}), TAU)[
        "_verdict_null_set_heterogeneous"] is True


def test_stratified_estimator_flags_outside_parameter_space():
    """Uoc luong ngoai `[0,1]` phai TU KHAI, khong duoc im lang."""
    R = _null_matrix({frozenset(("uA", "uB")): 0.60,
                      frozenset(("vC", "vD")): 0.62})
    st = A.omega_hat_stratified(R, TAU)
    assert st["omega_hat_stratified"] < 0.0
    assert st["outside_parameter_space"] is True


# ------------------------------------------- phan xu H1/H2
def test_signed_scenarios_are_applied_verbatim():
    """`adjudicate` phai thi hanh DUNG lien ket cua `A078` muc 5.

    `K1` la mot LIEN KET VA: `sd < 0.30` VA `|r_offered| < 0.15`. Ban dau
    tien chi dung Test A nen bao `H1` trong khi ve thu hai HONG.
    """
    meas = {"uA-uB": {"sd_r_across_runs": 0.20, "n_runs_negative": 0,
                      "r_pooled_fisher": 0.6},
            "vC-vD": {"sd_r_across_runs": 0.18, "n_runs_negative": 0,
                      "r_pooled_fisher": 0.6}}
    off_ok = {k: {"r_pooled_fisher": 0.05} for k in meas}
    off_bad = {k: {"r_pooled_fisher": 0.20} for k in meas}

    assert S.adjudicate(meas, off_ok)["overall"] == "H1_ENDPOINT_CONFOUND"
    # ve thu hai hong -> KHONG duoc bao H1
    a = S.adjudicate(meas, off_bad)
    assert a["overall"] != "H1_ENDPOINT_CONFOUND"
    assert a["K1_met"] is False


def test_scenario_gap_is_reported_not_rounded_away():
    """★ Ket qua roi ngoai ca ba kich ban PHAI tu khai la KHE HO.

    Chon dai gan nhat la dien giai lai sau khi nhin so. Xem `L145`.
    """
    meas = {"uA-uB": {"sd_r_across_runs": 0.28, "n_runs_negative": 1,
                      "r_pooled_fisher": 0.6},
            "vC-vD": {"sd_r_across_runs": 0.18, "n_runs_negative": 0,
                      "r_pooled_fisher": 0.6}}
    off = {k: {"r_pooled_fisher": 0.17} for k in meas}
    a = S.adjudicate(meas, off)
    assert a["overall"] == "GAP_IN_SIGNED_SCENARIOS"
    assert a["scenarios_partition_outcome_space"] is False
    assert "K3" in a["fallback_if_gap"]


def test_H2_wins_when_series_is_noisy():
    meas = {"uA-uB": {"sd_r_across_runs": 0.55, "n_runs_negative": 5,
                      "r_pooled_fisher": 0.3},
            "vC-vD": {"sd_r_across_runs": 0.50, "n_runs_negative": 4,
                      "r_pooled_fisher": 0.3}}
    assert S.adjudicate(meas, None)["overall"] == "H2_SHORT_SERIES_ARTEFACT"


def test_locked_constants_are_not_flags():
    for mod in (A, S):
        src = inspect.getsource(mod.main)
        for bad in ("--slow", "--sd-h1", "--sd-h2", "--r-offered",
                    "--outlier-mad", "--timescale"):
            assert bad not in src


# ------------------------------------------- artifact da chay
@pytest.mark.skipif(not os.path.exists(ART), reason="chua chay link_corr_matrix")
def test_T7_present_and_T0_T6_untouched_shape():
    with open(ART, encoding="utf-8") as fh:
        d = json.load(fh)
    assert "T7_null_audit" in d
    t7 = d["T7_null_audit"]
    assert t7["omega_hat_weighted"]["n_pairs_fast_fast"] == 0
    assert t7["null_homogeneity"]["_verdict_null_set_heterogeneous"] is True
    # dau hieu bootstrap lech VI TRI (`L143`)
    assert t7["omega_hat_outside_own_bootstrap_ci"] is True
    assert t7["ci_width_ratio_correct_over_bootstrap"] > 3.0
    # quyet dinh `D` ben vung (`M-257`)
    assert t7["snr_sensitivity"]["decision_unchanged"] is True


@pytest.mark.skipif(not os.path.exists(STAB), reason="chua chay pair_stability")
def test_fast_control_pairs_differ_from_slow_pairs():
    """`ac-ad`/`bc-bd` (cung host, NHANH) phai khac han `uA-uB`/`vC-vD`."""
    with open(STAB, encoding="utf-8") as fh:
        d = json.load(fh)
    m = d["testA_measured_per_run"]
    assert m["ac-ad"]["r_pooled_fisher"] < 0.10
    assert m["bc-bd"]["r_pooled_fisher"] < 0.10
    assert m["uA-uB"]["r_pooled_fisher"] > 0.50
    assert m["vC-vD"]["r_pooled_fisher"] > 0.50
    # va so run AM khac han: cap nhanh vang loan, cap cham thi khong
    assert m["ac-ad"]["n_runs_negative"] >= 3
    assert m["uA-uB"]["n_runs_negative"] <= 1

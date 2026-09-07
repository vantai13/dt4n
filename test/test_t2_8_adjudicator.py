"""T2 luot 2 -- bon fixture tong hop, bon trang thai.

Dap an DUNG THEO KIEN TAO: du lieu duoc dung sao cho ket qua dung la biet
truoc, nen test khong can oracle doc lap. Neu test bo phan quyet bang
artifact THAT, ta dang kiem no bang chinh thu no phai kiem.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from cert import adjudicate as ADJ

K_SIGNED = 3.0
N_SEED = 20
RNG = np.random.default_rng(2808)


def _cell(true_value: float, noise_sd: float, n_seed: int = N_SEED):
    return RNG.normal(true_value, noise_sd, n_seed)


# --- bon trang thai ----------------------------------------------------

def test_pass_when_truth_matches_prediction():
    v = ADJ.adjudicate(obs=_cell(0.20, 0.01), predicted=0.20, null=1.0, k=K_SIGNED)
    assert v["state"] == "PASS", v


def test_fail_when_truth_is_far_from_prediction():
    """Neu cai nay ra PASS thi bang qua rong hoac dau bi lat."""
    v = ADJ.adjudicate(obs=_cell(0.60, 0.01), predicted=0.20, null=1.0, k=K_SIGNED)
    assert v["state"] == "FAIL", v


def test_insufficient_power_when_noise_swamps_the_effect():
    """h2@0.960 duoi dang tong hop: san nhieu >= hieu ung."""
    v = ADJ.adjudicate(obs=_cell(0.20, 1.5), predicted=0.20, null=1.0, k=K_SIGNED)
    assert v["state"] == "INSUFFICIENT_POWER", v
    assert v["noise_floor"] >= v["effect"]


def test_vacuous_when_a_signed_band_exceeds_the_effect():
    """Bang DA CHON rong hon hieu ung -> du doan khong the sai.

    Khac INSUFFICIENT_POWER o CHO SUA DUOC: san nhieu con thap, chi la
    bang bi chon qua rong.
    """
    v = ADJ.adjudicate(obs=_cell(0.20, 0.01), predicted=0.20, null=1.0,
                       k=K_SIGNED, signed_band=1.0)
    assert v["state"] == "VACUOUS", v
    assert v["noise_floor"] < v["effect"] <= v["band_used"]


def test_not_evaluated_with_too_few_seeds():
    v = ADJ.adjudicate(obs=[0.2], predicted=0.20, null=1.0, k=K_SIGNED)
    assert v["state"] == "NOT_EVALUATED"


# --- bac tu do PHAI duoc dung ------------------------------------------

def test_degrees_of_freedom_are_actually_used():
    """Bat dung loi T2.8 PHAN A: dung z thay vi t.

    Cung se, cung k -> bang voi n=5 phai RONG HON bang voi n=20.
    """
    small = ADJ.band(se=0.01, k=3.0, n_seed=5)
    large = ADJ.band(se=0.01, k=3.0, n_seed=20)
    assert small > large, "bo phan quyet dang bo qua bac tu do"
    assert small / large > 1.5


def test_the_two_k_conventions_reconcile():
    """Boi so THO cua quy uoc (A) == boi so ma quy uoc (B) thuc su ap.

    Kiem bang so tren dung cac cap trong bang cua T2.8 PHAN B.
    """
    for n, K, m_expected in ((5, 35, 7.84), (20, 35, 3.73),
                             (20, 7, 3.01), (10, 35, 4.53), (3, 35, 26.43)):
        got = ADJ.required_multiplier(n_seed=n, n_tests=K)
        assert got == pytest.approx(m_expected, abs=0.01), (n, K, got)


def test_k_three_with_five_seeds_is_not_three_sigma():
    """So chinh cua PHAN A: k=3 tho voi n=5 KHONG phai 0.27%/phep."""
    p_raw = 2 * stats.t.sf(3.0, 4)
    assert p_raw == pytest.approx(0.03994, abs=1e-4)
    assert p_raw / (2 * stats.norm.sf(3.0)) > 14.0


# --- BIEN THAI ---------------------------------------------------------

def test_widening_the_band_never_turns_pass_into_fail():
    obs = _cell(0.35, 0.02)
    a = ADJ.adjudicate(obs=obs, predicted=0.20, null=1.0, k=2.0)
    b = ADJ.adjudicate(obs=obs, predicted=0.20, null=1.0, k=8.0)
    assert not (a["state"] == "PASS" and b["state"] == "FAIL")


def test_more_seeds_never_widens_the_band_at_fixed_se():
    prev = None
    for n in (3, 5, 10, 20, 40):
        cur = ADJ.band(se=0.01, k=3.0, n_seed=n)
        if prev is not None:
            assert cur <= prev, n
        prev = cur


def test_shifting_prediction_and_observations_together_is_invariant():
    """Doi he quy chieu khong duoc doi phan quyet."""
    obs = _cell(0.30, 0.02)
    a = ADJ.adjudicate(obs=obs, predicted=0.20, null=1.0, k=K_SIGNED)
    b = ADJ.adjudicate(obs=obs + 5.0, predicted=5.20, null=6.0, k=K_SIGNED)
    assert a["state"] == b["state"]
    assert a["deviation"] == pytest.approx(b["deviation"], rel=1e-9)


# --- gop: mau so CHI dem READABLE --------------------------------------

def test_summary_denominator_counts_only_readable():
    v = {
        "a": {"state": "PASS"}, "b": {"state": "PASS"}, "c": {"state": "FAIL"},
        "d": {"state": "VACUOUS"}, "e": {"state": "INSUFFICIENT_POWER"},
        "f": {"state": "NOT_EVALUATED"},
    }
    s = ADJ.summarize(v)
    assert s["n_readable"] == 3 and s["n_pass"] == 2 and s["n_fail"] == 1
    assert s["n_vacuous"] == 1 and s["n_insufficient_power"] == 1
    assert s["n_total"] == 6


def test_summary_has_no_pass_rate_or_overall_verdict():
    """Mot ti so an mau so di, va mau so LA thong tin (Q5)."""
    s = ADJ.summarize({"a": {"state": "PASS"}, "b": {"state": "VACUOUS"}})
    for banned in ("pass_rate", "score", "overall_verdict", "verdict"):
        assert banned not in s


def test_summary_rejects_unknown_states():
    with pytest.raises(ValueError):
        ADJ.summarize({"a": {"state": "MOSTLY_FINE"}})


# --- tau*(lift_min): null khac "dat o bien" ----------------------------

def test_tau_star_null_means_not_reached_on_the_grid():
    c = ADJ.tau_star_curve(taus=[1.0, 5.0, 28.0], lifts=[0.5, 0.4, 0.35],
                           lift_min_grid=[0.05, 0.45])
    # 0.05: khong lift nao tut duoi -> None, KHONG phai 28.0
    assert c["tau_star_s"]["0.05"] is None
    # 0.45: lift(5.0)=0.40 la diem dau tien tut duoi
    assert c["tau_star_s"]["0.45"] == 5.0
    assert c["tau_grid_max"] == 28.0


def test_tau_star_curve_is_monotone_in_lift_min():
    c = ADJ.tau_star_curve(taus=[1.0, 2.0, 5.0, 10.0, 20.0],
                           lifts=[0.50, 0.40, 0.22, 0.08, 0.03],
                           lift_min_grid=[0.05, 0.10, 0.25])
    got = [c["tau_star_s"][k] for k in ("0.05", "0.1", "0.25")]
    assert got == [20.0, 10.0, 5.0]

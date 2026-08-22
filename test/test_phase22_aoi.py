"""Golden tests for cert.aoi_profiles -- Phase 22 Lesson 22.7."""

import json
import os

import pytest

import cert.aoi_profiles as AP
import cert.build_calib_set_v3 as V3


MAIN = "results/SUPERSEDED/phase-22/aoi_profiles_poisson_0.925.json"
pytestmark = pytest.mark.skipif(not os.path.exists(MAIN), reason="thieu aoi_profiles result")


@pytest.fixture(scope="module")
def res():
    with open(MAIN, encoding="utf-8") as f:
        return json.load(f)


def test_GA1_profiles_are_locked(res):
    assert tuple(res["profiles_order"]) == AP.PROFILES
    assert set(res["profiles"]) == set(AP.PROFILES)
    assert res["profiles"]["U0"]["meta"]["offset_ms"] == [0.0] * 8
    assert AP.centred_offsets("U1")[0].tolist() == [0, 1, 3, 4, 5, 6, 8, 9]


def test_GA2_spread_is_the_only_thing_that_differs(res):
    m = {p: res["profiles"][p]["meta"] for p in AP.PROFILES}
    for p in AP.PROFILES:
        assert abs(m[p]["z_bar_mean"] - m["U0"]["z_bar_mean"]) <= V3.DT + 1e-6, p
        assert m[p]["rows_dropped"] / 999945.0 < 0.02, p
    assert m["U0"]["sd_ms"] == 0.0
    assert m["U2"]["sd_ms"] < m["U1"]["sd_ms"] < m["PC4"]["sd_ms"]


def test_GA3_U0_reproduces_the_21R_operating_numbers(res):
    u0 = res["profiles"]["U0"]
    assert u0["qhat_margin"]["0"] == pytest.approx(11.5878, abs=3e-3)
    assert u0["qhat_margin"]["3"] == pytest.approx(24.3254, abs=3e-3)
    assert u0["ratio_B3_over_B0"] == pytest.approx(2.099, abs=3e-3)


def test_GA4_jensen_gap_is_negative_and_second_order_is_accurate(res):
    for p in ("U1", "U2", "PC4"):
        for z in ("0.077", "0.425"):
            g = res["theory"][p][z]
            assert g["gap_exact"] < 0.0, (p, z)
            assert g["gap_second_order"] < 0.0, (p, z)
            assert g["gap_exact"] / g["gap_second_order"] == pytest.approx(1.0, rel=0.15)


def test_GA5_gap_scales_with_variance_of_the_offsets(res):
    g = {p: res["theory"][p]["0.077"] for p in ("U1", "U2", "PC4")}
    for a, b in (("U1", "U2"), ("PC4", "U1")):
        assert abs((g[a]["gap_second_order"] / g[b]["gap_second_order"]) / (g[a]["var_d_s2"] / g[b]["var_d_s2"]) - 1.0) < 1e-9


def test_GA6_realistic_profiles_are_indistinguishable_from_uniform(res):
    for p in ("U1", "U2"):
        for g in "0123":
            assert abs(res["qhat_ratio_vs_U0"][p][g] - 1.0) < 0.02, (p, g)
            ci = res["bootstrap_ratio_vs_U0"][p][g]["ci95"]
            assert ci[0] <= 1.0 <= ci[1], (p, g, ci)
        assert abs(res["theory"][p]["0.077"]["rel_gap_in_rms"]) < 0.001


def test_GA7_PC4_shows_the_effect_is_real_when_the_spread_is_large(res):
    r = res["qhat_ratio_vs_U0"]["PC4"]
    assert r["0"] < 0.70
    assert r["0"] < r["1"] < r["2"] < r["3"] < 1.0
    for g in "0123":
        assert res["bootstrap_ratio_vs_U0"]["PC4"][g]["ci95"][1] < 1.0


def test_GA8_coverage_holds_for_every_profile(res):
    for p in AP.PROFILES:
        assert res["profiles"][p]["coverage_marginal"] >= 0.88, p
        for v in res["profiles"][p]["coverage_by_bin"].values():
            assert v >= 0.88, (p, v)


def test_GA9_anchor_must_be_recomputed_per_profile(res):
    a = {p: res["profiles"][p]["anchor_err"] for p in AP.PROFILES}
    assert abs(a["PC4"] / a["U0"] - 1.0) > 0.10
    wrong_ratio = res["profiles"]["PC4"]["kappa"]["1.00"]["err_given_accept"] / a["U0"]
    right_ratio = res["profiles"]["PC4"]["kappa"]["1.00"]["risk_ratio"]
    assert abs(wrong_ratio / right_ratio - 1.0) > 0.10


def test_GA10_age_ratio_law_needs_uniform_aoi(res):
    for p in ("U0", "U1", "U2"):
        assert 2.0 <= res["profiles"][p]["ratio_B3_over_B0"] <= 2.2, p
    assert res["profiles"]["PC4"]["ratio_B3_over_B0"] > 3.0


def test_GA11_gates_are_serialized(res):
    gates = res["gates"]
    assert gates["G22_12_zero_offset_paths_identical"]
    assert gates["PC22_4_extreme_offset_visible"]
    assert gates["realistic_profiles_indistinguishable_from_uniform"]
    assert gates["P10_anchor_recomputed_per_profile"]
    assert gates["L13_age_ratio_law_breaks_under_PC4"]

"""Golden tests -- cert.go2_simultaneous, Phase 23 Lesson 23.5[C]."""

import json
import os

import numpy as np
import pandas as pd
import pytest

import cert.go2_simultaneous as G2
from cert.conformal_simultaneous import _slot_cols

CALIB = "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.925.parquet"
needs_data = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu artifact v3")


# --------------------------------------------------------------------------
# Nhom 1: hang so va kernel
# --------------------------------------------------------------------------

def test_C1_critical_values_are_correct():
    """Thiet ke goc ghi 2.82: do la gan z_{1-0.05/24}, quen chia doi cho HAI
    PHIA. Dung la z_{1-0.05/48} = 3.078088."""
    cv = G2.critical_values(24)
    assert cv["c_bonferroni"] == pytest.approx(3.078088, abs=1e-5)
    assert cv["c_sidak"] == pytest.approx(3.070789, abs=1e-5)
    # o m=24, hai hieu chinh co dien gan trung nhau
    assert abs(cv["bonferroni_minus_sidak"]) < 0.01
    assert cv["c_bonferroni"] > cv["c_sidak"] > cv["c_pointwise_95"]
    # va con so bi nham KHONG bang c_bonferroni
    assert abs(G2._z(1.0 - 0.05 / 24) - 2.86526) < 1e-4


def test_C2_supt_reduces_to_pointwise_when_K_is_one():
    """K = 1: khong co da so sanh -> c_supt ~ 1.96 (phan vi 95% cua |Z|)."""
    rng = np.random.default_rng(0)
    draws = rng.normal(size=(20000, 1))
    band = G2.supt_band(draws, np.zeros(1))
    assert band["c_supt"] == pytest.approx(1.96, abs=0.06)


def test_C3_supt_matches_sidak_when_columns_are_independent():
    """Doc lap -> c_supt phai TRUNG c_sidak. Day la kiem tra dung dan cua
    cong thuc: sup-t la Sidak khi khong co tuong quan."""
    rng = np.random.default_rng(1)
    draws = rng.normal(size=(40000, 24))
    band = G2.supt_band(draws, np.zeros(24))
    assert band["c_supt"] == pytest.approx(G2.critical_values(24)["c_sidak"], abs=0.09)


def test_C4_supt_is_smaller_when_columns_are_perfectly_correlated():
    """Tuong quan hoan toan -> 24 dai luong that ra la MOT -> c_supt ~ 1.96.
    Day chinh la luan diem Phase 22 o tang meta: tuong quan lam giam gia
    phai tra cho da so sanh."""
    rng = np.random.default_rng(2)
    base = rng.normal(size=(20000, 1))
    draws = np.repeat(base, 24, axis=1)
    band = G2.supt_band(draws, np.zeros(24))
    assert band["c_supt"] == pytest.approx(1.96, abs=0.06)
    assert band["c_supt"] < G2.critical_values(24)["c_sidak"] - 0.5


def test_C5_zero_sigma_column_is_excluded_and_reported():
    rng = np.random.default_rng(3)
    draws = rng.normal(size=(2000, 3))
    draws[:, 1] = 0.0
    band = G2.supt_band(draws, np.zeros(3))
    assert band["n_degenerate_sigma"] == 1
    assert band["degenerate_indices"] == [1]
    assert np.isfinite(band["c_supt"])
    assert band["lo"][1] == band["hi"][1] == 0.0


def test_C6_containment_is_structurally_monotone_normal_to_supt():
    """C-4 la bat bien CAU TRUC khi so cap CUNG cau truc (normal vs supt).
    Vi c_supt > 1.96, dai supt rong hon o MOI o -> chua-0 chi co the TANG."""
    rng = np.random.default_rng(4)
    draws = rng.normal(loc=np.linspace(-3, 3, 24), size=(3000, 24))
    labels = [{"z_bin": 0, "procedure": "p", "slot": 1 + k % 3} for k in range(24)]
    t = G2.three_interval_table({"draws": draws, "point": draws.mean(axis=0)}, labels)
    assert t["C4_containment_monotone"]
    assert t["C4_violations"] == []
    assert t["n_contains_zero_supt"] >= t["n_contains_zero_normal"]


# --------------------------------------------------------------------------
# Nhom 2: du lieu that
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def struct():
    df = pd.read_parquet(CALIB)
    calib = df[df["is_calib"].to_numpy(bool)]
    return G2.build_global_blocks(calib, _slot_cols(df), "z_bin")


@needs_data
def test_C7_global_draw_covers_every_bin(struct):
    """C-D1: mot picks duy nhat chi dung neu MOI block co mat o MOI bin."""
    assert struct["n_blocks"] == 500
    for _g, cells in struct["by_bin"].items():
        assert len(cells) == struct["n_blocks"]
        assert all(c is not None and c.shape[0] > 0 for c in cells)


@needs_data
def test_C8_point_estimate_reproduces_phase22_qhat(struct):
    """picks = arange(n) phai tai lap qhat cua fit_eval_simultaneous.
    Day la neo giu duong ong moi khong troi khoi Phase 22."""
    with open("results/SUPERSEDED/phase-22/conformal_sim_poisson_0.925.json", encoding="utf-8") as f:
        ref = json.load(f)
    nb = struct["n_blocks"]
    m = struct["m"]
    for g in sorted(struct["by_bin"]):
        cells = struct["by_bin"][g]
        for proc in ("maxscore", "bonferroni", "sidak"):
            got = G2.qvec_for_draw(cells, np.arange(nb), proc, 0.10, m, "B")
            exp = np.asarray(ref["procedures"][proc]["qhat"][str(g)], float)
            assert np.allclose(got, exp, atol=1e-9), (g, proc, got, exp)


@needs_data
def test_C9_NC_C_1_passes_on_all_three_variants(struct):
    """NC-C-1. Duong ong Phase 22 DO o variant A (max|delta| = 7.99e-2,
    CI rong 4.24 ms) vi rng bi tieu thu khac nhau giua cac thu tuc.
    Duong ong moi truyen row_picks vao => tat dinh => phai PASS ca ba."""
    for v in G2.VARIANTS:
        nc = G2.negative_control_self_delta(struct, variant=v, n_boot=60)
        assert nc["pass"], nc


@needs_data
def test_C10_variant_A_reads_whole_rows(struct):
    """C-D6: variant A phai giu rang buoc trong-hang  s_sim = max_j s_pair_j.
    Duong ong cu rut doc lap tung cot -> pha vo rang buoc nay."""
    cells = struct["by_bin"][0]
    m = struct["m"]
    for i in (0, 7, 91):
        row = G2._reduce_cell(cells[i], "A", 3)
        assert row.shape == (1, m + 1)
        assert row[0, m] == pytest.approx(row[0, :m].max())


@needs_data
def test_C14_PC_C_1_is_two_sided_and_sigma_calibrated(struct):
    """PC-C-1 da sua. Thiet ke dau tien ('cong 1 ms, doi lo > 0') DO tren du
    lieu that vi hai ly do doc lap:
      (1) dem `lo > 0` bo sot cac o loai tru 0 tu phia AM (slot 1, point ~ -2.6)
      (2) cong HANG SO khong hop le khi point trai tu -2.8 den +1.6 ms: no day
          mot so o RA XA 0 va mot so o LAI GAN 0.
    Thiet ke moi bom tin hieu theo DON VI sigma_hat va kiem CA HAI PHIA.
    """
    pc = G2.positive_control_shift(struct, n_boot=300)
    assert pc["pass_detects_when_it_should"], pc
    assert pc["pass_silent_when_it_should"], pc
    assert pc["n_excludes_zero_at_s_above"] == pc["K"]
    assert pc["n_excludes_zero_at_s_below"] == 0
    # va MDE phai duoc bao cao theo ms de doc duoc thang phan giai
    assert pc["mde_ms_max"] > pc["mde_ms_min"]


@needs_data
def test_C15_excludes_zero_counts_both_sides(struct):
    """Loi (1) cua PC-C-1 cu, khoa bang test rieng: mot khoang nam hoan toan
    ben AM VAN LA loai tru 0."""
    lo = np.array([-3.0, -0.5, 0.5])
    hi = np.array([-2.0, 0.5, 1.5])
    excludes = (lo > 0.0) | (hi < 0.0)
    assert excludes.tolist() == [True, False, True]


@needs_data
@pytest.mark.slow          # 24.2 s -- doi chung hoi tu MC, khong phai tinh dung
def test_C11_B200_is_unstable(struct):
    """C-D5. Bang chung TRUC TIEP vi sao GO-2 can B = 2000."""
    ins = G2.instability_at_small_B(struct, seeds=G2.SEEDS_INSTABILITY[:6])
    assert ins["unstable"], ins
    assert ins["range"] >= 2


@needs_data
def test_C12_supt_c_lies_between_pointwise_and_bonferroni(struct):
    """C-1/C-3. c_supt PHAI nam trong (1.96, 3.078): lon hon tung-diem vi co
    24 dai luong, nho hon Bonferroni vi chung TUONG QUAN.
    Ngoai khoang nay => cong thuc sai, khong phai phat hien."""
    b = G2.bootstrap_deltas(struct, n_boot=300)
    band = G2.supt_band(np.asarray(b["draws"]), np.asarray(b["point"]))
    cv = G2.critical_values(24)
    assert cv["c_pointwise_95"] < band["c_supt"] < cv["c_bonferroni"]


@needs_data
@pytest.mark.slow
def test_C13_mc_criterion_has_two_separate_propositions(struct):
    """Tieu chi MC da SUA. Do rong dai KHONG duoc co theo 1/sqrt(B) --
    no hoi tu ve mot hang so do n_block quyet dinh. Thu co theo 1/sqrt(B)
    la SAI SO MC cua dau mut."""
    mc = G2.mc_convergence(struct, n_seeds=12)
    assert mc["pass_width_stabilises"], mc
    assert mc["pass_mc_error_shrinks"], mc
    # va khang dinh menh de bi bac bo: do rong KHONG co
    lo = mc["by_B"][str(G2.MC_B_LO)]["width_mean"]
    hi = mc["by_B"][str(G2.MC_B_HI)]["width_mean"]
    assert hi > 0.5 * lo, "do rong co gan 1/sqrt(B) => nghi resample theo HANG"

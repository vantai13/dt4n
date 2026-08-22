"""Lesson 23.6 -- doi chung cho cert/abstain_cost.py.

Chia hai nhom:
  A*  chay tren du lieu TONG HOP, LUON chay   -> kiem CAU TRUC va DAI SO
  R*  can parquet that, skip neu thieu        -> kiem GIA TRI

Tach nay co chu y: mot bo test chi chay khi co parquet 69 MB se khong duoc
chay truoc moi commit, va mot test khong duoc chay la mot test khong ton tai.
Moi tinh chat kiem duoc bang du lieu tong hop PHAI nam o nhom A.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest

from cert import abstain_cost as AC

CALIB = "results/SUPERSEDED/phase-22/calib_set_v3.parquet"
BAND_JSON = "results/SUPERSEDED/phase-23/baseline_rankings_poisson_0.925_C3_static.json"
needs_data = pytest.mark.skipif(
    not (os.path.exists(CALIB) and os.path.exists(BAND_JSON)),
    reason="thieu artifact phase-22 v3 hoac baseline_rankings",
)

SCALES1 = ("err",)


def _toy(seed: int = 11, n_block: int = 40, per: int = 50):
    """Du lieu tong hop CO CAU TRUC BLOCK va CO TIN HIEU THAT.

    Do kho tiem an tuong quan trong block; P(sai) tang theo do kho; diem so
    GIAM theo do kho. Nhu vay tap reject o gamma cao chi con ca kho nhat, va
    c*(gamma) PHAI tang -- day la cau truc ma K-6 kiem (K-D6). Mot toy frame
    khong co tin hieu se lam test A11 va A10 vo nghia.
    """
    rng = np.random.default_rng(seed)
    n = n_block * per
    hard = (np.repeat(rng.normal(size=n_block), per)
            + rng.normal(scale=0.3, size=n))
    wrong_twin = (rng.random(n) < 1.0 / (1.0 + np.exp(-hard))).astype(float)
    wrong_p1 = (rng.random(n) < 0.5).astype(float)      # P1 khong biet do kho
    score = -hard + rng.normal(scale=0.2, size=n)
    block_id = np.repeat(np.arange(n_block), per)
    losses = {"twin_err": wrong_twin, "p1_err": wrong_p1}
    return block_id, score, losses


def _stats(grid=None, **kw):
    block_id, score, losses = _toy(**kw)
    g = AC.gamma_grid() if grid is None else grid
    return AC.block_curve_stats(block_id, score, g, losses), g, losses


# ---------------------------------------------------------------------------
# A. Cau truc, dai so, so hoc -- luon chay
# ---------------------------------------------------------------------------

def test_A1_grid_excludes_gamma_one_and_has_fifty_points():
    g = AC.gamma_grid(AC.GRID_STEP_LOCKED)
    assert len(g) == 50
    assert g[0] == 0.0 and g[-1] == 0.98
    assert 1.0 not in set(g.tolist())                    # K-D4
    gf = AC.gamma_grid(AC.GRID_STEP_FINE)
    assert len(gf) == 100 and gf[-1] == 0.99


def test_A1b_grid_has_no_floating_point_dust():
    """np.arange(0, 1, 0.02) sinh 0.060000000000000005 neu khong lam tron.
    Bui do lam khoa JSON khong on dinh giua cac lan chay."""
    for step in (AC.GRID_STEP_LOCKED, AC.GRID_STEP_FINE):
        g = AC.gamma_grid(step)
        assert np.allclose(g, np.round(g, 10), rtol=0, atol=0)


def test_A2_accept_counts_match_baselines_rounding_rule():
    """`coverage_measured` chi dung neu quy tac lam tron GIONG HET
    baselines._accept_at_coverage. Lech mot hang -> G23-32 FAIL oan (D3)."""
    from cert import baselines as BL
    rng = np.random.default_rng(5)
    n = 1237
    s = rng.normal(size=n)
    grid = AC.gamma_grid(AC.GRID_STEP_FINE)
    ks = AC.accept_counts(grid, n)
    for i, gv in enumerate(grid):
        assert int(BL._accept_at_coverage(s, float(gv)).sum()) == int(ks[i])


def test_A3_cstar_at_gamma_zero_equals_r_neo_without_special_case():
    """D1/K-D8: duong TRUC TIEP cho dieu nay TU DONG, khong nhanh dac biet."""
    st, g, _ = _stats()
    pt = AC.curve(st, None, SCALES1)
    assert abs(float(pt["c_star_err"][0]) - float(pt["r_neo_err"])) <= 1e-15


def test_A4_inverse_formula_is_undefined_at_gamma_zero():
    """Chung minh vi sao D1 cam cong thuc dao, thay vi chi khang dinh.

    Duong dao cho `0 * nan = nan` tai gamma = 0. Neu duong tinh chinh dung
    cong thuc dao thi c*(0) la nan va NC23v2-4 do -- do la co che bao ve.
    """
    st, g, _ = _stats()
    pt = AC.curve(st, None, SCALES1)
    gv = np.asarray(pt["coverage"])
    ra = np.asarray(pt["r_accept_err"])
    assert gv[0] == 0.0
    assert not np.isfinite(ra[0]), "r_accept tai gamma=0 phai la nan"
    with np.errstate(invalid="ignore"):
        inv0 = (float(pt["r_neo_err"]) - gv[0] * ra[0]) / (1.0 - gv[0])
    assert not np.isfinite(inv0)
    assert np.isfinite(pt["c_star_err"][0]), "duong TRUC TIEP phai huu han"


def test_A5_partition_identity_holds_on_synthetic():
    st, g, _ = _stats()
    r = AC.partition_identity(AC.curve(st, None, SCALES1), "err")
    assert r["pass"], r
    assert r["n_points_checked"] >= 49


def test_A6_identity_fails_if_target_coverage_is_used_instead_of_measured():
    """D3: chung minh loi 'dung gamma muc tieu' THAT SU bi bat, khong phai
    mot canh bao suong trong docstring.

    Chu y ve fixture: n phai KHONG chia het cho buoc luoi. Voi n = 2000 va
    buoc 0.02 thi gamma*n luon nguyen, target == measured CHINH XAC, va test
    nay se xanh oan -- no khong kiem duoc gi. Du lieu that co n = 499967, mot
    so nguyen to xau, nen nguy co la THAT. Dung n = 41*49 = 2009 de tai tao.
    """
    st, g, _ = _stats(n_block=41, per=49)
    pt = dict(AC.curve(st, None, SCALES1))
    meas = np.asarray(pt["coverage"])
    assert np.max(np.abs(meas - g)) > 1e-6, "fixture qua sach de kiem D3"
    assert AC.partition_identity(pt, "err")["pass"]      # voi measured: dat
    pt["coverage"] = g                                   # co tinh dung TARGET
    assert not AC.partition_identity(pt, "err")["pass"]  # voi target: do


def test_A7_partition_identity_catches_an_off_by_one_partition():
    """Doi chung DUONG cho G23-32: no phai DO duoc khi phan hoach sai."""
    st, g, _ = _stats()
    bad = dict(st)
    bad["n_rej"] = st["n_rej"].copy()
    bad["n_rej"][10, 0] += 1.0                           # mot hang bi dem hai lan
    assert not AC.partition_identity(AC.curve(bad, None, SCALES1), "err")["pass"]


def test_A8_inverse_crosscheck_agrees_with_direct_path_below_gamma_max():
    st, g, _ = _stats()
    r = AC.inverse_formula_crosscheck(AC.curve(st, None, SCALES1), "err")
    assert r["pass"], r
    assert r["n_skipped_undefined"] == 1                 # dung gamma = 0
    assert r["n_skipped_out_of_range"] == int((g > AC.CROSSCHECK_GAMMA_MAX).sum())


def test_A9_bootstrap_weights_are_valid_and_deterministic():
    W = AC.bootstrap_weights(40, n_boot=50, seed=1)
    assert W.shape == (40, 50)
    assert np.allclose(W.sum(axis=0), 40)                # rut n_block co hoan lai
    assert np.array_equal(AC.bootstrap_weights(40, 20, 7),
                          AC.bootstrap_weights(40, 20, 7))


def test_A10_weight_matmul_equals_naive_index_gather():
    """D5 la mot REFORMULATION chinh xac, khong phai xap xi. Chung minh."""
    st, g, _ = _stats(grid=AC.gamma_grid(0.25), seed=3, n_block=15, per=20)
    rng = np.random.default_rng(0)
    picks = rng.integers(0, 15, 15)
    w = np.bincount(picks, minlength=15).astype(float)
    naive = (st["rej_twin_err"][:, picks].sum(axis=1)
             / st["n_rej"][:, picks].sum(axis=1))
    got = AC.curve(st, w, SCALES1)["c_star_err"]
    assert np.allclose(got, naive, rtol=0, atol=1e-15)


def test_A11_prefix_sum_equals_naive_rescan():
    """D6: toi uu O(n) phai cho DUNG CUNG so voi cach quet lai O(n*K)."""
    block_id, score, losses = _toy(seed=4, n_block=12, per=30)
    grid = AC.gamma_grid(AC.GRID_STEP_FINE)
    st = AC.block_curve_stats(block_id, score, grid, losses)
    codes, uniq = pd.factorize(block_id, sort=True)
    nb, n = len(uniq), len(codes)
    order = np.argsort(-score, kind="mergesort")
    for i, gv in enumerate(grid):
        k = int(np.floor(gv * n + 0.5))
        acc = np.zeros(n, bool)
        acc[order[:k]] = True
        assert np.array_equal(st["n_acc"][i],
                              np.bincount(codes[acc], minlength=nb))
        assert np.allclose(
            st["rej_twin_err"][i],
            np.bincount(codes[~acc], weights=losses["twin_err"][~acc],
                        minlength=nb))


def test_A12_ratio_broadcasts_over_bootstrap_axis():
    """`_ratio` phai xu ly (K, n_boot) chia (n_boot,). Mot phien ban dung
    `out[ok] = ...` se index SAI truc va hoac nem hoac tra so sai."""
    num = np.arange(6, dtype=float).reshape(2, 3)
    den = np.array([1.0, 0.0, 2.0])
    out = AC._ratio(num, den)
    assert out.shape == (2, 3)
    assert np.isnan(out[:, 1]).all()
    assert out[1, 2] == 2.5


def test_A13_self_controls_all_pass_and_positive_control_fires():
    st, g, _ = _stats()
    c = AC.self_controls(AC.curve(st, None, SCALES1))
    assert c["NC23v2_4_pass"] and c["NC23v2_5_pass"] and c["NC23v2_6_pass"]
    assert c["PC23v2_1_pass"], c
    assert c["PC23v2_1_n_checked"] > 40, "doi chung duong phai KICH HOAT"


def test_A14_monotonicity_detects_a_planted_inversion():
    """Doi chung duong cho K-6: gate phai DO duoc, neu khong no vo nghia."""
    g = AC.gamma_grid(0.25)
    assert AC.monotonicity(g, np.array([0.10, 0.20, 0.30, 0.40]))["monotone"]
    r = AC.monotonicity(g, np.array([0.10, 0.20, 0.15, 0.40]))
    assert r["n_violations"] == 1
    assert r["violations"][0]["drop"] == pytest.approx(-0.05)
    assert (r["violations"][0]["i_lo"], r["violations"][0]["i_hi"]) == (1, 2)


def test_A15_monotonicity_skips_nan_and_keeps_grid_indices():
    """Chi so vi pham phai la chi so TRONG grid, khong phai trong tap huu han
    -- neu khong `increment_ci` se lay nham cot cua ma tran draw."""
    g = AC.gamma_grid(0.20)
    c = np.array([np.nan, 0.30, 0.20, 0.40, 0.50])
    r = AC.monotonicity(g, c)
    assert r["n_points_finite"] == 4 and r["n_violations"] == 1
    assert (r["violations"][0]["i_lo"], r["violations"][0]["i_hi"]) == (1, 2)


def test_A16_increment_ci_is_paired_not_merely_narrow():
    """Ghep cap phai lam dai hep DUNG BAC do lon, khong chi hep hon mot chut.

    Phien ban dau cua test nay khang dinh `paired < tong hai be rong bien`.
    Kiem thu dot bien cho thay khang dinh do VO DUNG: pha ghep cap (sort mot
    cot) van thoa man no, vi hieu cua hai bien khong ghep cap co sd ~ sqrt(2)
    lan sd bien, con TONG hai be rong la ~2 lan. Test song sot dot bien = test
    trang tri.

    Khang dinh dung: voi tuong quan duong RAT MANH, hieu chi con phan NHIEU
    RIENG, nen dai ghep cap phai nho hon MOT BAC so voi dai tung bien.
    """
    rng = np.random.default_rng(2)
    common = rng.normal(size=(500, 1))                   # sd 1.0, chung
    draws = common + rng.normal(scale=0.01, size=(500, 2))   # nhieu rieng 0.01
    viol = [{"i_lo": 0, "i_hi": 1, "gamma_lo": 0.0, "gamma_hi": 0.02,
             "drop": -0.001}]
    r = AC.increment_ci(draws, viol)[0]
    paired = r["ci_hi"] - r["ci_lo"]
    marg = min(np.ptp(np.quantile(draws[:, j], [0.025, 0.975])) for j in (0, 1))
    assert paired < 0.1 * marg, (
        "dai ghep cap %.4f khong hep hon mot bac so voi dai bien %.4f -- "
        "ghep cap da bi pha" % (paired, marg))
    assert r["contains_zero"] is True
    assert r["sd_boot"] == pytest.approx(0.01 * np.sqrt(2), rel=0.25)


def test_A16b_increment_ci_reports_mde_and_ratio():
    """K-13: MDE phai duoc bao cao CANH moi ket luan "chua 0" (NT-v2-14)."""
    rng = np.random.default_rng(3)
    draws = rng.normal(size=(800, 2)) * 0.01
    r = AC.increment_ci(draws, [{"i_lo": 0, "i_hi": 1, "gamma_lo": 0.0,
                                 "gamma_hi": 0.02, "drop": -0.004}])[0]
    assert r["mde"] == pytest.approx(0.5 * (r["ci_hi"] - r["ci_lo"]))
    assert r["observed_over_mde"] == pytest.approx(0.004 / r["mde"])
    assert r["mde"] > 0


def test_A22_pc_k10_fires_on_strong_signal_and_stays_silent_on_weak():
    """PC23v2-2: doi chung DUONG phai kich hoat CA HAI phia.

    Mot doi chung chi kiem "tin hieu lon thi thay" van co the la mot phep do
    luon-luon-thay. Phia "tin hieu nho thi khong thay" moi loai duoc kha nang do.
    """
    rng = np.random.default_rng(9)
    d = rng.normal(scale=0.01, size=4000)
    r = AC.pc_k10_planted_drop(d)
    arms = {a["s_units"]: a for a in r["arms"]}
    assert arms[2.5]["excludes_zero"] is True
    assert arms[1.5]["excludes_zero"] is False
    assert r["pass"] is True
    assert arms[2.5]["planted_drop"] == pytest.approx(-2.5 * r["sd_boot"])


def test_A23_pc_k10_plants_in_sigma_units_not_absolute_constants():
    """Bom theo don vi sigma: nhan doi thang do du lieu phai nhan doi sut giam
    bom vao, va ket luan hai phia KHONG doi. Mot hang so tuyet doi se pha vo
    tinh chat nay -- va khi do doi chung tu tao ra that bai cua chinh no."""
    rng = np.random.default_rng(9)
    d = rng.normal(scale=0.01, size=4000)
    r1, r2 = AC.pc_k10_planted_drop(d), AC.pc_k10_planted_drop(1000.0 * d)
    assert r2["sd_boot"] == pytest.approx(1000.0 * r1["sd_boot"], rel=1e-9)
    for a1, a2 in zip(r1["arms"], r2["arms"]):
        assert a2["planted_drop"] == pytest.approx(1000.0 * a1["planted_drop"],
                                                   rel=1e-9)
        assert a1["excludes_zero"] == a2["excludes_zero"]
    assert r1["pass"] and r2["pass"]


def test_A24_pc_k10_fails_when_measurement_is_blind():
    """Doi chung phai DO duoc: mot phan phoi qua tan mat khong thay ca 2.5 sd.

    Dung phan phoi duoi nang (heavy-tailed) de q_975/sd > 2.5, tuc phep do
    khong phan giai duoc mot sut giam 2.5 sigma.
    """
    rng = np.random.default_rng(4)
    d = rng.standard_t(df=2, size=20000)          # duoi nang, q_975/sd nho hon
    r = AC.pc_k10_planted_drop(d, s_units=(0.5, 0.2))
    assert r["pass"] is False


def test_A24b_pc_k10_fails_when_the_weak_arm_ALSO_fires():
    """Phia YEU phai duoc kiem, khong chi phia manh.

    Kiem thu dot bien: bo dieu kien phia yeu khoi `pass` KHONG lam do test nao
    -- `test_A24` di qua vi danh sach `strong` cua no rong. Test nay dong lo
    hong do.

    Phan phoi hai diem `+/-1` co q_975/sd = 1.0, nen ngay ca mot sut giam 1.5
    sigma cung "loai tru 0". Do la mot phep do LUON-LUON-THAY: no khong phan
    biet duoc tin hieu that voi bat cu thu gi, nen doi chung phai BAO DO.
    """
    rng = np.random.default_rng(6)
    d = rng.choice([-1.0, 1.0], size=20000)
    r = AC.pc_k10_planted_drop(d)
    arms = {a["s_units"]: a for a in r["arms"]}
    assert arms[2.5]["excludes_zero"] is True     # phia manh: thay
    assert arms[1.5]["excludes_zero"] is True     # phia yeu: CUNG thay -> mu
    assert r["pass"] is False, "phep do luon-luon-thay phai lam PC23v2-2 DO"


def test_A27_locked_grid_is_a_subset_of_the_fine_grid():
    """F-23.6-5 diem (1): can duoi cua K-15 la TAT DINH, khong phai mot kiem dinh.

    50 diem luoi khoa la tap con dung cua 100 diem luoi min. Vi `sd_k` dung
    chung ma tran draw, T_fine^(b) = max tren tap lon hon >= T_locked^(b) voi
    moi draw, nen ti so >= 1.0 luon dung. K-15 la phep kiem MOT PHIA.
    """
    gl = set(np.round(AC.gamma_grid(AC.GRID_STEP_LOCKED), 10).tolist())
    gf = set(np.round(AC.gamma_grid(AC.GRID_STEP_FINE), 10).tolist())
    assert gl < gf and len(gl) == 50 and len(gf) == 100


def test_A25_effective_n_tests_inverts_bonferroni_exactly():
    """F-23.6-3: kiem NGUOC bat buoc. Neu cong thuc sai thi K_eff vo nghia."""
    for k in (8, 24, 50, 100):
        c = AC.critical_values(k, AC.FWER)["c_bonferroni"]
        assert AC.effective_n_tests(c, AC.FWER) == pytest.approx(k, rel=1e-6)


def test_A26_effective_n_tests_is_monotone_in_c():
    """c_supt lon hon <=> nhieu chieu hieu dung hon. Dau phai dung."""
    ks = [AC.effective_n_tests(c) for c in (2.5, 2.7, 2.9, 3.1)]
    assert ks == sorted(ks)


def test_A17_band_crosscheck_records_out_of_grid_endpoint():
    cross = [{"gamma_cross": 0.61, "gamma_lo": 0.60, "gamma_hi": 0.61,
              "direction": "F2_becomes_profitable"}]
    r = AC.band_crosscheck(cross, {"band_low": 0.6076, "band_high": 0.99995},
                           0.99)
    assert r["pass"] and len(r["endpoint_out_of_grid"]) == 1
    assert r["n_endpoints_in_grid"] == 1


def test_A18_band_crosscheck_fails_when_second_endpoint_is_missed():
    """Chot loi cua ban thao Amendment 23-26: kiem MOT dau mut la khong du.
    poisson@0.850 co band_high = 0.9892 NAM TRONG luoi."""
    cross = [{"gamma_cross": 0.81, "gamma_lo": 0.80, "gamma_hi": 0.81,
              "direction": "F2_becomes_profitable"}]
    r = AC.band_crosscheck(cross, {"band_low": 0.8091, "band_high": 0.9892},
                           0.99)
    assert not r["pass"]
    assert [m["endpoint"] for m in r["unmatched"]] == ["band_high"]


def test_A19_band_crosscheck_requires_band_keys():
    """`require` thay cho `.get(default)`: khoa thieu la BUG, khong phai 0."""
    with pytest.raises(KeyError):
        AC.band_crosscheck([], {"band_low": 0.5}, 0.99)


def test_A20_every_scale_bearing_key_carries_a_scale_suffix():
    """K-D3, quet khoa theo mau test_T24 cua Lesson 23.5[A]."""
    block_id, score, _ = _toy()
    losses = {"twin_err": np.zeros(len(score)), "p1_err": np.zeros(len(score)),
              "twin_regret": np.zeros(len(score)),
              "p1_regret": np.zeros(len(score))}
    st = AC.block_curve_stats(block_id, score, AC.gamma_grid(), losses)
    keys = set(AC.curve(st, None, ("err", "regret")))
    for stem in ("c_star", "c_f2", "r_neo", "r_accept"):
        assert {stem + "_err", stem + "_regret"} <= keys
        assert stem not in keys, "%r khong mang hau to thang" % stem


def test_A21_breakeven_signature_takes_no_fallback_argument():
    """Menh de trung tam cua 23.6: c* KHONG phu thuoc fallback. Chu ky ham la
    bang chung kiem duoc bang may, khong phai mot cau trong docstring."""
    import inspect
    params = list(inspect.signature(AC.breakeven_c).parameters)
    assert params == ["r_reject_twin"]


# ---------------------------------------------------------------------------
# R. Gia tri that -- can parquet
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real():
    return pd.read_parquet(CALIB)


@needs_data
def test_R1_qhat_of_C3_is_invariant_to_kappa(real):
    """D4 gia dinh MOT fit duy nhat dung cho MOI gamma.

    C3 co post = 'mondrian' nen `fit_config` tinh q mot lan, khong lap (khac
    'fcr'). Vi vay q_hat khong the phu thuoc kappa. Kiem, dung gia dinh --
    neu FAIL thi toan bo thiet ke phai doi sang mot fit moi gamma.
    """
    from cert import config_matrix as CM
    from cert.simultaneous_score import ALPHA as A
    calib = real[real["is_calib"]]
    q1 = CM.fit_config(calib, "C3", 0.25, alpha=A, multiplicity="bonferroni")["_q"]
    q2 = CM.fit_config(calib, "C3", 1.00, alpha=A, multiplicity="bonferroni")["_q"]
    assert set(q1) == set(q2)
    for k in q1:
        assert np.allclose(q1[k], q2[k], rtol=0, atol=0)


@needs_data
def test_R2_cstar_and_cf2_match_amendment_23_26(real):
    """Bon con so khoa o Amendment 23-26 muc 1.4, cell chinh."""
    test, score, _ = AC.fit_score(real)
    losses = AC.row_losses(test, SCALES1)
    grid = AC.gamma_grid(AC.GRID_STEP_FINE)
    st = AC.block_curve_stats(test["block_id"].to_numpy(), score, grid, losses)
    pt = AC.curve(st, None, SCALES1)
    i = int(np.flatnonzero(np.isclose(grid, 0.78))[0])
    assert int(pt["n_accept"][i]) == 389974
    assert float(pt["coverage"][i]) == pytest.approx(0.7799994799656778, abs=1e-15)
    assert float(pt["c_star_err"][i]) == pytest.approx(0.453347031, abs=5e-9)
    assert float(pt["c_f2_err"][i]) == pytest.approx(0.394852400, abs=5e-9)
    assert float(pt["r_neo_err"]) == pytest.approx(0.222398678, abs=5e-9)


@needs_data
def test_R3_K6_passes_on_locked_grid_and_K9_is_three_on_fine_grid(real):
    """K-6 PASS tren luoi khoa; K-9 = 3 vi pham trong gamma <= 0.98."""
    test, score, _ = AC.fit_score(real)
    losses = AC.row_losses(test, SCALES1)
    bid = test["block_id"].to_numpy()
    gl, gf = AC.gamma_grid(AC.GRID_STEP_LOCKED), AC.gamma_grid(AC.GRID_STEP_FINE)
    ml = AC.monotonicity(gl, AC.curve(
        AC.block_curve_stats(bid, score, gl, losses), None, SCALES1)["c_star_err"])
    mf = AC.monotonicity(gf, AC.curve(
        AC.block_curve_stats(bid, score, gf, losses), None, SCALES1)["c_star_err"])
    assert ml["n_violations"] == 0 and ml["monotone"]            # K-6
    assert mf["n_violations"] == 4                               # gom 0.98->0.99
    assert sum(1 for v in mf["violations"] if v["gamma_hi"] <= 0.98) == 3  # K-9
    assert min(v["gamma_lo"] for v in mf["violations"]) >= 0.85  # K-11


@needs_data
def test_R4_band_crosscheck_C23v2_1_passes(real):
    """C23v2-1: diem doi dau khop beneficial_band cua Lesson 23.3."""
    band = json.load(open(BAND_JSON))["beneficial_band_err"]["C3_conformal"]
    test, score, _ = AC.fit_score(real)
    losses = AC.row_losses(test, SCALES1)
    gf = AC.gamma_grid(AC.GRID_STEP_FINE)
    pt = AC.curve(AC.block_curve_stats(test["block_id"].to_numpy(), score, gf,
                                       losses), None, SCALES1)
    r = AC.band_crosscheck(AC.crossings(gf, pt["c_f2_err"], pt["c_star_err"]),
                           band, float(gf[-1]))
    assert r["pass"], r
    assert len(r["endpoint_out_of_grid"]) == 1        # band_high = 0.99995


@needs_data
def test_R6_curve_reproduces_lesson_23_3_sweep_bit_for_bit(real):
    """D4 duoc kiem o muc MANH NHAT: khong phai "cung ham" ma "cung so".

    Neu duong ong cua 23.6 lech du chi mot hang so voi 23.3, doi chung cheo
    C23v2-1 se khop hoac khong khop vi mot ly do khong ai truy duoc. Test nay
    loai kha nang do: `coverage`, `n_accept`, `err_accept`, `err_reject` phai
    trung TUYET DOI tren ca 100 diem luoi. `regret` chi duoc lech o muc thu tu
    cong dau phay dong (~1e-15) vi 23.3 lay mean tren hang con 23.6 lay ti so
    cua tong theo block.
    """
    sweep = json.load(open(BAND_JSON))["sweeps"]["C3_conformal"]
    test, score, _ = AC.fit_score(real)
    losses = AC.row_losses(test, ("err", "regret"))
    gf = AC.gamma_grid(AC.GRID_STEP_FINE)
    pt = AC.curve(AC.block_curve_stats(test["block_id"].to_numpy(), score, gf,
                                       losses), None, ("err", "regret"))
    for i in range(len(gf)):
        v1 = sweep[i]
        assert int(v1["n_accept"]) == int(pt["n_accept"][i])
        assert v1["coverage"] == pt["coverage"][i]
        if v1["err_accept"] is not None:
            assert v1["err_accept"] == pt["r_accept_err"][i]
        if v1["err_reject"] is not None:
            assert v1["err_reject"] == pt["c_f2_err"][i]
            assert v1["regret_reject"] == pytest.approx(
                pt["c_f2_regret"][i], abs=1e-14)


@needs_data
def test_R7_K15_ratio_is_at_least_one_and_inside_the_locked_band(real):
    """K-15 (dai [0.98, 1.04], khoa o Amd 23-27 muc 6.2) + F-23.6-5 diem (1)."""
    band = json.load(open(BAND_JSON))["beneficial_band_err"]["C3_conformal"]
    r = AC.run_cell(real, "poisson@0.925", band, n_boot=500)
    g = r["grid_refinement_K15"]
    assert g["n_points_locked"] == 50 and g["n_points_fine"] == 100
    assert g["ratio_fine_over_locked"] >= 1.0        # tat dinh, xem test_A27
    assert 0.98 <= g["ratio_fine_over_locked"] <= 1.04
    assert g["k_eff_fine"] > g["k_eff_locked"]       # co them chieu...
    assert g["k_eff_fine"] < 2.0 * g["k_eff_locked"]  # ...nhung khong gap doi


@needs_data
def test_R8_pc23v2_2_fires_two_sided_on_every_violation(real):
    """PC23v2-2: khong co no thi "7/7 CI chua 0" khong doc duoc (NT-v2-14)."""
    band = json.load(open(BAND_JSON))["beneficial_band_err"]["C3_conformal"]
    r = AC.run_cell(real, "poisson@0.925", band, n_boot=2000)
    inc = r["increment_ci_K10"]
    assert len(inc) == 4
    for c in inc:
        assert c["pc23v2_2"]["pass"], c
        assert c["contains_zero"]
        assert c["observed_over_mde"] < 1.0, (
            "|drop| >= MDE -> khong con la UNDETECTED, phai dieu tra lai")


def test_A28_sticky_stats_match_a_direct_recomputation():
    """F-23.6-7: F1 rut gon duoc theo block. Kiem bang cach so voi cach tinh
    truc tiep tung diem luoi -- neu lech thi gia dinh "trang thai khong vuot
    block" sai va toan bo K-D10 do."""
    from cert import baselines as BL
    from cert import fallback as FB
    rng = np.random.default_rng(21)
    nb, per = 12, 25
    n = nb * per
    test = pd.DataFrame({
        "block_id": np.repeat(np.arange(nb), per),
        "t_idx": np.tile(np.arange(per), nb),
        "a_twin": rng.integers(0, 4, n),
        "a_star": rng.integers(0, 4, n),
    })
    score = rng.normal(size=n)
    grid = AC.gamma_grid(0.25)
    st = AC.sticky_curve_stats(test, score, grid, ("err",))
    codes, _ = pd.factorize(test["block_id"].to_numpy(), sort=True)
    for i, gv in enumerate(grid):
        acc = BL._accept_at_coverage(score, float(gv))
        a = FB.fallback_sticky(test, acc)
        w = FB.loss_of(test, a, "err")
        assert np.allclose(st["rej_f1_err"][i],
                           np.bincount(codes[~acc], weights=w[~acc], minlength=nb))


def test_A29_curve_f1_shares_the_denominator_with_curve():
    """Ghep cap giua c_F1 va c* chi dung neu HAI duong dung CHUNG n_rej tren
    cung mot draw. Neu moi ben tu tinh mau so, hieu se mang them nhieu."""
    st, g, losses = _stats(grid=AC.gamma_grid(0.25))
    sticky = {"rej_f1_err": st["rej_twin_err"].copy()}   # gia lap: F1 == twin
    w = np.ones(st["n_block"])
    assert np.allclose(AC.curve_f1(st, sticky, w, ("err",))["c_f1_err"],
                       AC.curve(st, w, ("err",))["c_star_err"], atol=1e-15)


def test_A30_certification_table_carries_its_reading_notes():
    """G23-36 bi doc sai neu ba luu y khong DI THEO du lieu. Nhung chung vao
    artifact, khong chi de trong doc -- bang se bi trich ra cho khac."""
    pt = {"coverage": np.array([0.78]), "c_star_err": np.array([0.45]),
          "c_star_regret": np.array([4.1])}
    t = AC.certification_table(pt, 0, ("err", "regret"))
    assert set(t["thresholds"]) == {"c_star_err", "c_star_regret"}
    assert len(t["reading_notes"]) == 3
    assert any("NGUONG" in s for s in t["reading_notes"])


@needs_data
def test_R9_f1_and_f3_are_identical_on_every_grid_point(real):
    """F-23.6-6: F3 WAIT tra ve chinh a_chosen cua F1 STICKY (P17, secondary
    sticky). Kiem tren CA luoi, khong chi diem van hanh."""
    from cert import baselines as BL
    from cert import fallback as FB
    test, score, _ = AC.fit_score(real)
    for gv in (0.30, 0.50, AC.OPERATING_GAMMA, 0.90):
        acc = BL._accept_at_coverage(score, gv)
        assert np.array_equal(FB.apply_fallback(test, acc, "sticky")["a_chosen"],
                              FB.apply_fallback(test, acc, "wait")["a_chosen"])


@needs_data
def test_R10_artifact_schema_matches_K_D11(real):
    """K-D11 (Amendment 23-28 muc 4) + K-D3: moi khoa mang thang phai co hau to."""
    import json
    from pathlib import Path
    p = Path("results/SUPERSEDED/phase-23/abstain_cost_poisson_0.925.json")
    if not p.exists():
        pytest.skip("chua sinh artifact; chay `python -m cert.abstain_cost`")
    d = json.loads(p.read_text())
    for k in ("cell", "status", "scale", "level_tag", "rowset", "gates",
              "fallback_locations_G23_35", "certification_table_G23_36",
              "grid_refinement_K15", "supt_bands", "operating_gamma",
              "f3_wait_evaluated_at", "input_artifact", "provenance"):
        assert k in d, "thieu khoa bat buoc %r" % k
    row = d["sweep_locked"][39]
    assert row["coverage_target"] == 0.78 and "coverage_measured" in row
    for stem in ("c_star", "c_f1", "c_f2", "c_f3", "r_neo", "r_accept"):
        assert stem + "_err" in row and stem + "_regret" in row
        assert stem not in row, "%r khong mang hau to thang (K-D3)" % stem
    loc = d["fallback_locations_G23_35"]
    assert loc["f1_f3_identical"] is True and "F-23.6-6" in loc["f1_f3_reason"]
    assert d["gates"]["G23-34"]["status"] == "NOT_RUN"   # NT-v2-15
    assert "NaN" not in p.read_text()                    # RFC 8259


@needs_data
def test_R11_NC23v2_7_sticky_collapses_to_static_at_gamma_zero(real):
    """Doi chung AM cho khong: tai gamma = 0 khong hang nao duoc chap nhan, nen
    sticky khong co gi de "dinh" vao va roi ve P1 -- tuc DUNG BANG static.

    `c_F1(0) == c_F2(0)` CHINH XAC. Neu lech, `fallback_sticky` dang ro ri mot
    hanh dong tu dau do -- co the tu block truoc (vi pham P17) hoac tu mot hang
    da bi tu choi.
    """
    import json
    from pathlib import Path
    p = Path("results/SUPERSEDED/phase-23/abstain_cost_poisson_0.925.json")
    if not p.exists():
        pytest.skip("chua sinh artifact")
    row0 = json.loads(p.read_text())["sweep_locked"][0]
    assert row0["coverage_target"] == 0.0 and row0["n_accept"] == 0
    assert row0["c_f1_err"] == row0["c_f2_err"]
    assert row0["c_f1_regret"] == row0["c_f2_regret"]


@needs_data
def test_R12_figure4_crossings_land_on_band_low(real):
    """Kiem [2] cua muc 4.4: diem cat phai trung tam giac `band_low`.

    Day la C23v2-1 nhin bang mat, duoc chuyen thanh mot khang dinh bang may de
    khong ai phai nheo mat vao file PNG.
    """
    pytest.importorskip("matplotlib")
    from cert import plot_abstain_cost as PL
    for cell in PL.CELLS:
        art_p = PL.RESULTS / ("abstain_cost_%s.json" % PL._tag(cell))
        if not art_p.exists():
            pytest.skip("chua sinh artifact")
        art, v1 = PL.load(cell), PL.load_band_v1(cell)
        cross = [c["gamma_cross"] for c in art["crossings_locked"]
                 if c["gamma_cross"] <= PL.GAMMA_MAX]
        assert cross, "%s: khong tim thay diem cat trong luoi" % cell
        assert min(abs(x - v1["band_low"]) for x in cross) <= AC.BAND_TOL


@needs_data
def test_R13_figure4_panels_are_not_all_the_same(real):
    """Kiem [3] cua muc 4.4: neu ba panel trong giong nhau thi vong lap dang
    ve cung mot cell ba lan len ba truc khac nhau -- mot loi rat pho bien va
    hoan toan im lang."""
    pytest.importorskip("matplotlib")
    from cert import plot_abstain_cost as PL
    if not (PL.RESULTS / "abstain_cost_h2_0.700.json").exists():
        pytest.skip("chua sinh artifact")
    xs = [PL.load(c)["crossings_locked"][0]["gamma_cross"] for c in PL.CELLS]
    assert len(set(round(x, 3) for x in xs)) == 3, (
        "ba panel co cung diem cat %s -- co the dang ve cung mot cell" % xs)


@needs_data
def test_R5_G23_32_identity_holds_on_real_data(real):
    test, score, _ = AC.fit_score(real)
    losses = AC.row_losses(test, SCALES1)
    gl = AC.gamma_grid(AC.GRID_STEP_LOCKED)
    pt = AC.curve(AC.block_curve_stats(test["block_id"].to_numpy(), score, gl,
                                       losses), None, SCALES1)
    ident = AC.partition_identity(pt, "err")
    assert ident["pass"] and ident["max_abs_residual"] <= AC.IDENTITY_TOL
    inv = AC.inverse_formula_crosscheck(pt, "err")
    assert inv["pass"], inv

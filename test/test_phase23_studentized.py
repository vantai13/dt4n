"""Golden tests -- cert.studentized_score, Phase 23 Lesson 23.5[A]."""

import os

import numpy as np
import pandas as pd
import pytest

import cert.studentized_score as ST
from cert.simultaneous_score import ALPHA, conformal_level


CALIB = "results/phase-22/calib_set_v3_poisson_0.925.parquet"
needs_data = pytest.mark.skipif(not os.path.exists(CALIB), reason="thieu artifact phase-22 v3")


def _toy_frame(rng, n_blocks=80, per_block=40, n_bins=2):
    rows = []
    for block in range(n_blocks):
        base = rng.normal(0.0, 1.0)
        for _ in range(per_block):
            scores = np.abs(rng.normal(base, 1.0, size=3) * np.array([1.0, 1.5, 2.5]))
            rows.append(
                {
                    "block_id": block,
                    "z_bin": block % n_bins,
                    "s_pair_1": scores[0],
                    "s_pair_2": scores[1],
                    "s_pair_3": scores[2],
                    "s_sim": scores.max(),
                }
            )
    df = pd.DataFrame(rows)
    df["is_calib"] = df["block_id"] < n_blocks // 2
    return df


def test_T1_fold_split_whole_blocks_and_deterministic():
    bid = np.repeat(np.arange(40), 25)
    m1, m2 = ST.split_folds_by_block(bid, seed=7001, frac_fold1=0.5)
    assert not (m1 & m2).any()
    assert (m1 | m2).all()
    for block in np.unique(bid):
        rows = bid == block
        assert len(set(m1[rows].tolist())) == 1
    again, _ = ST.split_folds_by_block(bid, seed=7001)
    assert np.array_equal(m1, again)
    other, _ = ST.split_folds_by_block(bid, seed=7002)
    assert not np.array_equal(m1, other)


def test_T2_estimate_sigma_rms_is_exact():
    scores = np.array([[3.0, 0.0], [4.0, 0.0], [0.0, 5.0]])
    sigma = ST.estimate_sigma(scores, "rms")
    assert sigma[0] == pytest.approx(np.sqrt((9.0 + 16.0) / 3.0))
    assert sigma[1] == pytest.approx(np.sqrt(25.0 / 3.0))


def test_T3_sigma_floor_guards_degenerate_slot():
    scores = np.zeros((100, 3))
    scores[:, 1] = 2.0
    sigma = ST.estimate_sigma(scores, "rms")
    assert np.all(sigma > 0.0)
    assert sigma[0] == pytest.approx(ST.SIGMA_FLOOR)
    v = ST.s_studentized(scores, sigma)
    assert np.all(np.isfinite(v))


def test_T4_s_studentized_is_max_of_ratios():
    scores = np.array([[1.0, 4.0], [6.0, 2.0]])
    sigma = np.array([1.0, 2.0])
    assert np.allclose(ST.s_studentized(scores, sigma), [2.0, 6.0])


def test_T5_qhat_is_exactly_proportional_to_sigma():
    rng = np.random.default_rng(0)
    scale = np.array([1.0, 2.0, 4.0])
    f1 = np.abs(rng.normal(size=(4000, 3)) * scale)
    f2 = np.abs(rng.normal(size=(4000, 3)) * scale)
    out = ST.qhat_studentized(f1, f2, n_blocks_fold2=200)
    qhat = np.asarray(out["qhat"])
    sigma = np.asarray(out["sigma"])
    assert np.allclose(qhat / sigma, out["c"], rtol=1e-12)


def test_T6_studentization_reallocates_not_shrinks():
    rng = np.random.default_rng(1)
    scale = np.array([1.0, 2.0, 5.0])
    f1 = np.abs(rng.normal(size=(8000, 3)) * scale)
    f2 = np.abs(rng.normal(size=(8000, 3)) * scale)
    out = ST.qhat_studentized(f1, f2, n_blocks_fold2=400)
    qhat = np.asarray(out["qhat"])
    qmax = ST.maxscore_on_rows(f2.max(axis=1), 400, ALPHA, 3)
    assert qhat[0] < qmax[0]
    assert qhat[2] > qmax[2]
    assert out["sigma_ratio_max_over_min"] > 1.0


def test_T7_n_eff_uses_blocks_not_rows():
    assert conformal_level(250, 0.10) == pytest.approx(226 / 250)
    assert conformal_level(250, 0.10) > conformal_level(250_000, 0.10)


def test_T8_status_label_is_enforced():
    assert ST.STATUS == "EXPLORATORY"
    df = _toy_frame(np.random.default_rng(2))
    out = ST.fit_eval_studentized(df, df["is_calib"].to_numpy(bool))
    assert out["status"] == "EXPLORATORY"


def test_T9_raises_when_fold2_too_thin():
    scores = np.abs(np.random.default_rng(3).normal(size=(50, 3)))
    with pytest.raises(ValueError, match="block"):
        ST.qhat_studentized(scores, scores, n_blocks_fold2=4)


def test_T10_NC_S_1_uniform_sigma_equals_maxscore_on_fold2():
    df = _toy_frame(np.random.default_rng(4))
    out = ST.negative_control_uniform_sigma(df, df["is_calib"].to_numpy(bool))
    assert out["max_abs_diff"] <= 1e-9
    assert out["pass_G23_26"]


def test_T11_global_fold_split_no_block_in_both_folds_across_bins():
    df = _toy_frame(np.random.default_rng(5))
    ic = df["is_calib"].to_numpy(bool)
    bid = df["block_id"].to_numpy()
    pos = np.flatnonzero(ic)
    m1, _ = ST.split_folds_by_block(bid[pos], ST.SEED_FOLD, ST.FRAC_FOLD1)
    f1_blocks = set(bid[pos][m1].tolist())
    f2_blocks = set(bid[pos][~m1].tolist())
    assert f1_blocks.isdisjoint(f2_blocks)


def test_T12_sigma_never_computed_from_test_rows(monkeypatch):
    df = _toy_frame(np.random.default_rng(6))
    ic = df["is_calib"].to_numpy(bool)
    n_calib = int(ic.sum())
    seen = []
    original = ST.estimate_sigma

    def spy(arr, *args, **kwargs):
        seen.append(len(arr))
        return original(arr, *args, **kwargs)

    monkeypatch.setattr(ST, "estimate_sigma", spy)
    ST.fit_eval_studentized(df, ic)
    assert seen and max(seen) <= n_calib


@pytest.fixture(scope="module")
def real():
    df = pd.read_parquet(CALIB)
    return df, df["is_calib"].to_numpy(bool)


@needs_data
def test_T13_coverage_holds_on_real_data(real):
    df, ic = real
    out = ST.fit_eval_studentized(df, ic)
    assert out["coverage_marginal"] >= 1.0 - ALPHA - 0.02
    for group, coverage in out["coverage_simultaneous"].items():
        assert coverage >= 1.0 - ALPHA - 0.05, "bin %s vo: %.4f" % (group, coverage)


@needs_data
def test_T14_sigma_ratio_matches_committed_artifact(real):
    df, ic = real
    out = ST.fit_eval_studentized(df, ic)
    ratios = [v["sigma_ratio_max_over_min"] for v in out["per_bin"].values()]
    assert 1.0 < min(ratios) and max(ratios) < 1.6, ratios


@needs_data
def test_T15_PC_S_1_reports_and_does_not_silently_pass(real):
    df, ic = real
    full = ST.positive_control_sigma_leak(df, ic)
    assert abs(full["coverage_drop"]) < 0.02
    assert full["detectable"] is False


def test_T16_pc_control_refuses_saturating_configuration():
    """Doi chung duong bi TRAN CHAN thi VO NGHIA. Chan tu trong code."""
    df = _toy_frame(np.random.default_rng(7))
    ic = df["is_calib"].to_numpy(bool)
    for target in (9, 10, 11, 15, 18):
        assert conformal_level(target, ALPHA) == 1.0, target
        with pytest.raises(ValueError, match="TRAN CHAN"):
            ST.positive_control_sigma_leak(df, ic, n_blocks_fold2_target=target)
        with pytest.raises(ValueError, match="TRAN CHAN"):
            ST.positive_control_high_dim_sigma(df, ic, n_blocks_fold2_target=target)


def test_T17_min_blocks_unsaturated_is_19_at_alpha_0p10():
    n_min = ST.min_blocks_unsaturated(0.10)
    assert n_min == 19
    assert conformal_level(n_min - 1, 0.10) == 1.0
    assert conformal_level(n_min, 0.10) < 1.0
    assert ST.min_blocks_unsaturated(0.05) == 39


def test_T18_pc_target_30_is_accepted_and_not_saturating():
    assert conformal_level(ST.PC_TARGET_BLOCKS_FOLD2, ALPHA) == pytest.approx(28 / 30)
    assert conformal_level(ST.PC_TARGET_BLOCKS_FOLD2, ALPHA) < 1.0


def test_T19_accept_set_contingency_cells_partition_the_test_rows():
    rng = np.random.default_rng(11)
    df = _toy_frame(rng)
    for j in (1, 2, 3):
        df["m_hat_%d" % j] = np.abs(rng.normal(3.0, 1.0, size=len(df)))
        df["m_true_%d" % j] = df["m_hat_%d" % j] + rng.normal(0.0, 0.5, size=len(df))
    df["wrong"] = df["m_true_1"] < 0.0
    ic = df["is_calib"].to_numpy(bool)
    a = ST.fit_eval_studentized(df, ic, force_uniform_sigma=1.0)
    b = ST.fit_eval_studentized(df, ic)
    out = ST.accept_set_contingency(df, ic, a, b)
    total = out["both"]["n"] + out["only_maxscore"]["n"] + out["only_studentized"]["n"] + out["neither"]["n"]
    assert total == out["n_test"]
    assert out["both"]["n"] + out["only_maxscore"]["n"] == out["n_accept_maxscore"]
    assert out["both"]["n"] + out["only_studentized"]["n"] == out["n_accept_studentized"]


def test_T20_high_dim_clean_arm_holds_coverage_and_leaked_arm_is_lower():
    """Bao dam khong phu thuoc sigma DUNG, chi phu thuoc sigma DOC LAP."""
    rng = np.random.default_rng(12)
    df = _toy_frame(rng, n_blocks=400, per_block=30, n_bins=2)
    df["m_hat_1"] = rng.normal(0.0, 1.0, size=len(df))
    out = ST.positive_control_high_dim_sigma(df, df["is_calib"].to_numpy(bool), n_mhat_cells=40)
    assert out["p_per_bin"] == 120
    assert out["coverage_clean"] >= 1.0 - ALPHA - 0.03, out["coverage_clean"]
    assert out["coverage_leaked"] <= out["coverage_clean"] + 1e-9


@needs_data
def test_T21_c_is_near_constant_across_bins_under_per_bin_sigma(real):
    """F-23.5A-1 -- phat hien ngoai du kien, giu la [MO TA]."""
    df, ic = real
    per_bin = ST.c_invariance_by_bin(ST.fit_eval_studentized(df, ic))
    glob = ST.c_invariance_by_bin(ST.fit_eval_studentized(df, ic, sigma_scope="global"))
    assert per_bin["relative_spread"] < 0.06, per_bin
    assert glob["relative_spread"] > 0.50, glob


@needs_data
def test_T22_maxscore_reproduces_phase22_artifact_exactly(real):
    """Doi env (pandas/numpy/pyarrow) khong duoc lam doi mot chu so nao."""
    from cert.conformal_simultaneous import acceptance_diagnostics, fit_eval_simultaneous

    df, ic = real
    maxscore = fit_eval_simultaneous(df, ic, "maxscore")
    check = ST.phase22_reproduction_check(
        "poisson@0.925",
        maxscore,
        acceptance_diagnostics(df, ic, maxscore),
    )
    assert check["available"], check
    assert check["acceptance"]["abs_diff"] == 0.0, check["acceptance"]
    assert check["coverage"]["abs_diff"] == 0.0, check["coverage"]
    assert check["qhat_max_abs_diff"] == 0.0, check
    assert check["bit_exact"]


def test_T23_nesting_is_measured_and_can_be_negative():
    """only_max = 0 la TINH CHAT DU LIEU, khong phai dinh ly.

    Ep mhat3/mhat1 xuong sat 1 -- dung truc ma Lesson 23.11 se thay doi -- thi
    nesting_margin phai am va only_max > 0.
    """
    rng = np.random.default_rng(13)
    df = _toy_frame(rng, n_blocks=200, per_block=40, n_bins=2)
    base = np.abs(rng.normal(6.0, 1.0, size=len(df))) + 1.0
    # Cost spread ~ 0.1%: cac duong gan nhu bang gia nhau.
    for j in (1, 2, 3):
        df["m_hat_%d" % j] = base * (1.0 + 0.0005 * (j - 1))
        df["m_true_%d" % j] = df["m_hat_%d" % j]
    df["wrong"] = np.zeros(len(df), dtype=bool)
    ic = df["is_calib"].to_numpy(bool)
    a = ST.fit_eval_studentized(df, ic, force_uniform_sigma=1.0)
    b = ST.fit_eval_studentized(df, ic)
    out = ST.accept_set_contingency(df, ic, a, b)

    assert out["nesting_is_structural"] is False
    assert out["sufficient_condition_threshold"] > 1.0
    assert out["only_maxscore"]["n"] > 0, out
    assert out["nesting_holds"] is False
    # slack_min la dai luong EXACT: < 1 <=> co hang bi mat.
    assert out["nesting_slack_min"] < 1.0, out


def test_T25_nesting_slack_min_is_exactly_equivalent_to_only_a_empty():
    """slack_min >= 1  <=>  only_a = 0. Kiem tren ca hai che do."""
    rng = np.random.default_rng(15)
    for spread, expect_nested in ((0.0005, False), (0.60, True)):
        df = _toy_frame(rng, n_blocks=200, per_block=40, n_bins=2)
        base = np.abs(rng.normal(6.0, 1.0, size=len(df))) + 1.0
        for j in (1, 2, 3):
            df["m_hat_%d" % j] = base * (1.0 + spread * (j - 1))
            df["m_true_%d" % j] = df["m_hat_%d" % j]
        df["wrong"] = np.zeros(len(df), dtype=bool)
        ic = df["is_calib"].to_numpy(bool)
        a = ST.fit_eval_studentized(df, ic, force_uniform_sigma=1.0)
        b = ST.fit_eval_studentized(df, ic)
        out = ST.accept_set_contingency(df, ic, a, b)
        assert (out["nesting_slack_min"] >= 1.0) == (out["only_maxscore"]["n"] == 0), out
        assert out["nesting_holds"] is expect_nested, (spread, out["only_maxscore"]["n"])


def test_T24_artifact_keys_with_ambiguous_units_carry_a_level_suffix():
    """Quy tac ba nhan, thuc thi bang may.

    Hai loi cua lesson nay (S-5 pooled-vs-per-bin, p 1200-vs-300) deu la so
    mot dai luong GOP voi mot dai luong PHAN HOACH. Khoa tran nhu 'p' hay
    'n_cells' khong duoc phep ton tai trong artifact.
    """
    rng = np.random.default_rng(14)
    df = _toy_frame(rng, n_blocks=400, per_block=30, n_bins=2)
    df["m_hat_1"] = rng.normal(0.0, 1.0, size=len(df))
    out = ST.positive_control_high_dim_sigma(df, df["is_calib"].to_numpy(bool), n_mhat_cells=40)

    banned = {"p", "n", "sigma_ratio", "coverage_by_mhat_cell"}
    suffixes = (
        "_per_bin", "_total", "_per_cell", "_pooled", "_by_bin", "_by_zbin",
        "_min", "_max", "_spread", "_mean", "_sd",
    )

    def walk(node, path=""):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str):  # bin ids are ints, not names
                    assert key not in banned, "khoa tran khong nhan level: %s/%s" % (path, key)
                    if key.split("_")[0] == "p" and key != "path":
                        assert key.endswith(suffixes), "khoa %s thieu hau to level" % key
                walk(value, "%s/%s" % (path, key))
        elif isinstance(node, list):
            for item in node:
                walk(item, path)

    walk(out)

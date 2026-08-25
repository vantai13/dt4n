#!/usr/bin/env python3
"""Golden test cho Lesson 23.22 Task A0.

Nam test dau khong can parquet -- chung bao ve LOGIC. Test cuoi can du lieu
va se skip neu thieu.

Ky truoc o: docs/phase-23/A064-amendment-64.md
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import config_matrix as CM
from cert import taxonomy_audit as TA
from cert.cell_matrices import ALPHA_FAMILY


def test_keys_mapping_is_what_we_think():
    """Bo truc m_hat = doi post sang bat ky thu gi khac 'mondrian'.

    Day la khang dinh trung tam cua amendment 23-64 muc 1 (LECH 2). Neu
    `_keys` doi hanh vi, ca lap luan cua lesson sup -- test nay bat duoc.
    """
    assert CM._keys("mondrian") == ["z_bin", "m_hat_bin"]
    assert CM._keys("none") == ["z_bin"]
    assert CM._keys("selective") == ["z_bin"]
    assert CM._keys("fcr") == ["z_bin"]


def test_alpha_each_is_bonferroni_over_three():
    """alpha/(K-1) = alpha/3 voi K=4. Doi so nay la doi bao dam."""
    a = CM._alpha_each(ALPHA_FAMILY, len(CM.SIM_COLS), True, "bonferroni")
    assert abs(a - ALPHA_FAMILY / 3.0) < 1e-12
    assert len(CM.SIM_COLS) == 3


def test_prediction_bands_match_signed_amendment():
    """Dai du doan trong code PHAI khop amendment 23-64 muc 4.

    Doi mot dai o day ma khong doi amendment se lam test nay do. Day la
    'kien truc chong chinh minh': dai la HANG SO da commit, khong phai co CLI.
    """
    assert TA.PREDICTIONS["M-181"]["lo"] == 440.0
    assert TA.PREDICTIONS["M-181"]["hi"] == 500.0
    assert TA.PREDICTIONS["M-182"]["lo"] == 1.00
    assert TA.PREDICTIONS["M-182"]["hi"] == 1.15
    assert TA.PREDICTIONS["M-184"]["hi"] == 1.30
    assert TA.PREDICTIONS["M-185"]["lo"] == 1.10
    assert TA.PREDICTIONS["M-186"]["hi"] == 1.00
    assert TA.PREDICTIONS["M-183"]["scored"] is False
    assert TA.KAPPA_OP == 1.00
    assert TA.VARIANTS == ("mondrian", "none", "selective")
    assert 0.0 in TA.KAPPA_GRID and 2.0 in TA.KAPPA_GRID


def test_census_counts_blocks_and_rows_separately():
    """Doi chung TONG HOP: block trai qua moi o -> block/o ~ tong block,
    trong khi hang/o = tong/|o|. Day la H-B duoi dang do choi."""
    n_blk, per_blk = 50, 40
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "block_id": np.repeat(np.arange(n_blk), per_blk),
        "z_bin": rng.integers(0, 4, n_blk * per_blk),
        "m_hat_bin": rng.integers(0, 4, n_blk * per_blk),
    })
    c16 = TA.taxonomy_census(df, ["z_bin", "m_hat_bin"])
    c4 = TA.taxonomy_census(df, ["z_bin"])

    assert c16["n_cells"] == 16 and c4["n_cells"] == 4
    # HANG: ti so ~ 4x
    assert 3.5 < c4["n_rows_mean"] / c16["n_rows_mean"] < 4.5
    # BLOCK: ti so ~ 1x  <-- day la diem cua ca lesson
    assert c4["n_blocks_mean"] / c16["n_blocks_mean"] < 1.15
    assert c16["block_touch_ratio"] > 0.90


def test_spread_m_and_M185_agree_when_effect_is_uniform_in_z():
    """DOI CHUNG AM cho M-185: khi hieu ung `m_hat` DEU tren moi z, hai do do
    PHAI trung nhau.

    Ghi lai vi ban review (va ban nhap dau cua amendment 23-64) khang dinh
    *"profile BIEN lam nhoe hieu ung don"* -- DIEU DO SAI. `spread_profiles`
    trung binh theo (z, slot) va GIU NGUYEN truc m, nen mot hieu ung 1.20x
    don o m=3 hien ra DAY DU la 1.20 tren `spread_m`.

    Neu M-185 khong bao gio khac `spread_m` thi no la mot cot thua. Test nay
    ghim canh "khong khac"; test sau ghim canh "co khac".
    """
    q = {}
    for z in range(4):
        base = 10.0 + 5.0 * z
        for m in range(4):
            val = base * (1.20 if m == 3 else 1.00)
            q[(z, m)] = np.array([val, val, val], dtype=np.float64)

    sp = TA.spread_profiles(q)
    conc = TA.mhat_concentration(q)
    assert abs(sp["M_184_spread_m"] - 1.20) < 1e-9
    assert abs(conc["M_185_ratio_mean"] - 1.20) < 1e-9
    assert abs(conc["spread_among_low_bins"] - 1.00) < 1e-9


def test_M185_diverges_from_spread_m_under_z_by_m_interaction():
    """CO CHE THAT cua H-A: TI SO CUA TRUNG BINH vs TRUNG BINH CUA TI SO.

        spread_m = max_m mean_z q(z,m) / min_m mean_z q(z,m)   <- RATIO OF MEANS
        M-185    = mean_z [ q(z,3) / mean_{m<3} q(z,m) ]       <- MEAN OF RATIOS

    `spread_m` bi CHI PHOI boi cac z_bin co qhat LON. Khi hieu ung `m_hat`
    nam o cac z_bin co qhat NHO, `spread_m` PHA LOANG no con M-185 thi khong.

    Dung cau truc do duoc: base qhat lech 10x giua z_bin (100 vs 10), hieu
    ung 1.5x chi o ba z_bin nho.
    """
    base = [100.0, 10.0, 10.0, 10.0]
    q = {}
    for z in range(4):
        for m in range(4):
            val = base[z] * (1.5 if (m == 3 and z >= 1) else 1.0)
            q[(z, m)] = np.array([val, val, val], dtype=np.float64)

    sp = TA.spread_profiles(q)["M_184_spread_m"]
    m185 = TA.mhat_concentration(q)["M_185_ratio_mean"]

    assert abs(sp - 1.1154) < 1e-3, sp        # pha loang boi z_bin base lon
    assert abs(m185 - 1.3750) < 1e-3, m185    # giu nguyen do lon that
    assert m185 > sp * 1.20                   # lech >= 20%


def test_bootstrap_relabels_blocks_so_n_eff_is_preserved():
    """Lay mau CO HOAN LAI roi dem `nunique()` se DEM THIEU ~37%.

    Do duoc: 500 block lay lai 500 lan co hoan lai -> ~311 nhan duy nhat
    (ky vong n*(1-1/e) = 316). `_qhat` dung `block_id.nunique()` lam `n_eff`,
    nen khong gan nhan lai se lam muc conformal bao thu gia tao o MOI vong.

    Test nay ghim rang `_resample_blocks` gan nhan MOI.
    """
    n_blk, per_blk = 200, 10
    df = pd.DataFrame({
        "block_id": np.repeat(np.arange(n_blk), per_blk),
        "x": np.arange(n_blk * per_blk, dtype=float),
    })
    by_block = {b: sub for b, sub in df.groupby("block_id", sort=True)}
    rng = np.random.default_rng(1)
    pick = rng.choice(np.arange(n_blk), size=n_blk, replace=True)

    # Neu KHONG gan nhan lai:
    naive = pd.concat([by_block[b] for b in pick], ignore_index=True)
    assert naive["block_id"].nunique() < 0.75 * n_blk       # dem thieu that

    # Co gan nhan lai:
    boot = TA._resample_blocks(by_block, pick)
    assert boot["block_id"].nunique() == n_blk              # giu dung n_eff
    assert len(boot) == n_blk * per_blk


@pytest.mark.skipif(
    not os.path.exists(TA.calib_path("poisson", 0.925)),
    reason="parquet LIVE khong co tren may nay",
)
@pytest.mark.slow
def test_main_cell_runs_and_controls_fire():
    out = TA.run_cell("poisson", 0.925, "MAIN", n_boot=20)
    assert out["census"]["flat_4cells"]["n_cells"] == 4
    assert out["census"]["mondrian_16cells"]["n_cells"] == 16
    assert out["controls"]["G23_235_negative_kappa0"]["acceptance_all_one"]


# ---------------------------------------------------------------------------
# `L93` -- che do `qhat = max mau`   (amendment 23-65b)
# ---------------------------------------------------------------------------

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_validity_floor_is_computed_not_hardcoded():
    """`L91`: san HOP LE phai TINH tu `alpha_each`.

    `9` dung cho `alpha=0.10` va SAI cho `alpha/3` (dung la 29). Mot nguong
    suy ra tu tham so khac khong bao gio duoc hard-code.
    """
    from cert.simultaneous_score import alpha_bonferroni

    assert CM.conformal_min_blocks(0.10) == 9
    assert CM.conformal_min_blocks(alpha_bonferroni(0.10, 3)) == 29


def test_stability_floor_is_above_validity_floor():
    """`L93`: hai san KHAC LOAI -- 29 hop le, 59 on dinh. Khong duoc gop."""
    from cert.simultaneous_score import alpha_bonferroni

    assert CM.conformal_min_blocks_below_one(0.10) == 19
    a3 = alpha_bonferroni(0.10, 3)
    assert CM.conformal_min_blocks_below_one(a3) == 59
    assert CM.conformal_min_blocks(a3) < CM.conformal_min_blocks_below_one(a3)


def test_level_is_exactly_one_between_the_two_floors():
    """Dai [29, 58]: `level == 1.0` -> `_qhat` tra ve MAX cua mau.

    Day la NOI DUNG cua canh bao `L93`, khong phai mot chi tiet ky thuat.
    """
    from cert.conformal_v2 import conformal_level, empirical_qhat
    from cert.simultaneous_score import alpha_bonferroni

    a3 = alpha_bonferroni(0.10, 3)
    assert conformal_level(28, a3) is None
    for n in (29, 40, 58):
        assert conformal_level(n, a3) == 1.0
    assert conformal_level(59, a3) < 1.0

    x = np.array([1.0, 5.0, 2.0, 9.0, 3.0])
    assert empirical_qhat(x, 1.0) == x.max()


def test_stability_floor_does_not_gate_anything():
    """`min_blocks_stable` chi de KHAI BAO. Chot chan van la `floor_blocks`.

    Neu ai do -- ke ca tac gia, sau nay -- thay `qhat_at_sample_max = true` va
    phan xa nang chot chan len san ON DINH, test nay do. Ly do o
    `A065b-amendment-65b.md` muc 2: 29 la san TOAN HOC, 59 la san VAN HANH
    dat SAU khi xem du lieu (HARKing), va gop hai san khac loai lam mot la
    mat kha nang phan biet "khong hop le" voi "hop le nhung bat on".
    """
    with open(os.path.join(REPO, "cert", "config_matrix.py"), encoding="utf-8") as fh:
        src = fh.read()
    assert "< floor_blocks" in src, "chot chan hop le da bien mat"
    assert "< stable_blocks" not in src, (
        "san ON DINH dang duoc dung lam CHOT CHAN -- xem A065b muc 2")


# ---------------------------------------------------------------------------
# `L95` -- `selective` tut ve `none` khi suy bien o vong 0  (amendment 23-65d)
# ---------------------------------------------------------------------------

# `L96`: cong cu co `--out*` mac dinh tro vao tang DA KHOA (`chmod -R a-w`,
# amendment 23-61). Chin cai duoi day co TU TRUOC khi tang bi khoa; chung
# duoc GHIM lam no da khai bao, khong duoc sua -- output cua chung da dong
# bang. Danh sach nay chi duoc NGAN di, khong duoc dai them.
KNOWN_FROZEN_TIER_WRITERS = {
    "abstain_cost.py",                    # cert/, --out-dir SUPERSEDED/phase-23
    "decomposition.py",                   # cert/, SUPERSEDED/phase-21R
    "gate_report.py",                     # cert/, SUPERSEDED/phase-21R
    "lesson23_7_calibration_2b.py",       # cert/, SUPERSEDED/phase-23
    "lesson23_7_feasibility.py",          # cert/, SUPERSEDED/phase-23
    "lesson23_7_range_calibration.py",    # cert/, SUPERSEDED/phase-23
    "operational_sigma.py",               # cert/, SUPERSEDED/phase-21R
    "threshold_families.py",              # cert/, SUPERSEDED/phase-23
    "g23_212a_partial_nc.py",             # tools/, RAW/phase-23
}


def _synthetic_calib(n_blk: int = 80, per_blk: int = 5, seed: int = 0) -> pd.DataFrame:
    """Calib nho nhat du de chay nhanh `selective` that.

    Hai `z_bin`, moi `z_bin` 40 block -- tren san hop le 29 (`L91`), nen vong 0
    KHONG suy bien khi `kappa` nho. `m_hat` duong va nho so voi `s`, nen mot
    `kappa` lon lam tap chon rong ngay vong 0.
    """
    rng = np.random.default_rng(seed)
    n = n_blk * per_blk
    blk = np.repeat(np.arange(n_blk), per_blk)
    df = pd.DataFrame({
        "block_id": blk,
        "z_bin": blk % 2,
        "m_hat_bin": blk % 2,
        "wrong": rng.random(n) < 0.2,
    })
    for j in (1, 2, 3):
        df["s_pair_%d" % j] = rng.gamma(2.0, 1.0, size=n)
        df["m_hat_%d" % j] = rng.gamma(2.0, 1.0, size=n)
        df["m_true_%d" % j] = df["m_hat_%d" % j] - 0.1
    return df


def test_degenerate_at_iter_zero_returns_the_qhat_of_none():
    """`L95`: suy bien o VONG 0 -> `q` chua tung duoc cap nhat.

    Gia tri khoi tao cua nhanh `selective` la `_qhat` tren TOAN BO calib, tuc
    DUNG BANG `qhat` cua thu tuc `none`. Nen hang do mang nhan `selective`
    nhung chay `none` -- va `none` la thu tuc DA DO LA VO bao dam hau chon loc
    (`M-187`). `qhat_source` phai KHAI BAO dieu do.
    """
    calib = _synthetic_calib()
    fit_s = CM.fit_config(calib, "C3", 100.0, alpha=ALPHA_FAMILY,
                          post_variant="selective")
    fit_n = CM.fit_config(calib, "C3", 100.0, alpha=ALPHA_FAMILY,
                          post_variant="none")

    assert fit_s["degenerate"] is True and fit_s["n_iter"] == 0
    assert fit_s["min_blocks_at_final_qhat"] is None
    assert fit_s["qhat_source"] == "degenerate_fallback_to_none"
    assert set(fit_s["_q"]) == set(fit_n["_q"])
    for k in fit_s["_q"]:
        assert np.array_equal(fit_s["_q"][k], fit_n["_q"][k]), k   # TRUNG BIT


def test_qhat_source_says_fixed_point_only_when_q_was_updated():
    """Doi chung duong: khi V-S chay THAT thi nhan phai la `fixed_point`.

    Neu khong co doi chung nay, mot cai vit `qhat_source` cung hang so
    `"degenerate_fallback_to_none"` se qua duoc test tren.
    """
    calib = _synthetic_calib()
    fit = CM.fit_config(calib, "C3", 0.0, alpha=ALPHA_FAMILY,
                        post_variant="selective")
    assert fit["degenerate"] is False and fit["converged"] is True
    assert fit["min_blocks_at_final_qhat"] is not None
    assert fit["qhat_source"] == "fixed_point"


def test_degenerate_after_iter_zero_is_still_a_real_selective():
    """Suy bien o `it > 0` KHONG phai truong hop cua `L95`.

    O do `q` da qua it nhat mot vong cap nhat tren TAP DUOC CHON, nen no la
    mot iterate hop le cua V-S -- nhan `selective` dung su that. Chi `it == 0`
    moi tra ve gia tri khoi tao. Hai truong hop phai co HAI ten.

    De den duoc nhanh nay can `n_eff` tren san on dinh 59 (`L93`): duoi 59 thi
    `level == 1.0` va `qhat` = max cua mau, nen tap chon chi co the NO RA qua
    cac vong -- suy bien khi do luon xay ra o vong 0. Day la 120 block moi o.
    """
    calib = _synthetic_calib(n_blk=240, per_blk=3, seed=0)
    fit = CM.fit_config(calib, "C3", 0.25, alpha=ALPHA_FAMILY,
                        post_variant="selective")
    assert fit["degenerate"] is True and fit["n_iter"] > 0
    assert fit["qhat_source"] == "degenerate_partial"


def test_evaluate_config_declares_the_procedure_that_actually_ran():
    """Chot chan: `post` la nhan MONG MUON, `procedure_actually_run` la SU THAT.

    Bang vong hai ghi `pass_coverage = false` o cac hang nay, nen khong ket
    luan nao da cong bo bi doi. Cai sai la NHAN. Truong nay bit cho do.
    """
    calib = _synthetic_calib()
    fit_deg = CM.fit_config(calib, "C3", 100.0, alpha=ALPHA_FAMILY,
                            post_variant="selective")
    ev_deg = CM.evaluate_config(calib, fit_deg, anchor_err=0.2, alpha=ALPHA_FAMILY)
    assert ev_deg["post"] == "selective"                     # nhan mong muon
    assert ev_deg["procedure_actually_run"] == "none"        # su that
    assert ev_deg["L95_collapsed_to_none"] is True

    fit_ok = CM.fit_config(calib, "C3", 0.0, alpha=ALPHA_FAMILY,
                           post_variant="selective")
    ev_ok = CM.evaluate_config(calib, fit_ok, anchor_err=0.2, alpha=ALPHA_FAMILY)
    assert ev_ok["procedure_actually_run"] == "selective"
    assert ev_ok["L95_collapsed_to_none"] is False


def test_selective_at_degenerate_kappa_is_bit_identical_to_none():
    """`L95` do tren ARTIFACT -- khong chay lai.

    Do duoc tren `b9d2774` (`git_hash = cced37a`): 8/8 cell `A=True` tai
    `kappa=2`, `qhat_slot1_mean` va `violation_given_accept` cua `selective`
    trung den chu so cuoi voi `none`. Day la su that DA NAM san trong artifact;
    truong `qhat_source` chi DAT TEN cho no, khong sinh so lieu moi.
    """
    import json

    path = os.path.join(REPO, "results", "LIVE", "phase-23", "taxonomy_audit.json")
    if not os.path.exists(path):
        pytest.skip("artifact khong co tren may nay")
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    n = 0
    for c in d["cells"]:
        S = {r["kappa"]: r for r in c["variant_sweep"] if r["post"] == "selective"}
        N = {r["kappa"]: r for r in c["variant_sweep"] if r["post"] == "none"}
        for k, r in S.items():
            if r.get("min_blocks_at_final_qhat") is None and float(k) > 0.0:
                assert r["n_iter"] == 0, (c["cell"], k)      # co che: vong 0
                assert r["qhat_slot1_mean"] == N[k]["qhat_slot1_mean"], (c["cell"], k)
                assert r["violation_given_accept"] == N[k]["violation_given_accept"]
                n += 1
    assert n >= 8, "chi tim thay %d truong hop suy bien, cho >= 8" % n


def test_qhat_source_default_is_the_pessimistic_one():
    """Mac dinh phai la gia dinh XAU NHAT.

    Neu mac dinh la `fixed_point` va ta HA xuong khi suy bien, thi mot nhanh
    `break` MOI trong tuong lai se im lang tra ve nhan SAI. Cung nguyen tac
    voi `git_dirty` mac dinh `True` khi khong do duoc (`L78`).
    """
    with open(os.path.join(REPO, "cert", "config_matrix.py"), encoding="utf-8") as fh:
        src = fh.read()
    i_default = src.index('info["qhat_source"] = "degenerate_fallback_to_none"')
    i_fixed = src.index('info["qhat_source"] = "fixed_point"')
    assert i_default < i_fixed, "mac dinh phai duoc dat TRUOC khi nang len"


def test_no_tool_writes_into_frozen_tiers():
    """`results/RAW` va `results/SUPERSEDED` da khoa `chmod -R a-w` (23-61).

    Mot `--out` mac dinh tro vao do la mot cai bay: hoac lenh hong, hoac ai do
    `chmod` nguoc lai "cho tien". Bat duoc mot lan roi -- `A065` muc 8 khai
    `--out` cua `g23_242_taxonomy_rerun_diff.py` vao `results/RAW/`
    (`A065d` muc 3).

    Chi soi co GHI (`--out*`). Mac dinh DOC tro vao tang khoa la HOP LE va co
    that -- `tools/check_phase20r6_structure.py` doc `--new-b/--new-c` tu
    `results/SUPERSEDED/`, va do dung la cach dung tang do.

    Chin cong cu DA CO tu truoc khi tang bi khoa (`L96`): chung duoc GHIM,
    khong duoc sua -- output cua chung da dong bang va doi duong dan se lam
    mat dau vet. So sanh la BANG NHAU, nen ca hai chieu deu do:
    them mot cong cu moi -> do; sua mot cong cu cu ma quen go khoi day -> do.
    """
    import glob
    import re

    pat = re.compile(
        r"""add_argument\(\s*["']--out[\w-]*["'][^)]*?"""
        r"""default\s*=\s*["']([^"']*results/(?:RAW|SUPERSEDED)/[^"']*)["']""",
        re.S)
    found = set()
    for f in sorted(glob.glob(os.path.join(REPO, "tools", "*.py"))
                    + glob.glob(os.path.join(REPO, "cert", "*.py"))):
        with open(f, encoding="utf-8") as fh:
            if pat.search(fh.read()):
                found.add(os.path.basename(f))
    assert found == KNOWN_FROZEN_TIER_WRITERS, (
        "them: %s | het: %s -- xem `L96`, `A065d` muc 3"
        % (sorted(found - KNOWN_FROZEN_TIER_WRITERS),
           sorted(KNOWN_FROZEN_TIER_WRITERS - found)))

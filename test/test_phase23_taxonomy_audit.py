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

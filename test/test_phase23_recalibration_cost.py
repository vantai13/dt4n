#!/usr/bin/env python3
"""Golden test cho Lesson 23.22 Task B-2 -- chi phi tai hieu chuan.

Ky truoc o: docs/phase-23/A067-amendment-67.md muc 7 (`M-199`, `G23-259`).

Menh de duoc kiem: C3 **biet truoc** khi no khong du du lieu (`qhat = +inf`
hoac `= max mau` -- `L91`, `L93`); B2 **luon** tra ve mot `c` huu han o moi
`n`, ke ca `n = 10`, va khong co cach nao biet `c` do vo nghia.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import config_matrix as CM
from cert import recalibration_cost as RC

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cell(n_blk: int = 240, per_blk: int = 3, seed: int = 0) -> pd.DataFrame:
    """Cell tong hop -- moi block cham CA HAI `z_bin` (dung `H-B`).

    Neu `z_bin` bam theo `block_id` thi lay `n` block se lam mot o rong va
    `_qhat` tra `+inf` vi ly do khac han cai ta muon do.
    """
    rng = np.random.default_rng(seed)
    n = n_blk * per_blk
    blk = np.repeat(np.arange(n_blk), per_blk)
    df = pd.DataFrame({
        "block_id": blk,
        "z_bin": np.tile(np.arange(per_blk), n_blk) % 2,
        "m_hat_bin": np.tile(np.arange(per_blk), n_blk) % 2,
        "wrong": rng.random(n) < 0.2,
        "is_calib": blk < int(0.7 * n_blk),
    })
    for j in (1, 2, 3):
        df["s_pair_%d" % j] = rng.gamma(2.0, 1.0, size=n)
        df["m_hat_%d" % j] = rng.gamma(2.0, 1.0, size=n) * 4.0
        df["m_true_%d" % j] = df["m_hat_%d" % j] - 0.1
    return df


def test_subsample_keeps_whole_blocks():
    """Don vi trao doi duoc la BLOCK. Lay mot phan hang cua mot block se pha
    `n_eff` va lam `conformal_level` sai -- cung bai hoc voi
    `test_bootstrap_relabels_blocks_so_n_eff_is_preserved`.
    """
    df = _cell()
    calib = df[df["is_calib"]].reset_index(drop=True)
    sub = RC.subsample_blocks(calib, 25, np.random.default_rng(0))
    assert sub["block_id"].nunique() == 25
    for b in sub["block_id"].unique():
        assert (sub["block_id"] == b).sum() == (calib["block_id"] == b).sum()


def test_grid_and_draws_match_the_signed_amendment():
    """Luoi `n` phai chua diem duoi san hop le 29 (`L91`), neu khong `M-199`
    khong cham duoc gi.
    """
    assert RC.N_GRID[0] < 29 and 29 < RC.N_GRID[-1]
    assert sum(1 for n in RC.N_GRID if n < 29) >= 2
    assert RC.KAPPA_OP == 0.50 and RC.POST_VARIANT == "selective"


def test_C3_raises_a_flag_below_the_validity_floor_and_B2_does_not():
    """★ Menh de trung tam cua `M-199`.

    Duoi san hop le, `conformal_level` tra `None` -> `_qhat` tra `+inf` ->
    `qhat_has_infinite`. B2 chi lay mot phan vi mau: no LUON tra mot so huu
    han, ke ca tu 10 block, va KHONG co truong nao bao rang so do vo nghia.
    """
    df = _cell()
    calib = df[df["is_calib"]].reset_index(drop=True)
    test = df[~df["is_calib"]].reset_index(drop=True)
    sub = RC.subsample_blocks(calib, 10, np.random.default_rng(0))
    row = RC.recalibrate_once(sub, test)

    assert row["C3_flagged"] is True
    assert row["C3_qhat_has_infinite"] is True
    assert np.isfinite(row["c_B2"])
    assert row["B2_flagged"] is False
    assert "B2_qhat_has_infinite" not in row      # B2 khong co `qhat` de gan co


def test_C3_does_not_raise_a_flag_when_it_has_enough_blocks():
    """Doi chung duong: neu co la hang so `True` thi test tren vo nghia."""
    df = _cell(n_blk=900)
    calib = df[df["is_calib"]].reset_index(drop=True)
    test = df[~df["is_calib"]].reset_index(drop=True)
    sub = RC.subsample_blocks(calib, 400, np.random.default_rng(0))
    row = RC.recalibrate_once(sub, test)
    assert row["C3_qhat_has_infinite"] is False
    assert row["C3_flagged"] is False


def test_score_M199_reads_the_signed_thresholds():
    """`A067` muc 7: C3 gan co >= 90% lan khi `n < 29`; B2 huu han 100% lan."""
    rows = ([{"n_blocks": 10, "C3_flagged": True, "B2_flagged": False,
              "c_B2_finite": True}] * 9
            + [{"n_blocks": 10, "C3_flagged": False, "B2_flagged": False,
                "c_B2_finite": True}]
            + [{"n_blocks": 500, "C3_flagged": False, "B2_flagged": False,
                "c_B2_finite": True}])
    out = RC.score_M199(rows)
    assert out["n_draws_below_floor"] == 10
    assert abs(out["C3_flag_rate_below_floor"] - 0.9) < 1e-12
    assert out["B2_finite_rate_below_floor"] == 1.0
    assert out["B2_flag_rate_below_floor"] == 0.0
    assert out["hit"] is True

    bad = [dict(r, C3_flagged=False) for r in rows]
    assert RC.score_M199(bad)["hit"] is False


def test_B2_fixed_target_is_not_dragged_down_by_a_degenerate_C3():
    """Duoi san, C3 co `qhat = +inf` nen chap nhan 0 hang.

    Neu B2 chi duoc khop voi acceptance cua C3 tren CUNG mau, no cung bi keo
    ve 0 va cot B2 o `n` nho khong noi duoc gi ve B2. Bien the MUC TIEU CO
    DINH giu diem van hanh, nen do duoc dieu ta muon do: B2 dat `c` chinh xac
    den dau tu `n` block.
    """
    df = _cell()
    calib = df[df["is_calib"]].reset_index(drop=True)
    test = df[~df["is_calib"]].reset_index(drop=True)
    sub = RC.subsample_blocks(calib, 10, np.random.default_rng(0))
    row = RC.recalibrate_once(sub, test, target_acceptance=0.40)

    assert row["C3_acceptance_test"] == 0.0          # C3 tu choi toan bo
    assert row["B2fix_acceptance_test"] > 0.15       # B2 van hanh dong
    assert np.isfinite(row["c_B2_fixed"])
    assert row["B2fix_target_acceptance"] == 0.40


def test_B2_threshold_is_finite_even_from_a_single_block():
    """Khong co so luong du lieu nao lam B2 tu choi tra loi.

    Do CHINH LA menh de: `c` khong co ly thuyet co mau, nen khong co nguong
    nao de no bao "toi khong du du lieu".
    """
    df = _cell()
    calib = df[df["is_calib"]].reset_index(drop=True)
    one = RC.subsample_blocks(calib, 1, np.random.default_rng(0))
    c = RC.fit_B2(one, target_acceptance=0.5)
    assert np.isfinite(c)

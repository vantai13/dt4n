#!/usr/bin/env python3
"""Golden test cho Lesson 23.22 Task B -- ma tran chuyen giao C3 vs B2.

Ky truoc o: docs/phase-23/A066-amendment-66.md, A066b-amendment-66b.md

Cac test o day KHONG can parquet LIVE. Chung bao ve CO CHE va CACH DOC:
`NC-3a`/`NC-3b` la hai nhanh khac nhau va phai cho hai ket qua khac nhau; o
`T3` cua B2 phai TRONG; diem van hanh phai lay tu `M-192` chu khong phai mot
hang so vit tay.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from cert import config_matrix as CM
from cert import transfer_matrix as TM

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# `m_hat` phai lon hon `s` mot he so de tap chon o `kappa=0.5` con du block:
# voi he so 1.0 thi acceptance ~ 0.002 va V-S suy bien ngay vong 0, tuc ta se
# dang do `none` chu khong phai `selective` (`L95`). Do duoc: he so 4.0 cho
# `min_blocks = 71` (tren san on dinh 59) va acceptance ~ 0.50.
MHAT_OVER_S = 4.0


def _cell(n_blk: int = 240, per_blk: int = 3, seed: int = 0,
          scale: float = 1.0) -> pd.DataFrame:
    """Mot cell tong hop: 2 `z_bin`, 120 block/o -- tren san on dinh 59.

    `scale` nhan CA `m_hat_*` lan `s_pair_*`, tuc mo phong mot che do trong do
    moi dai luong chi phi gian theo cung he so. `is_calib` KHONG duoc phu
    thuoc `z_bin`, neu khong hai o se co so block rat khac nhau.
    """
    rng = np.random.default_rng(seed)
    n = n_blk * per_blk
    blk = np.repeat(np.arange(n_blk), per_blk)
    df = pd.DataFrame({
        "block_id": blk,
        "z_bin": blk % 2,
        "m_hat_bin": blk % 2,
        "wrong": rng.random(n) < 0.2,
        "is_calib": blk < int(0.7 * n_blk),
    })
    for j in (1, 2, 3):
        df["s_pair_%d" % j] = rng.gamma(2.0, 1.0, size=n) * float(scale)
        df["m_hat_%d" % j] = (rng.gamma(2.0, 1.0, size=n)
                              * MHAT_OVER_S * float(scale))
        df["m_true_%d" % j] = df["m_hat_%d" % j] - 0.1
    return df


# ---------------------------------------------------------------------------
# Diem van hanh va cach doc -- `A066` muc 2.1 va 3
# ---------------------------------------------------------------------------


def test_operating_point_is_the_one_M192_licensed():
    """`kappa = 0.5` la HE QUA cua `M-192`, khong phai mot hang so vit tay.

    Tai `kappa=1` co 4/8 cell song roi duoi san on dinh (`M-191`); tai
    `kappa=2` thi V-S khong chay (`L95`). Doi hang so nay ma khong doi
    amendment se lam test do -- cung kien truc "chong chinh minh" voi
    `test_prediction_bands_match_signed_amendment`.
    """
    assert TM.KAPPA_OP == 0.50
    assert TM.POST_VARIANT == "selective"
    assert TM.MULTIPLICITY == "bonferroni"


def test_B2_has_no_coverage_claim_and_the_hole_is_declared():
    """`A066` muc 3: o trong cua B2 o `T3` CHINH LA ket qua.

    Nguy tao mot `qhat` cho B2 de "so cho cong bang" la tu tay che ra thu ma
    ta dang chung minh la B2 khong co. Test nay cam dieu do bang cach doi o
    do phai la `None` VA co mot co khai bao di kem.
    """
    df = _cell()
    fit = TM.fit_on_A(df[df["is_calib"]].reset_index(drop=True))
    out = TM.deploy_on_B(fit, df[~df["is_calib"]].reset_index(drop=True))
    assert out["T3_viol_given_accept_B2"] is None
    assert out["T3_B2_has_no_coverage_claim"] is True
    assert np.isfinite(out["T3_viol_given_accept_C3"])


def test_B2_threshold_matches_C3_acceptance_on_the_calibration_cell():
    """`A066` muc 2.4: B2 duoc cho dieu kien TOT NHAT co the.

    `c` duoc do de khop DUNG acceptance cua C3 tren chinh cell A. Neu B2 troi
    khi sang B, do khong phai vi ta dat no o mot diem bat loi.
    """
    df = _cell()
    calib = df[df["is_calib"]].reset_index(drop=True)
    fit = TM.fit_on_A(calib)
    acc_b2_on_A = float(
        (calib["m_hat_1"].to_numpy(np.float64) >= fit["c_B2"]).mean())
    assert abs(acc_b2_on_A - fit["acceptance_on_A"]) <= 0.01


# ---------------------------------------------------------------------------
# `NC-3a` / `NC-3b` -- amendment 23-66b
# ---------------------------------------------------------------------------


def test_NC3a_rescaling_and_recalibrating_leaves_C3_bit_identical():
    """`NC-3a`: tham so chuyen giao cua C3 la `kappa`, KHONG THU NGUYEN.

    Nhan CA calib va test x2 roi HIEU CHUAN LAI -> `qhat -> 2*qhat` chinh xac
    (`lambda=2` la luy thua cua 2; `conformal_level` chi phu thuoc `n_eff` va
    `alpha`; `empirical_qhat` la mot thong ke thu tu), nen acceptance TRUNG
    BIT. Day la kiem CO CHE truc tiep, tat dinh.
    """
    base, big = _cell(), _cell(scale=2.0)
    out = TM.nc3_rescale_report(base, big)
    assert out["NC3a_acceptance_C3_base"] == out["NC3a_acceptance_C3_rescaled"]
    assert out["NC3a_delta_acceptance_C3"] == 0.0
    assert out["NC3a_delta_acceptance_B2"] > 0.05      # `c` co thu nguyen


def test_NC3b_carrying_qhat_over_drifts_for_BOTH_methods():
    """`NC-3b`: chan cach doc "C3 mien nhiem voi doi che do".

    Mang nguyen `qhat_A` sang mot che do da gian thi ve trai cua
    `m_hat >= kappa*qhat` nhan lambda con ve phai dung yen -- C3 troi y nhu
    B2. No khong mien nhiem; no chi CHUYEN GIAO DUOC bang mot tham so khong
    thu nguyen (`NC-3a`).
    """
    base, big = _cell(), _cell(scale=2.0)
    out = TM.nc3_rescale_report(base, big)
    assert out["NC3b_delta_acceptance_C3"] > 0.05
    assert out["NC3b_delta_acceptance_B2"] > 0.05


def test_NC3a_and_NC3b_are_not_the_same_measurement():
    """Hai nhanh phai cho hai ket qua KHAC nhau, neu khong mot cai la thua."""
    base, big = _cell(), _cell(scale=2.0)
    out = TM.nc3_rescale_report(base, big)
    assert out["NC3a_delta_acceptance_C3"] < out["NC3b_delta_acceptance_C3"]


# ---------------------------------------------------------------------------
# Chot chan `L95` -- `A066` muc 2.1
# ---------------------------------------------------------------------------


def test_fit_on_A_refuses_a_cell_where_selective_collapsed_to_none():
    """`A066` muc 2.1: neu V-S suy bien o vong 0 thi Task B DUNG.

    `M-192` noi dieu do khong duoc xay ra tai `kappa=0.5`. Chay tiep se la dan
    nhan `selective` len mot hang thuc su chay `none` (`L95`), tuc thu tuc DA
    DO LA VO (`M-187`).
    """
    tiny = _cell(n_blk=40, per_blk=2)        # 20 block/o < san hop le 29
    with pytest.raises(RuntimeError, match="suy bien|degenerate"):
        TM.fit_on_A(tiny)


# ---------------------------------------------------------------------------
# Tap cell sinh TU artifact -- `A066` muc 2.2
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not os.path.exists(os.path.join(
    REPO, "results/LIVE/phase-23/live_region_sweep_slaB.json")),
    reason="artifact live_region khong co tren may nay")
def test_cell_roles_come_from_the_artifact_not_a_hardcoded_list():
    """8 song / 4 chet phai duoc SINH tu `live_region_flags()`.

    Ghi tay danh sach nay la mo cua cho no lech khoi tieu chi A da ky
    (amendment 23-62) ma khong ai biet.
    """
    live, dead = TM.cells_by_role()
    assert len(live) == 8 and len(dead) == 4
    assert set(live) == {
        "poisson@0.850", "poisson@0.875", "poisson@0.900",
        "poisson@0.925", "poisson@0.960",
        "h2@0.650", "h2@0.675", "h2@0.700"}
    assert set(dead) == {
        "poisson@0.700", "h2@0.850", "h2@0.925", "h2@0.960"}


def test_matrix_blocks_partition_the_64_cells():
    """8 duong cheo + 26 trong ho + 30 giua ho = 64. `A066` muc 2.2.

    Ban thao noi bo ghi "TRONG HO 22 o ... thuc: 20+6=26-8=18" -- ba con so
    khac nhau cho cung mot khoi. Test nay khoa phep dem.
    """
    live = ("poisson@0.850", "poisson@0.875", "poisson@0.900",
            "poisson@0.925", "poisson@0.960",
            "h2@0.650", "h2@0.675", "h2@0.700")
    blocks = TM.classify_pairs(live)
    assert len(blocks["diagonal"]) == 8
    assert len(blocks["within_family"]) == 26
    assert len(blocks["cross_family"]) == 30
    total = sum(len(v) for v in blocks.values())
    assert total == 64 == len(live) ** 2
    seen = [p for v in blocks.values() for p in v]
    assert len(set(seen)) == 64, "mot o bi dem hai lan"

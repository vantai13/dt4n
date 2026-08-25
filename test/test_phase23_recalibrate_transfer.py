#!/usr/bin/env python3
"""Golden test cho Lesson 23.22 Task B-3 -- tai hieu chuan qua che do.

Ky truoc o: `docs/phase-23/A068-amendment-68.md`, tag `lesson-23-22-b3-prereg`.

Hai nhom kiem tra:

  (1) DUONG ONG THU HAI PHAI TRUNG BIT VOI DUONG ONG THU NHAT.
      `recalibrate_transfer` tang toc hai cho (`q_rows_from_index`,
      `_err_at_coverage`). Moi cai la mot duong ong thu hai co the lech khoi
      duong ong goc ma khong ai biet -- dung ban chat loi cua `S12` va cua
      `L98`. Chung chi duoc phep ton tai vi hai test duoi day buoc chung
      trung BIT voi `cert/config_matrix.py` va `cert/baselines.py`.

  (2) CAU TRUC DA KY (`A068` muc 2).
      S-2 noi B2-R/B1-R KHONG phu thuoc A. Neu chung phu thuoc thi
      `NC-B3-2` se bat -- nhung `NC-B3-2` chi chay tren du lieu that. Test
      nay bat cung menh de tren du lieu tong hop, o muc don vi.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cert import baselines as BL
from cert import config_matrix as CM
from cert import recalibrate_transfer as RT
from cert import recalibration_cost as RC


def _cell(n_blk: int = 240, per_blk: int = 3, seed: int = 0) -> pd.DataFrame:
    """Cell tong hop -- moi block cham CA HAI `z_bin` (dung `H-B`).

    Cung ham voi `test_phase23_recalibration_cost.py`: neu `z_bin` bam theo
    `block_id` thi lay `n` block se lam mot o rong va `_qhat` tra `+inf` vi
    ly do khac han cai ta muon do.
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


def _split(df: pd.DataFrame):
    return (df[df["is_calib"]].reset_index(drop=True),
            df[~df["is_calib"]].reset_index(drop=True))


# ---------------------------------------------------------------------------
# (1) duong ong thu hai
# ---------------------------------------------------------------------------

def test_fast_q_rows_is_bit_identical_to_config_matrix():
    """★ `q_rows_from_index` phai tra ve DUNG mang cua `CM._q_rows`.

    Khong phai "gan bang", khong phai "trong dung sai": TUNG BIT. Neu mot
    ngay `CM._q_rows` doi, test nay FAIL -- do la muc dich cua no.
    """
    calib, test = _split(_cell())
    fit = CM.fit_config(calib, "C3", 0.5, alpha=0.10,
                        post_variant="selective", multiplicity="bonferroni")
    keys = CM._keys("selective")
    n_cols = len(CM.SIM_COLS)

    slow = CM._q_rows(test, keys, fit["_q"], n_cols)
    uniq, idx = RT.key_index(test, keys)
    fast = RT.q_rows_from_index(uniq, idx, fit["_q"], n_cols)

    assert fast.shape == slow.shape
    assert np.array_equal(fast, slow), "duong ong thu hai lech khoi CM._q_rows"


def test_fast_q_rows_handles_a_key_absent_from_qhat():
    """Khoa cua `test` khong co trong `calib` -> `+inf`, y het `CM._q_rows`.

    Day chinh la cho mot bang tra de lech: `dict.get` co mac dinh, `tab[idx]`
    thi khong. Doi chung duong cho nhanh `miss`.
    """
    calib, test = _split(_cell())
    fit = CM.fit_config(calib, "C3", 0.5, alpha=0.10,
                        post_variant="selective", multiplicity="bonferroni")
    keys = CM._keys("selective")
    q = {k: v for k, v in fit["_q"].items()}
    q.pop(sorted(q)[0])                      # go MOT khoa ra

    slow = CM._q_rows(test, keys, q, len(CM.SIM_COLS))
    uniq, idx = RT.key_index(test, keys)
    fast = RT.q_rows_from_index(uniq, idx, q, len(CM.SIM_COLS))
    assert np.isposinf(slow).any(), "test nay chi co nghia khi co hang `+inf`"
    assert np.array_equal(fast, slow)


def test_err_at_coverage_matches_baselines_accept_at_coverage():
    """`_err_at_coverage` phai chon DUNG tap hang cua `BL._accept_at_coverage`."""
    rng = np.random.default_rng(7)
    score = rng.random(5000)
    wrong = rng.random(5000) < 0.3
    order = np.argsort(-score, kind="mergesort")
    for t in RT.MATCHED_ACCEPTANCE:
        mask = BL._accept_at_coverage(score, t)
        assert RT._err_at_coverage(order, wrong, t) == pytest.approx(
            float(wrong[mask].mean()), abs=0.0, rel=0.0)


def test_err_at_coverage_is_nan_when_nothing_is_accepted():
    """`k = 0` -> KHONG XAC DINH, khong phai `err = 0` (`A068` muc 3.3)."""
    wrong = np.zeros(100, dtype=bool)
    order = np.arange(100)
    assert np.isnan(RT._err_at_coverage(order, wrong, 0.0))


# ---------------------------------------------------------------------------
# (2) cau truc da ky
# ---------------------------------------------------------------------------

def test_B2R_and_B1R_do_not_depend_on_A():
    """★ S-2 (`A068` muc 2): `a*` la hang so toan cuc.

    Chay `run_one` voi ba `kappa_A` khac han nhau tren CUNG `n` block. Cot C3
    PHAI doi; cot B2/B1 PHAI trung BIT. Day la menh de ma `NC-B3-2` cham
    tren du lieu that.
    """
    calib, test = _split(_cell())
    tv = RT.prepare_test(test)
    sub = RC.subsample_blocks(calib, 80, np.random.default_rng(0))
    out = [RT.run_one(sub, tv, k) for k in (0.30, 0.50, 0.90)]

    for f in ("c_B2", "B2_acceptance_test", "B2_err_given_accept",
              "c_B1", "B1_acceptance_test", "B1_err_given_accept"):
        vals = [r[f] for r in out]
        assert vals[0] == vals[1] == vals[2], "%s phu thuoc kappa_A: %r" % (f, vals)

    accs = [r["C3_acceptance_test"] for r in out]
    assert len(set(accs)) == 3, (
        "C3 KHONG doi theo kappa_A -- truc A sap, va B-3 se trung Task B-2")


def test_B2_has_no_violation_field():
    """O TRONG chinh la ket qua (`A066` muc 3, `A067b` muc 2).

    Do `viol` cho B2 phai muon `qhat` cua C3. Khi `qhat = +inf` no con cho ra
    "viol = 0.0000" -- mot con so hoan hao sinh ra tu mot cong cu do hong.
    """
    calib, test = _split(_cell())
    tv = RT.prepare_test(test)
    sub = RC.subsample_blocks(calib, 80, np.random.default_rng(0))
    row = RT.run_one(sub, tv, 0.5)
    assert "B2_viol_given_accept" not in row
    assert "B1_viol_given_accept" not in row
    assert row["B2_has_no_coverage_claim"] is True


def test_zero_accept_gives_nan_not_zero_violation():
    """`n_accept = 0` -> `viol` KHONG XAC DINH (`A068` muc 3.3).

    `kappa` rat lon lam C3 chap nhan 0 hang. Neu cho ra `0.0` thi bang cham
    se doc thanh "khong mot vi pham nao" -- dung cai bay doc 44 muc 4.4.
    """
    calib, test = _split(_cell())
    tv = RT.prepare_test(test)
    sub = RC.subsample_blocks(calib, 80, np.random.default_rng(0))
    row = RT.run_one(sub, tv, 50.0)
    assert row["C3_n_accept"] == 0
    assert np.isnan(row["C3_viol_given_accept"])
    assert np.isnan(row["C3_err_given_accept"])


def test_crn_gives_the_same_blocks_for_every_kappa_and_procedure():
    """CRN (`A068` muc 3): tap block chi phu thuoc `(B, n, draw)`."""
    calib, _test = _split(_cell(n_blk=900))
    a = RT.block_draws(calib, np.random.default_rng(RT.SEED))
    b = RT.block_draws(calib, np.random.default_rng(RT.SEED))
    assert len(a) == len(b)
    for (n1, d1, k1), (n2, d2, k2) in zip(a, b):
        assert (n1, d1) == (n2, d2)
        assert np.array_equal(k1, k2)


def test_full_n_draw_is_collapsed_to_one():
    """`n >= so block calib` -> tap con la TOAN BO, chin lan kia chi ton may."""
    calib, _test = _split(_cell(n_blk=100))     # 70 block calib
    got = RT.block_draws(calib, np.random.default_rng(RT.SEED))
    by_n = {}
    for n, d, _k in got:
        by_n[n] = by_n.get(n, 0) + 1
    for n, cnt in by_n.items():
        assert cnt == (1 if n >= 70 else RT.N_DRAWS), (n, cnt)


def test_constants_match_the_signed_amendment():
    """Dai va hang so PHAI khop `A068`. Doi mot so o day la doi mot du doan."""
    assert RT.A_STAR == 0.42679
    assert RT.N_GRID == (30, 60, 120, 250, 500)
    assert RT.N_GRID[0] > 29, "san hop le cua alpha/3 la 29 (`L91`)"
    assert RT.N_DRAWS == 10 and RT.SEED == 232301
    assert RT.N_MAIN == 250 and RT.N_FULL == 500
    assert RT.ACCEPT_FLOOR == 0.20
    assert RT.KAPPA_OP == 0.50 and RT.POST_VARIANT == "selective"
    assert (RT.KAPPA_LO, RT.KAPPA_HI) == (0.0, 8.0)


def test_solve_kappa_hits_the_target_on_a_synthetic_cell():
    """Bisection phai giai duoc, va bao TRUNG THUC khi khong bat duoc khoang."""
    calib, _test = _split(_cell(n_blk=600))
    got = RT.solve_kappa(calib, target=0.40)
    assert got["bracketed"] is True
    assert abs(got["acceptance_at_kappa_A"] - 0.40) <= 1e-3
    assert RT.KAPPA_LO <= got["kappa_A"] <= RT.KAPPA_HI

    imp = RT.solve_kappa(calib, target=1.5)          # ngoai tam
    assert imp["bracketed"] is False
    assert imp["converged_on_acceptance"] is False


def test_NC_B3_2_fires_when_B2_is_wired_to_A():
    """Doi chung DUONG cho chinh doi chung: neu B2 phu thuoc A thi phai BAT.

    Mot kiem "trung bit" luon xanh la mot kiem khong kiem gi. Boi mot hang de
    B2 lech theo A, va doi `score_NC_B3_2` phai tra `hit = False`.
    """
    base = {"c_B2": 1.0, "B2_acceptance_test": 0.4, "B2_err_given_accept": 0.1,
            "c_B1": 0.5, "B1_acceptance_test": 0.4, "B1_err_given_accept": 0.2}
    good = [dict(base, A=a, B="b", n=30, draw=0) for a in ("a1", "a2", "a3")]
    assert RT.score_NC_B3_2(good)["hit"] is True

    bad = [dict(r) for r in good]
    bad[1]["c_B2"] = 1.0 + 1e-12
    out = RT.score_NC_B3_2(bad)
    assert out["hit"] is False
    assert out["max_abs_delta"]["c_B2"] > 0.0


def test_aggregation_drops_non_finite_and_never_counts_them_as_zero():
    """Quy uoc gop (`A068` muc 3.1b): trung binh chi tren gia tri HUU HAN."""
    rows = [
        {"A": "a", "B": "b", "n": 250, "draw": 0, "C3_viol_given_accept": 0.08,
         "C3_acceptance_test": 0.4, "C3_err_given_accept": 0.05,
         "B2_acceptance_test": 0.43, "B2_err_given_accept": 0.06,
         "B1_acceptance_test": 0.43, "B1_err_given_accept": 0.2,
         "C3_n_accept": 10, "anchor_err": 0.2},
        {"A": "a", "B": "b", "n": 250, "draw": 1,
         "C3_viol_given_accept": float("nan"),
         "C3_acceptance_test": 0.0, "C3_err_given_accept": float("nan"),
         "B2_acceptance_test": 0.43, "B2_err_given_accept": 0.06,
         "B1_acceptance_test": 0.43, "B1_err_given_accept": 0.2,
         "C3_n_accept": 0, "anchor_err": 0.2},
    ]
    got = RT.cells_at_n(rows, 250)[("a", "b")]
    assert got["C3_viol_given_accept"] == pytest.approx(0.08)
    assert got["n_draws_zero_accept"] == 1.0

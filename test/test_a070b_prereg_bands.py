"""Dai da ky cua A070b phai KHOP van ban amendment, tung con so mot.

Vi sao: `PRED` trong `cert/a070_overlap.py` la thu THUC SU cham diem, con
`A070b-amendment-70b.md` la thu duoc KY. Neu hai cai lech nhau thi phep do
khong con la phep do da tien dang ky nua -- va khong ai phat hien ra, vi ca
hai deu "trong ma nguon".

Test nay doc SO tu van ban amendment, khong hard-code lai chung. Sua mot
nguong trong ma nhung quen sua amendment (hoac nguoc lai) -> DO.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from cert.a070_overlap import (A_STAR, ACCEPT_FLOOR, N_FULL, N_MAIN, PRED,
                               OVERLAP_4, OVERLAP_RHOS, LIVE_15, SEED_NCW)

AMENDMENT = pathlib.Path("docs/phase-23/A070b-amendment-70b.md")


@pytest.fixture(scope="module")
def text() -> str:
    return AMENDMENT.read_text(encoding="utf-8", errors="replace")


def test_amendment_exists(text):
    assert "M-222" in text and "M-223" in text and "M-224" in text
    assert "NC-W-1" in text


def test_m222_bands_match_amendment(text):
    p = PRED["M-222"]
    assert re.search(r"`viol\|accept <= 0\.10`", text), "amendment doi nguong viol"
    assert p["viol_max"] == 0.10
    assert re.search(r"`acceptance >= 0\.20`", text), "amendment doi san acceptance"
    assert p["acc_min"] == 0.20 == ACCEPT_FLOOR
    assert re.search(r"phai >= 2", text), "amendment doi so cap toi thieu"
    assert p["min_pairs"] == 2
    assert re.search(r"tai n=250", text)
    assert p["n"] == N_MAIN == 250


def test_m223_bands_match_amendment(text):
    p = PRED["M-223"]
    assert re.search(r"slope thuoc \[0\.40, 0\.62\]", text)
    assert (p["slope_lo"], p["slope_hi"]) == (0.40, 0.62)
    assert re.search(r"\|he so\| <= 0\.02", text)
    assert p["coef_max"] == 0.02
    assert re.search(r"delta R\^2 <= 0\.02", text)
    assert p["dr2_max"] == 0.02
    assert re.search(r"Spearman >= \+0\.90", text)
    assert p["spearman_min"] == 0.90
    assert re.search(r"n=500", text)
    assert p["n"] == N_FULL == 500


def test_m224_band_matches_amendment(text):
    p = PRED["M-224"]
    assert re.search(r"median residual khac_ho - median residual cung_ho\| <= 0\.02",
                     text), "amendment doi nguong chenh residual"
    assert p["resid_gap_max"] == 0.02
    assert p["n"] == N_FULL == 500


def test_nc_w_1_seed_matches_amendment(text):
    assert re.search(r"seed 232301", text), "amendment doi seed doi chung"
    assert SEED_NCW == 232301


def test_cell_sets_match_amendment(text):
    """OVERLAP-4 va LIVE-15 la TAP CELL da ky; doi tap cell la doi phep do."""
    for cell in OVERLAP_4:
        mode, rho = cell.split("@")
        assert re.search(r"%s@%s" % (mode, rho), text), f"amendment khong ky {cell}"
    assert len(OVERLAP_4) == 4
    assert len(LIVE_15) == 15, "LIVE-15 = 8 cu + 3 A069 + 4 overlap"
    assert len(set(LIVE_15)) == 15, "LIVE-15 co cell trung"
    assert tuple(OVERLAP_RHOS) == (0.744, 0.750)
    assert re.search(r"rho.{0,20}0\.744", text) and "0.750" in text


def test_a_star_is_the_signed_one(text):
    assert re.search(r"a\* = 0\.42679", text)
    assert A_STAR == 0.42679

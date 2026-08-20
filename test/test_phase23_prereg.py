"""Phase 23 preregistration controls.

These tests do not run a Phase 23 experiment.  They check the measurement
device needed before fallback policies can be trusted.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from twin import topology_v7 as T7


ARTIFACT = "results/phase-22/calib_set_v3.parquet"


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    if not os.path.exists(ARTIFACT):
        pytest.skip("thieu artifact Phase 23 prereg: %s" % ARTIFACT)
    return pd.read_parquet(ARTIFACT)


def relcost_matrix(frame: pd.DataFrame, k: int = 4) -> np.ndarray:
    """True cost relative to a1 for every path, shape (n, k)."""
    n = len(frame)
    out = np.full((n, k), np.nan, dtype=np.float64)
    rows = np.arange(n)

    out[rows, frame["a1"].to_numpy(np.int64)] = 0.0
    for slot in range(1, k):
        act = frame["a_rank_%d" % slot].to_numpy(np.int64)
        out[rows, act] = frame["m_true_%d" % slot].to_numpy(np.float64)

    assert not np.isnan(out).any(), "a1/a_rank_* khong phu het K action"
    return out


def regret_of(frame: pd.DataFrame, a_chosen: np.ndarray, k: int = 4) -> np.ndarray:
    rel = relcost_matrix(frame, k)
    rows = np.arange(len(frame))
    return rel[rows, np.asarray(a_chosen, dtype=np.int64)] - rel.min(axis=1)


def test_per_path_sla_columns_exist(df: pd.DataFrame) -> None:
    """Phase 23 cannot compute fallback sla_rate without these columns."""
    for j in range(len(T7.PATH_NAMES)):
        assert "sla_viol_p%d" % j in df.columns, "thieu sla_viol_p%d" % j


def test_y_hat_a1_exists_for_relative_margin_baseline(df: pd.DataFrame) -> None:
    """B5 needs the actual twin cost scale of the chosen path, not a proxy."""
    assert "y_hat_a1" in df.columns
    values = df["y_hat_a1"].to_numpy(np.float64)
    assert np.isfinite(values).all()
    assert float(values.min()) > 0.0


def test_per_path_sla_agrees_with_twin_and_star(df: pd.DataFrame) -> None:
    """Positive control: new columns must reproduce twin/star SLA flags."""
    k = len(T7.PATH_NAMES)
    mat = np.column_stack([df["sla_viol_p%d" % j].to_numpy(bool) for j in range(k)])
    rows = np.arange(len(df))

    got_twin = mat[rows, df["a_twin"].to_numpy(np.int64)]
    got_star = mat[rows, df["a_star"].to_numpy(np.int64)]

    assert np.array_equal(got_twin, df["viol_twin"].to_numpy(bool))
    assert np.array_equal(got_star, df["viol_star"].to_numpy(bool))


def test_d_sla_anchor_reproduced(df: pd.DataFrame) -> None:
    """Reproduce the inherited 21R d_sla anchor."""
    d_sla = float(df["viol_twin"].mean() - df["viol_star"].mean())
    assert abs(d_sla - 0.060125306891879) < 1e-6, d_sla


def test_regret_reconstruction_matches_stored_column(df: pd.DataFrame) -> None:
    """Positive control for arbitrary-action regret reconstruction."""
    got = regret_of(df, df["a_twin"].to_numpy())
    want = df["regret"].to_numpy(np.float64)
    assert np.abs(got - want).max() < 1e-4, np.abs(got - want).max()


# ---------------------------------------------------------------------------
# Bang du doan la mot REGISTRY, khong phai van xuoi (NT-v2-18)
# ---------------------------------------------------------------------------
#
# Amendment 23-28 muc 7 dem 14 dong chua dien. Con so dung la 15. Dong bi sot
# la `B1p`, va ly do la mot ONG THOAT trong o mo ta:
#
#     | B1p | 23.3 | err\|accept cua B1 ... | [CO CHE] | 0.212-0.232 | ___ | ___ |
#
# `str.split("|")` cho dong nay 8 o thay vi 7, cot "Do duoc" truot mot vi tri,
# va dong bien mat khoi moi phep quet -- KHONG nem loi, KHONG canh bao.
#
# Day la lan thu BA cung mot loai loi trong Phase 23 (ky hieu khoang trong so
# gate; do min luoi o 23.5[B]; ong thoat o day). Mot nguyen nhan: phan tich mot
# dinh dang danh cho NGUOI DOC bang mot phep cat danh cho MAY.

import re as _re
from pathlib import Path as _Path

PREREG = _Path(__file__).resolve().parents[1] / "docs" / "phase-23" / "00-preregistration.md"

# Cat tren `|` KHONG bi escape. Day la khac biet giua 14 va 15.
CELL_SPLIT = _re.compile(r"(?<!\\)\|")
PRED_ID = _re.compile(r"[A-Z][-\w']*")

# GHIM tap dong chua dien, giong PINNED_DEBT cua so gate. Sau Amendment 23-29
# tap nay RONG: moi lesson da dong deu duoc cham.
PINNED_UNFILLED: set[str] = set()


def _pred_rows() -> dict[str, dict[str, str]]:
    """Doc bang du doan thanh dict. Dung CELL_SPLIT, KHONG dung str.split('|')."""
    rows: dict[str, dict[str, str]] = {}
    for ln in PREREG.read_text(encoding="utf-8").splitlines():
        if not ln.startswith("| "):
            continue
        cells = [c.strip().replace("\\|", "|")
                 for c in CELL_SPLIT.split(ln.strip().strip("|"))]
        if len(cells) == 7 and PRED_ID.fullmatch(cells[0]):
            rows[cells[0]] = {"lesson": cells[1], "quantity": cells[2],
                              "label": cells[3], "range": cells[4],
                              "measured": cells[5], "verdict": cells[6]}
    return rows


def test_every_markdown_table_row_has_a_consistent_cell_count():
    """Mot dong sai so o bi BO QUA lang le boi moi phep quet. Test nay bien su
    bo qua do thanh mot loi DO.

    Kiem theo TUNG BANG (nhom dong lien tiep), vi tai lieu co nhieu bang voi so
    cot khac nhau: bang pilot disclosure 3 cot, bang du doan 7 cot, v.v.
    """
    bad, block, start = [], [], 0
    lines = PREREG.read_text(encoding="utf-8").splitlines()

    def flush(blk, first):
        if len(blk) < 2:
            return
        widths = {n for n, _ in blk}
        if len(widths) != 1:
            bad.append((first, sorted(widths),
                        [ln[:52] for n, ln in blk if n != blk[0][0]][:2]))

    for i, ln in enumerate(lines, 1):
        if ln.startswith("| "):
            if set(ln.strip()) <= set("|- :"):      # dong ngan cach
                continue
            if not block:
                start = i
            block.append((len(CELL_SPLIT.split(ln.strip().strip("|"))), ln))
        else:
            flush(block, start)
            block = []
    flush(block, start)
    assert not bad, "bang co dong lech so o: %s" % bad


def test_prediction_table_rows_all_have_seven_cells():
    rows = _pred_rows()
    assert len(rows) >= 30, "chi doc duoc %d dong du doan, qua it" % len(rows)
    for key in ("F4", "B1p", "K-10", "K-13", "A-7'", "C-1"):
        assert key in rows, "thieu dong %r -- co the bi ong thoat lam truot cot" % key


def test_unfilled_prediction_set_is_pinned():
    """GHIM tap dong chua dien. Mot dong moi bi bo trong -- hoac mot dong da
    dien bi xoa -- se lam DO test, giong PINNED_DEBT cua so gate."""
    unfilled = {k for k, v in _pred_rows().items() if v["measured"] == "___"}
    assert unfilled == PINNED_UNFILLED, (
        "tap dong chua dien lech ban ghim.\n  them: %s\n  bot : %s"
        % (sorted(unfilled - PINNED_UNFILLED), sorted(PINNED_UNFILLED - unfilled)))


def test_naive_split_would_miss_B1p_and_the_escaped_parser_does_not():
    """Chot chinh bai hoc, khong chi ket qua cua no.

    Neu ai do "don dep" CELL_SPLIT thanh str.split('|'), test nay do.
    """
    line = next(ln for ln in PREREG.read_text(encoding="utf-8").splitlines()
                if ln.startswith("| B1p |"))
    naive = line.strip().strip("|").split("|")
    escaped = CELL_SPLIT.split(line.strip().strip("|"))
    assert len(naive) == 8 and len(escaped) == 7
    assert escaped[5].strip() != "___"          # da dien
    assert naive[5].strip() == "0.212-0.232"    # phep cat ngay tho doc NHAM cot


def test_reading_dependent_rows_are_flagged_as_such():
    """K-D14: B3p va B6p doi ket qua theo cach doc `err`. Chung KHONG duoc
    trinh bay nhu HIT chac chan."""
    rows = _pred_rows()
    for key in ("B3p", "B6p"):
        assert "READING-DEPENDENT" in rows[key]["verdict"], (
            "%s phai duoc danh dau READING-DEPENDENT (Amd 23-29 muc 5.2)" % key)
    assert "B3p" in rows["B4p"]["quantity"], (
        "B4p phai ghi ro no do CUNG dai luong voi B3p (K-D13)")

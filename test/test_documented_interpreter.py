"""Trinh thong dich ghi o `L117` phai con ton tai.

Vi sao co test nay ma KHONG co test "moi lenh trong doc deu chay duoc":
7 doc da ky in `.venv/bin/python`, mot duong dan khong ton tai. Viet lai
chung la sua GHI CHEP LICH SU -- dieu repo da tu choi lam mot lan roi khi
phan tang (xem dau `results/PATH_MAP.tsv`). Nen cach xu ly la ANH XA:
`L117` ghi duong dan that, va test nay chan cho anh xa do khoi muc.

Marker `custody` vi no chi co nghia tren may tac gia; CI khong chay.
"""
from __future__ import annotations

import os
import pathlib
import re

import pytest

LIMITS = pathlib.Path("docs/phase-23/LIMITS.md")
INTERP = re.compile(r"`(/[\w./\-]*/envs/[\w.\-]+/bin/python)`")


def _documented_interpreters() -> list[str]:
    text = LIMITS.read_text(encoding="utf-8", errors="replace")
    row = [ln for ln in text.splitlines() if ln.startswith("| L117 |")]
    assert row, "L117 khong con trong LIMITS.md -- anh xa trinh thong dich da mat"
    return sorted(set(INTERP.findall(row[0])))


def test_l117_names_an_interpreter():
    found = _documented_interpreters()
    assert found, "L117 khong ghi duong dan trinh thong dich nao"


@pytest.mark.custody
def test_documented_interpreter_exists():
    """Neu env bi doi ten/xoa, anh xa cua `L117` muc im lang. Chan o day."""
    for path in _documented_interpreters():
        assert os.path.exists(path), (
            f"L117 ghi trinh thong dich {path} nhung no khong con ton tai; "
            "cap nhat L117 thay vi de doc chi sang cho trong")

"""A071 QUY TAC 23-STOP -- test cau truc, khong phai test do luong.

Ly do ton tai: mot quy tac khong duoc may kiem tra la mot quy tac se bi
quen. Hai test nay bien R2/R3 tu loi hua thanh rang buoc.
"""
from __future__ import annotations

import re
import pathlib

import pytest

DOCS = pathlib.Path("docs/phase-23")
BACKLOG = DOCS / "BACKLOG.md"

# Doc dong lesson tu 23.23 tro di. 47-close-23-22.md duoc mien theo `A071` N1.
CLOSE_DOC = re.compile(r"^\d+-close-23-(\d+)\.md$")
FIRST_GOVERNED_LESSON = 23


def _governed_close_docs() -> list[pathlib.Path]:
    out = []
    for p in sorted(DOCS.glob("*-close-23-*.md")):
        m = CLOSE_DOC.match(p.name)
        if m and int(m.group(1)) >= FIRST_GOVERNED_LESSON:
            out.append(p)
    return out


@pytest.mark.parametrize("doc", _governed_close_docs() or [None],
                         ids=lambda p: p.name if p else "chua-co-doc-nao")
def test_close_doc_has_budget_section(doc):
    """R3: moi doc dong lesson >= 23.23 phai in ngan sach thoi gian."""
    if doc is None:
        pytest.skip("chua co doc dong lesson nao tu 23.23 tro di")
    text = doc.read_text(encoding="utf-8", errors="replace")
    assert "## Ngan sach" in text, f"{doc.name} thieu muc '## Ngan sach' (A071 R3)"
    assert re.search(r"Da tieu\s*:\s*\d", text), f"{doc.name} muc Ngan sach de trong"


def test_backlog_rows_have_three_columns():
    """R2: moi dong backlog phai co du (a) chi phi, (b) phat bieu, (c) canh bao."""
    assert BACKLOG.exists(), "thieu docs/phase-23/BACKLOG.md (A071 R2)"
    bad = []
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| L") and not line.startswith("| **L"):
            continue
        if line.startswith("| L*"):          # dong tieu de
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 6:
            bad.append((line[:60], f"chi co {len(cols)} cot"))
            continue
        # cot 1 = (a) chi phi, cot 2 = (b) phat bieu, cot 3 = (c) canh bao
        if not cols[1]:
            bad.append((line[:60], "cot (a) chi phi de trong"))
        if not cols[2]:
            bad.append((line[:60], "cot (b) phat bieu de trong -- dung '(rong)' neu khong doi"))
        if not cols[3]:
            bad.append((line[:60], "cot (c) canh bao de trong"))
    assert not bad, f"dong backlog thieu cot: {bad}"


CLAIMS = DOCS / "CLAIMS.md"
CL_ID = re.compile(r"\bCL-\d+\b")


def _claim_ids() -> set[str]:
    assert CLAIMS.exists(), "thieu docs/phase-23/CLAIMS.md (S-A3)"
    return set(re.findall(r"^\| (CL-\d+) \|",
                          CLAIMS.read_text(encoding="utf-8"), re.M))


def test_claims_file_has_unique_ids():
    text = CLAIMS.read_text(encoding="utf-8")
    ids = re.findall(r"^\| (CL-\d+) \|", text, re.M)
    dupes = {i for i in ids if ids.count(i) > 1}
    assert ids, "CLAIMS.md khong co dong claim nao"
    assert not dupes, f"CLAIMS.md co ID trung: {sorted(dupes)}"


def test_backlog_claim_refs_point_at_real_claims():
    """R2 cot (b) tra loi 'no doi PHAT BIEU nao'. Mot cau tra loi tro toi mot
    `CL-*` khong ton tai lam ca quy tac thanh trang tri: cot quyet dinh khi do
    khong con duoc kiem tra boi bat cu cai gi."""
    have = _claim_ids()
    bad: dict[str, str] = {}
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if not (line.startswith("| L") or line.startswith("| **L")):
            continue
        if line.startswith("| L*"):
            continue
        for ref in CL_ID.findall(line):
            if ref not in have:
                bad[ref] = line[:60]
    assert not bad, f"BACKLOG tro toi claim khong ton tai: {bad}"


def test_gates_and_limits_cited_by_claims_exist():
    """Nguoc lai: moi `L*` va `G23-*` ma CLAIMS vien dan phai co that."""
    claims = CLAIMS.read_text(encoding="utf-8")
    limits = (DOCS / "LIMITS.md").read_text(encoding="utf-8")
    gates = (DOCS / "GATES.md").read_text(encoding="utf-8")
    known_l = set(re.findall(r"^\| (L\d+[a-z]?) \|", limits, re.M))
    known_g = set(re.findall(r"^\| (G23-\d+) \|", gates, re.M))
    missing_l = sorted({m for m in re.findall(r"`(L\d+[a-z]?)`", claims)
                        if m not in known_l})
    missing_g = sorted({m for m in re.findall(r"`?(G23-\d+)`?", claims)
                        if m not in known_g})
    assert not missing_l, f"CLAIMS vien dan L* khong co trong LIMITS.md: {missing_l}"
    assert not missing_g, f"CLAIMS vien dan gate khong co trong GATES.md: {missing_g}"

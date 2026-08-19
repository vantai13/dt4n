"""So gate phai TOAN VEN va PHU HET moi ma gate duoc nhac den trong repo.

Vi sao can file nay
-------------------
Ma gate la mot GIAO UOC ba ben: ke hoach dinh nghia no, artifact chung minh no,
paper trich dan no. Giao uoc khong duoc thuc thi bang may se troi.

Kiem tra doc lap ngay 2026-08-19 cho thay hau qua cu the: nam ma gate cua
Lesson 23.5 (`G23-24`, `G23-28`, `G23-29`, `G23-30`, `G23-31`) KHONG ton tai o
bat ky file nao trong repo, vi ban ke hoach v2 chi song ngoai repo. Cung luc do
ba ma (`G23-10`, `G23-12a`, `G23-12b`) duoc dinh nghia nhung chua bao gio duoc
cham. Xem Amendment 23-26 muc 7, `NT-v2-12`.

Thiet ke
--------
`docs/phase-23/GATES.md` la NGUON CHAN LY DUY NHAT. Test kiem tinh toan ven cua
chinh no, doi chieu voi cac ma xuat hien trong tai lieu, roi DOI CHIEU MEM voi
`PLAN_v2.md` neu file do ton tai.

Doi chieu voi ban ke hoach phai MEM va pattern phai CHAT, vi van xuoi chua ky
hieu khoang:

    "[1] Bang gate G23-1 ... G23-73, BON muc:"

`G23-1` o do la mot dau mut cua khoang, khong phai mot dong bang. Mot regex long
tim thay 58 ma trong khi chi co 52 dong bang that. Bai hoc: khong phan tich van
xuoi de lay du lieu quan trong; doc tu mot REGISTRY co dinh dang co dinh.
Kiem tra `test_plan_row_pattern_does_not_match_range_notation` ghim bai hoc do.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "phase-23"
LEDGER = DOCS / "GATES.md"
PLAN = DOCS / "PLAN_v2.md"

# Tu vung trang thai -- KHOA o Amendment 23-26 muc 7.
VALID_STATUS = {
    "PASS",
    "FAIL",
    "UNDETECTED",
    "DIAGNOSTIC",
    "ADJUDICATED",
    "DEBT",
    "NOT_RUN",
}

# Dai gate lien tuc ma ban ke hoach v2 dinh nghia. Duoi 24 la tam thua ke tu v1
# va KHONG lien tuc (2, 3, 6, 13, 16, 18, 19, 22 khong ton tai).
CONTIGUOUS_LO, CONTIGUOUS_HI = 24, 73

# Lesson da dong: gate cua chung khong duoc NOT_RUN.
CLOSED_LESSONS = {"23.1", "23.2", "23.3", "23.4", "23.5A", "23.5B", "23.5C"}

# Mon no GHIM (Amendment 23-26 muc 7.3). Them mot mon no moi phai sua dong nay,
# tuc phai co mot amendment -- no khong duoc xuat hien im lang.
PINNED_DEBT = {"G23-10", "G23-12a", "G23-12b"}

# Noi duoc quet de tim ma gate duoc nhac den.
SCAN_DIRS = (DOCS, ROOT / "cert", ROOT / "test")
SCAN_SUFFIXES = (".md", ".py")

GATE_ID = re.compile(r"^G23-(\d+)([a-z]?)$")
GATE_MENTION = re.compile(r"\bG23-\d+[a-z]?\b")

# Pattern CHAT cho ban ke hoach: ma o dau dong (cho phep thut le), roi >= 2
# khoang trang, roi noi dung. Dung dinh dang bang cua PART 7; KHONG khop
# "G23-1 ... G23-73" trong van xuoi vi sau ma chi co MOT khoang trang.
PLAN_ROW = re.compile(r"^\s*(G23-\d+[a-z]?)\s{2,}\S")


def _rows() -> list[tuple[str, str, str, str]]:
    """Doc GATES.md thanh (id, lesson, status, evidence)."""
    out = []
    for raw in LEDGER.read_text(encoding="utf-8").splitlines():
        if not raw.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) >= 4 and GATE_ID.match(cells[0]):
            out.append((cells[0], cells[1], cells[2], cells[3]))
    return out


def _sort_key(gate_id: str) -> tuple[int, str]:
    m = GATE_ID.match(gate_id)
    assert m, gate_id
    return int(m.group(1)), m.group(2)


# --------------------------------------------------------------------------
# 1. Toan ven cua chinh so
# --------------------------------------------------------------------------


def test_ledger_file_exists():
    assert LEDGER.exists(), "thieu %s -- xem Amendment 23-26 muc 7" % LEDGER


def test_ledger_is_not_empty():
    n = len(_rows())
    assert n >= 50, "so gate chi co %d dong, qua it" % n


def test_no_duplicate_gate_id():
    ids = [r[0] for r in _rows()]
    dup = sorted({g for g in ids if ids.count(g) > 1}, key=_sort_key)
    assert not dup, "ma gate lap: %s" % dup


def test_every_status_is_in_locked_vocabulary():
    bad = {r[0]: r[2] for r in _rows() if r[2] not in VALID_STATUS}
    assert not bad, (
        "trang thai ngoai tu vung da khoa: %s. Them muc moi phai qua amendment."
        % bad
    )


def test_contiguous_range_is_complete():
    """G23-24..G23-73 phai co DU. Thieu mot ma = mot nghia vu bi bo quen."""
    have = {int(GATE_ID.match(r[0]).group(1)) for r in _rows()}
    missing = [n for n in range(CONTIGUOUS_LO, CONTIGUOUS_HI + 1) if n not in have]
    assert not missing, "thieu gate: %s" % ["G23-%d" % n for n in missing]


def test_evidence_present_unless_not_run():
    bad = [r[0] for r in _rows() if r[2] != "NOT_RUN" and r[3] in ("", "-")]
    assert not bad, "gate da co trang thai nhung khong co bang chung: %s" % bad


def test_evidence_absent_when_not_run():
    bad = [r[0] for r in _rows() if r[2] == "NOT_RUN" and r[3] not in ("", "-")]
    assert not bad, "gate NOT_RUN nhung co bang chung: %s" % bad


def test_rows_are_sorted_by_lesson_then_number():
    """Doc so tu tren xuong phai la doc theo thu tu thoi gian cua lesson."""
    order = [r[1] for r in _rows()]
    seen: list[str] = []
    for lesson in order:
        if lesson not in seen:
            seen.append(lesson)
    assert len(seen) == len(set(seen)), (
        "mot lesson xuat hien o hai cho roi rac trong bang: %s" % seen
    )


# --------------------------------------------------------------------------
# 2. G23-71 thu nho, chay lien tuc thay vi chi mot lan o 23.13
# --------------------------------------------------------------------------


def test_no_closed_lesson_gate_is_still_not_run():
    bad = [r[0] for r in _rows() if r[1] in CLOSED_LESSONS and r[2] == "NOT_RUN"]
    assert not bad, (
        "gate thuoc lesson DA DONG nhung con NOT_RUN: %s. Day la G23-71 that bai "
        "som. Neu chua ai cham no, trang thai dung la DEBT." % bad
    )


def test_debt_set_is_pinned():
    """Mon no chi duoc xuat hien qua amendment, khong duoc troi vao im lang."""
    debt = {r[0] for r in _rows() if r[2] == "DEBT"}
    assert debt == PINNED_DEBT, (
        "tap DEBT lech ban ghim.\n  them: %s\n  bot : %s\n"
        "Them mon no moi phai sua PINNED_DEBT va viet mot amendment."
        % (sorted(debt - PINNED_DEBT, key=_sort_key),
           sorted(PINNED_DEBT - debt, key=_sort_key))
    )


def test_debt_rows_point_at_where_they_were_defined():
    for gid, _lesson, status, evidence in _rows():
        if status == "DEBT":
            assert "dinh nghia" in evidence, (
                "%s la DEBT nhung evidence khong chi ra noi no duoc dinh nghia: %r"
                % (gid, evidence)
            )


def test_g23_27_is_recorded_as_undetected_not_pass():
    """Chot cung mot ket luan de no khong bi 'lam tron len' khi viet paper.

    docs/phase-23/08-studentized-and-go-debts.md ghi ro:
    'KET LUAN: KHONG PHAT HIEN DUOC o che do du lieu day. KHONG PHAI PASS.'
    """
    st = {r[0]: r[2] for r in _rows()}
    assert st.get("G23-27") == "UNDETECTED", (
        "G23-27 phai la UNDETECTED. Doi thanh PASS la doc sai doi chung duong."
    )


# --------------------------------------------------------------------------
# 3. NT-v2-12 -- ma duoc nhac den o dau cung phai co trong so
# --------------------------------------------------------------------------


def test_every_gate_id_mentioned_in_repo_is_in_the_ledger():
    """Day la NT-v2-12 duoc thuc thi.

    Kiem tra la MEMBERSHIP chu khong phai DEM, nen no an toan truoc ky hieu
    khoang: "G23-1 ... G23-73" chi cho hai dau mut, va ca hai deu la gate that.
    Mot DEM se sai; mot MEMBERSHIP thi khong.
    """
    known = {r[0] for r in _rows()}
    unknown: dict[str, set[str]] = {}
    for d in SCAN_DIRS:
        for p in sorted(d.rglob("*")):
            if p.suffix not in SCAN_SUFFIXES or not p.is_file():
                continue
            for gid in GATE_MENTION.findall(p.read_text(encoding="utf-8")):
                if gid not in known:
                    unknown.setdefault(gid, set()).add(str(p.relative_to(ROOT)))
    assert not unknown, (
        "ma gate duoc nhac den nhung khong co trong GATES.md: %s"
        % {k: sorted(v) for k, v in sorted(unknown.items(), key=lambda kv: _sort_key(kv[0]))}
    )


# --------------------------------------------------------------------------
# 4. Doi chieu mem voi ban ke hoach
# --------------------------------------------------------------------------


def test_plan_row_pattern_does_not_match_range_notation():
    """Chot bai hoc: pattern phai KHONG khop ky hieu khoang trong van xuoi.

    Test nay KHONG can PLAN_v2.md ton tai -- no kiem chinh cai pattern.
    """
    assert PLAN_ROW.match("G23-24   G3a/G3b do duoc va dien vao 00-prereg")
    assert PLAN_ROW.match("  G23-73   bao cao cuoi")
    assert PLAN_ROW.match("[1] Bang gate G23-1 ... G23-73, BON muc:") is None
    assert PLAN_ROW.match("G23-1 ... G23-73") is None


@pytest.mark.skipif(not PLAN.exists(), reason="PLAN_v2.md chua duoc commit")
def test_every_gate_row_in_plan_has_a_ledger_entry():
    lines = PLAN.read_text(encoding="utf-8").splitlines()
    in_plan = {m.group(1) for m in (PLAN_ROW.match(l) for l in lines) if m}
    missing = sorted(in_plan - {r[0] for r in _rows()}, key=_sort_key)
    assert not missing, "gate co trong ke hoach nhung thieu o so: %s" % missing


# --------------------------------------------------------------------------
# 5. NT-v2-10 -- khoa sap xep cua ten file amendment
# --------------------------------------------------------------------------

AMD = re.compile(r"^(00[a-z]+)-amendment-(\d+)\.md$")


def _amendments() -> list[tuple[str, int]]:
    return [
        (m.group(1), int(m.group(2)))
        for m in (AMD.match(p.name) for p in DOCS.iterdir())
        if m
    ]


def test_amendment_filenames_sort_by_number():
    """Thu tu TU DIEN cua ten file phai trung thu tu SO cua amendment.

    Bang chu cai da het o amendment 25 (`00z`). Quy uoc tiep theo la
    `00za`, `00zb`, ... `00aa` se sap TRUOC `00b` va pha thu tu doc lich su
    quyet dinh. Xem Amendment 23-26 muc 0.
    """
    pairs = _amendments()
    assert pairs, "khong tim thay file amendment nao"
    by_name = [n for _, n in sorted(pairs, key=lambda t: t[0])]
    assert by_name == sorted(by_name), (
        "ten file khong sap dung thu tu so: %s. Xem Amendment 23-26 muc 0."
        % by_name
    )


def test_amendment_numbers_are_contiguous_from_one():
    nums = sorted(n for _, n in _amendments())
    assert nums == list(range(1, len(nums) + 1)), (
        "so amendment khong lien tuc: %s" % nums
    )

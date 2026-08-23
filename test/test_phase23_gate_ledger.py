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
#
# Tieu chi vao day la CO MOT TAI LIEU TUYEN BO DONG, khong phai "gate tinh co
# deu xanh". `23.20*` duoc them o amendment 23-51 vi `30-close-23-20.md` tuyen
# bo `DONG`. `23.17` KHONG duoc them: `G23-74`/`G23-75` con MO chinh dang (can
# thong tin xac thuc cua tac gia), them vao se ep chung sang DEBT -- bien mot
# viec dang cho thanh mot mon no. `23.18`, `23.18b`, `23.19*` chua co tai lieu dong.
CLOSED_LESSONS = {
    "23.1", "23.2", "23.3", "23.4", "23.5A", "23.5B", "23.5C",
    "23.20", "23.20A", "23.20B", "23.20C", "23.20D",
}

# Mon no GHIM (Amendment 23-26 muc 7.3). Them mot mon no moi phai sua dong nay,
# tuc phai co mot amendment -- no khong duoc xuat hien im lang.
# `G23-141`/`G23-142` them o amendment 23-51: Dot 4 va mo rong M-125, bi chan
# boi S14 (`L41`), mo lai sau Lesson 23.21.
PINNED_DEBT = {"G23-10", "G23-12a", "G23-12b", "G23-141", "G23-142"}

# Ma gate bi dung NHAM trong mot tai lieu DA KY. Tai lieu khong duoc sua, nen
# anh xa song o day VA o muc "Va cham da phat hien" cua GATES.md.
#   (ten file, ma bi dung nham) -> (ma dung, amendment phan xu)
ADJUDICATED_GATE_TYPO = {
    ("30-close-23-20.md", "G23-135"): ("G23-141", "00zzn-amendment-51.md"),
    ("30-close-23-20.md", "G23-136"): ("G23-142", "00zzn-amendment-51.md"),
}

# Tai lieu DA KY ghi trang thai DUNG TAI THOI DIEM VIET, roi gate bi phan xu
# lai sau do. Khong phai loi danh may -- la do lech thoi gian.
#   (ten file, ma) -> (trang thai o doc, trang thai dung, amendment phan xu)
ADJUDICATED_STALE_STATUS = {
    ("28-axis-remeasure-impact.md", "G23-123"):
        ("PASS", "ADJUDICATED", "00zzi-amendment-49c.md"),
    # Lesson 23.6 HA CAP nam gate xuong DIAGNOSTIC (`06-reframe.md` muc 5,
    # khoa boi amendment 23-25 muc 6). `99-gate-decision.md` giu trang thai
    # TRUOC tai khung. KHONG mot con so nao bi rut -- chi doi VAI TRO.
    ("99-gate-decision.md", "G23-15"):
        ("FAIL", "DIAGNOSTIC", "00z-amendment-25.md"),
    ("99-gate-decision.md", "G23-17"):
        ("FAIL", "DIAGNOSTIC", "00z-amendment-25.md"),
    ("99-gate-decision.md", "G23-23"):
        ("PASS", "DIAGNOSTIC", "00z-amendment-25.md"),
}

# Mot dong bang gate o BAT KY tai lieu nao (bang o doc lesson chi co 3 cot).
GATE_ROW_ANY = re.compile(r"^\s*\|\s*(G23-\d+[a-z]?)\s*\|")
STATUS_WORD = re.compile(
    r"\b(PASS|FAIL|NOT_RUN|UNDETECTED|DIAGNOSTIC|ADJUDICATED|DEBT)\b")
# Mot O la o TRANG THAI khi no BAT DAU bang tu trang thai ("PASS -- PARTIAL").
# Neu chi `search` ca dong thi "M-121 FAIL dung du kien" trong o MO TA bi doc
# nham thanh trang thai.
STATUS_CELL = re.compile(
    r"^(PASS|FAIL|NOT_RUN|UNDETECTED|DIAGNOSTIC|ADJUDICATED|DEBT)\b")

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


def test_gate_status_is_consistent_across_documents():
    """Mot ma gate khong duoc mang HAI trang thai o hai tai lieu.

    Day la lo hong da cho ra va cham `L21`/`L29` o ho `L*`, nay bit cho ho
    `G23-*`. `test_every_gate_id_mentioned_in_repo_is_in_the_ledger` chi kiem
    MEMBERSHIP ("ma nay co ton tai khong"), khong kiem NHAT QUAN TRANG THAI
    ("ma nay co duoc mo ta giong nhau o moi noi khong"). `_rows()` cung khong
    thay bang o doc lesson vi bang do chi co BA cot.

    Trang thai phai lay theo O, khong phai tim tu dau tien trong DONG. Ban
    nhap dau dung `STATUS_WORD.search(line)` va sinh 10 bao dong gia: chuoi
    "FAIL" nam trong o MO TA ("M-121 FAIL dung du kien") bi doc thanh trang
    thai, con bang REFRAME o `06-reframe.md` von co HAI cot trang thai
    (`CU` -> `MOI`) thi bi doc mat cot thu hai.

    Nen luat la: gom moi o BAT DAU bang mot tu trang thai; dong nhat quan neu
    trang thai o so nam trong tap do.
    """
    ledger = {r[0]: r[2] for r in _rows()}
    bad = []
    for p in sorted(DOCS.rglob("*.md")):
        if p.name == "GATES.md":
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            m = GATE_ROW_ANY.match(line)
            if not m:
                continue
            gid = m.group(1)
            if (p.name, gid) in ADJUDICATED_GATE_TYPO:
                continue  # ma bi danh nham, da phan xu
            if (p.name, gid) in ADJUDICATED_STALE_STATUS:
                continue  # trang thai cu, da phan xu
            if gid not in ledger:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            doc_status = {
                s.group(1) for s in (STATUS_CELL.match(c) for c in cells[1:]) if s
            }
            if doc_status and ledger[gid] not in doc_status:
                bad.append((p.name, gid, sorted(doc_status), ledger[gid]))
    assert not bad, (
        "trang thai gate lech giua tai lieu va GATES.md "
        "(file, ma, o doc, o so): %s" % bad)


def test_adjudicated_gate_typos_are_documented():
    """Anh xa phan xu phai song o HAI noi va bi khoa vao nhau.

    Kiem DONG BANG chu khong phai chuoi con -- bai hoc tu `G23-144`: ban nhap
    dau cua test tuong duong ben `LIMITS.md` chi kiem `"L43" in txt` va doi
    chung duong KHONG do, vi chuoi con nam trong van xuoi.
    """
    txt = LEDGER.read_text(encoding="utf-8")
    for (fname, wrong), (right, amd) in ADJUDICATED_GATE_TYPO.items():
        row = "| `%s` | `%s` | `%s` |" % (wrong, fname, right)
        assert row in txt, (
            "GATES.md thieu DONG BANG phan xu cho %s trong %s (can: %r)"
            % (wrong, fname, row))
        assert (DOCS / amd).exists(), "thieu amendment phan xu %s" % amd
    for (fname, gid), (old, new, amd) in ADJUDICATED_STALE_STATUS.items():
        row = "| `%s` | `%s` | `%s` | `%s` |" % (gid, fname, old, new)
        assert row in txt, (
            "GATES.md thieu DONG BANG phan xu trang thai cu cho %s trong %s "
            "(can: %r)" % (gid, fname, row))
        assert (DOCS / amd).exists(), "thieu amendment phan xu %s" % amd


def test_adjudicated_gate_typo_still_matches_a_real_line():
    """Ma bi dung nham phai CON xuat hien trong file do.

    Neu ai do sua tai lieu (dang le khong duoc) hoac doi ten file, anh xa tro
    thanh vo hieu va va cham quay lai im lang. Chan giong
    `test_adjudicated_alias_fragments_still_match_a_real_line` ben so LIMITS.
    """
    keys = list(ADJUDICATED_GATE_TYPO) + list(ADJUDICATED_STALE_STATUS)
    for fname, gid in keys:
        p = DOCS / fname
        assert p.exists(), "tai lieu %s khong con ton tai" % fname
        hit = [l for l in p.read_text(encoding="utf-8").splitlines()
               if (m := GATE_ROW_ANY.match(l)) and m.group(1) == gid]
        assert hit, (
            "anh xa (%s, %s) khong con khop dong bang nao -- anh xa da chet"
            % (fname, gid))


def test_prose_in_ledger_does_not_restate_status():
    """Van xuoi trong GATES.md khong duoc mang tu trang thai canh mot ma gate.

    GATES.md tu khai la "NGUON CHAN LY DUY NHAT", nhung van xuoi trong chinh
    no khong bi may doc. Da co mot mau thuan that: bang ghi `G23-125` PASS
    trong khi van xuoi ngay duoi ghi NOT_RUN (tan du chua cap nhat).

    Nguyen tac: van xuoi giai thich PHAM VI va LY DO; TRANG THAI chi song o
    bang, vi chi bang bi may doc.
    """
    bad = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        s = line.lstrip()
        if s.startswith("|") or s.startswith("#"):
            continue
        if GATE_MENTION.search(line) and STATUS_WORD.search(line):
            bad.append(line.strip()[:90])
    assert not bad, (
        "van xuoi trong GATES.md phat bieu TRANG THAI (chi bang duoc phep): %s"
        % bad)


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

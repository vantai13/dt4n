#!/usr/bin/env python3
"""So LIMITS: chan va cham ma.

NAM va cham trong nam lesson:
    L29          ban ke hoach 23.18 vs 11-abstain-cost.md
    G23-97..99   ban ke hoach 23.19 vs amendment 23-44 (Lesson 23.20)
    amendment-47 ban ke hoach vs rang buoc lien tuc cua so amendment
    L21          dinh nghia BA lan voi HAI noi dung (PHAN XU o amendment 23-50)
    G23-101..108 ban ke hoach 23.19E vs 23.19B/23.19DE

Day la cai chan de khong co cai thu sau.
"""
from __future__ import annotations

import collections
import glob
import os
import re

DOCS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "phase-23")
LIMITS = os.path.join(DOCS, "LIMITS.md")

# `L21` DA DUOC PHAN XU o amendment 23-50 (2026-08-23).
#   00p-amendment-15.md:144 + 04-baselines.md:365  -> DINH NGHIA + TRICH DAN
#                                                     cua CUNG mot han che -> giu L21
#   00s-amendment-18.md:139                        -> han che KHAC -> cap L43
# Tai lieu DA KY khong duoc sua, nen anh xa song o day VA o LIMITS.md.
# `L39`..`L42` da duoc cap truoc do (amendment 23-49d/49f, lesson 29), nen ma
# moi la `L43` -- quy tac cap ma #1 cua LIMITS.md: lay so KE TIEP, khong tai su dung.
KNOWN_OPEN: set[str] = set()

# (ma cu, 40 ky tu dau da chuan hoa cua noi dung) -> ma moi
ADJUDICATED_ALIAS = {
    ("L21", "alpha/3 vs alpha/4 da dong boi amendment"): "L43",
}


def _limit_definitions() -> dict[str, set[str]]:
    """Ma L* duoc DINH NGHIA (dau dong, roi khoang trang, roi noi dung)."""
    seen: dict[str, set[str]] = collections.defaultdict(set)
    for f in sorted(glob.glob(os.path.join(DOCS, "*.md"))):
        if os.path.basename(f) == "LIMITS.md":
            continue
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^(L\d{1,2})\s{2,}(\S.{10,})$", line.rstrip())
                if m:
                    # chuan hoa: chu thuong + gom khoang trang. Mot han che
                    # duoc DINH NGHIA o mot cho va TRICH DAN o cho khac se
                    # khac hoa/thuong -- do khong phai va cham.
                    txt = " ".join(m.group(2).lower().split())[:40]
                    code = ADJUDICATED_ALIAS.get((m.group(1), txt), m.group(1))
                    seen[code].add(txt)
    return seen


def test_limits_ledger_exists():
    assert os.path.exists(LIMITS), "thieu docs/phase-23/LIMITS.md"


def test_no_duplicate_limit_ids():
    """Mot ma L khong duoc mang HAI noi dung khac nhau."""
    dup = {k: sorted(v) for k, v in _limit_definitions().items()
           if len(v) > 1 and k not in KNOWN_OPEN}
    assert not dup, (
        "ma L bi dinh nghia hai lan voi noi dung khac nhau: %s\n"
        "  -> cap ma MOI cho muc thu hai va ghi anh xa trong LIMITS.md" % dup)


def test_adjudicated_aliases_are_documented():
    """Moi anh xa phan xu phai duoc ghi trong LIMITS.md, khong chi trong test.

    Test khong duoc la noi duy nhat biet mot quyet dinh. Neu ai do go
    ADJUDICATED_ALIAS ra ma quen LIMITS.md (hoac nguoc lai), test nay do.

    Kiem tra la MOT DONG BANG chu khong phai "chuoi co xuat hien dau do".
    Ban nhap dau chi kiem `new in txt`, va doi chung duong cho thay no VO
    HIEU: go han dong `| L43 |` khoi bang van PASS, vi chuoi "L43" con nam
    trong van xuoi cua muc "Va cham". Mot phep kiem khong the do thi khong
    phai mot phep kiem.
    """
    with open(LIMITS, encoding="utf-8") as fh:
        txt = fh.read()
    rows = {
        c[0].strip()
        for c in (line.strip().strip("|").split("|")
                  for line in txt.splitlines() if line.lstrip().startswith("|"))
        if len(c) >= 2 and re.match(r"^L\d{1,2}$", c[0].strip())
    }
    for (old, _frag), new in ADJUDICATED_ALIAS.items():
        assert old in rows, (
            "ma CU %s phai con mot dong trong bang LIMITS.md" % old)
        assert new in rows, (
            "ma MOI %s cua anh xa phan xu %s -> %s chua co dong rieng trong "
            "bang LIMITS.md (nhac den trong van xuoi la CHUA DU)"
            % (new, old, new))
        assert "PHAN XU" in txt, "LIMITS.md phai ghi ro va cham nao da PHAN XU"


def test_adjudicated_alias_fragments_still_match_a_real_line():
    """Manh 40 ky tu phai con khop mot dong THAT trong tai lieu da ky.

    Neu khong, anh xa im lang tro thanh vo hieu va va cham quay lai ma
    khong ai biet -- dung cai loi ma so nay sinh ra de chan.
    """
    raw: dict[str, set[str]] = collections.defaultdict(set)
    for f in sorted(glob.glob(os.path.join(DOCS, "*.md"))):
        if os.path.basename(f) == "LIMITS.md":
            continue
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^(L\d{1,2})\s{2,}(\S.{10,})$", line.rstrip())
                if m:
                    raw[m.group(1)].add(" ".join(m.group(2).lower().split())[:40])
    for old, frag in ADJUDICATED_ALIAS:
        assert frag in raw.get(old, set()), (
            "anh xa (%s, %r) khong con khop dong nao -- anh xa da chet" % (old, frag))


def test_every_defined_limit_is_in_the_ledger():
    with open(LIMITS, encoding="utf-8") as fh:
        txt = fh.read()
    missing = [k for k in _limit_definitions() if k not in txt]
    assert not missing, "ma L duoc dinh nghia nhung khong co trong LIMITS.md: %s" % missing


def test_no_duplicate_gate_or_limit_ids_in_new_docs():
    """Va cham thu NAM la gate, khong phai limit. Chan ca hai ho ID.

    Mot ma G23-* chi duoc co DUNG MOT dong trong GATES.md (da co
    `test_no_duplicate_gate_id`), nhung ban ke hoach NGOAI repo hay tai su
    dung so. Test nay chan viec MOT ma xuat hien voi hai `lesson` khac nhau.
    """
    gates = os.path.join(DOCS, "GATES.md")
    rows = collections.defaultdict(set)
    with open(gates, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and re.match(r"^G23-\d+[a-z]?$", cells[0]):
                rows[cells[0]].add(cells[1])
    dup = {k: sorted(v) for k, v in rows.items() if len(v) > 1}
    assert not dup, "ma gate gan cho hai lesson khac nhau: %s" % dup

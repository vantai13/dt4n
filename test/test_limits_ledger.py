#!/usr/bin/env python3
"""So LIMITS: chan va cham ma.

NAM va cham trong nam lesson:
    L29          ban ke hoach 23.18 vs 11-abstain-cost.md
    G23-97..99   ban ke hoach 23.19 vs amendment 23-44 (Lesson 23.20)
    amendment-47 ban ke hoach vs rang buoc lien tuc cua so amendment
    L21          dinh nghia BA lan voi HAI noi dung (con MO)
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

# `L21` da biet la va cham, dang MO, cho amendment 23-50 phan xu.
KNOWN_OPEN = {"L21"}


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
                    seen[m.group(1)].add(txt)
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


def test_known_collision_is_still_recorded_as_open():
    """L21 chua duoc phan xu -- test nay nhac cho den khi co amendment 23-50."""
    with open(LIMITS, encoding="utf-8") as fh:
        txt = fh.read()
    assert "L21" in txt and "MO" in txt, (
        "L21 la va cham DA BIET; LIMITS.md phai ghi no dang MO cho den khi "
        "co amendment phan xu")


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

"""Moi dinh danh NT dung trong repo phai truy duoc ve docs/NT_REGISTRY.md.

Ly do ton tai: mot chi dan dau vao de xuat `G-L27--G-L30` va `NT56` trong khi
cac dinh danh do da co nghia da ky (docs/phase-G/17-amendment-G-A005-
reclassification.md:41). Su co lap lai o Phase T2 voi 17 dinh danh.

Trich dan bia la loai loi KHONG TU LO: khong test nao do, khong gate nao FAIL,
khong so nao lech. Nguoi dau tien phat hien se la reviewer. Nen no phai co
mot test rieng.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from tools.lint_identifiers import ID_PAT, ids_in, main, norm, registered, scan

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_registry_exists_and_is_not_empty():
    known, rejected = registered()
    assert (ROOT / "docs/NT_REGISTRY.md").exists()
    assert len(known) >= 30
    assert rejected, "bang DA TU CHOI trong -- phan quan trong nhat cua so"


def test_every_identifier_used_in_the_repo_is_registered():
    """Cong chinh. Do o day = co ID khong co nguon, hoac so chua cap nhat."""
    assert main([]) == 0


def test_registered_and_rejected_sets_do_not_overlap():
    """Mot ID khong the vua duoc cap vua bi tu choi."""
    known, rejected = registered()
    assert not (known & rejected), sorted(known & rejected)


def test_active_ids_actually_appear_in_their_cited_source():
    """So dang ky phai TRO DUNG cho. Mot so tro sai con te hon khong co so."""
    text = (ROOT / "docs/NT_REGISTRY.md").read_text(errors="replace")
    _known, rejected = registered()
    checked = 0
    for line in text.splitlines():
        if not line.startswith("|") or ".md:" not in line:
            continue
        cells = [c.strip().strip("`") for c in line.split("|")]
        m = ID_PAT.fullmatch(cells[1]) if len(cells) > 1 else None
        if not m:
            continue
        # bang DA TU CHOI tro vao noi chua NOI DUNG, khong chua ID -- do la
        # thong tin dung, nhung khong phai mot dinh nghia de kiem o day.
        if norm(m.group(1), m.group(2)) in rejected:
            continue
        src = next((c for c in cells if ".md:" in c), None)
        if not src:
            continue
        loc = re.search(r"([\w./-]+\.md):(\d+)", src)
        if not loc:
            continue
        path, lineno = loc.group(1), loc.group(2)
        f = ROOT / path
        if not f.is_file():
            pytest.fail("so dang ky tro vao file khong ton tai: %s" % src)
        lines = f.read_text(errors="replace").splitlines()
        i = int(lineno)
        assert 1 <= i <= len(lines), "%s: so dong ngoai pham vi" % src
        # ID phai xuat hien trong lan can dong duoc tro (+/- 2 dong)
        window = "\n".join(lines[max(0, i - 3): i + 2])
        want = norm(m.group(1), m.group(2))
        # dung ids_in: nguon that co dang nen `NT 63/64/65`
        found = ids_in(window)
        assert want in found, "%s khong xuat hien quanh %s" % (want, src)
        checked += 1
    assert checked >= 10, "kiem duoc qua it dong (%d)" % checked


def test_normalisation_catches_spacing_variants():
    """Repo that co ca `NT33` (khong dau cach) lan `NT 53`. Chuan hoa la
    BAT BUOC, khong phai trang tri."""
    assert norm("", "33") == norm("", "33")
    variants = ["NT33", "NT 33", "NT-33"]
    got = {norm(m.group(1), m.group(2))
           for v in variants for m in [ID_PAT.fullmatch(v)] if m}
    assert got == {"NT 33"}, got
    assert norm("L", "22") == "NT-L22"


def test_scan_covers_code_not_just_docs():
    """ID bi bia co the nam trong docstring cua code, khong chi trong docs/."""
    found = scan()
    srcs = [hit for hits in found.values() for hit in hits]
    assert any(h.endswith(".py") or ".py:" in h for h in srcs)


def test_compressed_id_lists_are_expanded():
    """`NT 63/64/65` phai lo ra CA BA. Neu khong, hai ID an khoi linter --
    dung loai lo hong linter nay sinh ra de chan.

    Vi du that: docs/phase-L2/99-gate-decision.md:41.
    """
    assert ids_in("NT 63/64/65 -- ky luat pham vi") == {"NT 63", "NT 64", "NT 65"}
    # fixture PHAI dung ID da dang ky: linter quet ca test/, va no dung khi
    # lam vay -- mot ID bia trong docstring test cung la mot ID bia.
    assert ids_in("NT 56/57/58") == {"NT 56", "NT 57", "NT 58"}
    assert ids_in("khong co dinh danh nao o day") == set()

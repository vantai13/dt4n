#!/usr/bin/env python3
"""Chan trich dan bia: moi ID phai co mot dong trong docs/NT_REGISTRY.md.

Ly do ton tai: mot chi dan dau vao de xuat `G-L27--G-L30` va `NT56` trong khi
cac dinh danh do da co nghia da ky; `docs/phase-G/17-amendment-G-A005-
reclassification.md:41` phai cap lai so khac. Su co lap lai o Phase T2 voi
quy mo lon hon: 17 ID duoc trich, phan lon khong kiem duoc.

Linter nay KHONG doc noi dung. No chi tra loi mot cau: ID nay co trong so
dang ky khong? Mot ID khong co nguon thi KHONG TON TAI -- khong duoc suy noi
dung tu ten no.

    python3 tools/lint_identifiers.py            # quet docs/ + code
    python3 tools/lint_identifiers.py --list     # in so dang ky da doc duoc
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Dict, List, Set, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/NT_REGISTRY.md"

# Bat ca `NT 53`, `NT53`, `NT-53`, `NT-L22`, `NT L22`.
ID_PAT = re.compile(r"\bNT[\s‐-―-]?(L?)[\s‐-―-]?(\d{1,3})\b")

# Dang NEN: `NT 63/64/65` chi lo ra `NT 63` cho ID_PAT; hai ID con lai bi AN
# khoi scanner. Do dung la loai lo hong linter nay sinh ra de chan, nen phai
# bung no. Vi du that: docs/phase-L2/99-gate-decision.md:41.
COMPRESSED_PAT = re.compile(
    r"\bNT[\s‐-―-]?(L?)[\s‐-―-]?(\d{1,3})((?:\s*/\s*\d{1,3})+)")

SCAN_SUFFIXES = (".md", ".py")
SKIP_DIRS = {".git", "legacy", "__pycache__", ".pytest_cache", "node_modules"}


def norm(letter: str, number: str) -> str:
    """`NT53` == `NT 53` == `NT-53`; `NT-L22` == `NT L22`.

    Chuan hoa la BAT BUOC, khong phai trang tri: repo that co ca `NT33`
    (measurements/aoi_decompose.py:438) lan `NT 53`. Khong chuan hoa thi
    linter bo sot dung nhung bien the duoc go voi khoang trang.
    """
    return ("NT-L%s" if letter else "NT %s") % int(number)


REJECTED_HEADING = "DA TU CHOI"


def registered() -> Tuple[Set[str], Set[str]]:
    """Doc so dang ky theo MUC.

    Tra ve (duoc_cap, bi_tu_choi). Muc "DA TU CHOI" KHONG cap tinh hop le:
    neu khong tach theo muc, mot ID bi tu choi viet tran trong bang do se
    lang le tro thanh "da dang ky" -- dung cai ma so nay sinh ra de chan.
    """
    if not REGISTRY.exists():
        sys.exit("THIEU %s -- khong the lint" % REGISTRY.relative_to(ROOT))
    ok: Set[str] = set()
    rejected: Set[str] = set()
    in_rejected = False
    for line in REGISTRY.read_text(errors="replace").splitlines():
        if line.startswith("#"):
            in_rejected = REJECTED_HEADING in line.upper()
            continue
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip().strip("`")
        m = ID_PAT.fullmatch(cell) or ID_PAT.match(cell)
        if not m:
            continue
        key = norm(m.group(1), m.group(2))
        (rejected if in_rejected else ok).add(key)
    return ok - rejected, rejected


def scan() -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {}
    for p in sorted(ROOT.rglob("*")):
        if p.suffix not in SCAN_SUFFIXES:
            continue
        if SKIP_DIRS & set(p.parts) or p == REGISTRY:
            continue
        try:
            lines = p.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            where = "%s:%d  |%s" % (p.relative_to(ROOT), i, line.strip()[:72])
            for key in ids_in(line):
                found.setdefault(key, []).append(where)
    return found


def ids_in(line: str) -> Set[str]:
    """Moi ID trong mot dong, KE CA dang nen `NT 63/64/65`."""
    out = {norm(a, b) for a, b in ID_PAT.findall(line)}
    for m in COMPRESSED_PAT.finditer(line):
        letter = m.group(1)
        out.add(norm(letter, m.group(2)))
        for num in re.findall(r"\d{1,3}", m.group(3)):
            out.add(norm(letter, num))
    return out


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="in so dang ky roi thoat")
    ap.add_argument("--max-show", type=int, default=40,
                    help="so dong vi pham in ra toi da")
    args = ap.parse_args(argv)

    known, rejected = registered()
    if args.list:
        for k in sorted(known, key=lambda s: (s.startswith("NT-L"),
                                              int(re.search(r"\d+", s).group()))):
            print(" ", k)
        print("tong: %d ID duoc cap" % len(known))
        print("bi tu choi (KHONG duoc dung): %s"
              % ", ".join(sorted(rejected)) if rejected else "(khong co)")
        return 0

    found = scan()
    used_rejected = {k: v for k, v in found.items() if k in rejected}
    if used_rejected:
        print("ID DA BI TU CHOI nhung van duoc dung: %d" % len(used_rejected))
        for k in sorted(used_rejected):
            print("\n  %s  -- xem muc DA TU CHOI trong so dang ky" % k)
            for hit in used_rejected[k][:5]:
                print("    " + hit)
        print("\nMot ID bi tu choi KHONG duoc tai dung cho nghia moi (tien le")
        print("docs/phase-G/17-amendment-G-A005-reclassification.md:41).")
        print("Viet noi dung tran, hoac cap so moi tu muc SO TIEP THEO DUOC CAP.")
        return 1

    unknown = {k: v for k, v in found.items() if k not in known}
    if unknown:
        n = sum(len(v) for v in unknown.values())
        print("ID KHONG CO TRONG SO DANG KY: %d ID, %d dong"
              % (len(unknown), n))
        shown = 0
        for k in sorted(unknown):
            print("\n  %s  (%d cho)" % (k, len(unknown[k])))
            for hit in unknown[k]:
                if shown >= args.max_show:
                    print("    ... (con nua)")
                    break
                print("    " + hit)
                shown += 1
        print("\nSua bang MOT trong hai cach:")
        print("  (a) them dong vao docs/NT_REGISTRY.md voi NGUON THAT (file:dong), hoac")
        print("  (b) xoa trich dan -- khong tim duoc nguon thi no khong ton tai.")
        print("Cap so moi: xem muc 'SO TIEP THEO DUOC CAP' trong so dang ky.")
        return 1

    print("OK: %d ID duoc dung, tat ca deu co trong so dang ky (%d muc)."
          % (len(found), len(known)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

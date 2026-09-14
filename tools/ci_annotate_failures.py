#!/usr/bin/env python3
"""Turn a pytest JUnit XML into GitHub annotations so CI failures are readable.

Vi sao can: nhat ky job cua GitHub Actions doi QUYEN ADMIN kho
(`GET /actions/jobs/{id}/logs` -> 403), nen mot nguoi khong phai admin chi doc
duoc "conclusion: failure" chu khong biet TEST NAO do. Mot co che phong thu ma
khong ai doc duoc thi da chet (Phu luc B).

Annotation thi NGUOC LAI: `GET /repos/{o}/{r}/check-runs/{id}/annotations` la
API CONG KHAI voi kho public. Nen buoc nay in ra `::error::` cho tung test that
bai; sau do bat ky ai cung doc duoc danh sach ten bang mot lenh curl.

GitHub chi hien khoang 10 annotation moi buoc, nen so luong that van duoc in ra
o dong dau va ghi ca vao $GITHUB_STEP_SUMMARY.
"""
from __future__ import annotations

import os
import pathlib
import sys
import xml.etree.ElementTree as ET

MAX_ANNOTATIONS = 20


def failures(path: pathlib.Path):
    root = ET.parse(path).getroot()
    for case in root.iter("testcase"):
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is None:
                continue
            name = "%s::%s" % (case.get("classname", ""), case.get("name", ""))
            first = (node.get("message") or "").strip().splitlines()
            yield kind, name.replace(".", "/", name.count(".") - 1), first[0] if first else ""
            break


def main() -> int:
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "pytest.xml")
    if not path.is_file():
        print("::error::khong tim thay %s -- pytest chua chay toi luc ghi XML "
              "(rat co the la LOI THU GOM, khong phai test do)" % path)
        return 0

    found = list(failures(path))
    print("::notice::pytest bao %d test that bai/loi" % len(found))
    for kind, name, message in found[:MAX_ANNOTATIONS]:
        print("::error title=%s::%s: %s" % (kind, name, message[:300]))
    if len(found) > MAX_ANNOTATIONS:
        print("::error::... va %d muc nua; xem bang tom tat cua job"
              % (len(found) - MAX_ANNOTATIONS))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## pytest: %d that bai\n\n" % len(found))
            for kind, name, message in found:
                handle.write("- `%s` (%s) — %s\n" % (name, kind, message[:200]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

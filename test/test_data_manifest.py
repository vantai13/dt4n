"""Moi file du lieu duoc mot doc phase-23 vien dan phai co trong so tong.

Vi sao: doc `47-close-23-22.md` muc 7 in lenh tai tao. Neu lenh do doc mot
parquet khong co trong `DATA_MANIFEST.json` thi khong ai chung minh duoc
file do la file nao.

Hai lop dich CO Y, ca hai deu la co che DA CO cua repo, khong phai noi test:

  1. `results/PATH_MAP.tsv` -- tai lieu trong `docs/` la GHI CHEP LICH SU va
     KHONG duoc viet lai khi phan tang 4 tang (23.17). Duong dan cu tra ve
     duong dan moi qua bang nay. Bo qua no thi test se doi doc noi doi ve
     lich su cua chinh no.
  2. Ellipsis trong van xuoi -- `results/LIVE/.../decision_error...` la mot
     duong dan bi RUT GON de doc, khong phai mot duong dan. Cho nay khong
     the ghim vi khong co gi de ghim.
"""
from __future__ import annotations

import json
import pathlib
import re

MANIFEST = pathlib.Path("results/DATA_MANIFEST.json")
DOCS = pathlib.Path("docs/phase-23")
PATH_MAP = pathlib.Path("results/PATH_MAP.tsv")
REF = re.compile(r"(results/[\w./\-@]+\.parquet)")


def _manifest_paths() -> set[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {r["path"] for r in data["files"]}


def _path_map() -> dict[str, str]:
    """cu -> moi. Cot 0 = duong dan cu, cot 1 = duong dan moi."""
    out: dict[str, str] = {}
    if not PATH_MAP.exists():
        return out
    for line in PATH_MAP.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) >= 2 and cols[0].strip() and cols[1].strip():
            out[cols[0].strip()] = cols[1].strip()
    return out


def _resolve(ref: str, mapping: dict[str, str]) -> str:
    seen = set()
    cur = ref
    while cur in mapping and cur not in seen:   # chan chu trinh trong bang
        seen.add(cur)
        cur = mapping[cur]
    return cur


def test_manifest_exists_and_is_wellformed():
    assert MANIFEST.exists(), "thieu results/DATA_MANIFEST.json (S-A4)"
    d = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert d["schema"] == "dt4n.data_manifest.v1"
    assert d["n_files"] == len(d["files"])
    assert all(len(r["sha256"]) == 64 for r in d["files"])


def test_path_map_is_loadable():
    """Neu bang anh xa rong thi test duoi PASS RONG: no se khong con dich
    duoc gi va moi duong dan cu se tinh la 'khop truc tiep hoac khong co'."""
    mapping = _path_map()
    assert len(mapping) > 100, (
        f"PATH_MAP.tsv chi doc duoc {len(mapping)} dong -- dinh dang da doi?")


def test_every_parquet_cited_in_docs_is_in_manifest():
    have = _manifest_paths()
    mapping = _path_map()
    missing: dict[str, list[str]] = {}
    for doc in sorted(DOCS.glob("*.md")):
        for ref in set(REF.findall(doc.read_text(encoding="utf-8",
                                                 errors="replace"))):
            if "{" in ref or "*" in ref:        # template, khong phai duong dan that
                continue
            if "..." in ref:                    # duong dan rut gon trong van xuoi
                continue
            if ref in have or _resolve(ref, mapping) in have:
                continue
            missing.setdefault(ref, []).append(doc.name)
    assert not missing, (
        "parquet duoc doc vien dan nhung khong co trong DATA_MANIFEST "
        "(da thu ca PATH_MAP.tsv): "
        f"{ {k: v[:2] for k, v in list(missing.items())[:8]} }")

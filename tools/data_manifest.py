#!/usr/bin/env python3
"""So tong hash cua MOI file du lieu, ke ca file bi gitignore.

Vi sao ton tai: `.gitignore` chan moi `*.parquet` cua tang LIVE. Nghia la
dau vao cua toan bo Lesson 23.22 KHONG nam trong repo, va `47-close-23-22.md`
muc 7 in mot lenh tai tao se crash tren may nguoi khac. Manifest KHONG sua
duoc dieu do -- no chi bao dam rang khi file duoc nap len Zenodo, ta chung
minh duoc do la DUNG file da dung.

    python -m tools.data_manifest --write
    python -m tools.data_manifest --verify     # doi chieu voi ban da ghi
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
from typing import Any, Dict, List

MANIFEST = "results/DATA_MANIFEST.json"
SCHEMA = "dt4n.data_manifest.v1"
PATTERNS = ("*.parquet", "*.csv.gz", "*.npz")
ROOTS = ("results",)
CHUNK = 1 << 20


def _preserved_custody() -> Dict[str, Any]:
    """Keep externally supplied custody metadata across manifest rescans."""
    path = pathlib.Path(MANIFEST)
    if not path.exists():
        return {"doi": None, "custody": {}}
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"doi": None, "custody": {}}
    return {
        "doi": current.get("doi"),
        "custody": current.get("custody", {}),
    }


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(["git", *cmd], text=True).strip()
    except Exception:
        return "unknown"


def _tier(path: str) -> str:
    """Tang chung cu -- cung phan tang da dung tu 23.21j."""
    for t in ("LIVE", "SUPERSEDED", "RAW", "PENDING", "SMOKE"):
        if f"/{t}/" in path.replace(os.sep, "/"):
            return t
    return "OTHER"


def scan() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()
    for root in ROOTS:
        base = pathlib.Path(root)
        if not base.exists():
            continue
        for pat in PATTERNS:
            for p in sorted(base.rglob(pat)):
                key = str(p)
                if key in seen or not p.is_file():
                    continue
                seen.add(key)
                st = p.stat()
                rows.append({
                    "path": key.replace(os.sep, "/"),
                    "tier": _tier(key),
                    "bytes": int(st.st_size),
                    "mtime_utc": datetime.datetime.fromtimestamp(
                        st.st_mtime, datetime.timezone.utc).isoformat(),
                    "sha256": _sha256(p),
                })
    return rows


def build() -> Dict[str, Any]:
    rows = scan()
    preserved = _preserved_custody()
    by_tier: Dict[str, Dict[str, int]] = {}
    for r in rows:
        t = by_tier.setdefault(r["tier"], {"n": 0, "bytes": 0})
        t["n"] += 1
        t["bytes"] += r["bytes"]
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "patterns": list(PATTERNS),
        "roots": list(ROOTS),
        "n_files": len(rows),
        "total_bytes": sum(r["bytes"] for r in rows),
        "by_tier": by_tier,
        "doi": preserved["doi"],
        "custody": preserved["custody"],
        "files": rows,
    }


def verify(manifest_path: str = MANIFEST) -> int:
    old = json.loads(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
    old_by_path = {r["path"]: r for r in old["files"]}
    new = {r["path"]: r for r in scan()}

    changed = [p for p in old_by_path.keys() & new.keys()
               if old_by_path[p]["sha256"] != new[p]["sha256"]]
    missing = sorted(old_by_path.keys() - new.keys())
    added = sorted(new.keys() - old_by_path.keys())

    print("file da ghi : %d" % len(old_by_path))
    print("file hien co: %d" % len(new))
    print("DOI NOI DUNG: %d   %s" % (len(changed), changed[:5]))
    print("MAT         : %d   %s" % (len(missing), missing[:5]))
    print("MOI         : %d   %s" % (len(added), added[:5]))
    return 1 if (changed or missing) else 0


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--verify", action="store_true")
    ap.add_argument("--out", default=MANIFEST)
    args = ap.parse_args(argv)

    if args.verify:
        return verify(args.out)
    if not args.write:
        raise AssertionError("phai chon --write hoac --verify")

    out = build()
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("%s: %d file, %.2f GB" % (args.out, out["n_files"],
                                    out["total_bytes"] / 1e9))
    for t, v in sorted(out["by_tier"].items()):
        print("   %-12s %4d file  %8.2f GB" % (t, v["n"], v["bytes"] / 1e9))
    return 0


if __name__ == "__main__":
    sys.exit(main())

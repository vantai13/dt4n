#!/usr/bin/env python3
"""Generate a SHA-256 manifest for raw experiment data.

Raw binary files should not live in git. The manifest pins the exact bytes used
to produce results, while the bytes themselves can live in an external archive.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time


def sha256(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def main(root: str) -> None:
    rows = []
    total = 0
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            if name.endswith((".sha256", ".json")):
                continue
            path = os.path.join(dirpath, name)
            size = os.path.getsize(path)
            total += size
            rows.append(
                {
                    "path": os.path.relpath(path, root),
                    "bytes": size,
                    "sha256": sha256(path),
                }
            )
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    except Exception:
        git_hash = None
        dirty = None

    out = {
        "root": root,
        "n_files": len(rows),
        "total_bytes": total,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_hash": git_hash,
        "git_dirty": dirty,
        "archive_doi": "TBD -- dien sau khi upload Zenodo",
        "files": rows,
    }
    dst = os.path.join(root, "MANIFEST.sha256.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("%d file, %.1f MB -> %s" % (len(rows), total / 1e6, dst))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/phase-L/raw")

#!/usr/bin/env python3
"""Capture the exact Lesson 23.21h Wave-4 parquet set by planned job identity."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from tools import run_23_20_matrix as runner


OUTPUT = Path("results/RAW/phase-21R/WAVE4_DIGESTS.json")
LEDGER = Path("results/RUN_LEDGER_wave4.json")
MANIFEST = Path(
    "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_14cells.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def planned_parquets() -> list[Path]:
    return [
        Path(runner.stem_of(cell, profile, axis, wave=4) + ".parquet")
        for cell, profile, axis in runner.WAVES[4]
    ]


def build() -> dict:
    paths = planned_parquets()
    if len(paths) != len(set(paths)) or len(paths) != 12:
        raise SystemExit("Wave 4 must resolve to exactly 12 unique parquets")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("missing Wave-4 parquets: %s" % missing)

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    if len(ledger) != 12 or not all(row.get("pass") for row in ledger.values()):
        raise SystemExit("Wave-4 ledger is not complete and passing")

    return {
        "schema": "dt4n.surviving_digests.v2",
        "lesson": "23.21h",
        "captured_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "selection": "exact tools.run_23_20_matrix.WAVES[4] job set",
        "tier_note": (
            "Measured Wave-4 artifacts are LIVE because measured_v7 and the "
            "exogenous S-B manifest are registered; legacy controls remain "
            "SUPERSEDED."
        ),
        "manifest": {
            "path": str(MANIFEST),
            "sha256": sha256(MANIFEST),
        },
        "ledger": {
            "path": str(LEDGER),
            "sha256": sha256(LEDGER),
            "jobs": len(ledger),
            "passed": sum(bool(row.get("pass")) for row in ledger.values()),
        },
        "files": {
            str(path): {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in sorted(paths)
        },
    }


def main() -> int:
    payload = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for path, row in payload["files"].items():
        print("%-82s %s" % (path, row["sha256"][:16]))
    print("\n->", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

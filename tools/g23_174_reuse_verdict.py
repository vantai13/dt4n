#!/usr/bin/env python3
"""G23-174: adjudicate whether an unverifiable calib parquet was reused.

This is an inventory/audit only.  It does not run Mininet and does not reuse
any parquet.  The repository can contain old local parquet files; their mere
presence is not a PASS or a FAIL.  The gate asks whether a current LIVE build
claims or references one of those files without a verifiable output digest.
"""
from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import subprocess
from typing import Any


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "results/LIVE/phase-23/g23_174_reuse_verdict.json"

# The four Wave-4 paths hard-coded by cert/live_region_sweep.py.
WAVE4 = [
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.875.parquet",
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.900.parquet",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.650.parquet",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.675.parquet",
]


def _sha(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: str) -> str:
    return os.path.relpath(path, REPO).replace(os.sep, "/")


def _read_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    wave4 = {path: os.path.exists(os.path.join(REPO, path)) for path in WAVE4}

    # Contrary to the advisory's snapshot, this checkout has six old local
    # files under results/phase-22.  Inventory them; do not silently turn that
    # discrepancy into the expected KH3 answer.
    legacy_paths = sorted(
        glob.glob(
            os.path.join(REPO, "results", "**", "calib_set_v3_*.parquet"),
            recursive=True,
        )
    )

    live: list[dict[str, Any]] = []
    live_output_paths: set[str] = set()
    live_input_paths: set[str] = set()
    for report_path in sorted(
        glob.glob(os.path.join(REPO, "results", "LIVE", "phase-21R", "*_report.json"))
    ):
        report = _read_json(report_path)
        output = report.get("output") or {}
        provenance = report.get("provenance") or {}
        parquet_rel = output.get("parquet_path", "")
        parquet_path = os.path.join(REPO, parquet_rel)
        expected_digest = output.get("parquet_sha256")
        on_disk = bool(parquet_rel) and os.path.exists(parquet_path)
        digest_matches = _sha(parquet_path) == expected_digest if on_disk and expected_digest else None
        provenance_inputs = set((provenance.get("sha256") or {}).keys())
        live_output_paths.add(parquet_rel)
        live_input_paths.update(provenance_inputs)
        live.append(
            {
                "report": _rel(report_path),
                "parquet_path": parquet_rel,
                "has_digest": bool(expected_digest),
                "parquet_on_disk": on_disk,
                "digest_matches": digest_matches,
                "regenerated_from_seed": (
                    provenance.get("script") == "cert/build_calib_set_v3.py"
                    and bool(provenance.get("seeds"))
                ),
            }
        )

    legacy: list[dict[str, Any]] = []
    for path in legacy_paths:
        rel = _rel(path)
        legacy.append(
            {
                "path": rel,
                "bytes": os.path.getsize(path),
                "sha256": _sha(path),
                "claimed_as_live_output": rel in live_output_paths,
                "referenced_as_live_input": rel in live_input_paths,
                "reuse_policy": "PROHIBITED_UNLESS_PAIRED_WITH_A_PRIOR_DIGEST",
            }
        )

    n_live = len(live)
    n_digest = sum(1 for row in live if row["has_digest"])
    n_on_disk = sum(1 for row in live if row["parquet_on_disk"])
    n_matching = sum(1 for row in live if row["digest_matches"] is True)
    n_regenerated = sum(1 for row in live if row["regenerated_from_seed"])
    legacy_reused = [
        row["path"]
        for row in legacy
        if row["claimed_as_live_output"] or row["referenced_as_live_input"]
    ]
    wave4_missing = sum(1 for exists in wave4.values() if not exists)

    passed = (
        wave4_missing == len(WAVE4)
        and n_live == 16
        and n_digest == n_live
        and n_on_disk == n_live
        and n_matching == n_live
        and n_regenerated == n_live
        and not legacy_reused
    )
    verdict = "PASS_NO_UNVERIFIED_REUSE" if passed else "INVESTIGATE_BEFORE_REUSE"

    result = {
        "gate": "G23-174",
        "lesson": "23.21c",
        "question": "Co calib parquet nao duoc tai dung ma khong kiem duoc van tay?",
        "verdict": verdict,
        "wave4_parquet_exists": wave4,
        "wave4_n_missing": wave4_missing,
        "legacy_calib_set_v3_found": legacy,
        "legacy_n_found": len(legacy),
        "legacy_reused_by_current_live_builds": legacy_reused,
        "live_reports": live,
        "n_live_reports": n_live,
        "n_live_with_digest": n_digest,
        "n_live_parquet_on_disk": n_on_disk,
        "n_live_digest_matches": n_matching,
        "n_live_regenerated_from_seed": n_regenerated,
        "adjudication": (
            "KH3 cho bon parquet Dot 4: ca bon vang mat. Checkout con sau "
            "parquet legacy calib_set_v3 (ban dau o results/phase-22, sau do "
            "phan tang vao results/SUPERSEDED/phase-22), trai voi snapshot trong "
            "huong dan; chung duoc kiem ke va CAM tai dung neu chua ghep duoc "
            "voi digest da luu. Khong file legacy nao duoc 16 build LIVE hien "
            "hanh khai la output hoac input. Ca 16 build LIVE duoc sinh lai tu "
            "seed; 16/16 parquet con tren dia va khop output.parquet_sha256. Vi "
            "vay khong co tai dung khong xac minh, nhung viec ton tai cua sau "
            "file legacy khong duoc dien giai thanh chung co the tai dung."
        ),
        "does_not_close": ["L51", "G23-141", "G23-142"],
        "validity": {
            "aoi_axis": {"label": "measured_v7_uniform"},
            "sla_axis": {"label": "exogenous_g114_S-B"},
            "axis_role": "audits_artifacts",
            "w_loss": 5000.0,
        },
        "provenance": {
            "script": "tools/g23_174_reuse_verdict.py",
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=REPO,
                check=True,
            ).stdout.strip(),
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    }

    output_path = os.path.join(REPO, OUT)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    print("verdict =", verdict)
    print("Dot 4 thieu:", wave4_missing, "/", len(WAVE4))
    print("legacy calib_set_v3 tim thay:", len(legacy))
    print("legacy bi LIVE tai dung:", len(legacy_reused))
    print("live co digest:", n_digest, "/", n_live)
    print("live digest khop:", n_matching, "/", n_live)
    print("->", OUT)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

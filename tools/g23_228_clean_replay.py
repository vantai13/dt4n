#!/usr/bin/env python3
"""G23-228: compare the clean replay with the 08b6879 headline bit-for-bit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from typing import Any, Dict, Mapping, Sequence


BASELINE_COMMIT = "08b6879"
ARTIFACT = "results/LIVE/phase-23/live_region_sweep_slaB.json"
OUTPUT = "results/RAW/phase-23/g23_228_clean_replay.json"
SECTIONS = ("cells", "metrics", "live_definition_table")


def _git(*args: str) -> str:
    return subprocess.check_output(("git",) + args, text=True).strip()


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _flat(value: Any, prefix: str = "") -> Dict[str, Any]:
    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for key in sorted(value):
            result.update(_flat(value[key], "%s/%s" % (prefix, key)))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            result.update(_flat(item, "%s/%d" % (prefix, index)))
        return result
    return {prefix or "/": value}


def compare(
    artifact: str = ARTIFACT,
    baseline_commit: str = BASELINE_COMMIT,
) -> Dict[str, Any]:
    baseline_raw = _git("show", "%s:%s" % (baseline_commit, artifact))
    baseline = json.loads(baseline_raw)
    with open(artifact, "r", encoding="utf-8") as handle:
        current = json.load(handle)

    section_rows: Dict[str, Any] = {}
    mismatches = []
    for section in SECTIONS:
        left = _flat(baseline[section])
        right = _flat(current[section])
        only = sorted(set(left) ^ set(right))
        unequal = [
            key for key in sorted(set(left) & set(right)) if left[key] != right[key]
        ]
        mismatches.extend("%s%s" % (section, key) for key in (only + unequal))
        section_rows[section] = {
            "bit_exact": not only and not unequal,
            "baseline_sha256": _canonical_sha256(baseline[section]),
            "current_sha256": _canonical_sha256(current[section]),
            "baseline_leaf_count": len(left),
            "current_leaf_count": len(right),
            "only_one_side_count": len(only),
            "unequal_count": len(unequal),
            "mismatch_sample": (only + unequal)[:10],
        }

    head = _git("rev-parse", "HEAD")
    provenance = current.get("provenance", {})
    clean_claim = provenance.get("git_dirty") is False
    head_claim = provenance.get("git_hash") == head
    sections_exact = all(row["bit_exact"] for row in section_rows.values())
    passed = bool(clean_claim and head_claim and sections_exact)
    return {
        "schema": "dt4n.g23_228.v1",
        "gate": "G23-228",
        "pass": passed,
        "baseline_commit": baseline_commit,
        "baseline_schema": baseline.get("schema"),
        "current_schema": current.get("schema"),
        "artifact": artifact,
        "baseline_git_dirty": baseline.get("provenance", {}).get("git_dirty"),
        "current_git_dirty": provenance.get("git_dirty"),
        "current_git_hash": provenance.get("git_hash"),
        "comparison_head": head,
        "current_clean_claim_pass": clean_claim,
        "current_head_matches_provenance": head_claim,
        "all_numeric_trees_bit_exact": sections_exact,
        "sections": section_rows,
        "total_mismatch_count": len(mismatches),
        "mismatch_sample": mismatches[:20],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", default=ARTIFACT)
    parser.add_argument("--baseline-commit", default=BASELINE_COMMIT)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    report = compare(args.artifact, args.baseline_commit)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    for section in SECTIONS:
        row = report["sections"][section]
        print(
            "%-22s exact=%s leaves=%d mismatches=%d"
            % (
                section,
                row["bit_exact"],
                row["current_leaf_count"],
                row["only_one_side_count"] + row["unequal_count"],
            )
        )
    print("provenance clean=%s hash_matches_HEAD=%s" % (
        report["current_clean_claim_pass"],
        report["current_head_matches_provenance"],
    ))
    print("G23-228 %s" % ("PASS" if report["pass"] else "FAIL"))
    print("artifact -> %s" % args.out)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

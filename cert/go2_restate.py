#!/usr/bin/env python3
"""GO-2 debt closure for Phase 23.

This script only reads the Phase 22 simultaneous-conformal artifact.  It turns
the paired-bootstrap q_hat deltas into a flat table, so the FWER ranking can be
stated by slot instead of as a false total order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any, Dict, List


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def flatten(block: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten by_bin into one row per (z_bin, procedure, slot)."""
    rows: List[Dict[str, Any]] = []
    for bin_id, procs in block["by_bin"].items():
        for proc, values in procs.items():
            n_slot = len(values["delta_mean"])
            for slot in range(n_slot):
                lo = float(values["ci95_low"][slot])
                hi = float(values["ci95_high"][slot])
                contains_zero = bool(lo <= 0.0 <= hi)
                rows.append(
                    {
                        "z_bin": int(bin_id),
                        "procedure": str(proc),
                        "slot": int(slot + 1),
                        "delta_mean": float(values["delta_mean"][slot]),
                        "ci95_low": lo,
                        "ci95_high": hi,
                        "contains_zero": contains_zero,
                        "sign": "0" if contains_zero else ("+" if lo > 0.0 else "-"),
                    }
                )
    return sorted(rows, key=lambda r: (r["z_bin"], r["procedure"], r["slot"]))


def summarize_by_slot(rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, int]]:
    out: Dict[int, Dict[str, int]] = {}
    for row in rows:
        slot = int(row["slot"])
        stats = out.setdefault(slot, {"n": 0, "zero": 0, "pos": 0, "neg": 0})
        stats["n"] += 1
        stats["zero"] += int(row["sign"] == "0")
        stats["pos"] += int(row["sign"] == "+")
        stats["neg"] += int(row["sign"] == "-")
    return out


def build_report(artifact: str) -> Dict[str, Any]:
    with open(artifact, "r", encoding="utf-8") as f:
        art = json.load(f)
    block = art["paired_bootstrap_delta_qhat"]
    rows = flatten(block)
    return {
        "kind": "go2_fwer_restatement",
        "baseline": block["baseline"],
        "n_boot": int(block["n_boot"]),
        "variant": block["variant"],
        "source_artifact": artifact,
        "source_sha256": sha256(artifact),
        "rows": rows,
        "n_total": len(rows),
        "n_contains_zero": int(sum(r["contains_zero"] for r in rows)),
        "summary_by_slot": summarize_by_slot(rows),
        "allowed_claim_scope": "FWER ranking depends on slot; do not state a total order.",
    }


def print_table(report: Dict[str, Any]) -> None:
    print(f'{"bin":>3} {"proc":>11} {"slot":>4} {"delta":>8} {"lo":>8} {"hi":>8}  0?')
    for row in report["rows"]:
        zero = "YES" if row["contains_zero"] else "no"
        print(
            f'{row["z_bin"]:>3} {row["procedure"]:>11} {row["slot"]:>4} '
            f'{row["delta_mean"]:>8.3f} {row["ci95_low"]:>8.3f} '
            f'{row["ci95_high"]:>8.3f}  {zero}'
        )
    print(f'\nchua 0: {report["n_contains_zero"]}/{report["n_total"]}')
    for slot, stats in sorted(report["summary_by_slot"].items()):
        print(
            "  slot %d: + %d  - %d  0 %d  (n=%d)"
            % (slot, stats["pos"], stats["neg"], stats["zero"], stats["n"])
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    report = build_report(str(args.artifact))
    print_table(report)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()

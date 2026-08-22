#!/usr/bin/env python3
"""Expose the cross-cell lift decomposition already present in G23-23.

This does not estimate anything new.  It reads the committed lift-law rows,
selects C3, and makes the axis-specific bottleneck visible.  It also reports
the C3-minus-B2 transfer contrast from the same artifact.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Mapping, Sequence

from cert.cell_matrices import git, json_clean, pin


INPUT = "results/SUPERSEDED/phase-23/g23_23_lift_law.json"
OUTPUT = "results/SUPERSEDED/phase-23/lift_decomposition_by_cell.json"


def analyze(payload: Mapping[str, Any]) -> Dict[str, Any]:
    rows = list(payload.get("rows", []))
    c3 = [row for row in rows if row.get("selector") == "C3_conformal"]
    if len(c3) != 3:
        raise ValueError("can dung 3 C3 rows, thay %d" % len(c3))
    by_key = {(row["cell"], row["selector"]): row for row in rows}

    def spread(name: str) -> Dict[str, float]:
        values = [float(row[name]) for row in c3]
        if min(values) <= 0.0:
            raise ValueError("spread max/min can so duong cho %s" % name)
        return {
            "min": min(values),
            "max": max(values),
            "max_over_min": max(values) / min(values),
            "absolute_range": max(values) - min(values),
        }

    table = []
    transfer = []
    for row in c3:
        cell = str(row["cell"])
        err_neo = float(row["err_neo"])
        swing = float(row["swing"])
        table.append(
            {
                "cell": cell,
                "selector": "C3_conformal",
                "err_neo": err_neo,
                "err_P1": err_neo + swing,
                "swing": swing,
                "twin_deg": float(row["twin_deg"]),
                "prior_deg": float(row["prior_deg"]),
                "lift": float(row["lift"]),
                "reject_share": float(row["reject_share"]),
                "delta": float(row["delta_vs_anchor"]),
            }
        )
        b2 = by_key.get((cell, "B2_constant_gap"))
        if b2 is None:
            raise ValueError("thieu B2 row cho %s" % cell)
        c3_delta = float(row["delta_vs_anchor"])
        b2_delta = float(b2["delta_vs_anchor"])
        transfer.append(
            {
                "cell": cell,
                "B2_delta": b2_delta,
                "C3_delta": c3_delta,
                "C3_minus_B2": c3_delta - b2_delta,
            }
        )

    spreads = {name: spread(name) for name in ("twin_deg", "prior_deg", "swing")}
    return json_clean(
        {
            "schema": "lift_decomposition_by_cell/v1",
            "source_status": "REANALYSIS_OF_COMMITTED_ARTIFACT_NO_NEW_MEASUREMENT",
            "rows": table,
            "spreads": spreads,
            "bottleneck": {
                "component": "fallback_prior_deg",
                "twin_deg_spread": spreads["twin_deg"]["max_over_min"],
                "prior_deg_spread": spreads["prior_deg"]["max_over_min"],
                "reason": "prior_deg max/min exceeds twin_deg max/min across cells",
            },
            "transfer_C3_minus_B2": transfer,
        }
    )


def print_report(report: Mapping[str, Any]) -> None:
    print(
        f"{'cell':<16}{'selector':<18}{'twin_deg':>10}{'prior_deg':>11}"
        f"{'lift':>10}{'swing':>10}{'delta':>11}"
    )
    for row in report["rows"]:
        print(
            f"{row['cell']:<16}{row['selector']:<18}"
            f"{row['twin_deg']:>10.5f}{row['prior_deg']:>11.5f}"
            f"{row['lift']:>10.5f}{row['swing']:>10.5f}{row['delta']:>11.6f}"
        )
    print()
    for name, values in report["spreads"].items():
        print(
            f"{name:<12} min={values['min']:.5f} max={values['max']:.5f} "
            f"spread={values['max_over_min']:.3f}x"
        )
    print()
    for row in report["transfer_C3_minus_B2"]:
        print(
            "C3-B2 %-16s %+0.9f" % (row["cell"], row["C3_minus_B2"])
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=INPUT)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as handle:
        report = analyze(json.load(handle))
    report["provenance"] = {
        "script": "tools/lift_decomposition_by_cell.py",
        "git_hash": git("git", "rev-parse", "HEAD"),
        "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input": pin(args.input),
    }
    print_report(report)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(json_clean(report), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("artifact -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

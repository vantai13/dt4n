#!/usr/bin/env python3
"""Phase 20R.6-v2 pilot power summary.

This intentionally does not print residual means.  The internal pilot may only
be used to estimate between-seed scatter and the seed count needed for power.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from measurements import cascade_residual as CR


DEFAULT_DELTAS = (0.005, 0.010)


def _parts(value: str) -> List[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _parse_deltas(value: str) -> List[float]:
    out = [float(part) for part in _parts(value)]
    if not out or any(delta <= 0.0 for delta in out):
        raise argparse.ArgumentTypeError("--deltas must contain positive numbers")
    return out


def _n_seed_for(sd: float, delta: float) -> Optional[int]:
    if not math.isfinite(sd):
        return None
    return int(math.ceil((1.645 * float(sd) / float(delta)) ** 2))


def summarize(
    branch_b: Sequence[str],
    branch_c: Sequence[str],
    modes: Sequence[str],
    rho_bar: float,
    deltas: Sequence[float],
) -> Dict[str, Any]:
    rows_b_all = CR.load_rows(branch_b, "B")
    rows_c_all = CR.load_rows(branch_c, "C")

    rows: List[Dict[str, Any]] = []
    invariants: Dict[str, Any] = {}
    for mode in modes:
        rows_b = [
            row for row in rows_b_all
            if str(row.get("mode")) == str(mode) and abs(float(row.get("rho_bar")) - float(rho_bar)) <= 1e-9
        ]
        rows_c = [
            row for row in rows_c_all
            if str(row.get("mode")) == str(mode) and abs(float(row.get("rho_bar")) - float(rho_bar)) <= 1e-9
        ]
        invariant_error: Optional[str] = None
        try:
            invariants[str(mode)] = {
                "status": "ok",
                "details": CR.assert_structural_invariant(rows_b, rows_c),
            }
        except AssertionError as exc:
            invariant_error = str(exc)
            invariants[str(mode)] = {"status": "fail", "reason": invariant_error}

        for channel in ("loss", "delay_ms"):
            if invariant_error is not None:
                item = {
                    "mode": str(mode),
                    "channel": channel,
                    "status": "insufficient_data",
                    "reason": invariant_error,
                    "n_observed_seed": 0,
                    "seed_ids": [],
                    "sd_d_s": None,
                    "n_seed_required": {
                        ("delta_%g" % float(delta)): None
                        for delta in deltas
                    },
                }
            else:
                try:
                    diffs, seeds = CR.paired_residuals(rows_b, rows_c, mode, rho_bar, channel)
                    sd = float(np.std(diffs, ddof=1)) if int(diffs.size) > 1 else float("nan")
                    item = {
                        "mode": str(mode),
                        "channel": channel,
                        "status": "ok",
                        "n_observed_seed": int(diffs.size),
                        "seed_ids": [int(seed) for seed in seeds],
                        "sd_d_s": sd,
                        "n_seed_required": {
                            ("delta_%g" % float(delta)): _n_seed_for(sd, float(delta))
                            for delta in deltas
                        },
                    }
                except (AssertionError, KeyError, ValueError) as exc:
                    item = {
                        "mode": str(mode),
                        "channel": channel,
                        "status": "insufficient_data",
                        "reason": str(exc),
                        "n_observed_seed": 0,
                        "seed_ids": [],
                        "sd_d_s": None,
                        "n_seed_required": {
                            ("delta_%g" % float(delta)): None
                            for delta in deltas
                        },
                    }
            rows.append(item)

    return {
        "schema": "phase20r6/pilot_power_only/v1",
        "note": "Pilot summary intentionally omits point estimates; use sd(d_s) only for power planning.",
        "rho_bar": float(rho_bar),
        "deltas": [float(delta) for delta in deltas],
        "invariant_by_mode": invariants,
        "rows": rows,
    }


def print_summary(summary: Dict[str, Any]) -> None:
    print("=== PILOT POWER ONLY ===")
    print("rho_bar = %.6f" % float(summary["rho_bar"]))
    print("deltas  = %s" % ", ".join("%.6g" % float(delta) for delta in summary["deltas"]))
    print()
    hdr = "%-8s %-9s %8s %14s %s"
    print(hdr % ("mode", "channel", "n_seed", "sd(d_s)", "n_seed_required"))
    for row in summary["rows"]:
        req = ", ".join("%s=%s" % (key, val) for key, val in sorted(row["n_seed_required"].items()))
        sd_text = "INSUFFICIENT" if row["sd_d_s"] is None else "%.9g" % float(row["sd_d_s"])
        print(
            hdr
            % (
                row["mode"],
                row["channel"],
                int(row["n_observed_seed"]),
                sd_text,
                req,
            )
        )
        if row.get("status") != "ok":
            print("  reason: %s" % row.get("reason", "insufficient data"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch-b", required=True, help="comma-separated branch B state files")
    ap.add_argument("--branch-c", required=True, help="comma-separated branch C state files")
    ap.add_argument("--modes", default="poisson,h2")
    ap.add_argument("--rho-bar", type=float, default=0.925)
    ap.add_argument("--deltas", type=_parse_deltas, default=list(DEFAULT_DELTAS))
    ap.add_argument("--out", help="optional JSON output path")
    args = ap.parse_args(argv)

    summary = summarize(
        _parts(args.branch_b),
        _parts(args.branch_c),
        _parts(args.modes),
        args.rho_bar,
        args.deltas,
    )
    print_summary(summary)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
        print()
        print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

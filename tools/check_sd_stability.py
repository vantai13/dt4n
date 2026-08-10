#!/usr/bin/env python3
"""Check seed-sd stability without printing residual means."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np

from measurements import cascade_residual as CR


def _parts(value: str) -> List[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _ints(value: str) -> List[int]:
    return [int(part) for part in _parts(value)]


def _filter_seeds(rows: Sequence[Mapping[str, Any]], seeds: Sequence[int]) -> List[Mapping[str, Any]]:
    wanted = {int(seed) for seed in seeds}
    return [row for row in rows if int(row.get("seed")) in wanted]


def _sd_for(
    rows_b_all: Sequence[Mapping[str, Any]],
    rows_c_all: Sequence[Mapping[str, Any]],
    mode: str,
    channel: str,
    rho_bar: float,
    seeds: Sequence[int],
) -> float:
    diffs, kept = CR.paired_residuals(
        _filter_seeds(rows_b_all, seeds),
        _filter_seeds(rows_c_all, seeds),
        mode,
        rho_bar,
        channel,
    )
    if set(int(seed) for seed in kept) != set(int(seed) for seed in seeds):
        raise ValueError("khong ghep du seed cho %s/%s: got %s" % (mode, channel, kept))
    return float(np.std(diffs, ddof=1))


def summarize(
    branch_b: Sequence[str],
    branch_c: Sequence[str],
    modes: Sequence[str],
    rho_bar: float,
    early_seeds: Sequence[int],
    late_seeds: Sequence[int],
) -> Dict[str, Any]:
    rows_b_all = CR.load_rows(branch_b, "B")
    rows_c_all = CR.load_rows(branch_c, "C")
    rows = []
    for mode in modes:
        for channel in ("loss", "delay_ms"):
            sd_early = _sd_for(rows_b_all, rows_c_all, mode, channel, rho_bar, early_seeds)
            sd_late = _sd_for(rows_b_all, rows_c_all, mode, channel, rho_bar, late_seeds)
            ratio = float(sd_late / sd_early) if sd_early > 0.0 else float("inf")
            rows.append(
                {
                    "mode": str(mode),
                    "channel": channel,
                    "early_seeds": [int(seed) for seed in early_seeds],
                    "late_seeds": [int(seed) for seed in late_seeds],
                    "sd_early": sd_early,
                    "sd_late": sd_late,
                    "ratio_late_over_early": ratio,
                    "status": "ok" if 0.4 < ratio < 2.5 else "drift_suspect",
                }
            )
    return {
        "schema": "phase20r6/sd_stability/v1",
        "note": "Only between-seed standard deviations are reported; residual means are intentionally omitted.",
        "rho_bar": float(rho_bar),
        "branch_b_files": list(branch_b),
        "branch_c_files": list(branch_c),
        "rows": rows,
    }


def print_summary(summary: Mapping[str, Any]) -> None:
    print("=== SD STABILITY CHECK ===")
    print("rho_bar = %.6f" % float(summary["rho_bar"]))
    print()
    hdr = "%-8s %-9s %14s %14s %8s %s"
    print(hdr % ("mode", "channel", "sd(early)", "sd(late)", "ratio", "status"))
    for row in summary["rows"]:
        print(
            hdr
            % (
                row["mode"],
                row["channel"],
                "%.9g" % float(row["sd_early"]),
                "%.9g" % float(row["sd_late"]),
                "%.2f" % float(row["ratio_late_over_early"]),
                "OK" if row["status"] == "ok" else "*** LECH -> nghi drift ***",
            )
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--branch-b",
        default=(
            "results/phase-20R/branch_b_fixed_pilot3.json,"
            "results/phase-20R/branch_b_fixed_s104_108.json"
        ),
        help="comma-separated Branch B state files",
    )
    ap.add_argument(
        "--branch-c",
        default=(
            "results/phase-20R/branch_c_fixed_pilot3.json,"
            "results/phase-20R/branch_c_fixed_s104_108.json"
        ),
        help="comma-separated Branch C state files",
    )
    ap.add_argument("--modes", default="poisson,h2")
    ap.add_argument("--rho-bar", type=float, default=0.925)
    ap.add_argument("--early-seeds", default="101,102,103")
    ap.add_argument("--late-seeds", default="104,105,106,107,108")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    summary = summarize(
        _parts(args.branch_b),
        _parts(args.branch_c),
        _parts(args.modes),
        args.rho_bar,
        _ints(args.early_seeds),
        _ints(args.late_seeds),
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

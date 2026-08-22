#!/usr/bin/env python3
"""Analyze path-composition calibration rows.

This checks the simulator assumption that path delay is well represented by
adding per-link delays. The raw measurement file stores one row per path edge;
this analyzer groups rows by run and compares summed queueing delay against the
observed path RTT.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from typing import Iterable, Mapping

import numpy as np


def _float(row: Mapping[str, str], key: str, default=None):
    value = row.get(key)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_runs(path: str):
    groups = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            run_id = row.get("run_id") or "%s:%s" % (
                row.get("timestamp_utc", ""),
                row.get("offered_mbps", ""),
            )
            groups[run_id].append(row)

    runs = []
    for run_id, rows in groups.items():
        first = rows[0]
        qsum = sum(_float(row, "q_delay_ms", 0.0) for row in rows)
        base = _float(first, "path_forward_base_delay_ms")
        if base is None:
            base = sum(_float(row, "delay_ms", 0.0) for row in rows)
        rtt = _float(first, "path_rtt_avg_ms")
        residual = _float(first, "rtt_minus_2base_minus_qsum_ms")
        if residual is None and rtt is not None:
            residual = rtt - 2.0 * base - qsum
        runs.append(
            {
                "run_id": run_id,
                "path": first.get("path", ""),
                "offered_mbps": _float(first, "offered_mbps", 0.0),
                "n_edges": len(rows),
                "sum_qdelay_ms": qsum,
                "base_oneway_ms": base,
                "rtt_avg_ms": rtt,
                "rtt_minus_2base_minus_qsum_ms": residual,
                "loss_pct": _float(first, "path_packet_loss_pct"),
            }
        )
    return sorted(runs, key=lambda row: (row["path"], row["offered_mbps"], row["run_id"]))


def corr(xs, ys):
    if len(xs) < 2 or np.std(xs) == 0.0 or np.std(ys) == 0.0:
        return float("nan")
    return float(np.corrcoef(np.asarray(xs), np.asarray(ys))[0, 1])


def parse_args(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="Analyze Lesson 9.0 path composition")
    p.add_argument("--csv", default="results/SUPERSEDED/calib/raw_topo_validate.csv")
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    runs = read_runs(args.csv)
    if not runs:
        raise SystemExit("no usable rows in %s" % args.csv)

    print("=" * 82)
    print("Path Composition Summary")
    print("=" * 82)
    print("run_id        rate  edges  qsum_ms  rtt_ms  residual_ms  loss%  path")
    print("-" * 82)
    for row in runs:
        print(
            "%-12s %5.2f %6d %8.3f %7s %12s %6s  %s"
            % (
                row["run_id"],
                row["offered_mbps"],
                row["n_edges"],
                row["sum_qdelay_ms"],
                "%.3f" % row["rtt_avg_ms"] if row["rtt_avg_ms"] is not None else "n/a",
                (
                    "%+.3f" % row["rtt_minus_2base_minus_qsum_ms"]
                    if row["rtt_minus_2base_minus_qsum_ms"] is not None
                    else "n/a"
                ),
                "%.2f" % row["loss_pct"] if row["loss_pct"] is not None else "n/a",
                row["path"],
            )
        )

    pairs = [
        (row["sum_qdelay_ms"], row["rtt_avg_ms"])
        for row in runs
        if row["rtt_avg_ms"] is not None
    ]
    print()
    print("=" * 82)
    print("Additivity Check")
    print("=" * 82)
    if len(pairs) >= 2:
        xs = [x for x, _ in pairs]
        ys = [y for _, y in pairs]
        print("corr(sum_qdelay_ms, path_rtt_avg_ms) = %.4f" % corr(xs, ys))
        residuals = [
            row["rtt_minus_2base_minus_qsum_ms"]
            for row in runs
            if row["rtt_minus_2base_minus_qsum_ms"] is not None
        ]
        if residuals:
            arr = np.asarray(residuals, dtype=float)
            print(
                "residual mean=%.3f ms  std=%.3f ms  max_abs=%.3f ms"
                % (float(np.mean(arr)), float(np.std(arr)), float(np.max(np.abs(arr))))
            )
    else:
        print("Need at least two runs/rates to compute correlation.")
    print()
    print("Interpretation:")
    print("  high correlation -> additive link-delay model is plausible")
    print("  large residuals  -> backpressure, shaping, or bottleneck effects matter")


if __name__ == "__main__":
    main()

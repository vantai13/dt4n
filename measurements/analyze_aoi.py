#!/usr/bin/env python3
"""Analyze Lesson 9.0c AoI calibration output.

Checks:
1. AoI/error by controlled load mode.
2. Whether ``abs_error ~= aoi_s * du_dt`` is a useful no-fit predictor.
3. Whether AoI is negatively correlated with du/dt under delta sync.
4. Whether sequential kernel/Ditto reads introduce too much measurement noise.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from typing import Iterable, List, Mapping

import numpy as np


def parse_float(row: Mapping[str, str], key: str):
    value = row.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_rows(path: str):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            row = dict(raw)
            row["ditto_ok"] = int(float(row.get("ditto_ok") or 0))
            for key in [
                "t_rel",
                "offered_mbps",
                "util_kernel",
                "util_ditto",
                "aoi_s",
                "error",
                "abs_error",
                "du_dt",
                "error_pred",
                "read_gap_s",
            ]:
                row[key] = parse_float(raw, key)
            rows.append(row)
    return rows


def mean(values: Iterable[float]) -> float:
    values = [v for v in values if v is not None]
    return float(sum(values) / len(values)) if values else float("nan")


def max_or_nan(values: Iterable[float]) -> float:
    values = [v for v in values if v is not None]
    return float(max(values)) if values else float("nan")


def corr(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 2 or len(ys) < 2:
        return float("nan")
    if np.std(xs) == 0.0 or np.std(ys) == 0.0:
        return float("nan")
    return float(np.corrcoef(np.asarray(xs), np.asarray(ys))[0, 1])


def r2_no_fit(pred: List[float], truth: List[float]) -> float:
    if not pred or not truth:
        return float("nan")
    y = np.asarray(truth, dtype=float)
    x = np.asarray(pred, dtype=float)
    ss_res = float(np.sum((y - x) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    if ss_tot == 0.0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def print_mode_table(rows) -> None:
    by_mode = defaultdict(list)
    for row in rows:
        by_mode[row["mode"]].append(row)

    header = (
        "mode      n  aoi_mean  aoi_max  du_dt_mean  err_mean  err_max"
    )
    print(header)
    print("-" * len(header))
    for mode in sorted(by_mode):
        items = by_mode[mode]
        print(
            "%-7s %4d %9.4f %8.4f %11.4f %9.4f %8.4f"
            % (
                mode,
                len(items),
                mean(row["aoi_s"] for row in items),
                max_or_nan(row["aoi_s"] for row in items),
                mean(row["du_dt"] for row in items),
                mean(row["abs_error"] for row in items),
                max_or_nan(row["abs_error"] for row in items),
            )
        )


def parse_args(argv: Iterable[str] | None = None):
    ap = argparse.ArgumentParser(description="Analyze Lesson 9.0c AoI CSV")
    ap.add_argument("--csv", default="results/calib/raw_aoi_routing.csv")
    return ap.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    rows = [
        row
        for row in load_rows(args.csv)
        if row["ditto_ok"] == 1
        and row["aoi_s"] is not None
        and row["error"] is not None
    ]

    print("=" * 70)
    print("1) AoI by mode")
    print("=" * 70)
    print_mode_table(rows)
    print()
    print("Expected if differ.py ignores tSource-only deltas:")
    print("  static: du_dt near 0 -> high aoi_max, low error")
    print("  ramp:   higher du_dt -> lower AoI, higher error")

    print()
    print("=" * 70)
    print("2) Hypothesis: abs_error ~= aoi_s * du_dt")
    print("=" * 70)
    pred_pairs = [
        (row["error_pred"], row["abs_error"])
        for row in rows
        if row["error_pred"] is not None and row["abs_error"] is not None
    ]
    if len(pred_pairs) > 10:
        xs = [p for p, _ in pred_pairs]
        ys = [y for _, y in pred_pairs]
        r = corr(xs, ys)
        print("  n=%d  corr(pred, actual) = %.4f" % (len(xs), r))
        print("  R2 no-fit pred=actual   = %.4f" % r2_no_fit(xs, ys))
        if r > 0.7:
            print("  -> Hypothesis is useful: calibrate wrapper with measured du_dt.")
        else:
            print("  -> Hypothesis is weak: investigate nonlinear delta-sync effects.")
    else:
        print("  Not enough rows with error_pred.")

    print()
    print("=" * 70)
    print("3) Correlation: AoI vs du_dt")
    print("=" * 70)
    corr_pairs = [
        (row["aoi_s"], row["du_dt"])
        for row in rows
        if row["aoi_s"] is not None and row["du_dt"] is not None
    ]
    if len(corr_pairs) > 10:
        aoi = [x for x, _ in corr_pairs]
        du_dt = [y for _, y in corr_pairs]
        r = corr(aoi, du_dt)
        print("  corr(aoi_s, du_dt) = %+.4f" % r)
        if r < -0.3:
            print("  -> Negative correlation: fast-changing util has lower AoI.")
            print("     Delta sync is content-aware; independent-AoI wrappers are wrong.")
        elif abs(r) < 0.3:
            print("  -> Near independent: the current wrapper may be acceptable.")
        else:
            print("  -> Positive correlation: inspect collector/pusher behavior.")
    else:
        print("  Not enough rows with du_dt.")

    print()
    print("=" * 70)
    print("4) Measurement noise from read_gap")
    print("=" * 70)
    read_gap_mean = mean(row["read_gap_s"] for row in rows)
    du_dt_mean = mean(row["du_dt"] for row in rows)
    abs_err_mean = mean(row["abs_error"] for row in rows)
    fake_error = read_gap_mean * du_dt_mean
    ratio = fake_error / max(abs_err_mean, 1e-9)
    print("  read_gap mean      = %.4f s" % read_gap_mean)
    print("  du_dt mean         = %.4f /s" % du_dt_mean)
    print("  fake read error    = %.5f" % fake_error)
    print("  abs_error mean     = %.5f" % abs_err_mean)
    print("  noise/signal       = %.1f%%" % (100.0 * ratio))
    if ratio > 0.2:
        print("  WARNING: measurement noise is high; reduce --interval or read faster.")


if __name__ == "__main__":
    main()

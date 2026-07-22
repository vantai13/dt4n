#!/usr/bin/env python3
"""Summarize eval_paired.py CSVs across agent seeds.

The paired eval CSV stores one row per episode. This script first averages
episodes within each agent seed and z, then reports seed-level statistics.
It also subtracts each seed's z=0 VoI to expose the staleness-dependent part:

    VoI_corrected(z) = VoI(z) - VoI(z=0)
"""

from __future__ import annotations

import argparse
import csv
import glob
import math
import os
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats


SEED_RE = re.compile(r"paired_seed(\d+)_")


def mean(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    return float(arr.mean()) if len(arr) else float("nan")


def as_float(value) -> float:
    text = str(value).strip()
    if text == "True":
        return 1.0
    if text == "False":
        return 0.0
    return float(text)


def se(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) <= 1:
        return 0.0
    return float(arr.std(ddof=1) / math.sqrt(len(arr)))


def parse_cases(text: str | None) -> set[str] | None:
    if not text or text == "all":
        return None
    return {item.strip() for item in text.split(",") if item.strip()}


def seed_from_path(path: str) -> int:
    match = SEED_RE.search(os.path.basename(path))
    if not match:
        raise ValueError(f"cannot infer seed from path: {path}")
    return int(match.group(1))


def load_episode_rows(pattern: str, cases: set[str] | None) -> list[dict]:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"no CSV files match {pattern!r}")

    rows = []
    for path in paths:
        seed = seed_from_path(path)
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                if cases is not None and row.get("case") not in cases:
                    continue
                row["agent_seed"] = seed
                rows.append(row)
    if not rows:
        raise RuntimeError("no rows left after case filtering")
    return rows


def bool_rate(rows: list[dict], key: str, value: str) -> float:
    return mean(row.get(key) == value for row in rows)


def summarize_seed_z(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(int(row["agent_seed"]), int(row["z"]))].append(row)

    out = []
    for (seed, z), group in sorted(grouped.items()):
        out.append({
            "agent_seed": seed,
            "z": z,
            "n_rows": len(group),
            "voi": mean(float(row["diff"]) for row in group),
            "aoi_return": mean(float(row["aoi_return"]) for row in group),
            "mask_return": mean(float(row["mask_return"]) for row in group),
            "aoi_wrong": mean(as_float(row["aoi_decision_wrong"]) for row in group),
            "mask_wrong": mean(as_float(row["mask_decision_wrong"]) for row in group),
            "target_f": bool_rate(group, "aoi_decision_target", "F"),
            "aoi_f": bool_rate(group, "aoi_decision_choice", "F"),
            "mask_f": bool_rate(group, "mask_decision_choice", "F"),
            "pre_diff": mean(
                row.get("aoi_pre_decision_path")
                != row.get("mask_pre_decision_path")
                for row in group
            ),
        })

    z0_by_seed = {
        row["agent_seed"]: row["voi"]
        for row in out
        if row["z"] == 0
    }
    missing = sorted({row["agent_seed"] for row in out} - set(z0_by_seed))
    if missing:
        raise RuntimeError(f"missing z=0 rows for seeds: {missing}")

    for row in out:
        row["voi_z0"] = z0_by_seed[row["agent_seed"]]
        row["voi_corr"] = row["voi"] - row["voi_z0"]
    return out


def summarize_by_z(seed_z_rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in seed_z_rows:
        grouped[int(row["z"])].append(row)

    out = []
    for z, group in sorted(grouped.items()):
        corr = [float(row["voi_corr"]) for row in group]
        if z == 0 or len(corr) <= 1 or np.std(corr, ddof=1) <= 1e-12:
            t_stat, p_value = 0.0, 1.0
        else:
            t_stat, p_value = stats.ttest_1samp(corr, 0.0)
        out.append({
            "z": z,
            "n_seed": len(group),
            "voi_raw_mean": mean(row["voi"] for row in group),
            "voi_raw_se": se(row["voi"] for row in group),
            "voi_corr_mean": mean(corr),
            "voi_corr_se": se(corr),
            "t_corr": float(t_stat),
            "p_corr": float(p_value),
            "aoi_return": mean(row["aoi_return"] for row in group),
            "mask_return": mean(row["mask_return"] for row in group),
            "aoi_wrong": mean(row["aoi_wrong"] for row in group),
            "mask_wrong": mean(row["mask_wrong"] for row in group),
            "target_f": mean(row["target_f"] for row in group),
            "aoi_f": mean(row["aoi_f"] for row in group),
            "mask_f": mean(row["mask_f"] for row in group),
            "pre_diff": mean(row["pre_diff"] for row in group),
        })
    return out


def write_csv(path: str | None, rows: list[dict]) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[CSV] wrote {out}")


def print_table(rows: list[dict]) -> None:
    print(
        f"{'z':>3} {'n':>3} {'VoI_raw':>9} {'SE':>8} "
        f"{'VoI_corr':>10} {'SE':>8} {'p':>8} "
        f"{'AoI_wrong':>10} {'mask_wrong':>10} "
        f"{'targetF':>8} {'AoI_F':>8} {'mask_F':>8} {'preDiff':>8}"
    )
    for row in rows:
        print(
            f"{row['z']:3d} {row['n_seed']:3d} "
            f"{row['voi_raw_mean']:+9.4f} {row['voi_raw_se']:8.4f} "
            f"{row['voi_corr_mean']:+10.4f} {row['voi_corr_se']:8.4f} "
            f"{row['p_corr']:8.4f} "
            f"{row['aoi_wrong']:10.4f} {row['mask_wrong']:10.4f} "
            f"{row['target_f']:8.4f} {row['aoi_f']:8.4f} "
            f"{row['mask_f']:8.4f} {row['pre_diff']:8.4f}"
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--glob",
        default="results/eval_asym_300/paired_seed*_probe.csv",
        help="CSV pattern produced by eval_paired.py",
    )
    parser.add_argument(
        "--cases",
        default="probe_C,probe_D",
        help="comma-separated cases to include, or 'all'",
    )
    parser.add_argument(
        "--out",
        default="results/eval_asym_300/summary_probe_5seed.csv",
    )
    parser.add_argument(
        "--seed-out",
        default="results/eval_asym_300/seed_z_probe_5seed.csv",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    rows = load_episode_rows(args.glob, parse_cases(args.cases))
    seed_z_rows = summarize_seed_z(rows)
    summary = summarize_by_z(seed_z_rows)

    print(f"files={len(sorted(glob.glob(args.glob)))} cases={args.cases}")
    print_table(summary)

    zs = np.asarray([row["z"] for row in summary], dtype=float)
    corr = np.asarray([row["voi_corr_mean"] for row in summary], dtype=float)
    slope, _intercept, r_value, p_value, _se_slope = stats.linregress(zs, corr)
    print(f"\ncorrected slope = {slope:+.5f} (p={p_value:.4f}, r={r_value:.3f})")

    write_csv(args.out, summary)
    write_csv(args.seed_out, seed_z_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compare exact offered load with counter-based measured load."""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Dict, Mapping

import numpy as np

from measurements.measure_tau import read_trace
from twin import topology_v7 as T7


def _drop(xs, frac: float):
    arr = np.asarray(xs, dtype=float)
    return arr[int(len(arr) * frac):]


def summarize_pair(offered, measured, warmup_frac: float = 0.2) -> Dict[str, object]:
    off = _drop(offered, warmup_frac)
    mea = _drop(measured, warmup_frac)
    if len(off) == 0 or len(mea) == 0:
        raise ValueError("empty offered/measured series after warm-up")

    sigma_off = float(off.std())
    sigma_mea = float(mea.std())
    mean_off = float(off.mean())
    mean_mea = float(mea.mean())
    noise_var = max(0.0, sigma_mea**2 - sigma_off**2)
    mean_ratio = mean_mea / mean_off if mean_off > 0 else float("inf")
    sigma_ratio = sigma_mea / sigma_off if sigma_off > 0 else float("inf")
    return {
        "rho_offered_mean": mean_off,
        "rho_measured_mean": mean_mea,
        "mean_log2_ratio": math.log2(mean_ratio) if mean_ratio > 0 else float("inf"),
        "sigma_offered": sigma_off,
        "sigma_measured": sigma_mea,
        "sigma_log2_ratio": math.log2(sigma_ratio) if sigma_ratio > 0 else float("inf"),
        "noise_sigma_est": math.sqrt(noise_var),
        "noise_var_share_of_measured": (
            noise_var / sigma_mea**2 if sigma_mea > 0 else None
        ),
        "n_offered": int(len(off)),
        "n_measured": int(len(mea)),
    }


def compare(offered_path: str, measured_path: str, warmup_frac: float = 0.2):
    offered, offered_dt = read_trace(offered_path)
    measured, measured_dt = read_trace(measured_path)
    out = {}
    for link in T7.LINK_NAMES:
        if link in offered and link in measured:
            out[link] = summarize_pair(
                offered[link],
                measured[link],
                warmup_frac=warmup_frac,
            )
    return out, offered_dt, measured_dt


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def print_report(result: Mapping[str, Mapping[str, object]], offered_dt: float, measured_dt: float) -> None:
    print("\n=== offered vs measured rho ===")
    print("  offered dt = %.3f ms | measured window = %.3f ms" % (
        offered_dt * 1000.0,
        measured_dt * 1000.0,
    ))
    for link in T7.LINK_NAMES:
        if link not in result:
            continue
        row = result[link]
        share = row["noise_var_share_of_measured"]
        print(
            "  %s: mean %.4f -> %.4f | sigma %.4f -> %.4f | noise_sigma %.4f | noise_var_share %s"
            % (
                link,
                float(row["rho_offered_mean"]),
                float(row["rho_measured_mean"]),
                float(row["sigma_offered"]),
                float(row["sigma_measured"]),
                float(row["noise_sigma_est"]),
                "n/a" if share is None else "%.2f" % float(share),
            )
        )


def parse_args():
    p = argparse.ArgumentParser(description="Compare rho_offered and rho_measured traces")
    p.add_argument("--offered", default="results/SUPERSEDED/phase-20/rho_offered.csv")
    p.add_argument("--measured", default="results/SUPERSEDED/phase-20/rho_measured.csv")
    p.add_argument("--warmup-frac", type=float, default=0.2)
    p.add_argument("--out", default="results/SUPERSEDED/phase-20/estimator_compare.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    result, offered_dt, measured_dt = compare(
        args.offered,
        args.measured,
        warmup_frac=args.warmup_frac,
    )
    print_report(result, offered_dt, measured_dt)
    write_json(
        args.out,
        {
            "offered": args.offered,
            "measured": args.measured,
            "offered_dt_s": offered_dt,
            "measured_dt_s": measured_dt,
            "warmup_frac": args.warmup_frac,
            "by_link": result,
        },
    )
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()

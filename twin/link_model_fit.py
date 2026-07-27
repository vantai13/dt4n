#!/usr/bin/env python3
"""Fit M/M/1, M/D/1 and free-form queueing curves to calibration data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


def _float(row: Dict[str, str], key: str, default=None):
    value = row.get(key, "")
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_rows(path: str) -> List[Dict[str, float]]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            bw = _float(raw, "cfg_bw_mbps", _float(raw, "bw_mbps"))
            delay = _float(raw, "cfg_delay_ms", _float(raw, "delay_ms"))
            queue = _float(raw, "cfg_queue_pkts")
            queue_target = _float(raw, "cfg_queue_target_ms")
            rho_offered = _float(raw, "rho_offered", _float(raw, "offered_load_frac"))
            rho_measured = _float(raw, "rho_measured", _float(raw, "utilization"))
            q_delay = _float(raw, "q_delay_ms")
            loss = _float(raw, "loss_rate", 0.0)
            if None in (bw, delay, rho_offered, rho_measured, q_delay):
                continue
            rows.append(
                {
                    "cfg_bw_mbps": float(bw),
                    "cfg_delay_ms": float(delay),
                    "cfg_queue_pkts": float(queue) if queue is not None else None,
                    "cfg_queue_target_ms": float(queue_target) if queue_target is not None else None,
                    "rho_offered": float(rho_offered),
                    "rho_measured": float(rho_measured),
                    "q_delay_ms": float(q_delay),
                    "loss_rate": float(loss or 0.0),
                }
            )
    return rows


def r_squared(y, yhat):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def fit_linear_scale(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    denom = float(np.sum(x * x))
    if denom <= 0:
        return 0.0
    return float(np.sum(x * y) / denom)


def summarize_fit(y, yhat, params):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    residual = y - yhat
    return {
        "params": [float(p) for p in params],
        "r2": float(r_squared(y, yhat)),
        "rmse": float(np.sqrt(np.mean(residual**2))) if len(y) else float("nan"),
        "residual_mean": float(np.mean(residual)) if len(y) else float("nan"),
        "max_abs_residual": float(np.max(np.abs(residual))) if len(y) else float("nan"),
    }


def group_curve(rows: Sequence[Dict[str, float]]):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["rho_offered"]].append(row)

    curve = []
    for rho_offered in sorted(grouped):
        values = grouped[rho_offered]
        q_values = np.array([item["q_delay_ms"] for item in values], dtype=float)
        curve.append(
            {
                "rho_offered": float(rho_offered),
                "rho": float(np.mean([item["rho_measured"] for item in values])),
                "q_delay": float(np.mean(q_values)),
                "q_delay_std": float(np.std(q_values, ddof=1)) if len(q_values) > 1 else 0.0,
                "loss": float(np.mean([item["loss_rate"] for item in values])),
                "n": int(len(values)),
            }
        )
    return curve


def _basis_mm1(rho):
    rho = np.clip(np.asarray(rho, dtype=float), 0.0, 0.99)
    return rho / np.maximum(1.0 - rho, 1e-9)


def _basis_md1(rho):
    return 0.5 * _basis_mm1(rho)


def _basis_free(rho, exponent):
    rho = np.clip(np.asarray(rho, dtype=float), 0.0, 0.99)
    return rho / np.power(np.maximum(1.0 - rho, 1e-9), exponent)


def fit_free_form(rho, y):
    best = None
    # Fine enough for calibration triage without scipy. The report tells us
    # whether M/M/1-like b=1 is plausible or whether the shape is different.
    for exponent in np.linspace(0.25, 3.0, 276):
        x = _basis_free(rho, exponent)
        scale = fit_linear_scale(x, y)
        yhat = scale * x
        sse = float(np.sum((np.asarray(y) - yhat) ** 2))
        if best is None or sse < best[0]:
            best = (sse, scale, float(exponent), yhat)
    _sse, scale, exponent, yhat = best
    return summarize_fit(y, yhat, [scale, exponent])


def fit_one_config(rows: Sequence[Dict[str, float]], bw: float, delay: float, queue_pkts):
    sub = [
        row for row in rows
        if row["cfg_bw_mbps"] == bw
        and row["cfg_delay_ms"] == delay
        and row["cfg_queue_pkts"] == queue_pkts
        and row["rho_measured"] < 0.97
    ]
    all_for_config = [
        row for row in rows
        if row["cfg_bw_mbps"] == bw
        and row["cfg_delay_ms"] == delay
        and row["cfg_queue_pkts"] == queue_pkts
    ]
    curve = group_curve(sub)
    rho = np.array([point["rho"] for point in curve], dtype=float)
    y = np.array([point["q_delay"] for point in curve], dtype=float)

    out = {
        "bw_mbps": float(bw),
        "delay_ms": float(delay),
        "queue_pkts": int(queue_pkts) if queue_pkts is not None else None,
        "queue_target_ms": (
            float(next((row["cfg_queue_target_ms"] for row in all_for_config
                        if row.get("cfg_queue_target_ms") is not None), float("nan")))
            if all_for_config else float("nan")
        ),
        "n_points": int(len(curve)),
        "noise_floor_ms": float(np.nanmean([point["q_delay_std"] for point in curve])) if curve else float("nan"),
        "curve": curve,
    }

    if len(curve) == 0:
        out.update({
            "mm1": {"error": "no points with rho_measured < 0.97"},
            "md1": {"error": "no points with rho_measured < 0.97"},
            "free": {"error": "no points with rho_measured < 0.97"},
            "loss_threshold_measured": None,
        })
        return out

    mm1_x = _basis_mm1(rho)
    mm1_d = fit_linear_scale(mm1_x, y)
    out["mm1"] = summarize_fit(y, mm1_d * mm1_x, [mm1_d])

    md1_x = _basis_md1(rho)
    md1_d = fit_linear_scale(md1_x, y)
    out["md1"] = summarize_fit(y, md1_d * md1_x, [md1_d])

    out["free"] = fit_free_form(rho, y)

    lossy_curve = group_curve(all_for_config)
    lossy = [point for point in lossy_curve if point["loss"] > 0.01]
    out["loss_threshold_measured"] = (
        float(min(point["rho"] for point in lossy)) if lossy else None
    )
    return out


def grouped_configs(rows: Iterable[Dict[str, float]]):
    return sorted({
        (row["cfg_bw_mbps"], row["cfg_delay_ms"], row["cfg_queue_pkts"])
        for row in rows
    })


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def _score(model):
    return model.get("r2", float("nan")) if isinstance(model, dict) else float("nan")


def write_report(path: str, profiles: Sequence[Dict[str, object]], source: str) -> None:
    ensure_parent(path)
    lines = [
        "# Lesson 9.0 Link Calibration Fit",
        "",
        "* Source: `%s`" % source,
        "* Fit region: `rho_measured < 0.97`",
        "",
        "| bw | delay | queue | target ms | M/M/1 R2 | M/D/1 R2 | Free R2 | free b | noise ms | loss threshold |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in profiles:
        free = profile.get("free", {})
        free_params = free.get("params", [float("nan"), float("nan")])
        lines.append(
            "| %.3g | %.3g | %s | %.3g | %.4f | %.4f | %.4f | %.3f | %.3f | %s |"
            % (
                profile["bw_mbps"],
                profile["delay_ms"],
                profile.get("queue_pkts"),
                profile.get("queue_target_ms", float("nan")),
                _score(profile.get("mm1", {})),
                _score(profile.get("md1", {})),
                _score(free),
                free_params[1] if len(free_params) > 1 else float("nan"),
                profile.get("noise_floor_ms", float("nan")),
                (
                    "%.4f" % profile["loss_threshold_measured"]
                    if profile.get("loss_threshold_measured") is not None
                    else "n/a"
                ),
            )
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


def parse_args():
    p = argparse.ArgumentParser(description="Fit Lesson 9.0 link models")
    p.add_argument("--csv", default="results/calib/raw_sweep_2node.csv")
    p.add_argument("--out-json", default="results/calib/link_profiles.json")
    p.add_argument("--out-report", default="results/calib/fit_report.md")
    return p.parse_args()


def main():
    args = parse_args()
    rows = read_rows(args.csv)
    if not rows:
        raise SystemExit("no usable rows in %s" % args.csv)

    profiles = [
        fit_one_config(rows, bw=bw, delay=delay, queue_pkts=queue_pkts)
        for bw, delay, queue_pkts in grouped_configs(rows)
    ]
    payload = {
        "profiles": profiles,
        "source": args.csv,
        "note": "Fit on rho_measured < 0.97. See fit_report.md.",
    }
    write_json(args.out_json, payload)
    write_report(args.out_report, profiles, args.csv)

    print("%-6s %-7s %-6s | %-12s %-12s %-12s | %-10s" % (
        "bw", "delay", "queue", "M/M/1 R2", "M/D/1 R2", "Free R2", "loss_thr"))
    for profile in profiles:
        print(
            "%-6s %-7s %-6s | %-12.4f %-12.4f %-12.4f | %s"
            % (
                profile["bw_mbps"],
                profile["delay_ms"],
                profile.get("queue_pkts"),
                _score(profile.get("mm1", {})),
                _score(profile.get("md1", {})),
                _score(profile.get("free", {})),
                profile.get("loss_threshold_measured"),
            )
        )
        free = profile.get("free", {})
        if "params" in free and len(free["params"]) > 1:
            print(
                "       noise_floor = %.3f ms | free exponent b = %.3f"
                % (profile["noise_floor_ms"], free["params"][1])
            )
    print("wrote %s and %s" % (args.out_json, args.out_report))


if __name__ == "__main__":
    main()

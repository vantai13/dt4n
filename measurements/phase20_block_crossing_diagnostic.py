#!/usr/bin/env python3
"""Block-level mechanism diagnostic for Phase 20 decision errors."""

from __future__ import annotations

import argparse
import json
import os
from typing import List

import numpy as np

from measurements.decision_error import (
    DEFAULT_D_SYNC_S,
    DEFAULT_SYNC_PERIOD_S,
    DEFAULT_TAU_CORE_S,
    DEFAULT_Z_LIST_S,
    crossed_operational,
    drop_warmup_matrix,
    evaluate,
    load_frozen_calibration,
    read_trace_matrix,
)
from twin import topology_v7 as T7


DEFAULT_CORE_LINKS = ("ac", "ad", "bc", "bd")


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_csv_list(text: str) -> List[str]:
    vals = [part.strip() for part in str(text).split(",") if part.strip()]
    if not vals:
        raise ValueError("expected a comma-separated list")
    return vals


def parse_float_list(text: str) -> List[float]:
    return [float(x) for x in parse_csv_list(text)]


def corr(xs: np.ndarray, ys: np.ndarray) -> float:
    if len(xs) != len(ys):
        raise ValueError("length mismatch: %d vs %d" % (len(xs), len(ys)))
    if len(xs) < 2 or float(np.std(xs)) == 0.0 or float(np.std(ys)) == 0.0:
        return float("nan")
    return float(np.corrcoef(xs, ys)[0, 1])


def fisher_ci95(r: float, n: int) -> dict:
    if n <= 3 or not np.isfinite(r):
        return {"lo": None, "hi": None, "n": int(n), "method": "fisher_z"}
    clipped = float(np.clip(r, -0.999999999, 0.999999999))
    z = float(np.arctanh(clipped))
    se = 1.0 / float(np.sqrt(n - 3))
    return {
        "lo": float(np.tanh(z - 1.96 * se)),
        "hi": float(np.tanh(z + 1.96 * se)),
        "n": int(n),
        "method": "fisher_z",
    }


def summarize_corr(name: str, xs: np.ndarray, ys: np.ndarray) -> dict:
    r = corr(xs, ys)
    ci = fisher_ci95(r, len(xs))
    r2_ci = {"lo": None, "hi": None}
    if ci["lo"] is not None and ci["hi"] is not None:
        r2_ci = {"lo": float(min(ci["lo"] ** 2, ci["hi"] ** 2)), "hi": float(max(ci["lo"] ** 2, ci["hi"] ** 2))}
    return {"name": name, "r": r, "r_squared": float(r * r), "r_squared_ci95": r2_ci, "ci95": ci}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--traces", required=True, help="Comma-separated offered rho traces.")
    p.add_argument("--calibration", default="results/phase-20/decision_error_offered.json")
    p.add_argument("--dt", type=float, default=0.010)
    p.add_argument("--warmup-frac", type=float, default=0.2)
    p.add_argument("--tau-core", type=float, default=DEFAULT_TAU_CORE_S)
    p.add_argument("--sync-period", type=float, default=DEFAULT_SYNC_PERIOD_S)
    p.add_argument("--d-sync", type=float, default=DEFAULT_D_SYNC_S)
    p.add_argument("--z-list", default=",".join("%g" % z for z in DEFAULT_Z_LIST_S))
    p.add_argument("--core-links", default=",".join(DEFAULT_CORE_LINKS))
    p.add_argument("--out", default="results/phase-20/block_crossing_diagnostic_n5.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    traces = parse_csv_list(args.traces)
    z_list = parse_float_list(args.z_list)
    core_links = parse_csv_list(args.core_links)
    core_idx = [T7.LINK_NAMES.index(link) for link in core_links]
    calibration = load_frozen_calibration(args.calibration)

    block_rows = []
    for trace_id, path in enumerate(traces):
        rho_raw, dt_s = read_trace_matrix(path, dt_s=args.dt)
        rho = drop_warmup_matrix(rho_raw, args.warmup_frac)
        evaluation = evaluate(
            rho,
            dt_s=dt_s,
            w_loss=float(calibration["w_loss"]),
            t_delay_ms=float(calibration["t_delay_ms"]),
            t_loss=float(calibration["t_loss"]),
            z_list_s=z_list,
            sync_period_s=args.sync_period,
            d_sync_s=args.d_sync,
        )
        rows = evaluation["_rows"]
        age = evaluation["_age"]
        wrong = np.asarray(evaluation["_wrong_flags"]["operational"], dtype=bool)
        crossed = crossed_operational(rho, rows, age)
        base_viol = np.asarray(evaluation["_arrays"]["base_violation"], dtype=bool)
        twin_viol = np.asarray(evaluation["_twin_viol_flags"]["operational"], dtype=bool)
        block_len = max(1, int(round(5.0 * args.tau_core / dt_s)))
        n_blocks = len(wrong) // block_len
        for block_id in range(n_blocks):
            start = block_id * block_len
            stop = start + block_len
            block_rows.append(
                {
                    "trace_id": trace_id,
                    "trace": path,
                    "block_id": block_id,
                    "block_len_samples": int(block_len),
                    "block_len_s": float(block_len * dt_s),
                    "err": float(wrong[start:stop].mean()),
                    "crossing_rate": float(crossed[start:stop].mean()),
                    "rho_core_mean": float(rho[rows[start:stop]][:, core_idx].mean()),
                    "d_sla": float(twin_viol[start:stop].mean() - base_viol[start:stop].mean()),
                    "base_violation": float(base_viol[start:stop].mean()),
                    "twin_violation": float(twin_viol[start:stop].mean()),
                }
            )

    crossing = np.asarray([row["crossing_rate"] for row in block_rows], dtype=float)
    rho_core = np.asarray([row["rho_core_mean"] for row in block_rows], dtype=float)
    err = np.asarray([row["err"] for row in block_rows], dtype=float)
    d_sla = np.asarray([row["d_sla"] for row in block_rows], dtype=float)
    result = {
        "n_blocks": len(block_rows),
        "n_traces": len(traces),
        "tau_core_s": float(args.tau_core),
        "warmup_frac": float(args.warmup_frac),
        "core_links": core_links,
        "correlations": {
            "crossing_rate_vs_err": summarize_corr("crossing_rate_vs_err", crossing, err),
            "crossing_rate_vs_d_sla": summarize_corr("crossing_rate_vs_d_sla", crossing, d_sla),
            "rho_core_mean_vs_err": summarize_corr("rho_core_mean_vs_err", rho_core, err),
            "rho_core_mean_vs_d_sla": summarize_corr("rho_core_mean_vs_d_sla", rho_core, d_sla),
            "rho_core_mean_vs_crossing_rate": summarize_corr(
                "rho_core_mean_vs_crossing_rate", rho_core, crossing
            ),
        },
        "means": {
            "crossing_rate": float(crossing.mean()),
            "rho_core_mean": float(rho_core.mean()),
            "err": float(err.mean()),
            "d_sla": float(d_sla.mean()),
        },
        "blocks": block_rows,
    }
    write_json(args.out, result)
    print("wrote %s" % args.out)
    for key, row in result["correlations"].items():
        ci = row["ci95"]
        print("%s: r=%.3f CI95[%.3f, %.3f]" % (key, row["r"], ci["lo"], ci["hi"]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Diagnose whether Phase 20 between-trace variance tracks core-link load."""

from __future__ import annotations

import argparse
import json
import os
from typing import List

import numpy as np

from measurements.decision_error import drop_warmup_matrix, read_trace_matrix
from twin import topology_v7 as T7


DEFAULT_CORE_LINKS = ("ac", "ad", "bc", "bd")


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def read_json(path: str) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


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


def corr(xs: np.ndarray, ys: np.ndarray) -> float:
    if len(xs) != len(ys):
        raise ValueError("length mismatch: %d vs %d" % (len(xs), len(ys)))
    if len(xs) < 2:
        return float("nan")
    return float(np.corrcoef(xs, ys)[0, 1])


def fisher_ci95(r: float, n: int) -> dict:
    if n <= 3 or not np.isfinite(r):
        return {"lo": None, "hi": None, "n": int(n), "method": "fisher_z"}
    clipped = float(np.clip(r, -0.999999999, 0.999999999))
    z = float(np.arctanh(clipped))
    se = 1.0 / float(np.sqrt(n - 3))
    lo = float(np.tanh(z - 1.96 * se))
    hi = float(np.tanh(z + 1.96 * se))
    return {"lo": lo, "hi": hi, "n": int(n), "method": "fisher_z"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--traces",
        required=True,
        help="Comma-separated offered rho traces in the same order as the summary points.",
    )
    p.add_argument("--summary", default="results/phase-20/between_trace_summary_n5.json")
    p.add_argument("--dt", type=float, default=0.010)
    p.add_argument("--warmup-frac", type=float, default=0.2)
    p.add_argument("--core-links", default=",".join(DEFAULT_CORE_LINKS))
    p.add_argument("--out", default="results/phase-20/core_load_diagnostic_n5.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    traces = parse_csv_list(args.traces)
    core = parse_csv_list(args.core_links)
    idx = [T7.LINK_NAMES.index(link) for link in core]
    summary = read_json(args.summary)
    if not isinstance(summary, dict):
        raise ValueError("%s must contain a JSON object" % args.summary)
    errs = np.asarray(summary["err"]["points"], dtype=float)
    d_sla = np.asarray(summary["d_sla"]["points"], dtype=float)

    raw_means = []
    warm_means = []
    warm_by_link = []
    for path in traces:
        rho, dt_s = read_trace_matrix(path, dt_s=args.dt)
        raw_means.append(float(rho[:, idx].mean()))
        warm = drop_warmup_matrix(rho, args.warmup_frac)
        warm_means.append(float(warm[:, idx].mean()))
        warm_by_link.append({link: float(warm[:, T7.LINK_NAMES.index(link)].mean()) for link in core})

    raw = np.asarray(raw_means, dtype=float)
    warm = np.asarray(warm_means, dtype=float)
    r_raw_err = corr(raw, errs)
    r_raw_d_sla = corr(raw, d_sla)
    r_warm_err = corr(warm, errs)
    r_warm_d_sla = corr(warm, d_sla)
    result = {
        "core_links": core,
        "trace_paths": traces,
        "warmup_frac": float(args.warmup_frac),
        "rho_core_mean_raw": raw.tolist(),
        "rho_core_mean_after_warmup": warm.tolist(),
        "rho_core_mean_after_warmup_by_link": warm_by_link,
        "err_points": errs.tolist(),
        "d_sla_points": d_sla.tolist(),
        "corr_raw_core_mean_vs_err": r_raw_err,
        "corr_raw_core_mean_vs_err_ci95": fisher_ci95(r_raw_err, len(raw)),
        "corr_raw_core_mean_vs_d_sla": r_raw_d_sla,
        "corr_raw_core_mean_vs_d_sla_ci95": fisher_ci95(r_raw_d_sla, len(raw)),
        "corr_warm_core_mean_vs_err": r_warm_err,
        "corr_warm_core_mean_vs_err_ci95": fisher_ci95(r_warm_err, len(warm)),
        "corr_warm_core_mean_vs_d_sla": r_warm_d_sla,
        "corr_warm_core_mean_vs_d_sla_ci95": fisher_ci95(r_warm_d_sla, len(warm)),
        "diagnosis": (
            "inconclusive_with_n5_trace_level; absence of evidence is not evidence of absence; "
            "use block-level crossing-rate diagnostic for a powered mechanism check"
        ),
    }
    write_json(args.out, result)
    print("wrote %s" % args.out)
    print("rho_core_after_warmup:", np.round(warm, 5).tolist())
    print("corr rho_core vs err: %.3f" % result["corr_warm_core_mean_vs_err"])
    print("corr rho_core vs d_sla: %.3f" % result["corr_warm_core_mean_vs_d_sla"])


if __name__ == "__main__":
    main()

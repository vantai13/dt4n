#!/usr/bin/env python3
"""Estimate topology_v7 AoI parameters from frozen v1 JSONL probes."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import glob
import json
import os
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

from cert.build_calib_set_v3 import AOI_PROFILES
from measurements.aoi_probe_v7 import SCHEMA
from twin import topology_v7 as T7


OUTPUT = "results/phase-23/aoi_v7_estimates.json"
FIGURE = "results/phase-23/fig8_aoi_v7.png"


def load_probe_file(path: str) -> Tuple[Dict[str, Any], list[Dict[str, Any]]]:
    with open(path, encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if not rows or rows[0].get("schema") != SCHEMA or rows[0].get("record") != "header":
        raise ValueError("invalid AoI v7 header: %s" % path)
    probes = [row for row in rows[1:] if row.get("record") == "probe"]
    return rows[0], probes


def estimate_offsets(probes: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Fit ``aoi ~ link dummy + beta*read_pos`` and centre link effects."""
    y, link_index, position = [], [], []
    for probe in probes:
        for logical, value in probe["links"].items():
            if value.get("aoi_s") is None:
                continue
            y.append(float(value["aoi_s"]))
            link_index.append(T7.LINK_NAMES.index(logical))
            position.append(float(value["read_pos"]))
    y_arr = np.asarray(y, dtype=np.float64)
    links = np.asarray(link_index, dtype=np.int64)
    pos = np.asarray(position, dtype=np.float64)
    n_links = len(T7.LINK_NAMES)
    matrix = np.zeros((len(y_arr), n_links + 1), dtype=np.float64)
    matrix[np.arange(len(y_arr)), links] = 1.0
    matrix[:, n_links] = pos
    coef, _residuals, rank, singular = np.linalg.lstsq(matrix, y_arr, rcond=None)
    raw = coef[:n_links]
    alpha = raw - raw.mean()
    fitted = matrix @ coef
    residual = y_arr - fitted
    return {
        "offset_ms": {
            name: float(value * 1000.0)
            for name, value in zip(T7.LINK_NAMES, alpha)
        },
        "max_offset_spread_ms": float((alpha.max() - alpha.min()) * 1000.0),
        "beta_ms_per_pos": float(coef[n_links] * 1000.0),
        "mu_ms": float(raw.mean() * 1000.0),
        "design_rank": int(rank),
        "design_columns": int(matrix.shape[1]),
        "condition_number": float(singular.max() / singular.min()),
        "residual_rmse_ms": float(np.sqrt(np.mean(residual**2)) * 1000.0),
        "n": int(len(y_arr)),
    }


def _summary(values: Sequence[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "sd": float(arr.std(ddof=0)),
        "cv": float(arr.std(ddof=0) / arr.mean()),
        "p05": float(np.percentile(arr, 5)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(arr.max()),
        "n_negative": int((arr < 0.0).sum()),
    }


def effective_periods(probes: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    by_link = defaultdict(list)
    for probe in probes:
        for logical, value in probe["links"].items():
            source = value.get("t_source")
            if source is not None:
                by_link[logical].append(float(source))
    out = {}
    all_diffs = []
    for logical in T7.LINK_NAMES:
        unique = []
        for value in by_link[logical]:
            if not unique or value != unique[-1]:
                unique.append(value)
        diff = np.diff(np.asarray(unique, dtype=np.float64))
        out[logical] = {
            "n_updates": int(len(unique)),
            "median_s": None if diff.size == 0 else float(np.median(diff)),
            "max_s": None if diff.size == 0 else float(diff.max()),
        }
        all_diffs.extend(diff.tolist())
    return {
        "by_link": out,
        "median_s": None if not all_diffs else float(np.median(all_diffs)),
        "max_s": None if not all_diffs else float(max(all_diffs)),
    }


def profile_match(offsets_ms: Mapping[str, float]) -> Dict[str, Any]:
    observed = np.asarray([offsets_ms[name] for name in T7.LINK_NAMES], dtype=float)
    observed -= observed.mean()
    rows = {}
    for name in ("U0", "U1", "U2"):
        profile = np.asarray(AOI_PROFILES[name], dtype=float)
        profile -= profile.mean()
        rows[name] = float(np.sqrt(np.mean((observed - profile) ** 2)))
    best = min(rows, key=rows.get)
    return {"rmse_ms": rows, "best_profile": best}


def _pearson_aoi_rho(probes: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    aoi, rho = [], []
    for probe in probes:
        for value in probe["links"].values():
            if value.get("aoi_s") is None or value.get("rho") is None:
                continue
            aoi.append(float(value["aoi_s"]))
            rho.append(float(value["rho"]))
    if len(aoi) < 3 or np.std(rho) == 0.0:
        return {"n": len(aoi), "pearson": None}
    return {"n": len(aoi), "pearson": float(np.corrcoef(aoi, rho)[0, 1])}


def estimate(paths: Sequence[str], cycle_paths: Sequence[str] = ()) -> Dict[str, Any]:
    runs = []
    all_by_mode = defaultdict(list)
    headers = []
    for path in paths:
        header, probes = load_probe_file(path)
        headers.append(header)
        mode = str(header["mode"])
        all_by_mode[mode].extend(probes)
        values = [
            float(value["aoi_s"])
            for probe in probes
            for value in probe["links"].values()
            if value.get("aoi_s") is not None
        ]
        runs.append({
            "path": path,
            "mode": mode,
            "rho_bar": float(header["rho_bar"]),
            "repeat": int(header["repeat"]),
            "aoi": _summary(values),
            "effective_period": effective_periods(probes),
            "aoi_rho": _pearson_aoi_rho(probes),
        })

    modes = {}
    for mode, probes in all_by_mode.items():
        values = [
            float(value["aoi_s"])
            for probe in probes
            for value in probe["links"].values()
            if value.get("aoi_s") is not None
        ]
        offsets = estimate_offsets(probes)
        modes[mode] = {
            "aoi": _summary(values),
            "effective_period": effective_periods(probes),
            "offset_regression": offsets,
            "profile_match": profile_match(offsets["offset_ms"]),
            "aoi_rho": _pearson_aoi_rho(probes),
        }

    cycle_rows = []
    for path in cycle_paths:
        with open(path, encoding="utf-8") as handle:
            cycle_rows.extend(json.loads(line) for line in handle if line.strip())
    cycle_controls = {
        "n": len(cycle_rows),
        "overrun_ratio": None if not cycle_rows else float(np.mean([row["overrun"] for row in cycle_rows])),
        "clean_all_full_push": bool(all(
            row.get("mode") != "clean" or row["n_pushed"] == row["n_things"]
            for row in cycle_rows
        )),
        "lock_wait_ms_p95": None if not cycle_rows else float(np.percentile([row["lock_wait_ms"] for row in cycle_rows], 95)),
    }
    return {
        "schema": "dt4n.aoi.v7.estimates.v1",
        "status": "MEASUREMENT_ESTIMATE",
        "closes_P23A": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_files": list(paths),
        "spec_sha256_values": sorted({str(header["spec_sha256"]) for header in headers}),
        "runs": runs,
        "modes": modes,
        "cycle_controls": cycle_controls,
    }


def plot(report: Mapping[str, Any], path: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for mode, values in report["modes"].items():
        aoi = values["aoi"]
        axes[0].plot(
            [5, 50, 95, 99], [aoi["p05"], aoi["p50"], aoi["p95"], aoi["p99"]],
            marker="o", label=mode,
        )
    axes[0].set_xlabel("percentile")
    axes[0].set_ylabel("AoI (s)")
    axes[0].grid(alpha=0.25)
    axes[0].legend()
    clean = report["modes"].get("clean")
    if clean:
        offsets = clean["offset_regression"]["offset_ms"]
        axes[1].bar(T7.LINK_NAMES, [offsets[name] for name in T7.LINK_NAMES])
    axes[1].set_ylabel("counterbalanced link offset (ms)")
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--cycles", nargs="*", default=[])
    parser.add_argument("--out", default=OUTPUT)
    parser.add_argument("--figure", default=FIGURE)
    args = parser.parse_args()
    paths = sorted({path for pattern in args.input for path in glob.glob(pattern)})
    cycles = sorted({path for pattern in args.cycles for path in glob.glob(pattern)})
    report = estimate(paths, cycles)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    plot(report, args.figure)
    print(json.dumps({"modes": report["modes"], "cycle_controls": report["cycle_controls"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

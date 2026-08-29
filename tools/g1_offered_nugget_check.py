#!/usr/bin/env python3
"""Decisive pre-G-A003 check: does the offered ledger contain a nugget?"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.measurement_path_calib import estimate_nugget

INPUT = Path("results/RAW/phase-D/cellA_long/rho_offered_rep1.csv")
OUT = Path("results/SMOKE/phase-G/g1_offered_nugget_check.json")
LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
EDGE_LINKS = ("uA", "uB", "vC", "vD")
CORE_LINKS = ("ac", "ad", "bc", "bd")
SOURCE_DT_S = 0.01
TARGET_DT_S = 0.20
SAMPLES_PER_BIN = 20
N_FIT_LAGS = 8
BOUNDARY_TOLERANCE = 0.05


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_by_link(path: Path) -> dict[str, np.ndarray]:
    values: dict[str, list[float]] = {link: [] for link in LINKS}
    indices: dict[str, list[int]] = {link: [] for link in LINKS}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            link = row["link"]
            if link not in values:
                continue
            indices[link].append(int(row["sample_index"]))
            values[link].append(float(row["rho_offered"]))

    output = {}
    for link in LINKS:
        if not values[link]:
            raise ValueError(f"{path}: missing link {link}")
        expected = np.arange(len(indices[link]))
        if not np.array_equal(np.asarray(indices[link]), expected):
            raise ValueError(f"{path}: non-contiguous sample_index for {link}")
        output[link] = np.asarray(values[link], dtype=float)
    return output


def main() -> None:
    raw = load_by_link(INPUT)
    rows = {}
    for link in LINKS:
        values = raw[link]
        if len(values) % SAMPLES_PER_BIN:
            raise ValueError(
                f"{link}: {len(values)} samples not divisible by {SAMPLES_PER_BIN}"
            )
        aggregated = values.reshape(-1, SAMPLES_PER_BIN).mean(axis=1)
        estimate = estimate_nugget(aggregated, TARGET_DT_S, N_FIT_LAGS)
        rows[link] = {
            "class": "edge" if link in EDGE_LINKS else "core",
            "n_source": len(values),
            "n_aggregated": len(aggregated),
            "rho_mean": float(aggregated.mean()),
            "rho_sd": float(aggregated.std(ddof=1)),
            **estimate,
            "within_boundary_band": bool(
                abs(float(estimate["sf"]) - 1.0) <= BOUNDARY_TOLERANCE
            ),
        }

    edge_sf = np.asarray([rows[link]["sf"] for link in EDGE_LINKS], dtype=float)
    core_sf = np.asarray([rows[link]["sf"] for link in CORE_LINKS], dtype=float)
    all_boundary = all(row["within_boundary_band"] for row in rows.values())
    edge_fast_component = float(np.median(edge_sf)) < 1.0 - BOUNDARY_TOLERANCE
    if all_boundary:
        verdict = "A_OFFERED_SF_AT_BOUNDARY_MEASUREMENT_PATH_NUGGET_SUPPORTED"
    elif edge_fast_component:
        verdict = "B_OFFERED_EDGE_SF_BELOW_BOUNDARY_GENERATOR_FAST_COMPONENT_PRESENT"
    else:
        verdict = "INCONCLUSIVE_MIXED_OFFERED_SF"

    artifact = {
        "schema": "dt4n.phase_g.g1_offered_nugget_check.v1",
        "status": "PREREGISTERED_DIAGNOSTIC_EXISTING_DATA",
        "question": (
            "Does rho_offered aggregated to the measurement interval have sf~1 "
            "on all links, as required if the measured nugget belongs only to "
            "the measurement path?"
        ),
        "input": {
            "path": str(INPUT),
            "sha256": sha256(INPUT),
            "source_dt_s": SOURCE_DT_S,
            "target_dt_s": TARGET_DT_S,
            "samples_per_bin": SAMPLES_PER_BIN,
        },
        "locked_constants": {
            "n_fit_lags": N_FIT_LAGS,
            "boundary_tolerance": BOUNDARY_TOLERANCE,
            "A_rule": "all eight abs(sf_hat-1)<=0.05",
            "B_rule": "median edge sf_hat<0.95",
        },
        "per_link": rows,
        "summary": {
            "edge_sf_median": float(np.median(edge_sf)),
            "edge_sf_min": float(edge_sf.min()),
            "edge_sf_max": float(edge_sf.max()),
            "core_sf_median": float(np.median(core_sf)),
            "core_sf_min": float(core_sf.min()),
            "core_sf_max": float(core_sf.max()),
            "all_eight_within_boundary_band": all_boundary,
            "edge_fast_component_detected": edge_fast_component,
            "verdict": verdict,
            "G_A003_may_proceed_without_H6_rewrite": bool(all_boundary),
        },
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True,
                capture_output=True, text=True
            ).stdout.strip(),
            "prereg_tag": "phase-G-offered-nugget-check-prereg",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g1_offered_nugget_check.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("%5s %5s %8s %10s %10s %9s %s" % (
        "link", "class", "sf_hat", "v_hat", "sigma_hat", "tau_fit", "boundary"))
    for link in LINKS:
        row = rows[link]
        print("%5s %5s %8.4f %10.3e %10.5f %9.3f %s" % (
            link, row["class"], row["sf"], row["v"], row["sigma_true"],
            row["tau_from_fit_s"],
            "IN" if row["within_boundary_band"] else "OUT"))
    print("\nedge sf median: %.4f" % artifact["summary"]["edge_sf_median"])
    print("core sf median: %.4f" % artifact["summary"]["core_sf_median"])
    print("verdict:", verdict)
    print("G-A003 may proceed without H6 rewrite:",
          artifact["summary"]["G_A003_may_proceed_without_H6_rewrite"])
    print("artifact:", OUT)


if __name__ == "__main__":
    main()

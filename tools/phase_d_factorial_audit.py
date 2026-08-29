#!/usr/bin/env python3
"""Phase D' factorial endpoint-by-load audit over the existing 8x8 matrix.

This is a reanalysis only: it reads all 28 unordered pairs from
``link_corr_matrix.json`` and groups them by two observed design factors:

* whether the two channels share any endpoint host;
* how many channels use the low-sigma/high-virtual-flow configuration.

No Mininet process is started and no measurement is generated.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from mininet.traffic_v7 import LOAD_CHANNELS


DEFAULT_SOURCE = Path("results/LIVE/phase-23/link_corr_matrix.json")
DEFAULT_CAMPAIGN = Path("results/RAW/phase-23/aoi_v7_campaign")
DEFAULT_DESIGN_META = DEFAULT_CAMPAIGN / "meta_clean_rho0.925_rep3.json"
DEFAULT_OUT = Path("results/SMOKE/phase-D/factorial_endpoint_x_load.json")
LOW_SIGMA = 0.03
CELL_C_SIGMA = 0.10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def load_campaign_design(campaign: Path) -> dict[str, dict[str, float]]:
    """Read sigma/rho/N/tau from every CLEAN metadata file.

    Sigma must be constant for each link across the campaign. N and tau are
    summarized rather than copied from a single operating cell because the
    source correlation matrix itself pools all 15 CLEAN runs.
    """
    paths = [Path(path) for path in sorted(glob.glob(str(campaign / "meta_clean_*.json")))]
    if not paths:
        raise FileNotFoundError(f"no CLEAN metadata under {campaign}")
    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for link, profile in payload["profile"].items():
            sigma = float(profile["sigma_target"])
            rho = float(profile["rho_target"])
            n_bar = float(profile.get("n_concurrent", rho**2 / sigma**2))
            values[link]["sigma"].append(sigma)
            values[link]["rho"].append(rho)
            values[link]["n_bar"].append(n_bar)
            values[link]["tau_pred_s"].append(float(profile["tau_pred_s"]))

    summary: dict[str, dict[str, float]] = {}
    for link, fields in sorted(values.items()):
        sigmas = np.asarray(fields["sigma"], dtype=float)
        if not np.allclose(sigmas, sigmas[0], rtol=0.0, atol=1e-12):
            raise ValueError(f"sigma changes across CLEAN campaign for {link}")
        summary[link] = {
            "sigma": float(sigmas[0]),
            "rho_median": float(np.median(fields["rho"])),
            "n_bar_median": float(np.median(fields["n_bar"])),
            "n_bar_min": float(np.min(fields["n_bar"])),
            "n_bar_max": float(np.max(fields["n_bar"])),
            "tau_pred_median_s": float(np.median(fields["tau_pred_s"])),
            "tau_pred_max_s": float(np.max(fields["tau_pred_s"])),
        }
    return summary


def analyze_matrix(
    links: list[str],
    matrix: np.ndarray,
    design: Mapping[str, Mapping[str, float]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    if matrix.shape != (len(links), len(links)):
        raise ValueError("correlation matrix shape does not match links")
    if set(links) != set(LOAD_CHANNELS):
        raise ValueError("matrix links do not match traffic_v7.LOAD_CHANNELS")
    if not np.allclose(matrix, matrix.T, atol=1e-12):
        raise ValueError("correlation matrix is not symmetric")

    pairs: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for i, first in enumerate(links):
        for j in range(i + 1, len(links)):
            second = links[j]
            shared_hosts = sorted(set(LOAD_CHANNELS[first]) & set(LOAD_CHANNELS[second]))
            n_low_sigma = int(np.isclose(design[first]["sigma"], LOW_SIGMA)) + int(
                np.isclose(design[second]["sigma"], LOW_SIGMA)
            )
            row = {
                "pair": f"{first}-{second}",
                "r": float(matrix[i, j]),
                "n_low_sigma": n_low_sigma,
                "both_high_virtual_flow": bool(n_low_sigma == 2),
                "shared_host": bool(shared_hosts),
                "shared_host_names": shared_hosts,
                "n_bar_min_median": float(
                    min(design[first]["n_bar_median"], design[second]["n_bar_median"])
                ),
            }
            key = f"nlow{n_low_sigma}_shared{int(bool(shared_hosts))}"
            grouped[key].append(row)
            pairs.append(row)

    cells: dict[str, dict[str, Any]] = {}
    for key in sorted(grouped, reverse=True):
        rows = grouped[key]
        correlations = np.asarray([row["r"] for row in rows], dtype=float)
        fisher = np.arctanh(np.clip(correlations, -0.999999, 0.999999))
        cells[key] = {
            "n": len(rows),
            "mean_r": float(correlations.mean()),
            "fisher_pooled_r": float(np.tanh(fisher.mean())),
            "min_r": float(correlations.min()),
            "max_r": float(correlations.max()),
            "pairs": [row["pair"] for row in rows],
        }

    required = {
        "nlow2_shared1",
        "nlow2_shared0",
        "nlow1_shared1",
        "nlow1_shared0",
        "nlow0_shared1",
        "nlow0_shared0",
    }
    if set(cells) != required:
        raise AssertionError(f"factorial cells mismatch: {sorted(cells)}")

    high_cell = cells["nlow2_shared1"]["mean_r"]
    next_highest = max(
        cell["mean_r"] for key, cell in cells.items() if key != "nlow2_shared1"
    )
    verdict = {
        "interpretation": "POST_HOC_REANALYSIS_NOT_CONFIRMATORY",
        "H1_endpoint_only": {
            "test_cell": "nlow0_shared1",
            "observed_mean_r": cells["nlow0_shared1"]["mean_r"],
            "descriptively_refuted": bool(abs(cells["nlow0_shared1"]["mean_r"]) < 0.10),
        },
        "H2_link_dynamics_only": {
            "test_cell": "nlow2_shared0",
            "observed_mean_r": cells["nlow2_shared0"]["mean_r"],
            "descriptively_refuted": bool(abs(cells["nlow2_shared0"]["mean_r"]) < 0.10),
        },
        "H3_sampling_or_shared_transient": {
            "test_cell": "nlow2_shared0",
            "observed_mean_r": cells["nlow2_shared0"]["mean_r"],
            "descriptively_refuted": bool(abs(cells["nlow2_shared0"]["mean_r"]) < 0.10),
        },
        "H4_endpoint_x_load_interaction": {
            "test_cell": "nlow2_shared1",
            "cell_mean_r": high_cell,
            "next_highest_cell_mean_r": next_highest,
            "cell_mean_ratio": float(high_cell / next_highest),
            "descriptively_supported": bool(high_cell > 5.0 * next_highest),
            "note": "Candidate mechanism; confirmation requires preregistered cell C.",
        },
    }
    return pairs, cells, verdict


def build_artifact(source: Path, campaign: Path, design_meta: Path) -> dict[str, Any]:
    source_payload = json.loads(source.read_text(encoding="utf-8"))
    t1 = source_payload["T1_corr_matrix_within_run"]
    links = list(t1["links"])
    design = load_campaign_design(campaign)
    pairs, cells, verdict = analyze_matrix(links, np.asarray(t1["R"], dtype=float), design)

    cell_c_source = json.loads(design_meta.read_text(encoding="utf-8"))["profile"]
    cell_c = {}
    for link, profile in sorted(cell_c_source.items()):
        rho = float(profile["rho_target"])
        old_sigma = float(profile["sigma_target"])
        new_sigma = CELL_C_SIGMA if np.isclose(old_sigma, LOW_SIGMA) else old_sigma
        cell_c[link] = {
            "rho_target": rho,
            "sigma_old": old_sigma,
            "sigma_cell_c": new_sigma,
            "n_bar_old": rho**2 / old_sigma**2,
            "n_bar_cell_c": rho**2 / new_sigma**2,
            "n_bar_reduction_ratio": (new_sigma / old_sigma) ** 2,
        }

    meta_paths = [Path(path) for path in sorted(glob.glob(str(campaign / "meta_clean_*.json")))]
    return {
        "schema": "dt4n.phase_d.factorial_endpoint_x_load.v1",
        "status": "REANALYSIS_OF_EXISTING_ARTIFACT",
        "source": str(source),
        "source_sha256": sha256_file(source),
        "campaign": str(campaign),
        "campaign_meta_sha256": {str(path): sha256_file(path) for path in meta_paths},
        "design_meta_for_cell_c": str(design_meta),
        "design_meta_sha256": sha256_file(design_meta),
        "n_pairs_analyzed": len(pairs),
        "design_by_link": design,
        "cell_c_prediction_by_link": cell_c,
        "cells": cells,
        "pairs": sorted(pairs, key=lambda row: -abs(row["r"])),
        "verdict": verdict,
        "provenance": {
            "git_hash": git_value("rev-parse", "HEAD"),
            "git_dirty": bool(git_value("status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_factorial_audit.py",
            "script_sha256": sha256_file(Path(__file__)),
            "traffic_layout_source": "mininet/traffic_v7.py::LOAD_CHANNELS",
            "traffic_layout_source_sha256": sha256_file(Path("mininet/traffic_v7.py")),
        },
        "validity": {
            "role": "POST_HOC_REANALYSIS",
            "uses_all_unordered_pairs": True,
            "generates_new_measurements": False,
            "confirmatory_use_allowed": False,
            "next_confirmatory_test": "docs/phase-D/00-preregistration.md::cell-C",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--campaign", type=Path, default=DEFAULT_CAMPAIGN)
    parser.add_argument("--design-meta", type=Path, default=DEFAULT_DESIGN_META)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = build_artifact(args.source, args.campaign, args.design_meta)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cells": artifact["cells"], "verdict": artifact["verdict"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

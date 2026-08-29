#!/usr/bin/env python3
"""Retrospective censoring audit for the Phase-D cellA physical run."""
from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.g_a003_split_sample import (
    ALL_LINKS,
    EDGE_LINKS,
    K09,
    MEASURED_INPUT,
    OFFERED_INPUT,
    aggregate_offered,
    load_by_link,
    sha256,
)


OUT = Path("results/SMOKE/phase-G/g1_censoring_retro_audit.json")
G0_RHO_MAX = 0.995
G0_Z = 2.58


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def clipped_normal_sd(mean: float, sd: float, ceiling: float) -> float:
    """SD of min(X, ceiling) for X ~ Normal(mean, sd**2)."""
    alpha = (ceiling - mean) / sd
    cdf = normal_cdf(alpha)
    pdf = normal_pdf(alpha)
    first = mean * cdf - sd * pdf + ceiling * (1.0 - cdf)
    second = (
        (mean * mean + sd * sd) * cdf
        - sd * (mean + ceiling) * pdf
        + ceiling * ceiling * (1.0 - cdf)
    )
    return math.sqrt(max(second - first * first, 0.0))


def main() -> None:
    measured = load_by_link(MEASURED_INPUT, "rho")
    n = len(measured[ALL_LINKS[0]])
    offered = aggregate_offered(
        load_by_link(OFFERED_INPUT, "rho_offered"), n
    )

    rows = {}
    for link in ALL_LINKS:
        offered_mean = float(np.mean(offered[link]))
        offered_sd = float(np.std(offered[link], ddof=1))
        measured_sd = float(np.std(measured[link], ddof=1))
        alpha = (K09 - offered_mean) / offered_sd
        gaussian_censor_fraction = 1.0 - normal_cdf(alpha)
        predicted_sd = clipped_normal_sd(offered_mean, offered_sd, K09)
        sigma_max = max((G0_RHO_MAX - offered_mean) / G0_Z, 0.0)
        rows[link] = {
            "class": "edge" if link in EDGE_LINKS else "core",
            "rho_offered_mean": offered_mean,
            "sd_offered": offered_sd,
            "sd_measured": measured_sd,
            "sd_measured_over_offered": measured_sd / offered_sd,
            "empirical_censor_fraction": float(np.mean(offered[link] > K09)),
            "gaussian_censor_fraction": gaussian_censor_fraction,
            "hard_clip_predicted_sd": predicted_sd,
            "hard_clip_match_fraction": measured_sd / predicted_sd,
            "g0_sigma_max": sigma_max,
            "offered_sd_over_g0_sigma_max": (
                offered_sd / sigma_max if sigma_max > 0.0 else None
            ),
        }

    core = [rows[link] for link in ALL_LINKS if link not in EDGE_LINKS]
    artifact = {
        "schema": "dt4n.phase_g.g1_censoring_retro_audit.v1",
        "status": "RETROSPECTIVE_POST_HOC_DIAGNOSTIC",
        "model": "Y=min(X,K09), X Gaussian with observed offered mean and sd",
        "free_fitted_parameters": 0,
        "input": {
            "measured_path": str(MEASURED_INPUT),
            "offered_path": str(OFFERED_INPUT),
            "sha256": {
                "measured": sha256(MEASURED_INPUT),
                "offered": sha256(OFFERED_INPUT),
            },
            "n_aggregated": n,
        },
        "constants": {
            "K09": K09,
            "g0_rho_max": G0_RHO_MAX,
            "g0_z": G0_Z,
        },
        "per_link": rows,
        "summary": {
            "core_gaussian_censor_fraction_min": min(
                row["gaussian_censor_fraction"] for row in core
            ),
            "core_gaussian_censor_fraction_max": max(
                row["gaussian_censor_fraction"] for row in core
            ),
            "core_hard_clip_match_fraction_min": min(
                row["hard_clip_match_fraction"] for row in core
            ),
            "core_hard_clip_match_fraction_max": max(
                row["hard_clip_match_fraction"] for row in core
            ),
            "all_edge_empirical_censor_fraction_zero": all(
                rows[link]["empirical_censor_fraction"] == 0.0
                for link in EDGE_LINKS
            ),
            "additive_nugget_model_valid_on_core": False,
        },
        "interpretation_scope": (
            "Post-hoc mechanism diagnostic. It supports the censoring exclusion "
            "and G.0 retrodiction but is not an independent confirmatory test."
        ),
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True,
                capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g1_censoring_retro_audit.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("%-5s %9s %9s %9s %9s %9s" % (
        "link", "p_gauss", "sd_offer", "sd_meas", "sd_clip", "match"))
    for link in ALL_LINKS:
        row = rows[link]
        print("%-5s %9.4f %9.5f %9.5f %9.5f %8.1f%%" % (
            link,
            row["gaussian_censor_fraction"],
            row["sd_offered"],
            row["sd_measured"],
            row["hard_clip_predicted_sd"],
            100.0 * row["hard_clip_match_fraction"],
        ))
    print("artifact:", OUT)


if __name__ == "__main__":
    main()

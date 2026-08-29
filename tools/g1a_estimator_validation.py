#!/usr/bin/env python3
"""Run preregistered Phase G1-A synthetic estimator validation."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tools.measurement_path_calib import g1a_estimator_validation

OUT = Path("results/SMOKE/phase-G/g1a_estimator_validation.json")


def main() -> None:
    rows = g1a_estimator_validation()
    sf_pass = all(row["gates"]["G1-0_sf"] for row in rows)
    rho_eps_pass = all(row["gates"]["G1-0_rho_eps_raw"] for row in rows)
    artifact = {
        "schema": "dt4n.phase_g.g1a_estimator_validation.v1",
        "status": "SYNTHETIC_DIAGNOSTIC_NO_EXPERIMENTAL_DATA",
        "constants": {
            "seed": 20260902,
            "dt_s": 0.20,
            "tau_s": 3.0,
            "sigma": 0.03,
            "n_samples": 30_000,
            "n_seed": 16,
            "sf_grid": [0.30, 0.50, 0.70, 0.85, 0.95],
            "rho_eps_true": 1.0,
            "r_true": 0.0,
            "n_fit_lags": 8,
        },
        "gates": {
            "sf_bias_tolerance_relative": 0.15,
            "rho_eps_tolerance_absolute": 0.10,
            "sf_all_pass": sf_pass,
            "rho_eps_raw_all_pass": rho_eps_pass,
            "G1-0_overall_pass": bool(sf_pass and rho_eps_pass),
        },
        "rows": rows,
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "prereg_tag": "phase-G-g1a-prereg",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g1a_estimator_validation.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        "%7s | %8s %8s | %8s %8s %8s | %8s %8s | %s"
        % (
            "sf_true",
            "sf_hat",
            "bias",
            "rho_true",
            "rho_hat",
            "rho_theory",
            "leak_est",
            "leak_true",
            "gates(sf,rho)",
        )
    )
    for row in rows:
        print(
            "%7.2f | %8.3f %8.3f | %8.3f %8.3f %8.3f | %8.3f %8.3f | %s,%s"
            % (
                row["sf_true"],
                row["sf_hat_median"],
                row["sf_bias_ratio"],
                row["rho_eps_true"],
                row["rho_eps_hat_median"],
                row["raw_diff_corr_theory"],
                row["signal_leakage_ratio_median"],
                row["signal_leakage_ratio_true"],
                "PASS" if row["gates"]["G1-0_sf"] else "FAIL",
                "PASS" if row["gates"]["G1-0_rho_eps_raw"] else "FAIL",
            )
        )
    print(
        "\nG1-0 overall: %s"
        % ("PASS" if artifact["gates"]["G1-0_overall_pass"] else "FAIL")
    )
    print("artifact: %s" % OUT)


if __name__ == "__main__":
    main()

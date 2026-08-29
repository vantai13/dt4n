#!/usr/bin/env python3
"""G1-4 preregistered reanalysis using offered load as physical ground truth."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from tools.measurement_path_calib import estimate_nugget, estimate_two_band

LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
PAIRS = tuple(
    (first, second)
    for index, first in enumerate(LINKS)
    for second in LINKS[index + 1 :]
)
PRIMARY = (("uA", "uB"), ("vC", "vD"))

CELL_A = (
    "cellA_long",
    Path("results/RAW/phase-D/cellA_long/rho_measured_rep1.csv"),
    Path("results/RAW/phase-D/cellA_long/rho_offered_rep1.csv"),
)
PHASE23 = tuple(
    (
        f"phase23_rho0.925_rep{rep}",
        Path(
            "results/RAW/phase-23/aoi_v7_campaign/"
            f"rho_measured_clean_rho0.925_rep{rep}.csv"
        ),
        Path(
            "results/RAW/phase-23/aoi_v7_campaign/"
            f"rho_offered_clean_rho0.925_rep{rep}.csv"
        ),
    )
    for rep in (1, 2, 3)
)

OUT = Path("results/SMOKE/phase-G/g1_4_physical_reanalysis.json")
DT_TARGET = 0.20
OFFERED_PER_BIN = 20
N_FIT_LAGS = 8
PAIR_ERROR_MAX = 0.10
PRIMARY_R_TRUE_ABS_MAX = 0.15
PRIMARY_RHO_EPS_ERROR_FROM_ONE_MAX = 0.20
COND_MAX = 10.0

SYNTHETIC_SEED = 20260904
SYNTHETIC_N = 30_000
SYNTHETIC_N_SEED = 16
SYNTHETIC_SIGMA = 0.03
SYNTHETIC_ERROR_MAX = 0.05
SYNTHETIC_CASES = (
    (3.0, 3.0, 0.40, 0.90, 0.85, 0.85),
    (3.0, 30.0, 0.40, 0.90, 0.85, 0.40),
    (30.0, 3.0, 0.00, 1.00, 0.40, 0.85),
    (30.0, 30.0, 0.00, 1.00, 0.40, 0.40),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_wide(path: Path, value_column: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(set(LINKS) - set(frame["link"].unique()))
    if missing:
        raise ValueError(f"{path}: missing links {missing}")
    return (
        frame.pivot(index="sample_index", columns="link", values=value_column)
        .sort_index()
        .loc[:, LINKS]
        .dropna()
    )


def aggregate_offered(wide: pd.DataFrame, target_length: int) -> pd.DataFrame:
    groups = np.arange(len(wide)) // OFFERED_PER_BIN
    aggregated = wide.groupby(groups).mean()
    if len(aggregated) < target_length:
        raise ValueError(
            f"offered aggregation has {len(aggregated)} bins; need {target_length}"
        )
    return aggregated.iloc[:target_length].reset_index(drop=True)


def correlated_ar1_pair(
    n: int,
    phi_l: float,
    phi_m: float,
    target_r: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    innovation_r = target_r * (1.0 - phi_l * phi_m) / np.sqrt(
        (1.0 - phi_l**2) * (1.0 - phi_m**2)
    )
    if abs(innovation_r) > 1.0:
        raise ValueError("requested unequal-phi stationary correlation is infeasible")
    initial_l = rng.standard_normal()
    initial_m = target_r * initial_l + np.sqrt(1.0 - target_r**2) * rng.standard_normal()
    innovation_l = rng.standard_normal(n)
    innovation_m = (
        innovation_r * innovation_l
        + np.sqrt(1.0 - innovation_r**2) * rng.standard_normal(n)
    )
    left = np.empty(n)
    right = np.empty(n)
    left[0], right[0] = initial_l, initial_m
    for index in range(1, n):
        left[index] = phi_l * left[index - 1] + np.sqrt(1.0 - phi_l**2) * innovation_l[index]
        right[index] = phi_m * right[index - 1] + np.sqrt(1.0 - phi_m**2) * innovation_m[index]
    return left, right


def synthetic_generalization_control() -> dict[str, object]:
    rng = np.random.default_rng(SYNTHETIC_SEED)
    rows = []
    for tau_l, tau_m, r_true, rho_eps, sf_l, sf_m in SYNTHETIC_CASES:
        phi_l = float(np.exp(-DT_TARGET / tau_l))
        phi_m = float(np.exp(-DT_TARGET / tau_m))
        r_hats, rho_hats, conditions = [], [], []
        for _ in range(SYNTHETIC_N_SEED):
            signal_l, signal_m = correlated_ar1_pair(
                SYNTHETIC_N, phi_l, phi_m, r_true, rng
            )
            v_l = SYNTHETIC_SIGMA**2 * (1.0 / sf_l - 1.0)
            v_m = SYNTHETIC_SIGMA**2 * (1.0 / sf_m - 1.0)
            noise_l = rng.standard_normal(SYNTHETIC_N)
            independent = rng.standard_normal(SYNTHETIC_N)
            noise_m = rho_eps * noise_l + np.sqrt(1.0 - rho_eps**2) * independent
            x_l = SYNTHETIC_SIGMA * signal_l + np.sqrt(v_l) * noise_l
            x_m = SYNTHETIC_SIGMA * signal_m + np.sqrt(v_m) * noise_m
            estimate = estimate_two_band(x_l, x_m, sf_l, sf_m, phi_l, phi_m)
            if not estimate["valid"]:
                raise RuntimeError(f"synthetic estimator invalid: {estimate}")
            r_hats.append(float(estimate["r_true_hat"]))
            rho_hats.append(float(estimate["rho_eps_hat"]))
            conditions.append(float(estimate["cond_A"]))
        r_median = float(np.median(r_hats))
        rho_median = float(np.median(rho_hats))
        row = {
            "tau_l_s": tau_l,
            "tau_m_s": tau_m,
            "sf_l": sf_l,
            "sf_m": sf_m,
            "r_true": r_true,
            "rho_eps_true": rho_eps,
            "r_true_hat_median": r_median,
            "rho_eps_hat_median": rho_median,
            "cond_A_max": float(max(conditions)),
            "gates": {
                "r_error": abs(r_median - r_true) <= SYNTHETIC_ERROR_MAX,
                "rho_eps_error": abs(rho_median - rho_eps) <= SYNTHETIC_ERROR_MAX,
                "condition": max(conditions) <= COND_MAX,
            },
        }
        rows.append(row)
    return {"rows": rows, "all_pass": all(all(r["gates"].values()) for r in rows)}


def analyze_run(
    label: str, measured_path: Path, offered_path: Path
) -> dict[str, object]:
    measured = load_wide(measured_path, "rho").reset_index(drop=True)
    offered_raw = load_wide(offered_path, "rho_offered")
    offered = aggregate_offered(offered_raw, len(measured))

    per_link = {}
    for link in LINKS:
        estimate = estimate_nugget(measured[link].to_numpy(), DT_TARGET, N_FIT_LAGS)
        tau = float(estimate.get("tau_from_fit_s", float("nan")))
        phi = float(np.exp(-DT_TARGET / tau)) if np.isfinite(tau) and tau > 0 else float("nan")
        per_link[link] = {**estimate, "phi": phi}

    pair_rows = {}
    for first, second in PAIRS:
        pair_name = f"{first}-{second}"
        sf_l = float(per_link[first]["sf"])
        sf_m = float(per_link[second]["sf"])
        estimate = estimate_two_band(
            measured[first].to_numpy(),
            measured[second].to_numpy(),
            sf_l,
            sf_m,
            float(per_link[first]["phi"]),
            float(per_link[second]["phi"]),
        )
        r_offered = float(np.corrcoef(offered[first], offered[second])[0, 1])
        r_measured = float(np.corrcoef(measured[first], measured[second])[0, 1])
        r_error = (
            float(estimate["r_true_hat"] - r_offered)
            if estimate.get("valid")
            else float("nan")
        )
        pair_rows[pair_name] = {
            "first": first,
            "second": second,
            "r_offered": r_offered,
            "r_measured": r_measured,
            **estimate,
            "r_true_error_vs_offered": r_error,
            "physical_positive_control_pass": bool(
                estimate.get("valid") and abs(r_error) <= PAIR_ERROR_MAX
            ),
        }

    return {
        "label": label,
        "measured_path": str(measured_path),
        "offered_path": str(offered_path),
        "input_sha256": {
            "measured": sha256(measured_path),
            "offered": sha256(offered_path),
        },
        "n_measured": len(measured),
        "n_offered_raw": len(offered_raw),
        "n_offered_aggregated": len(offered),
        "dt_target_s": DT_TARGET,
        "offered_samples_per_bin": OFFERED_PER_BIN,
        "per_link": per_link,
        "pairs": pair_rows,
        "gates": {
            "all_link_nugget_valid": all(row["ok"] for row in per_link.values()),
            "all_pairs_valid": all(row.get("valid", False) for row in pair_rows.values()),
            "all_28_physical_controls_pass": all(
                row["physical_positive_control_pass"] for row in pair_rows.values()
            ),
        },
    }


def aggregate_phase23(runs: list[dict[str, object]]) -> dict[str, object]:
    pairs = {}
    for first, second in PAIRS:
        name = f"{first}-{second}"
        rows = [run["pairs"][name] for run in runs]
        r_true_values = [float(row["r_true_hat"]) for row in rows if row.get("valid")]
        rho_values = [float(row["rho_eps_hat"]) for row in rows if row.get("valid")]
        offered_values = [float(row["r_offered"]) for row in rows]
        pairs[name] = {
            "n_valid": len(r_true_values),
            "r_true_hat_median": float(np.median(r_true_values)) if r_true_values else float("nan"),
            "rho_eps_hat_median": float(np.median(rho_values)) if rho_values else float("nan"),
            "r_offered_median": float(np.median(offered_values)),
        }
        pairs[name]["r_error_vs_offered"] = float(
            pairs[name]["r_true_hat_median"] - pairs[name]["r_offered_median"]
        )
        pairs[name]["physical_positive_control_pass"] = bool(
            pairs[name]["n_valid"] == len(runs)
            and abs(pairs[name]["r_error_vs_offered"]) <= PAIR_ERROR_MAX
        )

    primary = {}
    for first, second in PRIMARY:
        name = f"{first}-{second}"
        row = pairs[name]
        primary[name] = {
            **row,
            "r_true_near_zero": abs(row["r_true_hat_median"]) <= PRIMARY_R_TRUE_ABS_MAX,
            "rho_eps_near_one": (
                abs(row["rho_eps_hat_median"] - 1.0)
                <= PRIMARY_RHO_EPS_ERROR_FROM_ONE_MAX
            ),
        }
    return {
        "pairs": pairs,
        "primary": primary,
        "gates": {
            "all_28_median_controls_pass": all(
                row["physical_positive_control_pass"] for row in pairs.values()
            ),
            "primary_r_true_near_zero": all(
                row["r_true_near_zero"] for row in primary.values()
            ),
            "primary_rho_eps_near_one": all(
                row["rho_eps_near_one"] for row in primary.values()
            ),
        },
    }


def main() -> None:
    synthetic = synthetic_generalization_control()
    if not synthetic["all_pass"]:
        raise SystemExit("G1-4S unequal-timescale synthetic control FAIL; physical data not read")

    cell_a = analyze_run(*CELL_A)
    phase23_runs = [analyze_run(*run) for run in PHASE23]
    phase23_summary = aggregate_phase23(phase23_runs)

    cell_a_primary = {
        name: cell_a["pairs"][name]
        for name in ("uA-uB", "vC-vD")
    }
    cell_a_mechanism = {
        "r_true_near_zero": all(
            abs(float(row["r_true_hat"])) <= PRIMARY_R_TRUE_ABS_MAX
            for row in cell_a_primary.values() if row.get("valid")
        ) and all(row.get("valid") for row in cell_a_primary.values()),
        "rho_eps_near_one": all(
            abs(float(row["rho_eps_hat"]) - 1.0)
            <= PRIMARY_RHO_EPS_ERROR_FROM_ONE_MAX
            for row in cell_a_primary.values() if row.get("valid")
        ) and all(row.get("valid") for row in cell_a_primary.values()),
    }
    cross_campaign_rho = {
        name: abs(
            float(cell_a_primary[name]["rho_eps_hat"])
            - float(phase23_summary["primary"][name]["rho_eps_hat_median"])
        )
        for name in cell_a_primary
    }
    cross_campaign_pass = all(value <= 0.20 for value in cross_campaign_rho.values())

    gate_summary = {
        "G1-4S_unequal_timescale_synthetic": synthetic["all_pass"],
        "G1-4A_cellA_link_estimators": cell_a["gates"]["all_link_nugget_valid"],
        "G1-4B_cellA_all_28_pairs": cell_a["gates"]["all_28_physical_controls_pass"],
        "G1-4C_phase23_link_estimators": all(
            run["gates"]["all_link_nugget_valid"] for run in phase23_runs
        ),
        "G1-4D_phase23_all_28_pairs_median": phase23_summary["gates"]["all_28_median_controls_pass"],
        "G1-4E_primary_r_true_near_zero_both_campaigns": bool(
            cell_a_mechanism["r_true_near_zero"]
            and phase23_summary["gates"]["primary_r_true_near_zero"]
        ),
        "G1-4F_primary_rho_eps_near_one_both_campaigns": bool(
            cell_a_mechanism["rho_eps_near_one"]
            and phase23_summary["gates"]["primary_rho_eps_near_one"]
        ),
        "G1-4G_cross_campaign_rho_eps_consistency": cross_campaign_pass,
    }
    gate_summary["overall_pass"] = all(gate_summary.values())

    artifact = {
        "schema": "dt4n.phase_g.g1_4_physical_reanalysis.v1",
        "status": "PREREGISTERED_REANALYSIS_EXISTING_DATA",
        "no_new_mininet": True,
        "no_new_raw_data": True,
        "locked_constants": {
            "dt_target_s": DT_TARGET,
            "offered_samples_per_bin": OFFERED_PER_BIN,
            "n_fit_lags": N_FIT_LAGS,
            "pair_error_max": PAIR_ERROR_MAX,
            "primary_r_true_abs_max": PRIMARY_R_TRUE_ABS_MAX,
            "primary_rho_eps_error_from_one_max": PRIMARY_RHO_EPS_ERROR_FROM_ONE_MAX,
            "condition_number_max": COND_MAX,
        },
        "synthetic_generalization_control": synthetic,
        "cellA_long": {**cell_a, "primary": cell_a_primary, "mechanism": cell_a_mechanism},
        "phase23_runs": phase23_runs,
        "phase23_summary": phase23_summary,
        "cross_campaign_primary_rho_eps_abs_difference": cross_campaign_rho,
        "gate_summary": gate_summary,
        "interpretation_scope": (
            "Existing outcomes and direction were known before this method was defined; "
            "PASS supports a quantitatively calibrated mechanism but is not an independent "
            "new-data confirmatory experiment."
        ),
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True,
                capture_output=True, text=True
            ).stdout.strip(),
            "prereg_tag": "phase-G-g1-4-prereg",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g1_4_physical_reanalysis.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("G1-4S unequal-timescale synthetic:", "PASS")
    print("\n%-24s %9s %9s %9s %9s %7s" % (
        "campaign/pair", "r_meas", "r_offer", "r_true", "rho_eps", "verdict"))
    for name, row in cell_a_primary.items():
        print("%-24s %9.4f %9.4f %9.4f %9.4f %7s" % (
            "cellA/" + name, row["r_measured"], row["r_offered"],
            row["r_true_hat"], row["rho_eps_hat"],
            "PASS" if row["physical_positive_control_pass"] else "FAIL"))
    for name, row in phase23_summary["primary"].items():
        measured_median = float(np.median([
            run["pairs"][name]["r_measured"] for run in phase23_runs
        ]))
        print("%-24s %9.4f %9.4f %9.4f %9.4f %7s" % (
            "phase23/" + name, measured_median, row["r_offered_median"],
            row["r_true_hat_median"], row["rho_eps_hat_median"],
            "PASS" if row["physical_positive_control_pass"] else "FAIL"))
    print("\nGates:")
    for key, value in gate_summary.items():
        print("  %-55s %s" % (key, "PASS" if value else "FAIL"))
    print("artifact:", OUT)


if __name__ == "__main__":
    main()

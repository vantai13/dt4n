#!/usr/bin/env python3
"""Lesson 23.15 -- locked eight-cell fallback and objective confirmation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

from cert import fallback_sweep as F
from cert.cell_matrices import TRUTH_TABLE, cell_matrices, git, json_clean, pin
from cert.objective_misspecification import _risk_at_truth
from measurements.decision_error_v2 import TruthTable


AMENDMENT = "docs/phase-23/00zp-amendment-39.md"
SLA_ARTIFACT = "results/LIVE/phase-20R/sla_calibration.json"
OUTPUT = "results/SUPERSEDED/phase-23/eight_cell_sweep.json"
SEEN_CELLS = ("poisson@0.925", "poisson@0.850", "h2@0.700")
NEW_CELLS = (
    "poisson@0.700",
    "poisson@0.960",
    "h2@0.850",
    "h2@0.925",
    "h2@0.960",
)
ALL_CELLS = SEEN_CELLS + NEW_CELLS
CELL_SPECS: Dict[str, Dict[str, Any]] = {
    "poisson@0.925": {"mode": "poisson", "rho_bar": 0.925, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3.parquet"},
    "poisson@0.850": {"mode": "poisson", "rho_bar": 0.850, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.850.parquet"},
    "h2@0.700": {"mode": "h2", "rho_bar": 0.700, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.700.parquet"},
    "poisson@0.700": {"mode": "poisson", "rho_bar": 0.700, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.700.parquet"},
    "poisson@0.960": {"mode": "poisson", "rho_bar": 0.960, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.960.parquet"},
    "h2@0.850": {"mode": "h2", "rho_bar": 0.850, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.850.parquet"},
    "h2@0.925": {"mode": "h2", "rho_bar": 0.925, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.925.parquet"},
    "h2@0.960": {"mode": "h2", "rho_bar": 0.960, "parquet": "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.960.parquet"},
}
RATIOS = tuple(float(x) for x in np.round(np.arange(0.50, 1.5001, 0.05), 2))
CONFIRM_RATIO = 0.8352557797157567
LEGACY_DELTA = {
    "poisson@0.925": -0.012868849344056688,
    "poisson@0.850": +0.0031202059335916077,
    "h2@0.700": +0.0038662551728414207,
}


def sla_objective_for_cell(
    cell: str,
    artifact: str = SLA_ARTIFACT,
    spec: Mapping[str, Any] | None = None,
) -> Dict[str, float]:
    """Read both objective parameters from the frozen SLA artifact."""
    spec = CELL_SPECS[cell] if spec is None else spec
    with open(artifact, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["cells"]
    matches = [
        row for row in rows
        if row.get("feasible")
        and str(row.get("role")) == "gate"
        and str(row.get("mode")) == str(spec["mode"])
        and abs(float(row.get("rho_bar")) - float(spec["rho_bar"])) <= 1e-12
    ]
    if len(matches) != 1:
        raise ValueError("can dung mot SLA gate cell cho %s, thay %d" % (cell, len(matches)))
    return {
        "w_loss": float(matches[0]["w_loss"]),
        "loss_exchange": float(matches[0]["loss_exchange"]),
    }


def w_loss_for_cell(
    cell: str,
    artifact: str = SLA_ARTIFACT,
    spec: Mapping[str, Any] | None = None,
) -> float:
    """Read the cell-specific objective weight from the frozen SLA artifact."""
    return float(sla_objective_for_cell(cell, artifact, spec=spec)["w_loss"])


def _decomposition_f2(
    df: pd.DataFrame,
    accept: np.ndarray,
    test_idx: np.ndarray,
    f2: Mapping[str, float],
) -> Dict[str, float]:
    a_star = df["a_star"].to_numpy(np.int64)
    a_twin = df["a_twin"].to_numpy(np.int64)
    reject_idx = test_idx[~accept[test_idx]]
    err_neo = float((a_twin[test_idx] != a_star[test_idx]).mean())
    err_p1 = float((a_star[test_idx] != 0).mean())
    c_star = float((a_twin[reject_idx] != a_star[reject_idx]).mean())
    err_p1_reject = float((a_star[reject_idx] != 0).mean())
    twin_deg = c_star - err_neo
    prior_deg = err_p1_reject - err_p1
    swing = err_p1 - err_neo
    lift = twin_deg - prior_deg
    delta = float(f2["delta_system_vs_neo"])
    reject_share = float(f2["reject_share"])
    residual = abs(delta - reject_share * (swing - lift))
    return {
        "err_neo": err_neo,
        "err_P1": err_p1,
        "c_star": c_star,
        "err_P1_given_reject": err_p1_reject,
        "twin_deg": twin_deg,
        "prior_deg": prior_deg,
        "swing": swing,
        "lift": lift,
        "reject_share": reject_share,
        "delta_vs_anchor": delta,
        "identity_residual": residual,
    }


def mondrian_capacity(folds: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    rows = []
    for fold in folds:
        mapping = fold["fits"]["F6"]["params"]["action_by_bin"]
        rows.append(
            {
                "scoring_seed": int(fold["scoring_seed"]),
                "nonempty_reject_bins": int(len(mapping)),
                "p1_bins": int(sum(int(action) == 0 for action in mapping.values())),
                "action_by_bin": dict(mapping),
            }
        )
    return {
        "nominal_bins": 16,
        "folds": rows,
        "mean_nonempty_reject_bins": float(np.mean([row["nonempty_reject_bins"] for row in rows])),
    }


def selection_vs_default(selected: Mapping[str, float], f2: Mapping[str, float]) -> Dict[str, Any]:
    diff = float(selected["delta_system_vs_neo"] - f2["delta_system_vs_neo"])
    return {
        "selected_delta": float(selected["delta_system_vs_neo"]),
        "default_F2_delta": float(f2["delta_system_vs_neo"]),
        "selected_minus_default": diff,
        "outcome": "win" if diff < 0.0 else ("loss" if diff > 0.0 else "tie"),
    }


def _objective_curve(
    cell: str,
    df: pd.DataFrame,
    accept: np.ndarray,
    crossfit: Mapping[str, Any],
    selected_at_one: Mapping[str, float],
    spec: Mapping[str, Any] | None = None,
    sla_artifact: str = SLA_ARTIFACT,
) -> Dict[str, Any]:
    spec = CELL_SPECS[cell] if spec is None else spec
    objective = sla_objective_for_cell(cell, sla_artifact, spec=spec)
    w_loss = float(objective["w_loss"])
    loss_exchange = float(objective["loss_exchange"])
    base = cell_matrices(
        TruthTable(TRUTH_TABLE),
        mode=str(spec["mode"]),
        rho_bar=float(spec["rho_bar"]),
        calibration_path=sla_artifact,
    )
    if len(base["y_true"]) != len(df):
        raise AssertionError("truth/parquet length mismatch for %s" % cell)
    y_base = np.asarray(base["y_true"], dtype=np.float64)
    loss = np.asarray(base["loss_true"], dtype=np.float64)
    a_twin = df["a_twin"].to_numpy(np.int64)
    test_idx = np.asarray(crossfit["test_idx"], dtype=np.int64)
    selected_probs = np.asarray(crossfit["selected_probs"], dtype=np.float32)

    def evaluate(ratio: float) -> Dict[str, Any]:
        y_eff = y_base + (float(ratio) - 1.0) * w_loss * loss
        a_star = y_eff.argmin(axis=1)
        row = _risk_at_truth(a_star, a_twin, accept, test_idx, selected_probs)
        row["w_eff_over_w_loss"] = float(ratio)
        row["loss_exchange"] = float(loss_exchange / float(ratio))
        return row

    curve = [evaluate(ratio) for ratio in RATIOS]
    confirm = evaluate(CONFIRM_RATIO)
    at_one = next(row for row in curve if abs(row["w_eff_over_w_loss"] - 1.0) <= 1e-12)
    parity = abs(float(at_one["delta_system_vs_neo"]) - float(selected_at_one["delta_system_vs_neo"]))
    if parity > 1e-12:
        raise AssertionError("objective ratio=1 parity fail for %s: %.3e" % (cell, parity))
    return {
        "w_loss": w_loss,
        "loss_exchange_at_ratio_one": loss_exchange,
        "w_loss_source": sla_artifact,
        "curve": curve,
        "confirm_ratio": {"ratio": CONFIRM_RATIO, "result": confirm},
        "ratio_one_selected_delta_gap": parity,
    }


def analyze_cell(
    cell: str,
    spec: Mapping[str, Any] | None = None,
    sla_artifact: str = SLA_ARTIFACT,
) -> Dict[str, Any]:
    spec = CELL_SPECS[cell] if spec is None else spec
    df = pd.read_parquet(spec["parquet"])
    score, accept = F.c3_accept_set(df)
    crossfit = F.build_crossfit_predictions(df, score, accept)
    test_idx = crossfit["test_idx"]
    f2 = F._risk_summary(crossfit["family_probs"]["F2"], df, accept, test_idx)
    selected = F._risk_summary(crossfit["selected_probs"], df, accept, test_idx)
    selected["families_by_fold"] = {
        str(fold["scoring_seed"]): fold["selected_family"] for fold in crossfit["folds"]
    }
    decomposition = _decomposition_f2(df, accept, test_idx, f2)
    if decomposition["identity_residual"] > 1e-12:
        raise AssertionError("lift/swing identity fail for %s" % cell)
    objective = _objective_curve(
        cell,
        df,
        accept,
        crossfit,
        selected,
        spec=spec,
        sla_artifact=sla_artifact,
    )
    return json_clean(
        {
            "cell": cell,
            "status": "seen" if cell in SEEN_CELLS else "new_confirmation",
            "n_rows": int(len(df)),
            "n_test": int(len(test_idx)),
            "F2": f2,
            "calibration_selected": selected,
            "selection_vs_default": selection_vs_default(selected, f2),
            "lift_swing_F2": decomposition,
            "mondrian_capacity": mondrian_capacity(crossfit["folds"]),
            "controls": {
                "NC_A_all_row_disjoint": bool(all(fold["row_disjoint"] for fold in crossfit["folds"])),
                "NC_A_all_seed_disjoint": bool(all(fold["seed_disjoint"] for fold in crossfit["folds"])),
                "NC_B_F6_information": ["z_bin", "m_hat_bin", "frozen_action_map"],
                "identity_residual_le_1e_12": bool(decomposition["identity_residual"] <= 1e-12),
            },
            "objective": objective,
        }
    )


def _spread(cells: Mapping[str, Any], field: str) -> Dict[str, Any]:
    values = [float(cells[cell]["lift_swing_F2"][field]) for cell in ALL_CELLS]
    lo, hi = min(values), max(values)
    ratio = float("inf") if lo == 0.0 and hi > 0.0 else (1.0 if lo == hi == 0.0 else hi / lo)
    return {
        "min": lo,
        "max": hi,
        "max_over_min": "inf" if np.isposinf(ratio) else ratio,
        "zero_denominator": bool(lo == 0.0),
    }


def _common_crossing(cells: Mapping[str, Any]) -> Dict[str, Any]:
    per_cell: Dict[str, Any] = {}
    boundaries = []
    for cell in NEW_CELLS:
        curve = cells[cell]["objective"]["curve"]
        y = [float(row["delta_system_vs_neo"]) for row in curve]
        x = [float(row["w_eff_over_w_loss"]) for row in curve]
        if y[0] >= 0.0:
            per_cell[cell] = {"upper_negative_boundary": None, "reason": "not_negative_at_grid_min"}
            continue
        boundary = x[-1]
        reason = "negative_through_grid_max"
        for i in range(1, len(x)):
            if y[i] >= 0.0:
                boundary = x[i - 1] + (0.0 - y[i - 1]) * (x[i] - x[i - 1]) / (y[i] - y[i - 1])
                reason = "linear_zero_crossing"
                break
        per_cell[cell] = {"upper_negative_boundary": float(boundary), "reason": reason}
        boundaries.append(float(boundary))
    common = min(boundaries) if len(boundaries) == len(NEW_CELLS) else None
    return {"r_cross": common, "per_cell": per_cell}


def run_eight_cells() -> Dict[str, Any]:
    cells = {cell: analyze_cell(cell) for cell in ALL_CELLS}
    nc_d = {
        cell: {
            "expected": expected,
            "got": float(cells[cell]["F2"]["delta_system_vs_neo"]),
            "absolute_gap": abs(float(cells[cell]["F2"]["delta_system_vs_neo"]) - expected),
        }
        for cell, expected in LEGACY_DELTA.items()
    }
    if max(row["absolute_gap"] for row in nc_d.values()) > 1e-12:
        raise AssertionError("NC-D old-cell parity failed")
    twin = _spread(cells, "twin_deg")
    prior = _spread(cells, "prior_deg")
    crossing = _common_crossing(cells)
    m47_by_cell = {
        cell: bool(cells[cell]["objective"]["confirm_ratio"]["result"]["delta_system_vs_neo"] < 0.0)
        for cell in NEW_CELLS
    }
    sign_by_cell = {
        cell: bool(
            np.sign(float(cells[cell]["lift_swing_F2"]["lift"]) - float(cells[cell]["lift_swing_F2"]["swing"]))
            == np.sign(-float(cells[cell]["lift_swing_F2"]["delta_vs_anchor"]))
        )
        for cell in ALL_CELLS
    }
    capacity = float(np.mean([
        fold["nonempty_reject_bins"]
        for cell in ALL_CELLS
        for fold in cells[cell]["mondrian_capacity"]["folds"]
    ]))
    selection_diffs = [float(cells[cell]["selection_vs_default"]["selected_minus_default"]) for cell in ALL_CELLS]
    selection_mean = float(np.mean(selection_diffs))
    r_cross = crossing["r_cross"]
    metrics = {
        "M_46_common_r_cross_new_cells": crossing,
        "M_47_confirm_ratio": CONFIRM_RATIO,
        "M_47_negative_by_new_cell": m47_by_cell,
        "M_48_twin_deg_spread_all_cells": twin,
        "M_49_prior_deg_spread_all_cells": prior,
        "M_50_sign_identity_by_cell": sign_by_cell,
        "M_51_mean_nonempty_mondrian_reject_bins": capacity,
        "M_52_mean_selected_minus_default_delta": selection_mean,
    }
    prior_ratio = float("inf") if prior["max_over_min"] == "inf" else float(prior["max_over_min"])
    verdict = {
        "M_46_r_cross_in_0_80_0_95": bool(r_cross is not None and 0.80 <= float(r_cross) <= 0.95),
        "M_47_delta_negative_all_new_at_confirm_ratio": bool(all(m47_by_cell.values())),
        "M_48_twin_deg_spread_in_1_00_1_30": bool(twin["max_over_min"] != "inf" and 1.00 <= float(twin["max_over_min"]) <= 1.30),
        "M_49_prior_deg_spread_gt_3": bool(prior_ratio > 3.0),
        "M_50_sign_identity_8_of_8": bool(all(sign_by_cell.values())),
        "M_51_capacity_in_4_8": bool(4.0 <= capacity <= 8.0),
        "M_52_selection_mean_not_worse": bool(selection_mean <= 0.0),
    }
    return json_clean(
        {
            "schema": "eight_cell_sweep/v1",
            "lesson": "23.15",
            "seen_cells": list(SEEN_CELLS),
            "new_confirmation_cells": list(NEW_CELLS),
            "ratios": list(RATIOS),
            "cells": cells,
            "metrics": metrics,
            "verdict": verdict,
            "controls": {
                "NC_D_old_cell_F2_parity": nc_d,
                "NC_D_max_absolute_gap": max(row["absolute_gap"] for row in nc_d.values()),
                "NC_E_all_leakage_controls": bool(all(
                    cells[cell]["controls"][name]
                    for cell in ALL_CELLS
                    for name in ("NC_A_all_row_disjoint", "NC_A_all_seed_disjoint", "identity_residual_le_1e_12")
                )),
                "NC_F_w_loss_source": SLA_ARTIFACT,
                "NC_F_no_hardcoded_cell_weights": True,
            },
            "provenance": {
                "script": "cert/eight_cell_sweep.py",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [pin(AMENDMENT), pin(SLA_ARTIFACT), pin(TRUTH_TABLE)]
                + [pin(CELL_SPECS[cell]["parquet"]) for cell in ALL_CELLS],
            },
        }
    )


def print_report(report: Mapping[str, Any]) -> None:
    print("=== LESSON 23.15: EIGHT-CELL CONFIRMATION ===")
    for cell in ALL_CELLS:
        row = report["cells"][cell]
        confirm = row["objective"]["confirm_ratio"]["result"]["delta_system_vs_neo"]
        print(
            "%-16s F2=%+.6f selected=%+.6f select-F2=%+.6f Delta@r*=%.6f=%+.6f"
            % (
                cell,
                row["F2"]["delta_system_vs_neo"],
                row["calibration_selected"]["delta_system_vs_neo"],
                row["selection_vs_default"]["selected_minus_default"],
                CONFIRM_RATIO,
                confirm,
            )
        )
    print("M-46 r_cross=%s" % report["metrics"]["M_46_common_r_cross_new_cells"]["r_cross"])
    print("verdict=%s" % json.dumps(report["verdict"], sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    report = run_eight_cells()
    print_report(report)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("artifact -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

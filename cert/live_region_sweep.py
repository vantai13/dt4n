#!/usr/bin/env python3
"""Lesson 23.16 -- prepare and score the preregistered live-region sweep."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Mapping, Sequence

import numpy as np

from cert import eight_cell_sweep as E
from cert.build_calib_set_v2 import SEEDS, SIGMA
from cert.cell_matrices import TRUTH_TABLE, git, json_clean, pin
from measurements import sla_calib_v2 as SLA
from measurements.decision_error_v2 import TruthTable, rho_matrix_from_cell
from twin import cost_v2 as C


AMENDMENT = "docs/phase-23/00zq-amendment-40.md"
BASE_SLA = "results/phase-20R/sla_calibration.json"
SLA_OUTPUT = "results/phase-23/sla_calibration_lesson23_16.json"
OUTPUT = "results/phase-23/live_region_sweep.json"
EIGHT_CELL_ARTIFACT = E.OUTPUT
DOMAIN_LIMIT = 1e-4
LIVE_THRESHOLD = 0.05
CONFIRM_RATIO = E.CONFIRM_RATIO
PRIMARY_CANDIDATES = (("poisson", 0.875), ("poisson", 0.900), ("h2", 0.650))
H2_FALLBACK = ("h2", 0.675)
NEW_SPECS: Dict[str, Dict[str, Any]] = {
    "poisson@0.875": {"mode": "poisson", "rho_bar": 0.875, "parquet": "results/phase-22/calib_set_v3_poisson_0.875.parquet"},
    "poisson@0.900": {"mode": "poisson", "rho_bar": 0.900, "parquet": "results/phase-22/calib_set_v3_poisson_0.900.parquet"},
    "h2@0.650": {"mode": "h2", "rho_bar": 0.650, "parquet": "results/phase-22/calib_set_v3_h2_0.650.parquet"},
    "h2@0.675": {"mode": "h2", "rho_bar": 0.675, "parquet": "results/phase-22/calib_set_v3_h2_0.675.parquet"},
}


def cell_name(mode: str, rho_bar: float) -> str:
    return "%s@%.3f" % (str(mode), float(rho_bar))


def truth_domain_check(cell: Mapping[str, Any]) -> Dict[str, Any]:
    """Gate on the builder distribution; retain SLA-regime as stress diagnostic."""
    mode = str(cell["mode"])
    rho_bar = float(cell["rho_bar"])
    rows = []
    for sigma_source, sigma in (
        ("sla_regime", float(cell["sigma_rho"])),
        ("calib_builder", float(SIGMA)),
    ):
        for seed in SEEDS:
            tt = TruthTable(TRUTH_TABLE)
            rho = rho_matrix_from_cell(
                mode,
                rho_bar,
                float(sigma),
                int(seed),
                tau=float(cell["tau_rho"]),
                n=int(cell["n"]),
                dt=float(cell["dt"]),
            )
            tt.path_tables(mode, rho, float(cell["w_loss"]))
            worst_key = max(tt.clip_log, key=tt.clip_log.get)
            worst = float(tt.clip_log[worst_key])
            rows.append(
                {
                    "sigma_source": sigma_source,
                    "sigma_rho": float(sigma),
                    "seed": int(seed),
                    "worst_link": worst_key,
                    "worst_fraction": worst,
                    "pass": bool(worst < DOMAIN_LIMIT),
                    "clip_by_link": dict(tt.clip_log),
                }
            )
    builder_rows = [row for row in rows if row["sigma_source"] == "calib_builder"]
    stress_rows = [row for row in rows if row["sigma_source"] == "sla_regime"]
    worst_row = max(builder_rows, key=lambda row: row["worst_fraction"])
    stress_worst = max(stress_rows, key=lambda row: row["worst_fraction"])
    return {
        "threshold_strict_lt": DOMAIN_LIMIT,
        "rows": rows,
        "max_fraction": float(worst_row["worst_fraction"]),
        "worst_link": str(worst_row["worst_link"]),
        "worst_seed": int(worst_row["seed"]),
        "worst_sigma_source": str(worst_row["sigma_source"]),
        "pass": bool(all(row["pass"] for row in builder_rows)),
        "eligibility_distribution": "calib_builder",
        "stress_sla_regime_pass": bool(all(row["pass"] for row in stress_rows)),
        "stress_sla_regime_max_fraction": float(stress_worst["worst_fraction"]),
        "stress_sla_regime_worst_link": str(stress_worst["worst_link"]),
    }


def _calibrate(mode: str, rho_bar: float) -> Dict[str, Any]:
    row = SLA.calibrate_cell(
        C.CostV2(strict_reliable=True),
        str(mode),
        float(rho_bar),
        seed=SLA.DEFAULT_SEED,
        n=SLA.DEFAULT_N,
        dt=SLA.DEFAULT_DT,
        tau=SLA.DEFAULT_TAU,
        a=SLA.DEFAULT_A,
    )
    if not row.get("feasible"):
        raise AssertionError("SLA candidate infeasible: %s" % cell_name(mode, rho_bar))
    row = dict(row)
    row["lesson"] = "23.16"
    row["domain_control"] = truth_domain_check(row)
    row["role_before_domain"] = row.get("role")
    if not row["domain_control"]["pass"]:
        row["role"] = "domain_excluded"
    return row


def prepare_sla() -> Dict[str, Any]:
    with open(BASE_SLA, "r", encoding="utf-8") as handle:
        base = json.load(handle)
    candidates = [_calibrate(mode, rho) for mode, rho in PRIMARY_CANDIDATES]
    primary_h2 = next(row for row in candidates if cell_name(row["mode"], row["rho_bar"]) == "h2@0.650")
    fallback_triggered = not bool(primary_h2["domain_control"]["pass"])
    if fallback_triggered:
        candidates.append(_calibrate(*H2_FALLBACK))
    passed = [cell_name(row["mode"], row["rho_bar"]) for row in candidates if row["domain_control"]["pass"]]
    excluded = [cell_name(row["mode"], row["rho_bar"]) for row in candidates if not row["domain_control"]["pass"]]
    return json_clean(
        {
            **{key: value for key, value in base.items() if key != "cells"},
            "schema": "sla_calibration_lesson23_16/v1",
            "lesson": "23.16",
            "base_artifact": pin(BASE_SLA),
            "requested_cells": [cell_name(*row) for row in PRIMARY_CANDIDATES],
            "fallback_cell": cell_name(*H2_FALLBACK),
            "fallback_triggered": fallback_triggered,
            "passed_cells": passed,
            "excluded_cells": excluded,
            "domain_limit": DOMAIN_LIMIT,
            "cells": list(base["cells"]) + candidates,
            "provenance": {
                "script": "cert/live_region_sweep.py::prepare_sla",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [
                    pin(AMENDMENT),
                    pin("docs/phase-23/00zr-amendment-41.md"),
                    pin(BASE_SLA),
                    pin(TRUTH_TABLE),
                ],
            },
        }
    )


def write_json(payload: Mapping[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(json_clean(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


def _load_sla() -> Dict[str, Any]:
    with open(SLA_OUTPUT, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _new_valid_cells(sla: Mapping[str, Any]) -> list[str]:
    return [cell for cell in sla["passed_cells"] if cell in NEW_SPECS]


def _sign_monotone(values: Sequence[float]) -> bool:
    signs = [1 if value > 0.0 else (-1 if value < 0.0 else 0) for value in values]
    seen_positive = False
    for sign in signs:
        if sign > 0:
            seen_positive = True
        elif sign < 0 and seen_positive:
            return False
    return True


def run_sweep() -> Dict[str, Any]:
    sla = _load_sla()
    with open(EIGHT_CELL_ARTIFACT, "r", encoding="utf-8") as handle:
        prior = json.load(handle)
    cells = dict(prior["cells"])
    valid_new = _new_valid_cells(sla)
    for cell in valid_new:
        cells[cell] = E.analyze_cell(cell, spec=NEW_SPECS[cell], sla_artifact=SLA_OUTPUT)

    poisson_axis = ["poisson@0.850", "poisson@0.875", "poisson@0.900", "poisson@0.925"]
    axis_values = [float(cells[cell]["lift_swing_F2"]["lift"] - cells[cell]["lift_swing_F2"]["swing"]) for cell in poisson_axis]
    positive = [cell for cell in poisson_axis if float(cells[cell]["lift_swing_F2"]["lift"] - cells[cell]["lift_swing_F2"]["swing"]) > 0.0]
    rho_hit = min(float(cell.split("@")[1]) for cell in positive) if positive else None
    bracket = None
    for left, right in zip(poisson_axis, poisson_axis[1:]):
        lv = float(cells[left]["lift_swing_F2"]["lift"] - cells[left]["lift_swing_F2"]["swing"])
        rv = float(cells[right]["lift_swing_F2"]["lift"] - cells[right]["lift_swing_F2"]["swing"])
        if lv <= 0.0 < rv:
            bracket = [float(left.split("@")[1]), float(right.split("@")[1])]
            break

    m55 = {cell: float(cells[cell]["lift_swing_F2"]["err_neo"]) for cell in ("poisson@0.875", "poisson@0.900")}
    h2_valid = [cell for cell in valid_new if cell.startswith("h2@")]
    h2_cell = h2_valid[0] if h2_valid else None
    h2_live = None if h2_cell is None else bool(cells[h2_cell]["lift_swing_F2"]["err_neo"] >= LIVE_THRESHOLD)
    h2_lift_minus_swing = None if h2_cell is None else float(cells[h2_cell]["lift_swing_F2"]["lift"] - cells[h2_cell]["lift_swing_F2"]["swing"])

    heldout_candidates = ["poisson@0.960"] + valid_new
    heldout_live = [cell for cell in heldout_candidates if float(cells[cell]["lift_swing_F2"]["err_neo"]) >= LIVE_THRESHOLD]
    m47b = {
        cell: float(cells[cell]["objective"]["confirm_ratio"]["result"]["delta_system_vs_neo"])
        for cell in heldout_live
    }
    live_23_15 = [cell for cell in E.ALL_CELLS if float(cells[cell]["lift_swing_F2"]["err_neo"]) >= LIVE_THRESHOLD]
    twin_values = [float(cells[cell]["lift_swing_F2"]["twin_deg"]) for cell in live_23_15]
    m48b = max(twin_values) / min(twin_values)

    verdict = {
        "M_53_rho_hit_in_0_860_0_925": bool(rho_hit is not None and 0.860 <= rho_hit <= 0.925),
        "M_54_poisson_sign_monotone": _sign_monotone(axis_values),
        "M_55_poisson_err_neo_both_in_0_15_0_26": bool(all(0.15 <= value <= 0.26 for value in m55.values())),
        "M_56_h2_candidate_live": None if h2_cell is None else bool(h2_live),
        "M_57_h2_live_lift_minus_swing_negative": None if h2_cell is None or not h2_live else bool(h2_lift_minus_swing < 0.0),
        "M_47b_delta_nonpositive_all_live_heldout": bool(m47b and all(value <= 0.0 for value in m47b.values())),
        "M_48b_twin_deg_spread_in_1_00_1_30": bool(1.00 <= m48b <= 1.30),
    }
    return json_clean(
        {
            "schema": "live_region_sweep/v1",
            "lesson": "23.16",
            "live_threshold": LIVE_THRESHOLD,
            "valid_new_cells": valid_new,
            "excluded_domain_cells": list(sla["excluded_cells"]),
            "cells": cells,
            "metrics": {
                "M_53_rho_hit": rho_hit,
                "M_53_boundary_bracket": bracket,
                "M_54_poisson_axis": dict(zip(poisson_axis, axis_values)),
                "M_55_err_neo": m55,
                "M_56_h2_candidate": h2_cell,
                "M_56_h2_live": h2_live,
                "M_57_h2_lift_minus_swing": h2_lift_minus_swing,
                "M_47b_live_heldout_delta_at_confirm_ratio": m47b,
                "M_48b_live_cells_23_15": live_23_15,
                "M_48b_twin_deg_spread": m48b,
            },
            "verdict": verdict,
            "controls": {
                "NC_G_old_cell_max_gap": float(prior["controls"]["NC_D_max_absolute_gap"]),
                "NC_H_domain_checked_before_build": True,
                "NC_H_domain_limit": DOMAIN_LIMIT,
                "NC_I_identity_all_valid": bool(all(cells[cell]["controls"]["identity_residual_le_1e_12"] for cell in valid_new)),
                "NC_J_crossfit_all_valid": bool(all(cells[cell]["controls"]["NC_A_all_row_disjoint"] and cells[cell]["controls"]["NC_A_all_seed_disjoint"] for cell in valid_new)),
                "NC_K_requested_cells": list(sla["requested_cells"]),
                "NC_K_passed_cells": list(sla["passed_cells"]),
                "NC_K_excluded_cells": list(sla["excluded_cells"]),
                "NC_K_fallback_triggered": bool(sla["fallback_triggered"]),
            },
            "provenance": {
                "script": "cert/live_region_sweep.py::run_sweep",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [pin(AMENDMENT), pin(SLA_OUTPUT), pin(EIGHT_CELL_ARTIFACT)]
                + [pin(NEW_SPECS[cell]["parquet"]) for cell in valid_new],
            },
        }
    )


def print_sla(report: Mapping[str, Any]) -> None:
    print("=== LESSON 23.16: SLA + TRUTH-DOMAIN CONTROL ===")
    for row in report["cells"][-len(report["requested_cells"])-int(report["fallback_triggered"]):]:
        if row.get("lesson") != "23.16":
            continue
        d = row["domain_control"]
        print("%-16s w_loss=%9.3f domain_max=%.6f %-4s %s" % (
            cell_name(row["mode"], row["rho_bar"]), row["w_loss"], d["max_fraction"],
            "PASS" if d["pass"] else "FAIL", d["worst_link"],
        ))
    print("passed=%s" % report["passed_cells"])
    print("excluded=%s" % report["excluded_cells"])


def print_sweep(report: Mapping[str, Any]) -> None:
    print("=== LESSON 23.16: LIVE-REGION SWEEP ===")
    for cell in report["valid_new_cells"]:
        row = report["cells"][cell]
        d = row["lift_swing_F2"]
        print("%-16s err_neo=%.6f lift-swing=%+.6f Delta=%+.6f" % (
            cell, d["err_neo"], d["lift"] - d["swing"], d["delta_vs_anchor"],
        ))
    print("rho_hit=%s bracket=%s" % (report["metrics"]["M_53_rho_hit"], report["metrics"]["M_53_boundary_bracket"]))
    print("verdict=%s" % json.dumps(report["verdict"], sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-sla", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--sla-out", default=SLA_OUTPUT)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    if args.prepare_sla == args.run:
        parser.error("chon dung mot trong --prepare-sla hoac --run")
    if args.prepare_sla:
        report = prepare_sla()
        print_sla(report)
        write_json(report, args.sla_out)
        print("artifact -> %s" % args.sla_out)
    else:
        report = run_sweep()
        print_sweep(report)
        write_json(report, args.out)
        print("artifact -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

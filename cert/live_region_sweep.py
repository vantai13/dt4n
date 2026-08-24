#!/usr/bin/env python3
"""Lesson 23.21h -- score the live region under the exogenous S-B SLA."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Mapping, Sequence

from cert import eight_cell_sweep as E
from cert.build_calib_set_v2 import SEEDS, SIGMA
from cert.build_calib_set_v3 import AOI_V7, AXIS_MEASURED, Z_EDGES_V7
from cert.cell_matrices import TRUTH_TABLE, git, json_clean, pin
from measurements.decision_error_v2 import TruthTable, rho_matrix_from_cell
from measurements.sla_exogenous import classify
from measurements.validity import validity_block


AMENDMENT = "docs/phase-23/A062-amendment-62.md"
SLA_EXOGENOUS_10 = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
SLA_EXOGENOUS_14 = (
    "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_14cells.json"
)
SLA_REGIME_BASE = "results/LIVE/phase-23/sla_exogenous_S-B.json"
SLA_REGIME_WAVE4 = "results/LIVE/phase-23/sla_exogenous_wave4.json"
WAVE4_DIGESTS = "results/RAW/phase-21R/WAVE4_DIGESTS.json"
OUTPUT = "results/LIVE/phase-23/live_region_sweep_slaB.json"

# These artifacts consume two approved axes, hence LIVE. The four legacy
# controls built alongside them remain in SUPERSEDED and are not sweep inputs.
BASE_CALIB_TEMPLATE = (
    "results/LIVE/phase-21R/"
    "calib_set_{mode}_{rho:.3f}_U3_measured_v7.parquet"
)
CALIB_TEMPLATE_WAVE4 = BASE_CALIB_TEMPLATE

DOMAIN_LIMIT = 1e-4
LIVE_THRESHOLD = 0.05
CONFIRM_RATIO = E.CONFIRM_RATIO
FIXPOINT_MARKS = (
    "fixpoint_history",
    "fixpoint_rounds",
    "fixpoint_converged",
    "percentile",
    "target_viol",
)

NEW_SPECS: Dict[str, Dict[str, Any]] = {
    "poisson@0.875": {"mode": "poisson", "rho_bar": 0.875},
    "poisson@0.900": {"mode": "poisson", "rho_bar": 0.900},
    "h2@0.650": {"mode": "h2", "rho_bar": 0.650},
    "h2@0.675": {"mode": "h2", "rho_bar": 0.675},
}
ANALYZED_CELLS = tuple(E.ALL_CELLS) + tuple(NEW_SPECS)


def cell_name(mode: str, rho_bar: float) -> str:
    return "%s@%.3f" % (str(mode), float(rho_bar))


def _calib_path(spec: Mapping[str, Any], tpl: str | None) -> str:
    """Resolve regenerated input and fail loudly instead of using dead L51 paths."""
    if tpl is None:
        if "parquet" not in spec:
            raise SystemExit(
                "cell %s@%.3f khong co duong parquet co dinh (4 parquet "
                "Phase 22 da mat -- L51b). Truyen --calib-template."
                % (spec["mode"], float(spec["rho_bar"]))
            )
        return str(spec["parquet"])
    path = tpl.format(mode=spec["mode"], rho=float(spec["rho_bar"]))
    if not os.path.exists(path):
        raise FileNotFoundError(
            "thieu calib_set: %s\n  -> chay tools/run_23_20_matrix.py "
            "--wave 4" % path
        )
    return path


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


def load_sla_exogenous(path: str = SLA_EXOGENOUS_14) -> Dict[str, Any]:
    """Load the external manifest without any endogenous calibration step."""
    with open(path, "r", encoding="utf-8") as handle:
        sla = json.load(handle)

    for cell in sla["cells"]:
        bad = sorted(set(cell) & set(FIXPOINT_MARKS))
        assert not bad, (
            "cell %s@%.3f con dau vet fixpoint: %s -- day la S14"
            % (cell["mode"], float(cell["rho_bar"]), bad)
        )
    ws = {float(cell["w_loss"]) for cell in sla["cells"]}
    assert ws == {5000.0}, "w_loss khong dong nhat: %s" % sorted(ws)

    have = {cell_name(cell["mode"], cell["rho_bar"]) for cell in sla["cells"]}
    missing = sorted(set(NEW_SPECS) - have)
    assert not missing, "thieu cell Dot 4: %s" % missing

    passed, excluded = [], []
    for cell in sla["cells"]:
        name = cell_name(cell["mode"], cell["rho_bar"])
        if name not in NEW_SPECS:
            continue
        cell["domain_control"] = truth_domain_check(cell)
        cell["role_before_domain"] = cell.get("role")
        if cell["domain_control"]["pass"]:
            passed.append(name)
        else:
            cell["role"] = "domain_excluded"
            excluded.append(name)

    sla["passed_cells"] = sorted(passed)
    sla["excluded_cells"] = sorted(excluded)
    sla["requested_cells"] = sorted(NEW_SPECS)
    # No calibration exists on this path. None means not applicable; False
    # would incorrectly claim that a fallback was evaluated and did not fire.
    sla["fallback_triggered"] = None
    return sla


def _new_valid_cells(sla: Mapping[str, Any]) -> list[str]:
    return [cell for cell in sla["passed_cells"] if cell in NEW_SPECS]


def analyze_base_cells(
    *,
    sla_path: str = SLA_EXOGENOUS_14,
    calib_template: str = BASE_CALIB_TEMPLATE,
    axis: str = AXIS_MEASURED,
    aoi_profile: str = "U3",
) -> Dict[str, Any]:
    """Shared eight-cell path used by the sweep and the G23-212b NC."""
    return {
        cell: E.analyze_cell(
            cell,
            spec=E.CELL_SPECS[cell],
            sla_artifact=sla_path,
            calib_template=calib_template,
            axis=axis,
            aoi_profile=aoi_profile,
        )
        for cell in E.ALL_CELLS
    }


def _sign_monotone(values: Sequence[float]) -> bool:
    signs = [1 if value > 0.0 else (-1 if value < 0.0 else 0) for value in values]
    seen_positive = False
    for sign in signs:
        if sign > 0:
            seen_positive = True
        elif sign < 0 and seen_positive:
            return False
    return True


def authoritative_regimes(cells_wanted: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """Recompute B from authoritative shares and cross-check stored labels."""
    rows: Dict[str, Dict[str, Any]] = {}
    for source in (SLA_REGIME_BASE, SLA_REGIME_WAVE4):
        with open(source, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for cell in payload["cells"]:
            name = cell_name(cell["mode"], cell["rho_bar"])
            if name not in cells_wanted:
                continue
            if name in rows:
                raise AssertionError("regime source trung cell: %s" % name)
            ci = (cell.get("S_pivotal_ci") or {}).get("ci95")
            recomputed = classify(cell, ci=None if ci is None else tuple(ci))
            rows[name] = {
                "source": source,
                "S_pivotal": float(cell["S_pivotal"]),
                "declared_regime": str(cell["regime"]),
                "recomputed_regime": recomputed,
                "match": bool(str(cell["regime"]) == recomputed),
            }
    missing = sorted(set(cells_wanted) - set(rows))
    if missing:
        raise AssertionError("thieu authoritative regime: %s" % missing)
    return rows


def _input_path(cell: str, base_template: str, wave_template: str) -> str:
    spec = NEW_SPECS.get(cell, E.CELL_SPECS.get(cell))
    template = wave_template if cell in NEW_SPECS else base_template
    return _calib_path(spec, template)


def run_sweep(
    calib_template: str | None = CALIB_TEMPLATE_WAVE4,
    sla_path: str = SLA_EXOGENOUS_14,
    base_calib_template: str = BASE_CALIB_TEMPLATE,
    base_aoi_profile: str = "U3",
) -> Dict[str, Any]:
    sla = load_sla_exogenous(sla_path)
    cells = analyze_base_cells(
        sla_path=sla_path,
        calib_template=base_calib_template,
        axis=AXIS_MEASURED,
        aoi_profile=base_aoi_profile,
    )
    valid_new = _new_valid_cells(sla)
    for cell in valid_new:
        _calib_path(NEW_SPECS[cell], calib_template)
        cells[cell] = E.analyze_cell(
            cell,
            spec=NEW_SPECS[cell],
            sla_artifact=sla_path,
            calib_template=calib_template,
            axis=AXIS_MEASURED,
            aoi_profile="U3",
        )

    analyzed = list(E.ALL_CELLS) + valid_new
    regime_rows = authoritative_regimes(analyzed)
    g23_214_matches = sum(row["match"] for row in regime_rows.values())
    if g23_214_matches != len(analyzed):
        raise AssertionError(
            "G23-214 FAIL: regime recomputed != authoritative (%d/%d)"
            % (g23_214_matches, len(analyzed))
        )

    agreement: Dict[str, bool] = {}
    for cell in analyzed:
        live_a = bool(
            float(cells[cell]["lift_swing_F2"]["err_neo"]) >= LIVE_THRESHOLD
        )
        live_b = regime_rows[cell]["recomputed_regime"] == "LIVE"
        agreement[cell] = live_a == live_b
        cells[cell]["live_definitions"] = {
            "A_err_neo_ge_0_05": live_a,
            "B_regime_eq_LIVE": live_b,
            "regime": regime_rows[cell]["recomputed_regime"],
            "S_pivotal": regime_rows[cell]["S_pivotal"],
            "agreement": agreement[cell],
        }

    poisson_axis = [
        "poisson@0.850",
        "poisson@0.875",
        "poisson@0.900",
        "poisson@0.925",
    ]
    axis_values = [
        float(
            cells[cell]["lift_swing_F2"]["lift"]
            - cells[cell]["lift_swing_F2"]["swing"]
        )
        for cell in poisson_axis
    ]
    positive = [
        cell for cell, value in zip(poisson_axis, axis_values) if value > 0.0
    ]
    rho_hit = min(float(cell.split("@")[1]) for cell in positive) if positive else None
    bracket = None
    for left, right, lv, rv in zip(
        poisson_axis, poisson_axis[1:], axis_values, axis_values[1:]
    ):
        if lv <= 0.0 < rv:
            bracket = [float(left.split("@")[1]), float(right.split("@")[1])]
            break

    m178 = {
        cell: float(cells[cell]["lift_swing_F2"]["err_neo"])
        for cell in ("poisson@0.875", "poisson@0.900")
    }
    h2_cell = "h2@0.650" if "h2@0.650" in valid_new else (
        "h2@0.675" if "h2@0.675" in valid_new else None
    )
    h2_live_a = None if h2_cell is None else bool(
        cells[h2_cell]["live_definitions"]["A_err_neo_ge_0_05"]
    )
    h2_lift_minus_swing = None if h2_cell is None else float(
        cells[h2_cell]["lift_swing_F2"]["lift"]
        - cells[h2_cell]["lift_swing_F2"]["swing"]
    )

    heldout_candidates = ["poisson@0.960"] + valid_new
    heldout_live = [
        cell
        for cell in heldout_candidates
        if cells[cell]["live_definitions"]["A_err_neo_ge_0_05"]
    ]
    m47b = {
        cell: float(
            cells[cell]["objective"]["confirm_ratio"]["result"][
                "delta_system_vs_neo"
            ]
        )
        for cell in heldout_live
    }
    all_a_live = [
        cell
        for cell in analyzed
        if cells[cell]["live_definitions"]["A_err_neo_ge_0_05"]
    ]
    twin_values = [
        float(cells[cell]["lift_swing_F2"]["twin_deg"]) for cell in all_a_live
    ]
    m179 = max(twin_values) / min(twin_values)
    agreement_count = sum(agreement.values())

    verdict = {
        "M_176_A_B_agreement_at_least_8_of_12": bool(
            len(analyzed) == 12 and agreement_count >= 8
        ),
        "M_177_rho_hit_in_0_900_0_925": bool(
            rho_hit is not None and 0.900 <= rho_hit <= 0.925
        ),
        "M_178_poisson_err_neo_both_in_0_20_0_30": bool(
            all(0.20 <= value <= 0.30 for value in m178.values())
        ),
        "M_179_A_live_twin_deg_spread_in_1_00_1_50": bool(
            1.00 <= m179 <= 1.50
        ),
        "M_54_poisson_sign_monotone": _sign_monotone(axis_values),
        "M_57_h2_A_live_lift_minus_swing_negative": (
            None
            if h2_cell is None or not h2_live_a
            else bool(h2_lift_minus_swing < 0.0)
        ),
        "M_47b_delta_nonpositive_all_A_live_heldout": bool(
            m47b and all(value <= 0.0 for value in m47b.values())
        ),
    }

    domain = {
        cell_name(row["mode"], row["rho_bar"]): row["domain_control"]
        for row in sla["cells"]
        if "domain_control" in row
    }
    return json_clean(
        {
            "schema": "live_region_sweep_slaB/v2",
            "lesson": "23.21h",
            "live_threshold": LIVE_THRESHOLD,
            "aoi_profile": base_aoi_profile,
            "analyzed_cells": analyzed,
            "valid_new_cells": valid_new,
            "excluded_domain_cells": list(sla["excluded_cells"]),
            "cells": cells,
            "live_definition_table": {
                cell: cells[cell]["live_definitions"] for cell in analyzed
            },
            "metrics": {
                "M_176_agreement_count": agreement_count,
                "M_176_total_cells": len(analyzed),
                "M_177_rho_hit": rho_hit,
                "M_177_boundary_bracket": bracket,
                "M_54_poisson_axis": dict(zip(poisson_axis, axis_values)),
                "M_178_err_neo": m178,
                "M_56_h2_candidate_A_and_B": (
                    None if h2_cell is None else cells[h2_cell]["live_definitions"]
                ),
                "M_57_h2_lift_minus_swing": h2_lift_minus_swing,
                "M_47b_A_live_heldout_delta_at_confirm_ratio": m47b,
                "M_179_A_live_cells": all_a_live,
                "M_179_twin_deg_spread": m179,
            },
            "verdict": verdict,
            "controls": {
                "G23_212b_evidence": "results/RAW/phase-23/g23_212b_after.json",
                "G23_214_regime_crosscheck": {
                    "matched": g23_214_matches,
                    "total": len(analyzed),
                    "pass": g23_214_matches == len(analyzed),
                    "rows": regime_rows,
                },
                "NC_H_domain_checked_before_build": True,
                "NC_H_checked": len(domain),
                "NC_H_passed": sum(row["pass"] for row in domain.values()),
                "NC_H_by_cell": domain,
                "NC_I_identity_all_valid": bool(
                    all(
                        cells[cell]["controls"]["identity_residual_le_1e_12"]
                        for cell in analyzed
                    )
                ),
                "NC_J_crossfit_all_valid": bool(
                    all(
                        cells[cell]["controls"]["NC_A_all_row_disjoint"]
                        and cells[cell]["controls"]["NC_A_all_seed_disjoint"]
                        for cell in analyzed
                    )
                ),
                "NC_K_requested_cells": list(sla["requested_cells"]),
                "NC_K_passed_cells": list(sla["passed_cells"]),
                "NC_K_excluded_cells": list(sla["excluded_cells"]),
                "NC_K_fallback_triggered": sla["fallback_triggered"],
            },
            "validity": validity_block(
                aoi_generator=AOI_V7,
                z_edges=Z_EDGES_V7,
                sla_path=sla_path,
                w_loss=5000.0,
            ),
            "provenance": {
                "script": "cert/live_region_sweep.py::run_sweep",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(
                    git("git", "status", "--porcelain", "--untracked-files=no")
                ),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [
                    pin(AMENDMENT),
                    pin(sla_path),
                    pin(SLA_REGIME_BASE),
                    pin(SLA_REGIME_WAVE4),
                    pin(WAVE4_DIGESTS),
                ]
                + [
                    pin(_input_path(cell, base_calib_template, str(calib_template)))
                    for cell in analyzed
                ],
            },
        }
    )


def write_json(payload: Mapping[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(json_clean(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


def print_sweep(report: Mapping[str, Any]) -> None:
    print("=== LESSON 23.21h: LIVE REGION UNDER EXOGENOUS S-B ===")
    print("cell              err_neo  A  regime     B  agree  lift-swing")
    for cell in report["analyzed_cells"]:
        row = report["cells"][cell]
        defs = row["live_definitions"]
        d = row["lift_swing_F2"]
        print(
            "%-17s %.6f  %d  %-9s %d    %d    %+.6f"
            % (
                cell,
                d["err_neo"],
                defs["A_err_neo_ge_0_05"],
                defs["regime"],
                defs["B_regime_eq_LIVE"],
                defs["agreement"],
                d["lift"] - d["swing"],
            )
        )
    print(
        "agreement=%d/%d rho_hit=%s spread=%.6f"
        % (
            report["metrics"]["M_176_agreement_count"],
            report["metrics"]["M_176_total_cells"],
            report["metrics"]["M_177_rho_hit"],
            report["metrics"]["M_179_twin_deg_spread"],
        )
    )
    print("verdict=%s" % json.dumps(report["verdict"], sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--sla", default=SLA_EXOGENOUS_14)
    parser.add_argument("--calib-template", default=CALIB_TEMPLATE_WAVE4)
    parser.add_argument("--base-calib-template", default=BASE_CALIB_TEMPLATE)
    parser.add_argument("--out", default=OUTPUT)
    parser.add_argument("--prepare-sla", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.prepare_sla:
        parser.error(
            "--prepare-sla DA BI GO (amendment 23-62). No goi "
            "SLA.calibrate_cell, chinh co che S14 da bi bac bo o Lesson 23.21.\n"
            "  Thay bang:\n"
            "    python3 -m measurements.sla_manifest_exogenous_14\n"
            "    python3 -m cert.live_region_sweep --run --sla <manifest>"
        )
    if not args.run:
        parser.error("can --run (khong con nhanh hieu chuan SLA noi sinh)")

    report = run_sweep(
        calib_template=args.calib_template,
        sla_path=args.sla,
        base_calib_template=args.base_calib_template,
    )
    print_sweep(report)
    write_json(report, args.out)
    print("artifact -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

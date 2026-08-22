#!/usr/bin/env python3
"""Audit Phase T controls after the live run, including V-T5 gates."""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Dict, List, Sequence

from measurements.gate_specs import GATES
from measurements.t4_validate import (
    gate_aggregate_z,
    gate_row,
    gate_vt5b_same_seed_aggregate,
    gate_vt5b_z_aggregate,
    phase_l_q_refs,
    phase_l_seed_refs,
)
from measurements.t5_campaign import (
    BW,
    PHASE_L_STATE,
    PROBE_PPS,
    Q,
    SEALED,
    build_controls_plan,
    build_controls_sameseed_plan,
    campaign_summary,
    load_state,
    make_traj,
    public_row,
    save_state,
)
from mininet.rho_schedule import build_varying_schedule


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _sealed_metrics(sealed_dir: str, pid: str) -> Dict[str, Any]:
    payload = _load_json(os.path.join(sealed_dir, pid + ".json"))
    return dict(payload.get("sealed", {}))


def _gate_counts(rows: Sequence[Dict[str, Any]], gate: str) -> Dict[str, int]:
    seen = 0
    passed = 0
    failed = 0
    for row in rows:
        gates = row.get("gates", {})
        if gate not in gates:
            continue
        seen += 1
        if gates[gate]:
            passed += 1
        else:
            failed += 1
    return {"seen": seen, "pass": passed, "fail": failed}


def _rescore_row(row: Dict[str, Any], refs, seed_refs, sealed_dir: str) -> Dict[str, Any]:
    full = dict(row)
    full.update(_sealed_metrics(sealed_dir, str(row["pid"])))
    traj = make_traj(full)
    sched = build_varying_schedule(full["mode"], traj, float(full["bw"]), int(full["seed"]))
    gates = gate_row(
        full,
        traj,
        sched,
        None,
        0.0,
        phase_l_ref=refs,
        phase_l_seed_ref=seed_refs,
    )
    full["gates"] = gates
    full["gate_fail"] = [name for name, ok in gates.items() if not ok]
    return public_row(full)


def rescore_controls(
    state_path: str,
    sealed_dir: str = SEALED,
    phase_l_state: str = PHASE_L_STATE,
    stage: str = "controls",
    update_state: bool = False,
) -> Dict[str, Any]:
    state = load_state(state_path)
    phase_l = _load_json(phase_l_state)
    phase_l_rows = phase_l.get("rows", [])
    refs = phase_l_q_refs(phase_l_rows, BW, Q, PROBE_PPS)
    seed_refs = phase_l_seed_refs(phase_l_rows, BW, Q, PROBE_PPS)
    if stage == "controls":
        seed_refs_for_rows = None
        plan = build_controls_plan()
    elif stage in ("controls-sameseed", "controls-samesed"):
        seed_refs_for_rows = seed_refs
        plan = build_controls_sameseed_plan()
    else:
        raise ValueError("stage khong hop le cho audit: %s" % stage)

    rows = [
        _rescore_row(row, refs, seed_refs_for_rows, sealed_dir)
        for row in state.get("rows", [])
    ]
    rows.sort(key=lambda row: int(row["idx"]))

    summary = {
        "campaign": campaign_summary({**state, "rows": rows}, plan),
        "stage": stage,
        "V-T5a_delegation": _gate_counts(rows, "V-T5a_delegation"),
        "V-T5a_phase_l_digest": _gate_counts(rows, "V-T5a_phase_l_digest"),
        "V-T4a_ca_operational": _gate_counts(rows, "V-T4a_ca_operational"),
        "V-T6b_rho_bias": _gate_counts(rows, "V-T6b_rho_bias"),
        "aggregate": {
            "V-T5b_q_phase_l": gate_vt5b_z_aggregate(rows),
            "V-T5b_h2_r070": gate_aggregate_z(
                [
                    row
                    for row in rows
                    if row.get("mode") == "h2"
                    and abs(float(row.get("rho_bar", -1.0)) - 0.70) < 1e-9
                ],
                "vt5b_z",
                group_by=None,
            ),
            "V-T5b_same_seed": gate_vt5b_same_seed_aggregate(rows),
            "rho_bias_z": gate_aggregate_z(
                rows,
                "rho_bias_z",
                group_by=GATES["V-T6b_rho_bias"].corr_group,
            ),
            "ca_operational_z_h2": gate_aggregate_z(
                [row for row in rows if row.get("mode") == "h2"],
                "ca_operational_z",
                group_by=GATES["V-T4a_ca_operational"].corr_group,
            ),
            "ca_operational_z_poisson": gate_aggregate_z(
                [row for row in rows if row.get("mode") == "poisson"],
                "ca_operational_z",
                group_by=GATES["V-T4a_ca_operational"].corr_group,
            ),
        },
        "fail_examples": [
            {
                "idx": row["idx"],
                "mode": row["mode"],
                "rho_bar": row["rho_bar"],
                "seed": row["seed"],
                "gate_fail": row.get("gate_fail", []),
                "vt5b_z": row.get("vt5b_z"),
            }
            for row in rows
            if row.get("gate_fail")
        ][:12],
    }

    if update_state:
        state["rows"] = rows
        state["failed_rows"] = []
        save_state(state, state_path)
        summary["state_updated"] = True
    else:
        summary["state_updated"] = False
    return summary


def _fmt_bool(value: Any) -> str:
    return "OK" if value is True else "FAIL"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit T5 controls and rescore V-T5.")
    parser.add_argument("--state", default="results/SUPERSEDED/phase-T/control_state.json")
    parser.add_argument("--sealed-dir", default=SEALED)
    parser.add_argument("--phase-l-state", default=PHASE_L_STATE)
    parser.add_argument("--stage", choices=("controls", "controls-sameseed", "controls-samesed"), default="controls")
    parser.add_argument("--update-state", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summary = rescore_controls(
        args.state,
        sealed_dir=args.sealed_dir,
        phase_l_state=args.phase_l_state,
        stage=args.stage,
        update_state=args.update_state,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    print("T5 %s audit" % summary["stage"])
    camp = summary["campaign"]
    print(
        "  rows=%d done=%d/%d failed=%d"
        % (camp["n_rows"], camp["n_done"], camp["n_plan"], camp["n_fail"])
    )
    for gate in ("V-T5a_delegation", "V-T5a_phase_l_digest", "V-T4a_ca_operational", "V-T6b_rho_bias"):
        c = summary[gate]
        print("  %-22s seen=%2d pass=%2d fail=%2d" % (gate, c["seen"], c["pass"], c["fail"]))

    for name, agg in summary["aggregate"].items():
        if name == "V-T5b_same_seed" and agg["n"] > 0:
            print(
                "  %-24s n=%2d mean_r=%+.4f sd_r=%.4f mean_gate=%s sd_gate=%s"
                % (
                    name,
                    agg["n"],
                    agg["mean_rel"],
                    agg["sd_rel"],
                    _fmt_bool(agg["pass_mean"]),
                    _fmt_bool(agg["pass_sd"]),
                )
            )
            continue
        if agg["n"] == 0:
            continue
        print(
            "  %-24s n=%2d n_eff=%2d mean=%+.3f sd=%.3f mean_gate=%s sd_gate=%s"
            % (
                name,
                agg["n"],
                agg["n_eff"],
                agg["mean_z"],
                agg["sd_z"],
                _fmt_bool(agg["pass_mean"]),
                _fmt_bool(agg["pass_sd"]),
            )
        )

    if summary["fail_examples"]:
        print("  fail examples, no sealed q_mean:")
        for row in summary["fail_examples"]:
            print(
                "    idx=%s mode=%s rho=%.3f seed=%s gates=%s vt5b_z=%s"
                % (
                    row["idx"],
                    row["mode"],
                    float(row["rho_bar"]),
                    row["seed"],
                    ",".join(row["gate_fail"]),
                    "%.3f" % row["vt5b_z"]
                    if row.get("vt5b_z") is not None and math.isfinite(float(row["vt5b_z"]))
                    else "NA",
                )
            )
    print("  state_updated=%s" % summary["state_updated"])


if __name__ == "__main__":
    main()

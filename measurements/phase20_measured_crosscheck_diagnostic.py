#!/usr/bin/env python3
"""Summarize Phase 20 measured-telemetry cross-check caveats."""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import List

import numpy as np

from measurements.decision_error import drop_warmup_matrix, read_trace_matrix
from twin import topology_v7 as T7


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def read_json(path: str) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_csv_list(text: str) -> List[str]:
    vals = [part.strip() for part in str(text).split(",") if part.strip()]
    if not vals:
        raise ValueError("expected a comma-separated list")
    return vals


def paired_summary(xs: np.ndarray) -> dict:
    mean = float(xs.mean())
    sd = float(xs.std(ddof=1)) if len(xs) > 1 else 0.0
    se = sd / math.sqrt(len(xs)) if len(xs) > 0 else 0.0
    return {
        "values": xs.tolist(),
        "mean": mean,
        "sd": sd,
        "se": se,
        "t_stat": mean / se if se > 0.0 else None,
        "df": max(0, len(xs) - 1),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--offered-summary", default="results/phase-20/between_trace_summary_n5.json")
    p.add_argument(
        "--offered-runs",
        default=",".join(
            "results/phase-20/decision_error_trace_s%d.json" % i for i in range(5)
        ),
    )
    p.add_argument(
        "--measured-summary",
        default="results/phase-20/decision_error_measured_fixed_replicates_summary.json",
    )
    p.add_argument(
        "--measured-runs",
        default=",".join(
            "results/phase-20/decision_error_measured_fixed_trace_s%d.json" % i
            for i in range(5)
        ),
    )
    p.add_argument(
        "--measured-traces",
        default=",".join(
            ["results/phase-20/rho_measured_long.csv"]
            + ["results/phase-20/rho_measured_long_s%d.csv" % i for i in range(1, 5)]
        ),
    )
    p.add_argument("--out", default="results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    offered = read_json(args.offered_summary)
    measured = read_json(args.measured_summary)
    offered_runs = parse_csv_list(args.offered_runs)
    runs = parse_csv_list(args.measured_runs)
    traces = parse_csv_list(args.measured_traces)

    offered_err = np.asarray(offered["err"]["points"], dtype=float)
    offered_d_sla = np.asarray(offered["d_sla"]["points"], dtype=float)
    measured_err = np.asarray(measured["err"]["points"], dtype=float)
    measured_d_sla = np.asarray(measured["d_sla"]["points"], dtype=float)

    offered_mechanism_rows = []
    for idx, path in enumerate(offered_runs):
        data = read_json(path)
        mech = data["runs"]["100"]["mechanism"]["operational"]
        offered_mechanism_rows.append(
            {
                "trace_id": idx,
                "path": path,
                "risk_ratio": float(mech["risk_ratio"]),
                "p_error_given_crossed": float(mech["p_error_given_crossed"]),
                "p_error_given_not_crossed": float(mech["p_error_given_not_crossed"]),
                "share_errors_with_crossing": float(mech["share_errors_with_crossing"]),
            }
        )

    run_rows = []
    measured_mechanism_rows = []
    for idx, path in enumerate(runs):
        data = read_json(path)
        run = data["runs"]["100"]
        gate = run["gate"]
        op = run["evaluation"]["operational"]
        summary = run["evaluation"]["summary"]
        mech = run["mechanism"]["operational"]
        measured_mechanism_rows.append(
            {
                "trace_id": idx,
                "path": path,
                "risk_ratio": float(mech["risk_ratio"]),
                "p_error_given_crossed": float(mech["p_error_given_crossed"]),
                "p_error_given_not_crossed": float(mech["p_error_given_not_crossed"]),
                "share_errors_with_crossing": float(mech["share_errors_with_crossing"]),
            }
        )
        false_bool_gates = [
            key for key, value in gate.items() if isinstance(value, bool) and not value
        ]
        run_rows.append(
            {
                "trace_id": idx,
                "path": path,
                "dt_s": float(data["config"]["dt_s"]),
                "operational_mode": str(data["config"].get("operational_mode", "sawtooth")),
                "n_raw": int(data["config"]["n_raw"]),
                "n_after_warmup": int(data["config"]["n_after_warmup"]),
                "n_eval": int(summary["n_eval"]),
                "mean_age_s": float(op["mean_age_s"]),
                "age_bracket": op.get("bracket"),
                "err": float(op["err"]),
                "d_sla": float(op["d_sla"]),
                "base_violation": float(summary["base_violation"]),
                "twin_violation": float(op["twin_violation"]),
                "G3_pairwise": bool(gate["G3_pairwise_err_delta_bonferroni_positive"]),
                "pass_without_G6": bool(gate["pass_without_G6"]),
                "false_bool_gates": false_bool_gates,
                "risk_ratio": float(mech["risk_ratio"]),
                "p_error_given_crossed": float(mech["p_error_given_crossed"]),
                "p_error_given_not_crossed": float(mech["p_error_given_not_crossed"]),
                "err_by_z": {
                    key: float(row["err"]) for key, row in run["evaluation"]["per_z"].items()
                },
            }
        )

    core = ["ac", "ad", "bc", "bd"]
    core_idx = [T7.LINK_NAMES.index(link) for link in core]
    trace_rows = []
    for idx, path in enumerate(traces):
        rho, dt_s = read_trace_matrix(path, dt_s=None)
        warm = drop_warmup_matrix(rho, 0.2)
        trace_rows.append(
            {
                "trace_id": idx,
                "path": path,
                "dt_s": float(dt_s),
                "n_raw": int(len(rho)),
                "duration_s": float(len(rho) * dt_s),
                "core_mean_after_warmup": float(warm[:, core_idx].mean()),
                "core_std_after_warmup": float(warm[:, core_idx].std()),
                "all_link_mean_after_warmup": float(warm.mean()),
            }
        )

    result = {
        "paired_offered_minus_measured": {
            "err": paired_summary(offered_err - measured_err),
            "d_sla": paired_summary(offered_d_sla - measured_d_sla),
        },
        "mechanism_comparison": {
            "offered": {
                "rows": offered_mechanism_rows,
                "risk_ratio_mean": float(np.mean([r["risk_ratio"] for r in offered_mechanism_rows])),
                "risk_ratio_sd": float(np.std([r["risk_ratio"] for r in offered_mechanism_rows], ddof=1)),
                "p_error_given_crossed_mean": float(np.mean([r["p_error_given_crossed"] for r in offered_mechanism_rows])),
                "p_error_given_not_crossed_mean": float(np.mean([r["p_error_given_not_crossed"] for r in offered_mechanism_rows])),
                "share_errors_with_crossing_mean": float(np.mean([r["share_errors_with_crossing"] for r in offered_mechanism_rows])),
            },
            "measured_fixed": {
                "rows": measured_mechanism_rows,
                "risk_ratio_mean": float(np.mean([r["risk_ratio"] for r in measured_mechanism_rows])),
                "risk_ratio_sd": float(np.std([r["risk_ratio"] for r in measured_mechanism_rows], ddof=1)),
                "p_error_given_crossed_mean": float(np.mean([r["p_error_given_crossed"] for r in measured_mechanism_rows])),
                "p_error_given_not_crossed_mean": float(np.mean([r["p_error_given_not_crossed"] for r in measured_mechanism_rows])),
                "share_errors_with_crossing_mean": float(np.mean([r["share_errors_with_crossing"] for r in measured_mechanism_rows])),
            },
            "paired_measured_minus_offered": {
                "risk_ratio": paired_summary(
                    np.asarray([r["risk_ratio"] for r in measured_mechanism_rows], dtype=float)
                    - np.asarray([r["risk_ratio"] for r in offered_mechanism_rows], dtype=float)
                ),
                "p_error_given_not_crossed": paired_summary(
                    np.asarray([r["p_error_given_not_crossed"] for r in measured_mechanism_rows], dtype=float)
                    - np.asarray([r["p_error_given_not_crossed"] for r in offered_mechanism_rows], dtype=float)
                ),
            },
        },
        "measured_summary": {
            "err": measured["err"],
            "d_sla": measured["d_sla"],
            "gates": measured["gates"],
        },
        "measured_run_diagnostics": run_rows,
        "measured_trace_stats": trace_rows,
        "diagnosis": (
            "corrected measured telemetry cross-check uses representable z values "
            "and bracket interpolation at the Phase 20 reference age; old sawtooth "
            "measured outputs are invalid because 200 ms telemetry aliases AoI"
        ),
    }
    write_json(args.out, result)
    print("wrote %s" % args.out)
    print("paired err diff:", [round(x, 5) for x in result["paired_offered_minus_measured"]["err"]["values"]])
    print("paired d_sla diff:", [round(x, 5) for x in result["paired_offered_minus_measured"]["d_sla"]["values"]])
    rr = result["mechanism_comparison"]["paired_measured_minus_offered"]["risk_ratio"]
    print("paired measured-offered risk ratio diff:", [round(x, 3) for x in rr["values"]])
    print("risk ratio diff t:", round(rr["t_stat"], 3) if rr["t_stat"] is not None else None)
    for row in run_rows:
        print(
            "s%d mean_age=%.3f G3=%s false=%s"
            % (row["trace_id"], row["mean_age_s"], row["G3_pairwise"], row["false_bool_gates"])
        )


if __name__ == "__main__":
    main()

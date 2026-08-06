#!/usr/bin/env python3
"""Phase 20R.6 -- decision-level quasistatic analyzer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements.additivity_check import DELTA_MS, parse_int_list, stable_digest, tost_equivalence, write_json


MODE = "poisson"
RHO_BAR = 0.925
SEEDS = (101, 102, 103, 104, 105)
DURATION_S = 600.0
WINDOW_S = 60.0
OUT = "results/phase-20R/quasistatic_check.json"


def build_plan(
    mode: str = MODE,
    rho_bar: float = RHO_BAR,
    seeds: Sequence[int] = SEEDS,
    duration_s: float = DURATION_S,
    window_s: float = WINDOW_S,
) -> Dict[str, Any]:
    rows = [
        {
            "mode": str(mode),
            "rho_bar": float(rho_bar),
            "seed": int(seed),
            "duration_s": float(duration_s),
            "window_s": float(window_s),
            "n_windows": int(round(float(duration_s) / float(window_s))),
        }
        for seed in seeds
    ]
    return {
        "phase": "20R.6",
        "kind": "quasistatic_design",
        "mode": str(mode),
        "rho_bar": float(rho_bar),
        "duration_s": float(duration_s),
        "window_s": float(window_s),
        "seeds": [int(seed) for seed in seeds],
        "rows": rows,
        "plan_digest": stable_digest(rows),
    }


def _load_rows(paths: Sequence[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in paths:
        if not path:
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows = data if isinstance(data, list) else data.get("rows", [])
        for row in rows:
            if "windows" in row:
                for win in row["windows"]:
                    merged = {k: v for k, v in row.items() if k != "windows"}
                    merged.update(win)
                    out.append(merged)
            else:
                out.append(dict(row))
    return out


def _value(row: Mapping[str, Any], names: Sequence[str]) -> Optional[float]:
    for name in names:
        if row.get(name) is not None:
            return float(row[name])
    return None


def _frame(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    flat = []
    for row in rows:
        measured = _value(row, ("measured_cost_ms", "dynamic_cost_ms", "observed_cost_ms", "cost_ms"))
        table = _value(row, ("table_cost_ms", "static_cost_ms", "predicted_cost_ms"))
        if measured is None or table is None:
            continue
        flat.append(
            {
                **dict(row),
                "seed": int(row["seed"]),
                "window_idx": int(row.get("window_idx", row.get("window", 0))),
                "measured_cost_ms": measured,
                "table_cost_ms": table,
                "diff_ms": measured - table,
            }
        )
    return pd.DataFrame(flat)


def _digest_report(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or "trajectory_digest" not in df.columns:
        return {"available": False, "pass": False, "reason": "missing trajectory_digest"}
    per_seed = df.groupby("seed")["trajectory_digest"].nunique(dropna=True)
    bad = per_seed[per_seed != 1]
    return {
        "available": True,
        "pass": bool(bad.empty),
        "n_problem": int(len(bad)),
        "problems": [{"seed": int(seed), "n_digest": int(n)} for seed, n in bad.items()],
    }


def analyze(
    rows: Sequence[Mapping[str, Any]],
    mode: str = MODE,
    rho_bar: float = RHO_BAR,
    seeds: Sequence[int] = SEEDS,
    duration_s: float = DURATION_S,
    window_s: float = WINDOW_S,
    delta_ms: float = DELTA_MS,
) -> Dict[str, Any]:
    plan = build_plan(mode=mode, rho_bar=rho_bar, seeds=seeds, duration_s=duration_s, window_s=window_s)
    df = _frame(rows)
    report: Dict[str, Any] = {
        "phase": "20R.6",
        "script": "measurements.quasistatic_check",
        "kind": "decision_quasistatic_analysis",
        "delta_ms": float(delta_ms),
        "plan_digest": plan["plan_digest"],
        "summary": {
            "n_input_rows": int(len(rows)),
            "n_windows": int(len(df)),
            "evaluated": bool(not df.empty),
        },
        "checks": [],
    }
    if df.empty:
        report["summary"].update({"pass": False, "reason": "no rows with measured/table cost fields"})
        return report

    max_abs = float(np.max(np.abs(df["diff_ms"])))
    report["summary"].update(
        {
            "mean_diff_ms": float(np.mean(df["diff_ms"])),
            "max_abs_diff_ms": max_abs,
            "threshold_ms": float(delta_ms),
            "pass": bool(max_abs <= float(delta_ms)),
        }
    )
    for seed, group in df.groupby("seed", sort=True):
        report["checks"].append(
            {
                "seed": int(seed),
                "n_windows": int(len(group)),
                "mean_diff_ms": float(np.mean(group["diff_ms"])),
                "max_abs_diff_ms": float(np.max(np.abs(group["diff_ms"]))),
                **tost_equivalence(group["diff_ms"], delta_ms=delta_ms),
            }
        )
    report["paired_schedule"] = _digest_report(df)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-state", default="", help="comma-separated JSON state/result files containing quasistatic rows")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--mode", default=MODE)
    ap.add_argument("--rho-bar", type=float, default=RHO_BAR)
    ap.add_argument("--seeds", default=",".join(str(seed) for seed in SEEDS))
    ap.add_argument("--duration-s", type=float, default=DURATION_S)
    ap.add_argument("--window-s", type=float, default=WINDOW_S)
    ap.add_argument("--delta-ms", type=float, default=DELTA_MS)
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--write-plan", default="")
    args = ap.parse_args(argv)

    seeds = parse_int_list(args.seeds)
    plan = build_plan(args.mode, args.rho_bar, seeds, args.duration_s, args.window_s)
    if args.plan_only:
        print(json.dumps({"plan_digest": plan["plan_digest"], "rows": len(plan["rows"]), "n_windows": plan["rows"][0]["n_windows"]}, indent=2, sort_keys=True))
        return 0
    if args.write_plan:
        write_json(args.write_plan, plan)
        print("plan rows=%d -> %s" % (len(plan["rows"]), args.write_plan))
        return 0
    paths = tuple(part.strip() for part in str(args.from_state).split(",") if part.strip())
    report = analyze(_load_rows(paths), args.mode, args.rho_bar, seeds, args.duration_s, args.window_s, args.delta_ms)
    write_json(args.out, report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("quasistatic -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

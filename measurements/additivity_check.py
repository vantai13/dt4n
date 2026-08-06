#!/usr/bin/env python3
"""Phase 20R.6 -- additivity design and G6 analyzer.

The live runner is intentionally separate from this analyzer. This file locks
the paired design, computes branch-A table sums, and evaluates TOST
equivalence on branch-C minus sum(branch-B) when the measured branch rows are
available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements import decision_error_v2 as D
from twin import cost_v2 as C
from twin import topology_v7 as T7


MODES = ("poisson", "h2")
RHO_BARS = (0.85, 0.925)
PATHS_MAIN = ("P1", "P4")
PATHS_EXTRA = ("P2",)
DEFAULT_BRANCH_B_PATHS = ("P1",)
DEFAULT_BRANCH_B_RHO_BARS = (0.925,)
DEFAULT_EXTRA_PATH_MODES = ("poisson",)
DEFAULT_EXTRA_PATH_RHO_BARS = (0.925,)
SEEDS = (101, 102, 103, 104, 105)
DELTA_MS = 0.44
PROBE_INTRUSION_MAX = 0.02
OUT = "results/phase-20R/additivity_check.json"


def stable_digest(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(path: str, data: object) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_list(text: str) -> Tuple[str, ...]:
    return tuple(part.strip() for part in str(text).split(",") if part.strip())


def parse_float_list(text: str) -> Tuple[float, ...]:
    return tuple(float(part.strip()) for part in str(text).split(",") if part.strip())


def parse_int_list(text: str) -> Tuple[int, ...]:
    vals = tuple(int(part.strip()) for part in str(text).split(",") if part.strip())
    if not vals:
        raise ValueError("expected at least one seed")
    return vals


def tcrit_95(df: int) -> float:
    table = {
        1: 6.313752,
        2: 2.919986,
        3: 2.353363,
        4: 2.131847,
        5: 2.015048,
        6: 1.943180,
        7: 1.894579,
        8: 1.859548,
        9: 1.833113,
        10: 1.812461,
        11: 1.795885,
        12: 1.782288,
        13: 1.770933,
        14: 1.761310,
        15: 1.753050,
        16: 1.745884,
        17: 1.739607,
        18: 1.734064,
        19: 1.729133,
        20: 1.724718,
        24: 1.710882,
        30: 1.697261,
    }
    if int(df) in table:
        return table[int(df)]
    if int(df) <= 0:
        raise ValueError("df must be positive")
    return 1.644854 if int(df) >= 120 else 1.697261


def tost_equivalence(samples: Sequence[float], delta_ms: float = DELTA_MS) -> Dict[str, Any]:
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        return {"n": 0, "equiv_pass": False, "power_ok": False, "reason": "no_samples"}
    mean = float(np.mean(arr))
    sd = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    se = sd / math.sqrt(float(arr.size)) if arr.size > 1 else 0.0
    tcrit = tcrit_95(int(arr.size) - 1) if arr.size > 1 else 0.0
    ci_lo = mean - tcrit * se
    ci_hi = mean + tcrit * se
    return {
        "n": int(arr.size),
        "mean_ms": mean,
        "sd_ms": sd,
        "se_ms": se,
        "ci90_lo_ms": float(ci_lo),
        "ci90_hi_ms": float(ci_hi),
        "delta_ms": float(delta_ms),
        "equiv_pass": bool(ci_lo >= -float(delta_ms) and ci_hi <= float(delta_ms)),
        "power_check_1p645se_ms": float(1.644854 * se),
        "power_ok": bool(1.644854 * se < float(delta_ms)),
    }


def selected_paths(main_paths: Sequence[str] = PATHS_MAIN, extra_paths: Sequence[str] = PATHS_EXTRA) -> Tuple[str, ...]:
    out = tuple(main_paths) + tuple(path for path in extra_paths if path not in main_paths)
    for path in out:
        if path not in T7.PATHS:
            raise ValueError("unknown path %r" % path)
    return out


def path_mode_rho_specs(
    modes: Sequence[str] = MODES,
    rho_bars: Sequence[float] = RHO_BARS,
    paths: Sequence[str] = selected_paths(),
    extra_paths: Sequence[str] = PATHS_EXTRA,
    extra_modes: Sequence[str] = DEFAULT_EXTRA_PATH_MODES,
    extra_rho_bars: Sequence[float] = DEFAULT_EXTRA_PATH_RHO_BARS,
) -> List[Tuple[str, float, str]]:
    specs: List[Tuple[str, float, str]] = []
    extra = set(str(path) for path in extra_paths)
    for path in paths:
        use_modes = extra_modes if path in extra else modes
        use_rhos = extra_rho_bars if path in extra else rho_bars
        for mode in use_modes:
            for rho_bar in use_rhos:
                specs.append((str(mode), float(rho_bar), str(path)))
    return specs


def build_plan(
    modes: Sequence[str] = MODES,
    rho_bars: Sequence[float] = RHO_BARS,
    seeds: Sequence[int] = SEEDS,
    paths: Sequence[str] = selected_paths(),
    branch_b_paths: Sequence[str] = DEFAULT_BRANCH_B_PATHS,
    branch_b_rho_bars: Sequence[float] = DEFAULT_BRANCH_B_RHO_BARS,
    extra_path_modes: Sequence[str] = DEFAULT_EXTRA_PATH_MODES,
    extra_path_rho_bars: Sequence[float] = DEFAULT_EXTRA_PATH_RHO_BARS,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    specs = path_mode_rho_specs(
        modes=modes,
        rho_bars=rho_bars,
        paths=paths,
        extra_modes=extra_path_modes,
        extra_rho_bars=extra_path_rho_bars,
    )
    for mode, rho_bar, path in specs:
        rows.append({"branch": "A", "mode": mode, "rho_bar": float(rho_bar), "path": path, "source": "truth_table"})
    for mode in modes:
        for rho_bar in branch_b_rho_bars:
            for path in branch_b_paths:
                for link in T7.PATHS[path]:
                    for seed in seeds:
                        rows.append(
                            {
                                "branch": "B",
                                "mode": mode,
                                "rho_bar": float(rho_bar),
                                "path": path,
                                "link": link,
                                "seed": int(seed),
                                "probe": "single_link",
                            }
                        )
    for mode, rho_bar, path in specs:
        for seed in seeds:
            rows.append(
                {
                    "branch": "C",
                    "mode": mode,
                    "rho_bar": float(rho_bar),
                    "path": path,
                    "seed": int(seed),
                    "probe": "end_to_end_path",
                }
            )
    counts = {
        "A_table_cells": sum(1 for row in rows if row["branch"] == "A"),
        "B_live_runs": sum(1 for row in rows if row["branch"] == "B"),
        "C_live_runs": sum(1 for row in rows if row["branch"] == "C"),
    }
    plan = {
        "phase": "20R.6",
        "kind": "additivity_design",
        "delta_ms": DELTA_MS,
        "modes": list(modes),
        "rho_bars": [float(rho) for rho in rho_bars],
        "seeds": [int(seed) for seed in seeds],
        "paths": list(paths),
        "branch_b_paths": list(branch_b_paths),
        "branch_b_rho_bars": [float(rho) for rho in branch_b_rho_bars],
        "extra_path_modes": list(extra_path_modes),
        "extra_path_rho_bars": [float(rho) for rho in extra_path_rho_bars],
        "counts": counts,
        "rows": rows,
    }
    plan["plan_digest"] = stable_digest(plan["rows"])
    return plan


def calibration_by_cell(calibration_path: str) -> Dict[Tuple[str, float], Mapping[str, Any]]:
    out = {}
    for cell in D.feasible_cells(calibration_path, include_pc1=False):
        out[(str(cell["mode"]), round(float(cell["rho_bar"]), 12))] = cell
    return out


def branch_a_rows(
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
    modes: Sequence[str] = MODES,
    rho_bars: Sequence[float] = RHO_BARS,
    paths: Sequence[str] = selected_paths(),
    extra_path_modes: Sequence[str] = DEFAULT_EXTRA_PATH_MODES,
    extra_path_rho_bars: Sequence[float] = DEFAULT_EXTRA_PATH_RHO_BARS,
) -> List[Dict[str, Any]]:
    tt = D.TruthTable(truth_table)
    calib = calibration_by_cell(calibration_path)
    rows = []
    for mode, rho_bar, path in path_mode_rho_specs(modes, rho_bars, paths, extra_modes=extra_path_modes, extra_rho_bars=extra_path_rho_bars):
        cell = calib[(str(mode), round(float(rho_bar), 12))]
        w_loss = float(cell["w_loss"])
        delay_sum = 0.0
        loss_sum = 0.0
        keep = 1.0
        clip_max = 0.0
        for link in T7.PATHS[path]:
            rho = float(rho_bar) + float(C.LINK_OFFSET[link])
            d, loss = tt.delay_loss(str(mode), link, np.asarray([rho], dtype=float))
            delay_sum += float(d[0])
            loss_sum += float(loss[0])
            keep *= 1.0 - float(loss[0])
            clip_max = max(clip_max, max(tt.clip_log.values()) if tt.clip_log else 0.0)
        rows.append(
            {
                "branch": "A",
                "mode": str(mode),
                "rho_bar": float(rho_bar),
                "path": str(path),
                "delay_ms": float(delay_sum),
                "loss_sum": float(loss_sum),
                "loss_e2e_composed": float(1.0 - keep),
                "w_loss": float(w_loss),
                "cost_ms": float(delay_sum + w_loss * loss_sum),
                "clip_fraction_max": float(clip_max),
            }
        )
    return rows


def load_rows(paths: Sequence[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        if not path:
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            rows.extend(dict(row) for row in data)
        else:
            rows.extend(dict(row) for row in data.get("rows", []))
    return rows


def _row_metric(row: Mapping[str, Any]) -> float:
    if row.get("cost_ms") is not None:
        return float(row["cost_ms"])
    delay = row.get("q_mean_ms", row.get("delay_ms", row.get("mean_ms")))
    if delay is None:
        raise ValueError("row lacks cost_ms/q_mean_ms/delay_ms")
    return float(delay) + float(row.get("w_loss", 0.0)) * float(row.get("loss", 0.0))


def _measurement_frame(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).copy()
    required = {"branch", "mode", "rho_bar", "path"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("measurement rows missing columns: %s" % sorted(missing))
    df["metric_ms"] = [_row_metric(row) for row in rows]
    df["rho_bar"] = df["rho_bar"].astype(float)
    if "seed" in df.columns:
        df["seed"] = df["seed"].astype(int)
    return df


def _digest_ok(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or "trajectory_digest" not in df.columns:
        return {"available": False, "pass": False, "reason": "missing trajectory_digest"}
    problems = []
    for key, group in df.groupby(["mode", "rho_bar", "path", "seed"], sort=True):
        digests = sorted(set(str(v) for v in group["trajectory_digest"] if pd.notna(v) and str(v)))
        if len(digests) != 1:
            problems.append({"mode": key[0], "rho_bar": float(key[1]), "path": key[2], "seed": int(key[3]), "digests": digests})
    return {"available": True, "pass": bool(not problems), "n_problem": len(problems), "problems": problems[:20]}


def _probe_intrusion(df: pd.DataFrame) -> Dict[str, Any]:
    col = None
    for candidate in ("probe_intrusion_ratio", "probe_intrusion", "probe_intrusion_frac"):
        if candidate in df.columns:
            col = candidate
            break
    if col is None:
        return {"available": False, "pass": False, "reason": "missing probe intrusion column"}
    vals = pd.to_numeric(df[col], errors="coerce").dropna()
    if vals.empty:
        return {"available": False, "pass": False, "reason": "probe intrusion column empty"}
    max_val = float(vals.max())
    return {"available": True, "max": max_val, "threshold": PROBE_INTRUSION_MAX, "pass": bool(max_val <= PROBE_INTRUSION_MAX)}


def analyze(
    measurement_rows: Sequence[Mapping[str, Any]],
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
    modes: Sequence[str] = MODES,
    rho_bars: Sequence[float] = RHO_BARS,
    paths: Sequence[str] = selected_paths(),
    delta_ms: float = DELTA_MS,
) -> Dict[str, Any]:
    a_rows = branch_a_rows(truth_table, calibration_path, modes=modes, rho_bars=rho_bars, paths=paths)
    df = _measurement_frame(measurement_rows)
    plan = build_plan(modes=modes, rho_bars=rho_bars, paths=paths)
    result: Dict[str, Any] = {
        "phase": "20R.6",
        "script": "measurements.additivity_check",
        "kind": "additivity_analysis",
        "delta_ms": float(delta_ms),
        "plan_digest": plan["plan_digest"],
        "branch_a": a_rows,
        "checks": [],
        "summary": {
            "n_measurement_rows": int(len(df)),
            "has_branch_b": bool(not df.empty and (df["branch"] == "B").any()),
            "has_branch_c": bool(not df.empty and (df["branch"] == "C").any()),
        },
    }
    if df.empty:
        result["summary"].update({"g6_evaluated": False, "g6_pass": False, "reason": "no live branch B/C rows"})
        return result

    result["paired_schedule"] = _digest_ok(df[df["branch"].isin(["B", "C"])])
    result["probe_intrusion"] = _probe_intrusion(df)
    b = df[df["branch"] == "B"].copy()
    c = df[df["branch"] == "C"].copy()
    if not b.empty:
        b_sum = b.groupby(["mode", "rho_bar", "path", "seed"], sort=True)["metric_ms"].sum().reset_index(name="sum_b_ms")
        merged = c.merge(b_sum, on=["mode", "rho_bar", "path", "seed"], how="inner")
        if not merged.empty:
            merged["delta_ms"] = merged["metric_ms"] - merged["sum_b_ms"]
            for key, group in merged.groupby(["mode", "rho_bar", "path"], sort=True):
                result["checks"].append(
                    {
                        "contrast": "C_minus_sumB",
                        "mode": key[0],
                        "rho_bar": float(key[1]),
                        "path": key[2],
                        **tost_equivalence(group["delta_ms"], delta_ms=delta_ms),
                    }
                )

    a = pd.DataFrame(a_rows)[["mode", "rho_bar", "path", "cost_ms"]].rename(columns={"cost_ms": "sum_a_ms"})
    merged_a = c.merge(a, on=["mode", "rho_bar", "path"], how="inner")
    if not merged_a.empty:
        merged_a["delta_ms"] = merged_a["metric_ms"] - merged_a["sum_a_ms"]
        for key, group in merged_a.groupby(["mode", "rho_bar", "path"], sort=True):
            result["checks"].append(
                {
                    "contrast": "C_minus_sumA",
                    "mode": key[0],
                    "rho_bar": float(key[1]),
                    "path": key[2],
                    **tost_equivalence(group["delta_ms"], delta_ms=delta_ms),
                }
            )
    g6_checks = [row for row in result["checks"] if row.get("contrast") == "C_minus_sumB"]
    result["summary"].update(
        {
            "g6_evaluated": bool(g6_checks),
            "g6_pass": bool(g6_checks and all(row.get("equiv_pass") for row in g6_checks)),
            "power_pass": bool(g6_checks and all(row.get("power_ok") for row in g6_checks)),
            "paired_schedule_pass": bool(result.get("paired_schedule", {}).get("pass")),
            "probe_intrusion_pass": bool(result.get("probe_intrusion", {}).get("pass")),
        }
    )
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth-table", default=D.TRUTH_TABLE)
    ap.add_argument("--calibration", default=D.CALIBRATION)
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--rho-bars", default=",".join("%.3f" % r for r in RHO_BARS))
    ap.add_argument("--paths", default=",".join(selected_paths()))
    ap.add_argument("--branch-b-paths", default=",".join(DEFAULT_BRANCH_B_PATHS))
    ap.add_argument("--branch-b-rho-bars", default=",".join("%.3f" % r for r in DEFAULT_BRANCH_B_RHO_BARS))
    ap.add_argument("--extra-path-modes", default=",".join(DEFAULT_EXTRA_PATH_MODES))
    ap.add_argument("--extra-path-rho-bars", default=",".join("%.3f" % r for r in DEFAULT_EXTRA_PATH_RHO_BARS))
    ap.add_argument("--seeds", default=",".join(str(seed) for seed in SEEDS))
    ap.add_argument("--delta-ms", type=float, default=DELTA_MS)
    ap.add_argument("--from-state", default="", help="comma-separated JSON state/result files containing branch B/C rows")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--write-plan", default="", help="write design plan JSON and exit")
    args = ap.parse_args(argv)

    modes = parse_list(args.modes)
    rho_bars = parse_float_list(args.rho_bars)
    paths = parse_list(args.paths)
    branch_b_paths = parse_list(args.branch_b_paths)
    branch_b_rho_bars = parse_float_list(args.branch_b_rho_bars)
    extra_path_modes = parse_list(args.extra_path_modes)
    extra_path_rho_bars = parse_float_list(args.extra_path_rho_bars)
    seeds = parse_int_list(args.seeds)
    plan = build_plan(
        modes=modes,
        rho_bars=rho_bars,
        seeds=seeds,
        paths=paths,
        branch_b_paths=branch_b_paths,
        branch_b_rho_bars=branch_b_rho_bars,
        extra_path_modes=extra_path_modes,
        extra_path_rho_bars=extra_path_rho_bars,
    )
    if args.plan_only:
        print(json.dumps({"counts": plan["counts"], "plan_digest": plan["plan_digest"]}, indent=2, sort_keys=True))
        return 0
    if args.write_plan:
        write_json(args.write_plan, plan)
        print("plan rows=%d -> %s" % (len(plan["rows"]), args.write_plan))
        return 0
    rows = load_rows(parse_list(args.from_state))
    report = analyze(rows, args.truth_table, args.calibration, modes=modes, rho_bars=rho_bars, paths=paths, delta_ms=args.delta_ms)
    write_json(args.out, report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("additivity -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

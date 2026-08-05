#!/usr/bin/env python3
"""Build the Phase 20R measured ground-truth lookup table.

The table combines Phase L static measurements with the Phase 20R fine grid.
Sentinels, failed rows, on/off rows, and probe-off controls are excluded.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from measurements import l6_campaign as L6
from measurements import l6_campaign_fine as FINE


PHASE_L_STATE = "results/phase-L/campaign_state.json"
PHASE_20R_STATE = "results/phase-20R/campaign_state.json"
CALIBRATION = FINE.CALIBRATION
CONTINUITY_STATE = "results/phase-20R/continuity_state.json"
TRUTH_TABLE = "results/phase-20R/truth_table.parquet"
TRUTH_TABLE_CSV = "results/phase-20R/truth_table.csv"
CONTINUITY_JSON = "results/phase-20R/continuity_check.json"
SENTINEL_JSON = "results/phase-20R/sentinel_control.json"
VALID_MODES = {"cbr", "poisson", "h2"}
TRUTH_FIELD = "q_mean_ms"
TRUTH_FIELD_NOTE = "probe_mean_ms KHONG dung -- probe deu dan, khong thoa PASTA"
TruthGrid = Mapping[Tuple[str, float, int], set[float]]


def load_state(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def usable_row(row: Mapping[str, Any]) -> bool:
    if row.get("gate_fail"):
        return False
    if row.get("block") == "E":
        return False
    if str(row.get("mode")) not in VALID_MODES:
        return False
    if float(row.get("probe_pps", 20.0)) != 20.0:
        return False
    return True


def truth_grid(calibration_path: str = CALIBRATION) -> Dict[Tuple[str, float, int], set[float]]:
    calib = FINE.load_calibration(calibration_path)
    need = FINE.required_rho_ranges(calib)
    return {
        key: {round(float(rho), 4) for rho in FINE.rho_grid(key[0], lo, hi)}
        for key, (lo, hi) in need.items()
    }


def in_truth_grid(row: Mapping[str, Any], grid: TruthGrid) -> bool:
    key = (str(row["mode"]), float(row["bw"]), int(row["q"]))
    return key in grid and round(float(row["rho"]), 4) in grid[key]


def rows_from_state(
    state: Mapping[str, Any],
    source: str,
    grid: Optional[TruthGrid] = None,
) -> List[Dict[str, Any]]:
    out = []
    for row in state.get("rows", []):
        if not usable_row(row):
            continue
        if grid is not None and not in_truth_grid(row, grid):
            continue
        assert TRUTH_FIELD in row, "thieu truong ground truth %s" % TRUTH_FIELD
        out.append(
            {
                "source": source,
                "mode": str(row["mode"]),
                "bw": float(row["bw"]),
                "q": int(row["q"]),
                "rho": round(float(row["rho"]), 4),
                "delay_ms": float(row[TRUTH_FIELD]),
                "loss": float(row["loss"]),
                "se_batch_ms": float(row["se_batch_ms"]) if row.get("se_batch_ms") is not None else math.nan,
                "se_naive_ms": float(row["se_naive_ms"]) if row.get("se_naive_ms") is not None else math.nan,
                "n_pkt": int(row["n_recv_unique"]),
                "seed": int(row["seed"]),
                "idx": int(row["idx"]),
                "schedule_digest": str(row.get("schedule_digest", "")),
            }
        )
    return out


def merge_states(
    phase_l_state: Mapping[str, Any],
    phase_20r_state: Mapping[str, Any],
    grid: Optional[TruthGrid] = None,
) -> pd.DataFrame:
    rows = rows_from_state(phase_l_state, "phase-L", grid) + rows_from_state(phase_20r_state, "phase-20R", grid)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "mode",
                "bw",
                "q",
                "rho",
                "delay_mean_ms",
                "delay_sd_ms",
                "loss",
                "se_batch_mean_ms",
                "se_naive_mean_ms",
                "n_seed",
                "n_rows",
                "n_pkt",
                "source",
                "se_mean_ms",
            ]
        )
    grouped = df.groupby(["mode", "bw", "q", "rho"], sort=True)
    table = grouped.agg(
        delay_mean_ms=("delay_ms", "mean"),
        delay_sd_ms=("delay_ms", "std"),
        loss=("loss", "mean"),
        se_batch_mean_ms=("se_batch_ms", "mean"),
        se_naive_mean_ms=("se_naive_ms", "mean"),
        n_seed=("seed", "nunique"),
        n_rows=("seed", "size"),
        n_pkt=("n_pkt", "sum"),
        source=("source", lambda x: "+".join(sorted(set(str(v) for v in x)))),
    ).reset_index()
    table["delay_sd_ms"] = table["delay_sd_ms"].fillna(0.0)
    table["se_mean_ms"] = table["delay_sd_ms"] / table["n_seed"].pow(0.5)
    table.attrs["truth_field"] = TRUTH_FIELD
    table.attrs["truth_field_note"] = TRUTH_FIELD_NOTE
    return table


def write_parquet_with_metadata(table: pd.DataFrame, out_path: str) -> None:
    metadata = {
        "phase": "20R",
        "truth_field": TRUTH_FIELD,
        "truth_field_note": TRUTH_FIELD_NOTE,
    }
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        arrow = pa.Table.from_pandas(table, preserve_index=False)
        merged = dict(arrow.schema.metadata or {})
        merged.update({k.encode("utf-8"): v.encode("utf-8") for k, v in metadata.items()})
        pq.write_table(arrow.replace_schema_metadata(merged), out_path)
    except Exception:
        table.to_parquet(out_path, index=False)
        Path(out_path + ".meta.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def write_truth_table(
    phase_l_path: str = PHASE_L_STATE,
    phase_20r_path: str = PHASE_20R_STATE,
    out_path: str = TRUTH_TABLE,
    csv_path: Optional[str] = TRUTH_TABLE_CSV,
    calibration_path: str = CALIBRATION,
) -> pd.DataFrame:
    table = merge_states(load_state(phase_l_path), load_state(phase_20r_path), truth_grid(calibration_path))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_parquet_with_metadata(table, str(out))
    if csv_path:
        table.to_csv(csv_path, index=False)
    return table


def _matching_phase_l_rows(
    phase_l_state: Mapping[str, Any],
    mode: str,
    bw: float,
    q: int,
    rho: float,
) -> List[Mapping[str, Any]]:
    rows = []
    for row in phase_l_state.get("rows", []):
        if not usable_row(row):
            continue
        if (
            str(row["mode"]) == mode
            and abs(float(row["bw"]) - float(bw)) < 1e-9
            and int(row["q"]) == int(q)
            and abs(float(row["rho"]) - float(rho)) < 1e-9
        ):
            rows.append(row)
    return rows


def continuity_report(
    phase_l_state: Mapping[str, Any],
    continuity_state: Mapping[str, Any],
) -> Dict[str, Any]:
    checks = []
    for row in continuity_state.get("rows", []):
        if row.get("block") != "G":
            continue
        refs = _matching_phase_l_rows(
            phase_l_state,
            str(row["mode"]),
            float(row["bw"]),
            int(row["q"]),
            float(row["rho"]),
        )
        if not refs:
            checks.append({**{k: row[k] for k in ("mode", "bw", "q", "rho", "seed")}, "pass": False, "reason": "no_phase_l_reference"})
            continue
        ref_mean = sum(float(r["q_mean_ms"]) for r in refs) / len(refs)
        ref_se = sum(float(r["se_batch_ms"]) for r in refs if r.get("se_batch_ms") is not None) / len(refs)
        new_se = float(row["se_batch_ms"]) if row.get("se_batch_ms") is not None else math.nan
        diff = float(row["q_mean_ms"]) - ref_mean
        tol = 2.0 * math.sqrt(ref_se * ref_se + new_se * new_se)
        checks.append(
            {
                "mode": str(row["mode"]),
                "bw": float(row["bw"]),
                "q": int(row["q"]),
                "rho": float(row["rho"]),
                "seed": int(row["seed"]),
                "phase_l_n": len(refs),
                "phase_l_mean_ms": ref_mean,
                "phase20r_ms": float(row["q_mean_ms"]),
                "diff_ms": diff,
                "tol_2se_ms": tol,
                "pass": bool(abs(diff) <= tol),
            }
        )
    return {
        "n": len(checks),
        "n_pass": sum(1 for row in checks if row.get("pass")),
        "all_pass": bool(checks and all(row.get("pass") for row in checks)),
        "checks": checks,
    }


def write_continuity_check(
    phase_l_path: str = PHASE_L_STATE,
    continuity_path: str = CONTINUITY_STATE,
    out_path: str = CONTINUITY_JSON,
) -> Dict[str, Any]:
    report = continuity_report(load_state(phase_l_path), load_state(continuity_path))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def sentinel_report(phase_20r_state: Mapping[str, Any]) -> Dict[str, Any]:
    summary = L6.sentinel_summary(phase_20r_state.get("sentinels", []))
    values = [float(row["q_mean_ms"]) for row in phase_20r_state.get("sentinels", [])]
    if summary.get("n", 0) and summary.get("sd_ms") is not None:
        summary["cv"] = float(summary["sd_ms"]) / max(abs(float(summary["mean_ms"])), 1e-12)
        summary["cv_pass_0p2pct"] = bool(summary["cv"] < 0.002)
    else:
        summary["cv"] = None
        summary["cv_pass_0p2pct"] = None
    return {"reference": L6.SENTINEL_REF, "values_ms": values, "summary": summary}


def write_sentinel_control(
    phase_20r_path: str = PHASE_20R_STATE,
    out_path: str = SENTINEL_JSON,
) -> Dict[str, Any]:
    report = sentinel_report(load_state(phase_20r_path))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase-l-state", "--phase-l", dest="phase_l_state", default=PHASE_L_STATE)
    ap.add_argument("--phase-20r-state", "--state", dest="phase_20r_state", default=PHASE_20R_STATE)
    ap.add_argument("--calibration", default=CALIBRATION)
    ap.add_argument("--continuity-state", default=CONTINUITY_STATE)
    ap.add_argument("--out", default=TRUTH_TABLE)
    ap.add_argument("--csv-out", default=TRUTH_TABLE_CSV)
    ap.add_argument("--continuity-out", default=CONTINUITY_JSON)
    ap.add_argument("--sentinel-out", default=SENTINEL_JSON)
    ap.add_argument("--skip-truth", action="store_true")
    ap.add_argument("--skip-continuity", action="store_true")
    ap.add_argument("--skip-sentinel", action="store_true")
    args = ap.parse_args(argv)

    if not args.skip_truth:
        table = write_truth_table(args.phase_l_state, args.phase_20r_state, args.out, args.csv_out, args.calibration)
        print("truth rows=%d field=%s -> %s" % (len(table), TRUTH_FIELD, args.out))
    if not args.skip_continuity:
        report = write_continuity_check(args.phase_l_state, args.continuity_state, args.continuity_out)
        print("continuity %d/%d pass -> %s" % (report["n_pass"], report["n"], args.continuity_out))
    if not args.skip_sentinel:
        report = write_sentinel_control(args.phase_20r_state, args.sentinel_out)
        print("sentinel n=%d -> %s" % (report["summary"].get("n", 0), args.sentinel_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

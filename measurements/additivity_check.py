#!/usr/bin/env python3
"""Phase 20R.6 -- four-branch tandem additivity analyzer.

Branches:

* A: existing one-link truth table.
* A': TandemTopo, only link i loaded, measurement over link i.
* B: TandemTopo, all three links loaded, measurement over link i.
* C: TandemTopo, all three links loaded, path probe over all three links.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements import decision_error_v2 as D
from mininet.topology_tandem import TANDEM_LINKS
from twin import cost_v2 as C
from twin import topology_v7 as T7


MODES = ("poisson", "h2")
APRIME_RHO_BARS = (0.925,)
B_RHO_BARS = (0.925,)
C_RHO_BARS = (0.85, 0.925)
SEEDS = (101, 102, 103, 104, 105)
TANDEM_PATH = "T123"
DELTA_MS = 0.44
GAP_FRACTION = 0.20
N_LINKS_IN_PATH = 3
DELTA_LOSS = 0.005
PROBE_INTRUSION_MAX = 0.02
OUT = "results/phase-20R/additivity_check.json"
DEFAULT_APRIME_STATE = "results/phase-20R/additivity_branch_a_state.json"
DEFAULT_B_STATE = "results/phase-20R/additivity_branch_b_state.json"
DEFAULT_C_STATE = "results/phase-20R/additivity_branch_c_state.json"


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


def measured_cost_gap_ms(
    mode: str,
    rho_bar: float,
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
) -> float:
    tt = D.TruthTable(truth_table)
    calib = calibration_by_cell(calibration_path)
    w_loss = float(calib[(str(mode), round(float(rho_bar), 12))]["w_loss"])
    rho = C.rho_vector(float(rho_bar))
    costs: List[float] = []
    for path in T7.PATH_NAMES:
        delay = 0.0
        keep = 1.0
        for link in T7.PATHS[path]:
            d, loss = tt.delay_loss(str(mode), link, np.asarray([rho[link]], dtype=float))
            delay += float(d[0])
            keep *= 1.0 - float(loss[0])
        costs.append(delay + w_loss * (1.0 - keep))
    ordered = sorted(costs)
    return float(ordered[1] - ordered[0])


def delta_for_cell(
    mode: str,
    rho_bar: float,
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
    per_link: bool = True,
) -> Dict[str, Any]:
    gap = measured_cost_gap_ms(mode, rho_bar, truth_table, calibration_path)
    delta_path = GAP_FRACTION * gap
    delta = delta_path / float(N_LINKS_IN_PATH) if per_link else delta_path
    return {
        "delta_ms": float(delta),
        "delta_path_ms": float(delta_path),
        "cost_gap_ms": float(gap),
        "gap_fraction": float(GAP_FRACTION),
        "per_link": bool(per_link),
        "delta_source": "runtime_cost_gap",
    }


def _link_names() -> Tuple[str, ...]:
    return tuple(row[0] for row in TANDEM_LINKS)


def _v7_link_for(tandem_link: str) -> str:
    for name, t7_link, _bw, _q, _base_ms in TANDEM_LINKS:
        if name == tandem_link:
            return t7_link
    raise KeyError(tandem_link)


def build_plan(
    modes: Sequence[str] = MODES,
    seeds: Sequence[int] = SEEDS,
    aprime_rho_bars: Sequence[float] = APRIME_RHO_BARS,
    b_rho_bars: Sequence[float] = B_RHO_BARS,
    c_rho_bars: Sequence[float] = C_RHO_BARS,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    a_rhos = sorted({float(rho) for rho in tuple(aprime_rho_bars) + tuple(b_rho_bars) + tuple(c_rho_bars)})
    for mode in modes:
        for rho_bar in a_rhos:
            for link in _link_names():
                rows.append(
                    {
                        "branch": "A",
                        "mode": str(mode),
                        "rho_bar": float(rho_bar),
                        "link": link,
                        "source": "truth_table",
                    }
                )
        for rho_bar in aprime_rho_bars:
            for link in _link_names():
                for seed in seeds:
                    rows.append({"branch": "Aprime", "mode": str(mode), "rho_bar": float(rho_bar), "link": link, "seed": int(seed)})
        for rho_bar in b_rho_bars:
            for link in _link_names():
                for seed in seeds:
                    rows.append({"branch": "B", "mode": str(mode), "rho_bar": float(rho_bar), "link": link, "seed": int(seed)})
        for rho_bar in c_rho_bars:
            for seed in seeds:
                rows.append({"branch": "C", "mode": str(mode), "rho_bar": float(rho_bar), "path": TANDEM_PATH, "seed": int(seed)})
    counts = {
        "A_table_cells": sum(1 for row in rows if row["branch"] == "A"),
        "Aprime_live_runs": sum(1 for row in rows if row["branch"] == "Aprime"),
        "B_live_runs": sum(1 for row in rows if row["branch"] == "B"),
        "C_live_runs": sum(1 for row in rows if row["branch"] == "C"),
    }
    plan = {
        "phase": "20R.6",
        "kind": "tandem_additivity_design",
        "legacy_delta_ms": DELTA_MS,
        "delta_policy": "runtime_cost_gap",
        "gap_fraction": GAP_FRACTION,
        "per_link_divisor": N_LINKS_IN_PATH,
        "modes": list(modes),
        "seeds": [int(seed) for seed in seeds],
        "tandem_links": [
            {"link": name, "topology_v7_link": t7_link, "bw": float(bw), "q": int(q), "base_ms": float(base_ms)}
            for name, t7_link, bw, q, base_ms in TANDEM_LINKS
        ],
        "aprime_rho_bars": [float(rho) for rho in aprime_rho_bars],
        "b_rho_bars": [float(rho) for rho in b_rho_bars],
        "c_rho_bars": [float(rho) for rho in c_rho_bars],
        "counts": counts,
        "rows": rows,
    }
    plan["plan_digest"] = stable_digest(rows)
    return plan


def calibration_by_cell(calibration_path: str) -> Dict[Tuple[str, float], Mapping[str, Any]]:
    out = {}
    for cell in D.feasible_cells(calibration_path, include_pc1=False):
        out[(str(cell["mode"]), round(float(cell["rho_bar"]), 12))] = cell
    return out


def branch_a_link_rows(
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
    modes: Sequence[str] = MODES,
    rho_bars: Sequence[float] = C_RHO_BARS,
) -> List[Dict[str, Any]]:
    tt = D.TruthTable(truth_table)
    calib = calibration_by_cell(calibration_path)
    rows: List[Dict[str, Any]] = []
    for mode in modes:
        for rho_bar in rho_bars:
            cell = calib[(str(mode), round(float(rho_bar), 12))]
            w_loss = float(cell["w_loss"])
            for link, t7_link, _bw, _q, _base_ms in TANDEM_LINKS:
                rho = float(C.rho_vector(float(rho_bar))[t7_link])
                delay, loss = tt.delay_loss(str(mode), t7_link, np.asarray([rho], dtype=float))
                rows.append(
                    {
                        "branch": "A",
                        "mode": str(mode),
                        "rho_bar": float(rho_bar),
                        "link": link,
                        "topology_v7_link": t7_link,
                        "rho_link": float(rho),
                        "delay_ms": float(delay[0]),
                        "loss": float(loss[0]),
                        "w_loss": w_loss,
                        "cost_ms": float(delay[0] + w_loss * loss[0]),
                        "clip_fraction_max": float(max(tt.clip_log.values()) if tt.clip_log else 0.0),
                    }
                )
    return rows


def load_rows(paths: Sequence[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        if not path:
            continue
        if not os.path.exists(path):
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
    required = {"branch", "mode", "rho_bar"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("measurement rows missing columns: %s" % sorted(missing))
    df["metric_ms"] = [_row_metric(row) for row in rows]
    df["rho_bar"] = df["rho_bar"].astype(float)
    if "seed" in df.columns:
        df["seed"] = df["seed"].astype(int)
    return df


def _probe_intrusion(df: pd.DataFrame) -> Dict[str, Any]:
    col = next((name for name in ("probe_intrusion_ratio", "probe_intrusion", "probe_intrusion_frac") if name in df.columns), None)
    if col is None:
        return {"available": False, "pass": False, "reason": "missing probe intrusion column"}
    vals = pd.to_numeric(df[col], errors="coerce").dropna()
    if vals.empty:
        return {"available": False, "pass": False, "reason": "probe intrusion column empty"}
    max_val = float(vals.max())
    return {"available": True, "max": max_val, "threshold": PROBE_INTRUSION_MAX, "pass": bool(max_val <= PROBE_INTRUSION_MAX)}


def _digest_report(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"available": False, "pass": False, "reason": "no rows"}
    problems: List[Dict[str, Any]] = []
    if "schedule_digest" in df.columns:
        a = df[df["branch"] == "Aprime"][["mode", "rho_bar", "link", "seed", "schedule_digest"]].rename(columns={"schedule_digest": "aprime_digest"})
        b = df[df["branch"] == "B"][["mode", "rho_bar", "link", "seed", "schedule_digest"]].rename(columns={"schedule_digest": "b_digest"})
        merged = a.merge(b, on=["mode", "rho_bar", "link", "seed"], how="inner")
        for _idx, row in merged.iterrows():
            if str(row["aprime_digest"]) != str(row["b_digest"]):
                problems.append(
                    {
                        "contrast": "Aprime_B",
                        "mode": row["mode"],
                        "rho_bar": float(row["rho_bar"]),
                        "link": row["link"],
                        "seed": int(row["seed"]),
                    }
                )
    if "trajectory_digest" in df.columns:
        b = df[df["branch"] == "B"]
        c = df[df["branch"] == "C"][["mode", "rho_bar", "seed", "trajectory_digest"]].rename(columns={"trajectory_digest": "c_digest"})
        b_comp = b.groupby(["mode", "rho_bar", "seed"], sort=True)["trajectory_digest"].agg(lambda xs: sorted(set(str(x) for x in xs if pd.notna(x)))).reset_index()
        merged = b_comp.merge(c, on=["mode", "rho_bar", "seed"], how="inner")
        for _idx, row in merged.iterrows():
            digests = list(row["trajectory_digest"])
            if len(digests) != 1 or str(digests[0]) != str(row["c_digest"]):
                problems.append(
                    {
                        "contrast": "B_C",
                        "mode": row["mode"],
                        "rho_bar": float(row["rho_bar"]),
                        "seed": int(row["seed"]),
                    }
                )
    return {"available": True, "pass": bool(not problems), "n_problem": len(problems), "problems": problems[:20]}


def _append_tost(
    checks: List[Dict[str, Any]],
    contrast: str,
    df: pd.DataFrame,
    group_cols: Sequence[str],
    delta_col: str,
    delta_ms: Optional[float] = None,
    per_link: bool = True,
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
    units: str = "ms",
) -> None:
    for key, group in df.groupby(list(group_cols), sort=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = {"contrast": contrast}
        row.update({name: value for name, value in zip(group_cols, key)})
        if "rho_bar" in row:
            row["rho_bar"] = float(row["rho_bar"])
        if delta_ms is None:
            delta_info = delta_for_cell(str(row["mode"]), float(row["rho_bar"]), truth_table, calibration_path, per_link=per_link)
            d = float(delta_info["delta_ms"])
            row.update(delta_info)
        else:
            d = float(delta_ms)
            row["delta_source"] = "fixed"
        row["delta_column"] = str(delta_col)
        row["units"] = str(units)
        row.update(tost_equivalence(group[delta_col], delta_ms=d))
        checks.append(row)


def analyze(
    measurement_rows: Sequence[Mapping[str, Any]],
    truth_table: str = D.TRUTH_TABLE,
    calibration_path: str = D.CALIBRATION,
    modes: Sequence[str] = MODES,
    delta_ms: Optional[float] = None,
) -> Dict[str, Any]:
    plan = build_plan(modes=modes)
    live_rhos = sorted({float(row["rho_bar"]) for row in measurement_rows if "rho_bar" in row} | set(C_RHO_BARS) | set(APRIME_RHO_BARS))
    a_rows = branch_a_link_rows(truth_table, calibration_path, modes=modes, rho_bars=live_rhos)
    a = pd.DataFrame(a_rows)
    df = _measurement_frame(measurement_rows)
    result: Dict[str, Any] = {
        "phase": "20R.6",
        "script": "measurements.additivity_check",
        "kind": "tandem_additivity_analysis",
        "delta_ms": None if delta_ms is None else float(delta_ms),
        "delta_policy": "runtime_cost_gap" if delta_ms is None else "fixed",
        "gap_fraction": GAP_FRACTION,
        "per_link_divisor": N_LINKS_IN_PATH,
        "delta_loss": DELTA_LOSS,
        "plan_digest": plan["plan_digest"],
        "branch_a": a_rows,
        "checks": [],
        "summary": {
            "n_measurement_rows": int(len(df)),
            "has_aprime": bool(not df.empty and (df["branch"] == "Aprime").any()),
            "has_branch_b": bool(not df.empty and (df["branch"] == "B").any()),
            "has_branch_c": bool(not df.empty and (df["branch"] == "C").any()),
        },
    }
    if df.empty:
        result["summary"].update({"g6_evaluated": False, "g6_pass": False, "reason": "no live A'/B/C rows"})
        return result

    result["paired_schedule"] = _digest_report(df)
    result["probe_intrusion"] = _probe_intrusion(df)
    checks = result["checks"]
    ap = df[df["branch"] == "Aprime"].copy()
    b = df[df["branch"] == "B"].copy()
    c = df[df["branch"] == "C"].copy()

    if not ap.empty:
        ma = ap.merge(
            a[["mode", "rho_bar", "link", "cost_ms", "delay_ms", "loss"]].rename(
                columns={"cost_ms": "a_cost_ms", "delay_ms": "a_delay_ms", "loss": "a_loss"}
            ),
            on=["mode", "rho_bar", "link"],
            how="inner",
        )
        ma["delta_ms"] = ma["metric_ms"] - ma["a_cost_ms"]
        ma["delta_delay_ms"] = pd.to_numeric(ma["delay_ms"], errors="coerce") - ma["a_delay_ms"]
        ma["delta_loss"] = pd.to_numeric(ma["loss"], errors="coerce") - ma["a_loss"]
        _append_tost(checks, "Aprime_minus_A", ma, ("mode", "rho_bar", "link"), "delta_ms", delta_ms, True, truth_table, calibration_path)
        _append_tost(checks, "Aprime_minus_A_delay", ma, ("mode", "rho_bar", "link"), "delta_delay_ms", delta_ms, True, truth_table, calibration_path)
        _append_tost(checks, "Aprime_minus_A_loss", ma, ("mode", "rho_bar", "link"), "delta_loss", DELTA_LOSS, True, truth_table, calibration_path, units="loss_fraction")

    if not ap.empty and not b.empty:
        mb = b.merge(
            ap[["mode", "rho_bar", "link", "seed", "metric_ms", "delay_ms", "loss"]].rename(
                columns={"metric_ms": "aprime_ms", "delay_ms": "aprime_delay_ms", "loss": "aprime_loss"}
            ),
            on=["mode", "rho_bar", "link", "seed"],
            how="inner",
        )
        mb["delta_ms"] = mb["metric_ms"] - mb["aprime_ms"]
        if {"delay_ms", "loss", "aprime_delay_ms", "aprime_loss"}.issubset(mb.columns):
            mb["delta_delay_ms"] = pd.to_numeric(mb["delay_ms"], errors="coerce") - pd.to_numeric(mb["aprime_delay_ms"], errors="coerce")
            mb["delta_loss"] = pd.to_numeric(mb["loss"], errors="coerce") - pd.to_numeric(mb["aprime_loss"], errors="coerce")
        _append_tost(checks, "B_minus_Aprime", mb, ("mode", "rho_bar", "link"), "delta_ms", delta_ms, True, truth_table, calibration_path)
        if "delta_delay_ms" in mb.columns:
            _append_tost(checks, "B_minus_Aprime_delay", mb, ("mode", "rho_bar", "link"), "delta_delay_ms", delta_ms, True, truth_table, calibration_path)
            _append_tost(checks, "B_minus_Aprime_loss", mb, ("mode", "rho_bar", "link"), "delta_loss", DELTA_LOSS, True, truth_table, calibration_path, units="loss_fraction")

    if not b.empty and not c.empty:
        b_sum = b.groupby(["mode", "rho_bar", "seed"], sort=True)["metric_ms"].sum().reset_index(name="sum_b_ms")
        mc = c.merge(b_sum, on=["mode", "rho_bar", "seed"], how="inner")
        mc["delta_ms"] = mc["metric_ms"] - mc["sum_b_ms"]
        if {"delay_ms", "loss"}.issubset(b.columns) and {"delay_ms", "loss"}.issubset(c.columns):
            b_dl = b.groupby(["mode", "rho_bar", "seed"], sort=True)["delay_ms"].sum().reset_index(name="sum_b_delay_ms")
            b_loss = (
                b.groupby(["mode", "rho_bar", "seed"], sort=True)["loss"]
                .agg(lambda xs: 1.0 - float(np.prod(1.0 - pd.to_numeric(xs, errors="coerce").to_numpy(float))))
                .reset_index(name="path_b_loss")
            )
            mc = mc.merge(b_dl, on=["mode", "rho_bar", "seed"], how="inner").merge(b_loss, on=["mode", "rho_bar", "seed"], how="inner")
            mc["delta_delay_ms"] = pd.to_numeric(mc["delay_ms"], errors="coerce") - mc["sum_b_delay_ms"]
            mc["delta_loss"] = pd.to_numeric(mc["loss"], errors="coerce") - mc["path_b_loss"]
        _append_tost(checks, "C_minus_sumB", mc, ("mode", "rho_bar"), "delta_ms", delta_ms, False, truth_table, calibration_path)
        if "delta_delay_ms" in mc.columns:
            _append_tost(checks, "C_minus_sumB_delay", mc, ("mode", "rho_bar"), "delta_delay_ms", delta_ms, False, truth_table, calibration_path)
            _append_tost(checks, "C_minus_sumB_loss", mc, ("mode", "rho_bar"), "delta_loss", DELTA_LOSS, False, truth_table, calibration_path, units="loss_fraction")

    if not c.empty:
        a_sum = a.groupby(["mode", "rho_bar"], sort=True)["cost_ms"].sum().reset_index(name="sum_a_ms")
        mc_a = c.merge(a_sum, on=["mode", "rho_bar"], how="inner")
        mc_a["delta_ms"] = mc_a["metric_ms"] - mc_a["sum_a_ms"]
        _append_tost(checks, "C_minus_sumA", mc_a, ("mode", "rho_bar"), "delta_ms", delta_ms, False, truth_table, calibration_path)

    if not ap.empty and not c.empty:
        ap_sum = ap.groupby(["mode", "rho_bar", "seed"], sort=True)["metric_ms"].sum().reset_index(name="sum_aprime_ms")
        mc_ap = c.merge(ap_sum, on=["mode", "rho_bar", "seed"], how="inner")
        mc_ap["delta_ms"] = mc_ap["metric_ms"] - mc_ap["sum_aprime_ms"]
        _append_tost(checks, "C_minus_sumAprime", mc_ap, ("mode", "rho_bar"), "delta_ms", delta_ms, False, truth_table, calibration_path)

    transfer = [row for row in checks if row.get("contrast") == "Aprime_minus_A"]
    g6 = [row for row in checks if row.get("contrast") == "C_minus_sumB"]
    result["summary"].update(
        {
            "topology_transfer_evaluated": bool(transfer),
            "topology_transfer_pass": bool(transfer and all(row.get("equiv_pass") for row in transfer)),
            "g6_evaluated": bool(g6),
            "g6_pass": bool(g6 and all(row.get("equiv_pass") for row in g6)),
            "power_pass": bool(g6 and all(row.get("power_ok") for row in g6)),
            "paired_schedule_pass": bool(result.get("paired_schedule", {}).get("pass")),
            "probe_intrusion_pass": bool(result.get("probe_intrusion", {}).get("pass")),
        }
    )
    return result


def default_analyze_inputs() -> Tuple[str, ...]:
    return (DEFAULT_APRIME_STATE, DEFAULT_B_STATE, DEFAULT_C_STATE)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth-table", default=D.TRUTH_TABLE)
    ap.add_argument("--calibration", default=D.CALIBRATION)
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--seeds", default=",".join(str(seed) for seed in SEEDS))
    ap.add_argument("--delta-ms", type=float, default=None, help="override runtime equivalence margin; omitted means 20%% of measured cost gap")
    ap.add_argument("--from-state", default="", help="comma-separated JSON state/result files containing A'/B/C rows")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--write-plan", default="", help="write design plan JSON and exit")
    ap.add_argument("--compare-a-vs-truthtable", action="store_true", help="analyze A' transfer using the default A' state")
    ap.add_argument("--analyze", action="store_true", help="analyze default A'/B/C states")
    args = ap.parse_args(argv)

    modes = parse_list(args.modes)
    seeds = parse_int_list(args.seeds)
    plan = build_plan(modes=modes, seeds=seeds)
    if args.plan_only:
        print(json.dumps({"counts": plan["counts"], "plan_digest": plan["plan_digest"]}, indent=2, sort_keys=True))
        return 0
    if args.write_plan:
        write_json(args.write_plan, plan)
        print("plan rows=%d -> %s" % (len(plan["rows"]), args.write_plan))
        return 0

    if args.compare_a_vs_truthtable:
        inputs = (DEFAULT_APRIME_STATE,)
    elif args.analyze and not args.from_state:
        inputs = default_analyze_inputs()
    else:
        inputs = parse_list(args.from_state)
    rows = load_rows(inputs)
    report = analyze(rows, args.truth_table, args.calibration, modes=modes, delta_ms=args.delta_ms)
    write_json(args.out, report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("additivity -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

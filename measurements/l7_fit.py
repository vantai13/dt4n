#!/usr/bin/env python3
"""Lesson L.7 -- fit link_model_v2 from the L.6 campaign state.

This is an offline step. It consumes ``campaign_state.json`` plus, when
available, the recorded ``*_bgtx.bin`` files for Reich/Lindley workload
summaries. It does not start Mininet.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import struct
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from measurements.l6_campaign import DUR, RAW, STATE as DEFAULT_STATE, WARM
from mininet.load_spec import FRAME_BG
from twin.link_model_v2 import MonotonePchip, is_non_decreasing, kingman_ceiling


OUT = "results/phase-L/link_model_v2_fit.json"
REICH_OUT = "results/phase-L/l7_reich_workload.json"
REPORT = "docs/phase-L/07-fit.md"
FIG_DIR = "docs/phase-L/figures"

RHO_ALL = (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 1.00, 1.02, 1.05)
HELD_IDX = (2, 5, 8, 11)
RHO_HELD = tuple(RHO_ALL[i] for i in HELD_IDX)
RHO_TRAIN = tuple(r for i, r in enumerate(RHO_ALL) if i not in HELD_IDX)
R2_GATE = 0.90
CBR_RMSE_GATE_MS = 0.05
MTU_BYTES = FRAME_BG
TX_REC = struct.Struct("<Qd")


def mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sd(values: Sequence[float]) -> float:
    if len(values) <= 1:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def rmse(y: Sequence[float], yhat: Sequence[float]) -> float:
    if not y:
        return float("nan")
    return math.sqrt(mean([(a - b) ** 2 for a, b in zip(y, yhat)]))


def r2(y: Sequence[float], yhat: Sequence[float]) -> float:
    if len(y) <= 1:
        return float("nan")
    ybar = mean(y)
    sst = sum((a - ybar) ** 2 for a in y)
    if sst <= 0.0:
        return float("nan")
    return 1.0 - sum((a - b) ** 2 for a, b in zip(y, yhat)) / sst


def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(float(x) for x in values)
    if len(xs) == 1:
        return xs[0]
    pos = max(0.0, min(1.0, float(q))) * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def corr(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    mx, my = mean(xs), mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0.0 or vy <= 0.0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def linspace(lo: float, hi: float, n: int) -> List[float]:
    if n <= 1:
        return [float(lo)]
    return [float(lo) + (float(hi) - float(lo)) * i / (n - 1) for i in range(n)]


def logspace(exp_lo: float, exp_hi: float, n: int) -> List[float]:
    return [10.0 ** x for x in linspace(exp_lo, exp_hi, n)]


def pava_non_decreasing(values: Sequence[float], weights: Optional[Sequence[float]] = None) -> List[float]:
    """Weighted pool-adjacent-violators projection onto nondecreasing values."""
    if not values:
        return []
    weights = list(weights) if weights is not None else [1.0] * len(values)
    blocks: List[Dict[str, float]] = []
    for i, (value, weight) in enumerate(zip(values, weights)):
        blocks.append({"start": i, "end": i, "weight": float(weight), "mean": float(value)})
        while len(blocks) >= 2 and blocks[-2]["mean"] > blocks[-1]["mean"]:
            b = blocks.pop()
            a = blocks.pop()
            w = a["weight"] + b["weight"]
            blocks.append(
                {
                    "start": a["start"],
                    "end": b["end"],
                    "weight": w,
                    "mean": (a["mean"] * a["weight"] + b["mean"] * b["weight"]) / w,
                }
            )
    out = [0.0] * len(values)
    for block in blocks:
        for i in range(int(block["start"]), int(block["end"]) + 1):
            out[i] = float(block["mean"])
    return out


def queue_ceiling_ms(bw_mbps: float, queue_pkts: int) -> float:
    return int(queue_pkts) * MTU_BYTES * 8.0 / (float(bw_mbps) * 1e6) * 1000.0


def fit_kingman(rhos: Sequence[float], ys: Sequence[float], floor: float, ceil_ms: float) -> Dict[str, float]:
    best: Optional[Tuple[float, float, float]] = None
    for k in logspace(-3.0, 1.5, 360):
        for w_max in linspace(0.2 * ceil_ms, 1.2 * ceil_ms, 110):
            pred = [kingman_ceiling(rho, k, w_max, floor) for rho in rhos]
            sse = sum((p - y) ** 2 for p, y in zip(pred, ys))
            if best is None or sse < best[0]:
                best = (sse, k, w_max)
    assert best is not None
    sse, k, w_max = best
    pred = [kingman_ceiling(rho, k, w_max, floor) for rho in rhos]
    return {
        "K": float(k),
        "w_max": float(w_max),
        "floor": float(floor),
        "r2": r2(ys, pred),
        "rmse_ms": rmse(ys, pred),
    }


def load_state(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fit_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        row
        for row in rows
        if float(row.get("probe_pps", -1.0)) == 20.0 and row.get("block") in ("A", "B", "C")
    ]


def group_cells(rows: Sequence[Dict[str, Any]]) -> Dict[Tuple[str, float, int, float], List[Dict[str, Any]]]:
    cells: Dict[Tuple[str, float, int, float], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        cells[(row["mode"], float(row["bw"]), int(row["q"]), round(float(row["rho"]), 4))].append(row)
    return cells


def cell_delay_values(cells: Dict[Tuple[str, float, int, float], List[Dict[str, Any]]], key: Tuple[str, float, int, float]) -> List[float]:
    return [float(row["q_mean_ms"]) for row in cells[key]]


def cell_loss_values(cells: Dict[Tuple[str, float, int, float], List[Dict[str, Any]]], key: Tuple[str, float, int, float]) -> List[float]:
    return [float(row["loss"]) for row in cells[key]]


def build_links(rows: Sequence[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[Any, ...]]]:
    rows = fit_rows(rows)
    cells = group_cells(rows)
    groups = sorted({(mode, bw, q) for mode, bw, q, _rho in cells})
    links: Dict[str, Dict[str, Any]] = {}
    report_rows: List[Tuple[Any, ...]] = []

    for mode, bw, q in groups:
        rhos = sorted(rho for m, b, qq, rho in cells if (m, b, qq) == (mode, bw, q))
        if len(rhos) < 4:
            continue

        y_values = {rho: cell_delay_values(cells, (mode, bw, q, rho)) for rho in rhos}
        loss_values = {rho: cell_loss_values(cells, (mode, bw, q, rho)) for rho in rhos}
        ybar_raw = [mean(y_values[rho]) for rho in rhos]
        counts = [len(y_values[rho]) for rho in rhos]
        ybar = pava_non_decreasing(ybar_raw, counts)
        lbar_raw = [mean(loss_values[rho]) for rho in rhos]
        lbar = [max(0.0, min(1.0, x)) for x in pava_non_decreasing(lbar_raw, counts)]

        train = [rho for rho in rhos if rho in RHO_TRAIN]
        held = [rho for rho in rhos if rho in RHO_HELD]
        train_idx = [rhos.index(rho) for rho in train]
        f_train = MonotonePchip(train, [ybar[i] for i in train_idx])
        held_in = [rho for rho in held if min(train) <= rho <= max(train)]
        held_ex = [rho for rho in held if rho not in held_in]
        held_in_y = [ybar_raw[rhos.index(rho)] for rho in held_in]
        held_in_pred = [f_train(rho) for rho in held_in]
        held_y = [ybar_raw[rhos.index(rho)] for rho in held]
        held_pred = [f_train(rho) for rho in held]
        cbr_eval = [rho for rho in held_in if rho <= 0.90]
        cbr_eval_y = [ybar_raw[rhos.index(rho)] for rho in cbr_eval]
        cbr_eval_pred = [f_train(rho) for rho in cbr_eval]
        cbr_critical = [rho for rho in held_in if rho > 0.90]

        floor = ybar[0] if mode == "cbr" else 0.0
        kg = fit_kingman(rhos, ybar, floor, queue_ceiling_ms(bw, q))

        f_full = MonotonePchip(rhos, ybar)
        resid: List[float] = []
        resid_by_rho: Dict[float, List[float]] = defaultdict(list)
        pooled_seed_resid: List[float] = []
        for rho in rhos:
            pred = f_full(rho)
            raw_mean = ybar_raw[rhos.index(rho)]
            for y in y_values[rho]:
                e = y - pred
                resid.append(e)
                resid_by_rho[rho].append(e)
                pooled_seed_resid.append(y - raw_mean)

        sigma_by_rho = [max(sd(resid_by_rho[rho]), 1e-6) for rho in rhos]
        ysd = [sd(y_values[rho]) for rho in rhos]
        resid_sd = sd(resid)
        sigma_schedule_mean = mean(ysd)
        sigma_schedule = sd(pooled_seed_resid)
        efficiency = sigma_schedule / max(resid_sd, 1e-9)
        key = "%s|%g|%d" % (mode, bw, q)
        held_r2 = r2(held_in_y, held_in_pred)
        held_rmse = rmse(held_in_y, held_in_pred)
        cbr_subcritical_rmse = rmse(cbr_eval_y, cbr_eval_pred)
        if mode == "cbr":
            predict_gate = cbr_subcritical_rmse <= CBR_RMSE_GATE_MS
            gate_basis = "cbr_subcritical_rmse_rho_le_0.90"
        else:
            predict_gate = held_r2 >= R2_GATE
            gate_basis = "heldout_r2_interp"

        links[key] = {
            "mode": mode,
            "bw": bw,
            "q": q,
            "rho_train": rhos,
            "delay_train": ybar,
            "delay_observed": ybar_raw,
            "delay_adjustment_ms": [a - b for a, b in zip(ybar, ybar_raw)],
            "loss_train": lbar,
            "loss_observed": lbar_raw,
            "sigma_train": sigma_by_rho,
            "sigma_observed_by_rho": sigma_by_rho,
            "n_by_rho": counts,
            "kingman": kg,
            "domain": [min(rhos), max(rhos)],
            "sigma_schedule": sigma_schedule,
            "sigma_schedule_mean_by_rho": sigma_schedule_mean,
            "sigma_schedule_rms": math.sqrt(mean([x * x for x in ysd])),
            "resid_sd": resid_sd,
            "resid_mean": mean(resid),
            "resid_p05": percentile(resid, 0.05),
            "resid_p95": percentile(resid, 0.95),
            "resid_n": len(resid),
            "model_efficiency": efficiency,
            "heldout_rho_interp": held_in,
            "heldout_rho_all": held,
            "heldout_extrapolated_rho": held_ex,
            "heldout_r2_interp": held_r2,
            "heldout_rmse_interp_ms": held_rmse,
            "heldout_rmse_cbr_subcritical_ms": cbr_subcritical_rmse if mode == "cbr" else None,
            "heldout_cbr_critical_rho": cbr_critical if mode == "cbr" else [],
            "heldout_r2_all": r2(held_y, held_pred),
            "heldout_rmse_all_ms": rmse(held_y, held_pred),
            "monotonic_observed": is_non_decreasing(ybar_raw),
            "monotonic_model": is_non_decreasing(ybar),
            "max_monotone_adjustment_ms": max(abs(a - b) for a, b in zip(ybar, ybar_raw)),
            "predict_gate_basis": gate_basis,
            "predict_gate_pass": bool(predict_gate),
        }
        report_rows.append(
            (
                mode,
                bw,
                q,
                held_r2,
                held_rmse,
                links[key]["heldout_r2_all"],
                kg["r2"],
                resid_sd,
                sigma_schedule,
                efficiency,
                links[key]["max_monotone_adjustment_ms"],
                links[key]["monotonic_model"],
                predict_gate,
            )
        )
    return links, report_rows


def _load_tx_times(path: str) -> List[float]:
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) % TX_REC.size:
        raise ValueError("%s has truncated TX records" % path)
    return [TX_REC.unpack_from(raw, i * TX_REC.size)[1] for i in range(len(raw) // TX_REC.size)]


def reich_workload_from_timestamps(
    timestamps: Sequence[float],
    bw_mbps: float,
    warmup_s: float = WARM,
    tail_s: float = 0.0,
) -> Dict[str, Any]:
    if not timestamps:
        return {
            "n": 0,
            "mean_ms": None,
            "p95_ms": None,
            "max_ms": None,
        }
    service_ms = FRAME_BG * 8.0 / (float(bw_mbps) * 1e6) * 1000.0
    service_s = service_ms / 1000.0
    t0 = float(timestamps[0])
    hi = float(timestamps[-1]) - float(tail_s)
    q = 0.0
    prev: Optional[float] = None
    values: List[float] = []
    for t in timestamps:
        t = float(t)
        gap = 0.0 if prev is None else max(0.0, t - prev)
        q = max(0.0, q - gap / service_s) + 1.0
        if t0 + float(warmup_s) <= t <= hi:
            values.append(q * service_ms)
        prev = t
    return {
        "n": len(values),
        "mean_ms": mean(values),
        "p95_ms": percentile(values, 0.95),
        "max_ms": max(values) if values else None,
    }


def compute_reich_rows(rows: Sequence[Dict[str, Any]], raw_dir: str = RAW) -> Dict[str, Any]:
    out_rows = []
    missing = []
    for row in rows:
        path = os.path.join(raw_dir, row["pid"] + "_bgtx.bin")
        if not os.path.exists(path):
            missing.append(row["pid"])
            continue
        w = reich_workload_from_timestamps(_load_tx_times(path), row["bw"], WARM)
        out_rows.append(
            {
                "idx": int(row["idx"]),
                "pid": row["pid"],
                "block": row["block"],
                "mode": row["mode"],
                "bw": float(row["bw"]),
                "q": int(row["q"]),
                "rho": float(row["rho"]),
                "seed": int(row["seed"]),
                "probe_pps": float(row["probe_pps"]),
                "schedule_digest": row.get("schedule_digest"),
                "workload_mean_ms": w["mean_ms"],
                "workload_p95_ms": w["p95_ms"],
                "workload_max_ms": w["max_ms"],
                "workload_n": w["n"],
            }
        )
    return {
        "source": raw_dir,
        "warmup_s": WARM,
        "n_rows": len(out_rows),
        "n_missing": len(missing),
        "missing_pid": missing[:20],
        "rows": out_rows,
    }


def summarize_variance(state: Dict[str, Any]) -> Dict[str, Any]:
    rows = state["rows"]
    cbr = [
        float(row["q_mean_ms"])
        for row in rows
        if row["mode"] == "cbr"
        and float(row["bw"]) == 6.0
        and int(row["q"]) == 13
        and abs(float(row["rho"]) - 0.90) < 1e-9
        and float(row["probe_pps"]) == 20.0
        and row["block"] == "A"
    ]
    h2 = [
        float(row["q_mean_ms"])
        for row in rows
        if row["mode"] == "h2"
        and float(row["bw"]) == 6.0
        and int(row["q"]) == 13
        and abs(float(row["rho"]) - 0.90) < 1e-9
        and float(row["probe_pps"]) == 20.0
        and row["block"] == "A"
    ]
    sent = [float(row["q_mean_ms"]) for row in state.get("sentinels", [])]
    sent_tail = sent[1:]
    sigma_machine = sd(cbr)
    sigma_repeat = sd(sent_tail)
    sigma_schedule = sd(h2)
    total = sigma_machine**2 + sigma_repeat**2 + sigma_schedule**2
    return {
        "sigma_machine_ms": sigma_machine,
        "sigma_repeat_ms": sigma_repeat,
        "sigma_schedule_ms": sigma_schedule,
        "sigma_schedule_over_repeat": sigma_schedule / sigma_repeat if sigma_repeat else None,
        "sigma_schedule_over_machine": sigma_schedule / sigma_machine if sigma_machine else None,
        "schedule_variance_share": sigma_schedule**2 / total if total else None,
        "alpha10_half_width_floor_ms": 1.645 * sigma_schedule,
        "sentinel_all": {"n": len(sent), "mean_ms": mean(sent), "sd_ms": sd(sent)},
        "sentinel_without_first": {"n": len(sent_tail), "mean_ms": mean(sent_tail), "sd_ms": sd(sent_tail)},
        "sentinel_first_z_vs_rest": (
            (sent[0] - mean(sent_tail)) / sd(sent_tail) if len(sent_tail) > 1 and sd(sent_tail) > 0 else None
        ),
    }


def summarize_ca_counterexample(rows: Sequence[Dict[str, Any]], reich: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    reich_by_idx = {int(row["idx"]): row for row in (reich or {}).get("rows", [])}
    out = {}
    for mode in ("cbr", "poisson", "h2", "onoff"):
        sub = [
            row
            for row in rows
            if row["mode"] == mode
            and float(row["bw"]) == 6.0
            and int(row["q"]) == 13
            and abs(float(row["rho"]) - 0.90) < 1e-9
            and float(row["probe_pps"]) == 20.0
            and row["block"] in ("A", "B")
        ]
        reich_vals = [
            float(reich_by_idx[int(row["idx"])]["workload_mean_ms"])
            for row in sub
            if int(row["idx"]) in reich_by_idx
            and reich_by_idx[int(row["idx"])]["workload_mean_ms"] is not None
        ]
        out[mode] = {
            "n": len(sub),
            "ca_mean": mean([float(row["ca_actual"]) for row in sub]),
            "ca_sd": sd([float(row["ca_actual"]) for row in sub]),
            "q_mean_ms": mean([float(row["q_mean_ms"]) for row in sub]),
            "q_sd_ms": sd([float(row["q_mean_ms"]) for row in sub]),
            "reich_mean_ms": mean(reich_vals) if reich_vals else None,
        }
    if all(out[mode]["reich_mean_ms"] is not None for mode in out):
        out["_reich_delay_corr"] = corr(
            [out[mode]["reich_mean_ms"] for mode in ("cbr", "poisson", "h2", "onoff")],
            [out[mode]["q_mean_ms"] for mode in ("cbr", "poisson", "h2", "onoff")],
        )
    return out


def add_reich_to_links(links: Dict[str, Dict[str, Any]], reich: Dict[str, Any]) -> None:
    rows = [
        row
        for row in reich.get("rows", [])
        if float(row["probe_pps"]) == 20.0 and row["block"] in ("A", "B", "C")
    ]
    by_cell: Dict[Tuple[str, float, int, float], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("workload_mean_ms") is None:
            continue
        by_cell[(row["mode"], float(row["bw"]), int(row["q"]), round(float(row["rho"]), 4))].append(row)
    for key, link in links.items():
        mode, bw_s, q_s = key.split("|")
        bw = float(bw_s)
        q = int(q_s)
        link["reich_mean_train"] = []
        link["reich_p95_train"] = []
        for rho in link["rho_train"]:
            vals = by_cell.get((mode, bw, q, round(float(rho), 4)), [])
            link["reich_mean_train"].append(mean([float(v["workload_mean_ms"]) for v in vals]) if vals else None)
            link["reich_p95_train"].append(mean([float(v["workload_p95_ms"]) for v in vals]) if vals else None)


def make_gates(report_rows: Sequence[Tuple[Any, ...]], links: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    n_predict = sum(1 for row in report_rows if row[-1])
    n_mono = sum(1 for link in links.values() if link["monotonic_model"])
    efficiencies = [link["model_efficiency"] for link in links.values() if link["sigma_schedule"] > 0.01]
    return {
        "G-L7a_predictive_gate_pass": bool(n_predict >= math.ceil(0.90 * len(report_rows))),
        "G-L7a_n_pass": n_predict,
        "G-L7a_n_total": len(report_rows),
        "G-L7b_monotonic_pass": bool(n_mono == len(links)),
        "G-L7b_n_pass": n_mono,
        "G-L7c_efficiency_pass": bool(efficiencies and min(efficiencies) > 0.30 and max(efficiencies) <= 1.0),
        "G-L7c_efficiency_mean": mean(efficiencies),
        "G-L7c_efficiency_min": min(efficiencies) if efficiencies else None,
        "G-L7c_efficiency_max": max(efficiencies) if efficiencies else None,
        "G-L7d_sigma_present_pass": bool(all(link.get("sigma_train") for link in links.values())),
        "G-L7e_extrapolated_105_marked_pass": bool(
            all(1.05 in link.get("heldout_extrapolated_rho", []) for link in links.values())
        ),
    }


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "NA"
    try:
        x = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(x):
        return "NA"
    return ("%." + str(digits) + "f") % x


def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_svg_curves(path: str, links: Dict[str, Dict[str, Any]], field: str, title: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    keys = ["cbr|6|13", "poisson|6|13", "h2|6|13", "onoff|6|13"]
    colors = {"cbr": "#555555", "poisson": "#1f77b4", "h2": "#d62728", "onoff": "#2ca02c"}
    series = []
    for key in keys:
        if key not in links:
            continue
        link = links[key]
        pts = [(float(r), float(v)) for r, v in zip(link["rho_train"], link[field]) if v is not None]
        series.append((link["mode"], pts))
    xs = [x for _name, pts in series for x, _y in pts]
    ys = [y for _name, pts in series for _x, y in pts]
    if not xs or not ys:
        return
    w, h = 760, 430
    ml, mr, mt, mb = 64, 24, 36, 58
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(0.0, min(ys)), max(ys)
    if ymax <= ymin:
        ymax = ymin + 1.0

    def sx(x: float) -> float:
        return ml + (x - xmin) / (xmax - xmin) * (w - ml - mr)

    def sy(y: float) -> float:
        return h - mb - (y - ymin) / (ymax - ymin) * (h - mt - mb)

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w, h, w, h),
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="%d" y="24" font-family="sans-serif" font-size="16">%s</text>' % (ml, html.escape(title)),
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222"/>' % (ml, h - mb, w - mr, h - mb),
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222"/>' % (ml, mt, ml, h - mb),
    ]
    for tick in RHO_ALL:
        if xmin <= tick <= xmax:
            x = sx(tick)
            lines.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#ddd"/>' % (x, mt, x, h - mb))
            lines.append(
                '<text x="%.1f" y="%d" text-anchor="middle" font-family="sans-serif" font-size="10">%.3g</text>'
                % (x, h - mb + 18, tick)
            )
    for i in range(6):
        yv = ymin + (ymax - ymin) * i / 5.0
        y = sy(yv)
        lines.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#eee"/>' % (ml, y, w - mr, y))
        lines.append(
            '<text x="%d" y="%.1f" text-anchor="end" dominant-baseline="middle" font-family="sans-serif" font-size="10">%.2f</text>'
            % (ml - 8, y, yv)
        )
    for name, pts in series:
        color = colors.get(name, "#333")
        d = " ".join(("M" if i == 0 else "L") + "%.2f %.2f" % (sx(x), sy(y)) for i, (x, y) in enumerate(pts))
        lines.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>' % (d, color))
        for x, y in pts:
            lines.append('<circle cx="%.2f" cy="%.2f" r="3" fill="%s"/>' % (sx(x), sy(y), color))
    for i, (name, _pts) in enumerate(series):
        y = mt + 18 + 18 * i
        color = colors.get(name, "#333")
        lines.append('<rect x="%d" y="%d" width="12" height="12" fill="%s"/>' % (w - 120, y - 10, color))
        lines.append('<text x="%d" y="%d" font-family="sans-serif" font-size="12">%s</text>' % (w - 102, y, html.escape(name)))
    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_report(
    path: str,
    fit: Dict[str, Any],
    report_rows: Sequence[Tuple[Any, ...]],
    variance: Dict[str, Any],
    ca_counter: Dict[str, Any],
) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    links = fit["links"]
    write_svg_curves(os.path.join(FIG_DIR, "l7_ref_curves.svg"), links, "delay_train", "L.7 ref curves: delay mean, bw=6 q=13")
    write_svg_curves(os.path.join(FIG_DIR, "l7_ref_sigma.svg"), links, "sigma_train", "L.7 ref curves: local sigma, bw=6 q=13")

    lines = [
        "# Phase L / Lesson L.7 -- Fit link_model_v2",
        "",
        "Source: `%s`" % fit["source"],
        "",
        "Output model: `results/phase-L/link_model_v2_fit.json`",
        "",
        "## Gates",
        "",
        "| gate | result |",
        "|---|---:|",
        "| G-L7a predictive gate | %d/%d %s |"
        % (
            fit["gates"]["G-L7a_n_pass"],
            fit["gates"]["G-L7a_n_total"],
            "PASS" if fit["gates"]["G-L7a_predictive_gate_pass"] else "FAIL",
        ),
        "| G-L7b monotone model | %d/%d %s |"
        % (
            fit["gates"]["G-L7b_n_pass"],
            len(links),
            "PASS" if fit["gates"]["G-L7b_monotonic_pass"] else "FAIL",
        ),
        "| G-L7c efficiency | mean %s, min %s, max %s %s |"
        % (
            _fmt(fit["gates"]["G-L7c_efficiency_mean"], 2),
            _fmt(fit["gates"]["G-L7c_efficiency_min"], 2),
            _fmt(fit["gates"]["G-L7c_efficiency_max"], 2),
            "PASS" if fit["gates"]["G-L7c_efficiency_pass"] else "FAIL",
        ),
        "| G-L7d sigma exported | %s |" % ("PASS" if fit["gates"]["G-L7d_sigma_present_pass"] else "FAIL"),
        "| G-L7e rho=1.05 marked extrapolated in held-out | %s |"
        % ("PASS" if fit["gates"]["G-L7e_extrapolated_105_marked_pass"] else "FAIL"),
        "",
        "## Fit Table",
        "",
        "| mode | bw | q | R2 interp | RMSE interp | R2 all | R2 kingman | resid sd | sigma sched | efficiency | adj max | gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in sorted(report_rows):
        mode, bw, q, r2_in, rmse_in, r2_all, r2_kg, resid_sd, sig, eff, adj, _mono, gate = row
        lines.append(
            "| %s | %g | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                mode,
                bw,
                q,
                _fmt(r2_in),
                _fmt(rmse_in),
                _fmt(r2_all),
                _fmt(r2_kg),
                _fmt(resid_sd),
                _fmt(sig),
                _fmt(eff, 2),
                _fmt(adj),
                "PASS" if gate else "FAIL",
            )
        )

    lines += [
        "",
        "CBR uses held-out RMSE instead of R2 because the curve is nearly flat at the software floor.",
        "For CBR, the predictive gate is evaluated only on subcritical held-out rho <= 0.90; the critical shoulder is reported separately because Amendment 6 marked rho near 1 as singular.",
        "Small non-monotone measurement wiggles are projected with weighted isotonic regression before PCHIP; the raw means remain in `delay_observed`.",
        "",
        "![Delay curves](figures/l7_ref_curves.svg)",
        "",
        "![Sigma curves](figures/l7_ref_sigma.svg)",
        "",
        "## Variance Floor",
        "",
        "| quantity | value ms |",
        "|---|---:|",
        "| sigma_machine | %s |" % _fmt(variance["sigma_machine_ms"]),
        "| sigma_repeat | %s |" % _fmt(variance["sigma_repeat_ms"]),
        "| sigma_schedule | %s |" % _fmt(variance["sigma_schedule_ms"]),
        "| alpha=0.10 half-width floor | %s |" % _fmt(variance["alpha10_half_width_floor_ms"]),
        "| schedule variance share | %s |" % _fmt(variance["schedule_variance_share"], 5),
        "",
        "## c_a Counterexample at bw=6 q=13 rho=0.90",
        "",
        "| mode | c_a mean | c_a sd | q mean ms | q sd ms | Reich mean ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("cbr", "poisson", "h2", "onoff"):
        v = ca_counter[mode]
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                mode,
                _fmt(v["ca_mean"]),
                _fmt(v["ca_sd"]),
                _fmt(v["q_mean_ms"]),
                _fmt(v["q_sd_ms"]),
                _fmt(v["reich_mean_ms"]),
            )
        )
    lines += [
        "",
        "Reich/delay correlation across the four modes: `%s`." % _fmt(ca_counter.get("_reich_delay_corr")),
        "",
        "Conclusion: do not build `f(rho, c_a)`. The deployable model remains conditioned by traffic family.",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def fit_from_state(
    state_path: str = DEFAULT_STATE,
    out_path: str = OUT,
    reich_path: str = REICH_OUT,
    report_path: str = REPORT,
    compute_reich: bool = True,
) -> Dict[str, Any]:
    state = load_state(state_path)
    rows = state["rows"]
    selected = fit_rows(rows)
    links, report_rows = build_links(selected)
    reich = compute_reich_rows(rows) if compute_reich else {"rows": [], "n_rows": 0, "n_missing": 0}
    if compute_reich:
        _write_json(reich_path, reich)
        add_reich_to_links(links, reich)
    variance = summarize_variance(state)
    ca_counter = summarize_ca_counterexample(rows, reich)
    gates = make_gates(report_rows, links)
    fit = {
        "source": state_path,
        "rho_all": RHO_ALL,
        "rho_train_grid_for_heldout": RHO_TRAIN,
        "rho_heldout": RHO_HELD,
        "r2_gate": R2_GATE,
        "cbr_rmse_gate_ms": CBR_RMSE_GATE_MS,
        "n_campaign_rows": len(rows),
        "n_fit_rows": len(selected),
        "n_links": len(links),
        "links": links,
        "variance_decomposition": variance,
        "ca_counterexample": ca_counter,
        "reich": {
            "path": reich_path if compute_reich else None,
            "n_rows": reich.get("n_rows", 0),
            "n_missing": reich.get("n_missing", 0),
            "computed_from": "recorded *_bgtx.bin timestamps",
        },
        "gates": gates,
    }
    _write_json(out_path, fit)
    write_report(report_path, fit, report_rows, variance, ca_counter)
    return fit


def print_summary(fit: Dict[str, Any]) -> None:
    print("Dung %d/%d campaign rows cho fit (probe=20, block A/B/C)" % (fit["n_fit_rows"], fit["n_campaign_rows"]))
    print("Ghi -> results/phase-L/link_model_v2_fit.json")
    print("Ghi -> docs/phase-L/07-fit.md")
    print("\n" + "=" * 112)
    print(
        "%-8s %-4s %-3s | %-9s %-9s %-9s | %-9s %-9s %-8s %-8s | %s"
        % ("mode", "bw", "q", "R2_in", "RMSE_in", "R2_all", "sd_du", "sig_sch", "eff", "adj", "gate")
    )
    print("=" * 112)
    for key in sorted(fit["links"]):
        v = fit["links"][key]
        print(
            "%-8s %-4g %-3d | %-9s %-9s %-9s | %-9s %-9s %-8s %-8s | %s"
            % (
                v["mode"],
                v["bw"],
                v["q"],
                _fmt(v["heldout_r2_interp"]),
                _fmt(v["heldout_rmse_interp_ms"]),
                _fmt(v["heldout_r2_all"]),
                _fmt(v["resid_sd"]),
                _fmt(v["sigma_schedule"]),
                _fmt(v["model_efficiency"], 2),
                _fmt(v["max_monotone_adjustment_ms"]),
                "PASS" if v["predict_gate_pass"] else "FAIL",
            )
        )
    print("\nGates:")
    for key, value in fit["gates"].items():
        print("  %-38s %s" % (key, value))
    ca = fit["ca_counterexample"]
    print("\nA7-4 counterexample, bw=6 q=13 rho=0.90:")
    for mode in ("cbr", "poisson", "h2", "onoff"):
        v = ca[mode]
        print(
            "  %-8s c_a=%s +/- %s | q=%s ms | Reich=%s ms"
            % (_fmt(mode), _fmt(v["ca_mean"], 3), _fmt(v["ca_sd"], 3), _fmt(v["q_mean_ms"], 3), _fmt(v["reich_mean_ms"], 2))
        )
    print("  corr(Reich, delay) = %s" % _fmt(ca.get("_reich_delay_corr"), 3))


def main() -> None:
    ap = argparse.ArgumentParser(description="Fit Phase L link_model_v2")
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--reich-out", default=REICH_OUT)
    ap.add_argument("--report", default=REPORT)
    ap.add_argument("--skip-reich", action="store_true")
    args = ap.parse_args()
    fit = fit_from_state(
        state_path=args.state,
        out_path=args.out,
        reich_path=args.reich_out,
        report_path=args.report,
        compute_reich=not args.skip_reich,
    )
    print_summary(fit)


if __name__ == "__main__":
    main()

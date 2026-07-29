#!/usr/bin/env python3
"""Lesson L.5 -- pilot grid and seed-variance measurement.

The full live run is intentionally long: 42 points x 70 s, about 50 minutes.
Pure helpers in this file are importable by unit tests without Mininet.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from typing import Any, Dict, Iterable, List, Sequence, Tuple


BW = 6.0
Q = 13
MODES = ("cbr", "poisson", "h2")
RHO_MAIN = (0.50, 0.70, 0.80, 0.90, 0.95, 1.00)
RHO_VAR = (0.80, 0.95)
SEEDS_VAR = (11, 12, 13, 14, 15)
DUR = 70.0
WARM = 10.0
PORT = 5555
RAW = "results/phase-L/raw"
LG = "python3 -m measurements.load_gen"
PB = "python3 -m measurements.owd_probe"
ORDER_SEED = 9000

# Prediction table signed before looking at pilot data. Do not tune from pilot.
PRED = {
    "cbr": {
        0.50: 0.00,
        0.70: 0.00,
        0.80: 0.00,
        0.90: 0.00,
        0.95: 0.00,
        1.00: 23.17,
    },
    "poisson": {
        0.50: 0.28,
        0.70: 1.16,
        0.80: 2.55,
        0.90: 5.77,
        0.95: 8.37,
        1.00: 11.70,
    },
    "h2": {
        0.50: 1.42,
        0.70: 5.31,
        0.80: 8.05,
        0.90: 10.67,
        0.95: 11.82,
        1.00: 12.89,
    },
}


def mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sd(values: Sequence[float]) -> float:
    if len(values) <= 1:
        return float("nan")
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def make_plan() -> List[Tuple[str, float, int]]:
    plan = [(mode, rho, SEEDS_VAR[0]) for mode in MODES for rho in RHO_MAIN]
    plan += [
        (mode, rho, seed)
        for mode in MODES
        for rho in RHO_VAR
        for seed in SEEDS_VAR[1:]
    ]
    random.Random(ORDER_SEED).shuffle(plan)
    return plan


def gate_point(row: Dict[str, Any]) -> List[str]:
    """Per-point gates from Amendment 5 A5-7."""
    bad: List[str] = []
    if int(row["socket_drops"]) != 0:
        bad.append("socket_drops=%d" % int(row["socket_drops"]))
    if int(row["n_foreign"]) != 0:
        bad.append("foreign=%d" % int(row["n_foreign"]))
    if abs(float(row["rate_ratio"]) - 1.0) > 0.001:
        bad.append("rate_ratio=%.4f" % float(row["rate_ratio"]))
    if abs(float(row["rho_actual"]) - float(row["rho_nominal"])) > 0.002:
        bad.append("rho lech")
    if float(row["n_late_ratio"]) > 0.001:
        bad.append("n_late=%.4f" % float(row["n_late_ratio"]))
    if float(row["max_late_ms"]) > 50.0:
        bad.append("max_late=%.1f" % float(row["max_late_ms"]))
    return bad


def summarize_pilot(rows: Sequence[Dict[str, Any]], floor: float | None = None) -> Dict[str, Any]:
    """Return machine-readable L.5 gates and power-analysis summary."""
    if floor is None:
        floor = next(
            (
                row["q_mean_ms"]
                for row in rows
                if row["mode"] == "cbr"
                and float(row["rho_nominal"]) == 0.50
                and int(row["seed"]) == SEEDS_VAR[0]
            ),
            0.15,
        )

    prediction_rows = []
    n_close = 0
    for mode in MODES:
        for rho in RHO_MAIN:
            row = next(
                row
                for row in rows
                if row["mode"] == mode
                and float(row["rho_nominal"]) == rho
                and int(row["seed"]) == SEEDS_VAR[0]
            )
            measured = float(row["q_mean_ms"]) - float(floor)
            pred = PRED[mode][rho]
            delta = measured - pred
            close = abs(delta) < max(0.5, 0.20 * pred)
            n_close += int(close)
            prediction_rows.append(
                {
                    "mode": mode,
                    "rho": rho,
                    "measured_minus_floor_ms": measured,
                    "pred_ms": pred,
                    "delta_ms": delta,
                    "close": bool(close),
                }
            )

    monotonic = {}
    for mode in MODES:
        values = [
            next(
                row["q_mean_ms"]
                for row in rows
                if row["mode"] == mode
                and float(row["rho_nominal"]) == rho
                and int(row["seed"]) == SEEDS_VAR[0]
            )
            for rho in RHO_MAIN
        ]
        monotonic[mode] = bool(
            all(values[i] <= values[i + 1] + 0.3 for i in range(len(values) - 1))
        )

    separated = {}
    for rho in RHO_MAIN:
        if rho < 0.70:
            continue
        vals = {
            mode: next(
                row["q_mean_ms"]
                for row in rows
                if row["mode"] == mode
                and float(row["rho_nominal"]) == rho
                and int(row["seed"]) == SEEDS_VAR[0]
            )
            for mode in MODES
        }
        separated[str(rho)] = bool(vals["cbr"] < vals["poisson"] < vals["h2"])

    seed_sd = {}
    smax = 0.0
    for mode in MODES:
        for rho in RHO_VAR:
            subset = [
                row
                for row in rows
                if row["mode"] == mode and float(row["rho_nominal"]) == rho
            ]
            q_values = [float(row["q_mean_ms"]) for row in subset]
            s = sd(q_values)
            seed_sd["%s_r%.2f" % (mode, rho)] = {
                "n": len(q_values),
                "mean_ms": mean(q_values),
                "sd_between_seed_ms": s,
                "se_batch_mean_ms": mean(
                    [
                        float(row["se_batch_ms"])
                        for row in subset
                        if row.get("se_batch_ms") is not None
                    ]
                ),
            }
            if math.isfinite(s):
                smax = max(smax, s)

    n_for_large_gap = max(2, math.ceil(8 * smax * smax / (4.72 * 4.72)))
    n_for_1ms = max(2, math.ceil(8 * smax * smax))
    point_fails = [row for row in rows if row.get("gate_fail")]

    pasta = {}
    for mode in MODES:
        for rho in RHO_VAR:
            values = [
                float(row["delta_pasta_ms"])
                for row in rows
                if row["mode"] == mode and float(row["rho_nominal"]) == rho
            ]
            if len(values) < 2:
                continue
            mu = mean(values)
            half_width = 2.776 * sd(values) / math.sqrt(len(values))
            pasta["%s_r%.2f" % (mode, rho)] = {
                "n": len(values),
                "mean_ms": mu,
                "ci95_half_width_ms": half_width,
                "ci95_covers_zero": bool(mu - half_width <= 0 <= mu + half_width),
            }

    loss_breakpoints = {}
    for mode in MODES:
        loss_breakpoints[mode] = None
        for rho in RHO_MAIN:
            row = next(
                row
                for row in rows
                if row["mode"] == mode
                and float(row["rho_nominal"]) == rho
                and int(row["seed"]) == SEEDS_VAR[0]
            )
            if float(row["loss"]) >= 0.01:
                loss_breakpoints[mode] = {"rho": rho, "loss": float(row["loss"])}
                break

    return {
        "floor_ms": floor,
        "prediction": {
            "rows": prediction_rows,
            "n_close": n_close,
            "n_total": len(prediction_rows),
            "pass": bool(n_close >= 14),
        },
        "monotonic": {"by_mode": monotonic, "pass": all(monotonic.values())},
        "separated": {"by_rho": separated, "pass": all(separated.values())},
        "power": {
            "seed_sd": seed_sd,
            "sd_between_seed_max_ms": smax,
            "n_for_gap_4p72_ms": n_for_large_gap,
            "n_for_gap_1p00_ms": n_for_1ms,
            "pass": bool(n_for_large_gap <= 5),
        },
        "pasta": pasta,
        "loss_breakpoints": loss_breakpoints,
        "point_gates": {
            "n_fail": len(point_fails),
            "n_total": len(rows),
            "pass": bool(len(point_fails) <= 2),
        },
    }


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def one_point(net: Any, tag: str, rho: float, mode: str, seed: int) -> Dict[str, Any]:
    from measurements.owd_analyze import analyze

    h1, h2 = net.get("h1"), net.get("h2")
    cwd = os.getcwd()
    prefix = "%s/%s" % (RAW, tag)

    h1.cmd("pkill -f 'measurements.load_gen' 2>/dev/null")
    h2.cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
    time.sleep(0.2)
    h2.cmd(
        "cd %s && %s recv --port %d --duration %g --out-prefix %s >/dev/null 2>&1 &"
        % (cwd, PB, PORT, DUR + 6.0, prefix)
    )
    time.sleep(0.8)
    h1.cmd(
        "cd %s && %s --dst 10.0.0.2 --port %d --bw %g --rho %g --mode %s "
        "--duration %g --seed %d --run-id %d --out-prefix %s >/dev/null 2>&1"
        % (cwd, LG, PORT, BW, rho, mode, DUR, seed, seed, prefix)
    )
    time.sleep(6.5)

    tx = _load_json(prefix + "_tx.meta.json")
    rx = _load_json(prefix + "_rx.meta.json")
    bg = analyze(prefix + "_bg.bin", prefix + "_bgtx.bin", warmup_s=WARM)
    probe = analyze(prefix + "_probe.bin", prefix + "_prtx.bin", warmup_s=WARM)
    steady = bg.get("steady_state", {})
    sent_total = max(tx["counts"]["n_bg_sent"] + tx["counts"]["n_probe_sent"], 1)
    return {
        "rho_nominal": float(rho),
        "mode": mode,
        "seed": int(seed),
        "rho_actual": tx["rates"]["rho_actual"],
        "rate_ratio": tx["rates"]["rate_ratio"],
        "ca_actual": tx["c_a"]["actual_bg"],
        "ca_aggregate": tx["c_a"]["aggregate_schedule"],
        "q_mean_ms": bg["owd_ms"]["mean"],
        "q_p50_ms": bg["owd_ms"]["p50"],
        "q_p95_ms": bg["owd_ms"]["p95"],
        "q_p99_ms": bg["owd_ms"]["p99"],
        "loss": bg["loss_rate"],
        "probe_mean_ms": probe["owd_ms"]["mean"],
        "delta_pasta_ms": bg["owd_ms"]["mean"] - probe["owd_ms"]["mean"],
        "se_batch_ms": steady.get("se_batch_means_ms"),
        "se_naive_ms": steady.get("se_naive_ms"),
        "inflation_factor": steady.get("inflation_factor"),
        "spread_ms": steady.get("spread_ms"),
        "n_late_ratio": tx["counts"]["n_late"] / sent_total,
        "max_late_ms": tx["counts"]["max_late_ms"],
        "socket_drops": rx["socket_drops_delta"],
        "n_foreign": rx["n_foreign_packets"],
    }


def _print_summary(rows: Sequence[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("1. DUONG CONG q(rho) vs DU DOAN DA KY")
    print("=" * 78)
    print("   san = %.3f ms\n" % summary["floor_ms"])
    print("   %-8s %-6s %-10s %-10s %-10s %-8s" % ("mode", "rho", "do-san", "du doan", "lech", "close"))
    for row in summary["prediction"]["rows"]:
        print(
            "   %-8s %-6.2f %-10.3f %-10.3f %-10.3f %-8s"
            % (
                row["mode"],
                row["rho"],
                row["measured_minus_floor_ms"],
                row["pred_ms"],
                row["delta_ms"],
                "OK" if row["close"] else "FAIL",
            )
        )
    print(
        "\n   KHOP: %d/%d  %s"
        % (
            summary["prediction"]["n_close"],
            summary["prediction"]["n_total"],
            "PASS" if summary["prediction"]["pass"] else "* FAIL",
        )
    )

    print("\n" + "=" * 78)
    print("2. DON DIEU + TACH BIET")
    print("=" * 78)
    print("   don dieu:", summary["monotonic"]["by_mode"])
    print("   tach biet:", summary["separated"]["by_rho"])

    print("\n" + "=" * 78)
    print("3. POWER ANALYSIS")
    print("=" * 78)
    for key, value in summary["power"]["seed_sd"].items():
        print(
            "   %-14s n=%d mean=%.3f sd_seed=%.3f se_batch=%.3f"
            % (
                key,
                value["n"],
                value["mean_ms"],
                value["sd_between_seed_ms"],
                value["se_batch_mean_ms"],
            )
        )
    print(
        "   sd max=%.3f -> n gap 4.72ms=%d, n gap 1ms=%d"
        % (
            summary["power"]["sd_between_seed_max_ms"],
            summary["power"]["n_for_gap_4p72_ms"],
            summary["power"]["n_for_gap_1p00_ms"],
        )
    )

    print("\n" + "=" * 78)
    print("4. PASTA DELTA")
    print("=" * 78)
    for key, value in summary["pasta"].items():
        print(
            "   %-16s delta=%+.3f +- %.3f ms CI95 phu 0: %s"
            % (
                key,
                value["mean_ms"],
                value["ci95_half_width_ms"],
                "CO" if value["ci95_covers_zero"] else "KHONG",
            )
        )

    print("\n" + "=" * 78)
    print("5. DIEM GAY LOSS")
    print("=" * 78)
    for mode, value in summary["loss_breakpoints"].items():
        if value is None:
            print("   %-8s loss < 1%% tren dai da do" % mode)
        else:
            print("   %-8s loss >= 1%% tu rho=%.2f (loss=%.4f)" % (mode, value["rho"], value["loss"]))


def run_live() -> str:
    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_split_qdisc import (
        SplitQdiscTopo,
        intf_toward,
        setup_measure_qdisc,
        setup_return_qdisc,
    )

    os.makedirs(RAW, exist_ok=True)
    stamp = time.strftime("%m%d_%H%M")
    rows = []
    plan = make_plan()
    print("Tong %d diem, thu tu ngau nhien seed=%d\n" % (len(plan), ORDER_SEED))

    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        setup_return_qdisc(intf_toward(s2, "s1"), 3.0)
        setup_measure_qdisc(intf_toward(s1, "s2"), BW, Q)

        t0 = time.time()
        for i, (mode, rho, seed) in enumerate(plan, 1):
            row = one_point(net, "l5_%s_r%03d_s%d" % (mode, int(rho * 100), seed), rho, mode, seed)
            row["gate_fail"] = gate_point(row)
            rows.append(row)
            eta_min = (time.time() - t0) / i * (len(plan) - i) / 60.0
            print(
                "[%2d/%2d] %-8s rho=%.2f s=%d | q=%7.3f p95=%7.3f "
                "loss=%.4f SE_b=%.3f | %s (con %.0f phut)"
                % (
                    i,
                    len(plan),
                    mode,
                    rho,
                    seed,
                    row["q_mean_ms"],
                    row["q_p95_ms"],
                    row["loss"],
                    row["se_batch_ms"] or -1,
                    "OK" if not row["gate_fail"] else "*" + ",".join(row["gate_fail"]),
                    eta_min,
                )
            )
    finally:
        try:
            net.get("h1").cmd("pkill -f 'measurements.load_gen' 2>/dev/null")
            net.get("h2").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
        except Exception:
            pass
        net.stop()

    summary = summarize_pilot(rows)
    _print_summary(rows, summary)

    out = "results/phase-L/l5_pilot_%s.json" % stamp
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "bw": BW,
                    "q": Q,
                    "dur": DUR,
                    "warm": WARM,
                    "order_seed": ORDER_SEED,
                },
                "prediction_signed": PRED,
                "summary": summary,
                "rows": rows,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    print("\nGhi -> %s" % out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase L / L.5 pilot")
    parser.add_argument("--dry-run", action="store_true", help="print randomized plan only")
    args = parser.parse_args()
    if args.dry_run:
        for i, (mode, rho, seed) in enumerate(make_plan(), 1):
            print("%02d %s rho=%.2f seed=%d" % (i, mode, rho, seed))
        return
    run_live()


if __name__ == "__main__":
    main()

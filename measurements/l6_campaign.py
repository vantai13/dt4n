#!/usr/bin/env python3
"""Lesson L.6 -- long measurement campaign with checkpoint/resume.

Live imports are intentionally inside ``run_live`` so plan/state/gate tests can
run without root or Mininet.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple


RHO = (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 1.00, 1.02, 1.05)
CONFIGS = ((8.0, 18), (6.0, 13), (4.0, 10))
MODES3 = ("cbr", "poisson", "h2")
SEEDS = (11, 12, 13, 14, 15)
SEEDS_CRIT = (16, 17, 18, 19, 20)
RHO_CRIT = (0.98, 1.00, 1.02)
RHO_CTRL = (0.70, 0.80, 0.90, 0.95)
REF = (6.0, 13)
DUR = 70.0
WARM = 10.0
DELAY_MS = 3.0
PORT = 5555
RAW = "results/phase-L/raw"
ORDER_SEED = 9000
SENTINEL_EVERY = 30
SENTINEL = {"mode": "h2", "rho": 0.90, "bw": 6.0, "q": 13, "seed": 999, "probe_pps": 20.0}
SENTINEL_REF = {"mean_ms": 10.751, "sd_ms": 0.212}
STATE = "results/phase-L/campaign_state.json"
LG = "python3 -m measurements.load_gen"
PB = "python3 -m measurements.owd_probe"


Point = Dict[str, Any]
State = Dict[str, Any]


def _pid(point: Point, idx: int) -> str:
    return "l6_%04d_%s_b%g_q%d_r%04d_s%d_p%g" % (
        idx,
        point["mode"],
        point["bw"],
        point["q"],
        int(round(float(point["rho"]) * 1000)),
        point["seed"],
        point["probe_pps"],
    )


def build_plan() -> List[Point]:
    """Return deterministic randomized plan with sentinel points inserted."""
    regular: List[Point] = []
    for mode in MODES3:
        for bw, q in CONFIGS:
            for rho in RHO:
                for seed in SEEDS:
                    regular.append(
                        {
                            "mode": mode,
                            "rho": rho,
                            "bw": bw,
                            "q": q,
                            "seed": seed,
                            "probe_pps": 20.0,
                            "block": "A",
                        }
                    )
    for rho in RHO:
        for seed in SEEDS:
            regular.append(
                {
                    "mode": "onoff",
                    "rho": rho,
                    "bw": REF[0],
                    "q": REF[1],
                    "seed": seed,
                    "probe_pps": 20.0,
                    "block": "B",
                }
            )
    for mode in MODES3:
        for rho in RHO_CRIT:
            for seed in SEEDS_CRIT:
                regular.append(
                    {
                        "mode": mode,
                        "rho": rho,
                        "bw": REF[0],
                        "q": REF[1],
                        "seed": seed,
                        "probe_pps": 20.0,
                        "block": "C",
                    }
                )
    for mode in MODES3:
        for rho in RHO_CTRL:
            for seed in SEEDS:
                regular.append(
                    {
                        "mode": mode,
                        "rho": rho,
                        "bw": REF[0],
                        "q": REF[1],
                        "seed": seed,
                        "probe_pps": 0.0,
                        "block": "D",
                    }
                )

    random.Random(ORDER_SEED).shuffle(regular)

    out: List[Point] = []
    for i, point in enumerate(regular, 1):
        out.append(point)
        if i % SENTINEL_EVERY == 0:
            out.append({**SENTINEL, "block": "E"})

    for idx, point in enumerate(out):
        point["idx"] = idx
        point["pid"] = _pid(point, idx)
    return out


def load_state(path: str = STATE) -> State:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "order_seed": ORDER_SEED,
        "sentinel_every": SENTINEL_EVERY,
        "done_idx": [],
        "rows": [],
        "sentinels": [],
    }


def save_state(state: State, path: str = STATE) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def select_todo(
    plan: Sequence[Point],
    state: State,
    session: Optional[int] = None,
    n_sessions: int = 4,
    max_points: Optional[int] = None,
) -> List[Point]:
    done = set(int(i) for i in state.get("done_idx", []))
    todo = [point for point in plan if int(point["idx"]) not in done]
    if session is not None:
        per = int(math.ceil(len(plan) / float(n_sessions)))
        lo = (int(session) - 1) * per
        hi = int(session) * per
        todo = [point for point in todo if lo <= int(point["idx"]) < hi]
    if max_points is not None:
        todo = todo[: int(max_points)]
    return todo


def gate(row: Dict[str, Any]) -> List[str]:
    bad: List[str] = []
    if int(row.get("socket_drops", 0)) != 0:
        bad.append("socket_drops=%d" % int(row["socket_drops"]))
    if int(row.get("n_foreign", 0)) != 0:
        bad.append("foreign=%d" % int(row["n_foreign"]))
    if abs(float(row["rate_ratio"]) - 1.0) > 0.001:
        bad.append("rate=%.5f" % float(row["rate_ratio"]))
    if abs(float(row["rho_actual"]) - float(row["rho"])) > 0.002:
        bad.append("rho lech")
    if float(row.get("n_late_ratio", 0.0)) > 0.001:
        bad.append("late=%.4f" % float(row["n_late_ratio"]))
    if float(row.get("max_late_ms", 0.0)) > 50.0:
        bad.append("maxlate=%.0f" % float(row["max_late_ms"]))
    return bad


def sentinel_summary(sentinels: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    values = [float(row["q_mean_ms"]) for row in sentinels]
    if not values:
        return {"n": 0}
    mean = sum(values) / len(values)
    sd = (
        math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1))
        if len(values) > 1
        else None
    )
    z = [(x - SENTINEL_REF["mean_ms"]) / SENTINEL_REF["sd_ms"] for x in values]
    out3 = sum(1 for x in z if abs(x) > 3.0)
    slope = None
    trend_flag = None
    if len(values) >= 4:
        xs = list(range(len(values)))
        mx = sum(xs) / len(xs)
        my = mean
        denom = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, values)) / denom
        trend_flag = abs(slope) * len(values) >= SENTINEL_REF["sd_ms"]
    return {
        "n": len(values),
        "mean_ms": mean,
        "sd_ms": sd,
        "min_ms": min(values),
        "max_ms": max(values),
        "z": z,
        "n_outside_3sigma": out3,
        "slope_ms_per_sentinel": slope,
        "trend_flag": trend_flag,
        "pass": bool(out3 == 0 and trend_flag is not True),
    }


def campaign_summary(state: State, plan: Sequence[Point]) -> Dict[str, Any]:
    rows = state.get("rows", [])
    fails = [row for row in rows if row.get("gate_fail")]
    done_unique = len(set(int(i) for i in state.get("done_idx", [])))
    sent = sentinel_summary(state.get("sentinels", []))
    return {
        "n_plan": len(plan),
        "n_done": done_unique,
        "n_rows": len(rows),
        "n_fail": len(fails),
        "coverage": done_unique / len(plan) if plan else 0.0,
        "coverage_pass": bool(done_unique >= math.ceil(0.98 * len(plan))),
        "fail_pass": bool(len(fails) <= 15),
        "sentinel": sent,
    }


def measure(net: Any, point: Point) -> Dict[str, Any]:
    from measurements.owd_analyze import analyze

    h1, h2 = net.get("h1"), net.get("h2")
    cwd = os.getcwd()
    prefix = "%s/%s" % (RAW, point["pid"])
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
        "--duration %g --seed %d --run-id %d --probe-pps %g --out-prefix %s "
        ">/dev/null 2>&1"
        % (
            cwd,
            LG,
            PORT,
            point["bw"],
            point["rho"],
            point["mode"],
            DUR,
            point["seed"],
            point["idx"],
            point["probe_pps"],
            prefix,
        )
    )
    time.sleep(6.5)

    with open(prefix + "_tx.meta.json", "r", encoding="utf-8") as f:
        tx = json.load(f)
    with open(prefix + "_rx.meta.json", "r", encoding="utf-8") as f:
        rx = json.load(f)
    bg = analyze(prefix + "_bg.bin", prefix + "_bgtx.bin", warmup_s=WARM)
    probe = None
    if point["probe_pps"] > 0 and os.path.getsize(prefix + "_probe.bin") > 0:
        probe = analyze(prefix + "_probe.bin", prefix + "_prtx.bin", warmup_s=WARM)

    steady = bg.get("steady_state", {})
    owd = bg["owd_ms"]
    sent_total = max(tx["counts"]["n_bg_sent"] + tx["counts"]["n_probe_sent"], 1)
    return {
        **point,
        "rho_actual": tx["rates"]["rho_actual"],
        "rate_ratio": tx["rates"]["rate_ratio"],
        "ca_actual": tx["c_a"]["actual_bg"],
        "ca_aggregate": tx["c_a"]["aggregate_schedule"],
        "schedule_digest": tx["schedule"]["digest_bg"],
        "q_mean_ms": owd["mean"],
        "q_sd_ms": owd["sd"],
        "q_p50_ms": owd["p50"],
        "q_p90_ms": owd["p90"],
        "q_p95_ms": owd["p95"],
        "q_p99_ms": owd["p99"],
        "loss": bg["loss_rate"],
        "n_recv_unique": bg["counts"]["n_recv_unique"],
        "probe_mean_ms": probe["owd_ms"]["mean"] if probe else None,
        "delta_pasta_ms": owd["mean"] - probe["owd_ms"]["mean"] if probe else None,
        "se_batch_ms": steady.get("se_batch_means_ms"),
        "se_naive_ms": steady.get("se_naive_ms"),
        "inflation": steady.get("inflation_factor"),
        "spread_ms": steady.get("spread_ms"),
        "n_late_ratio": tx["counts"]["n_late"] / sent_total,
        "max_late_ms": tx["counts"]["max_late_ms"],
        "socket_drops": rx["socket_drops_delta"],
        "n_foreign": rx["n_foreign_packets"],
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run_live(args: argparse.Namespace) -> None:
    plan = build_plan()
    state = load_state(args.state)
    todo = select_todo(plan, state, args.session, args.n_sessions, args.max_points)
    print(
        "Ke hoach %d diem | da xong %d | phien nay %d diem (~%.1f gio)"
        % (
            len(plan),
            len(set(int(i) for i in state.get("done_idx", []))),
            len(todo),
            len(todo) * 77.0 / 3600.0,
        )
    )
    if args.plan_only:
        for point in todo:
            print(
                "%04d %-7s bw=%g q=%d rho=%.3f seed=%d probe=%g block=%s"
                % (
                    point["idx"],
                    point["mode"],
                    point["bw"],
                    point["q"],
                    point["rho"],
                    point["seed"],
                    point["probe_pps"],
                    point["block"],
                )
            )
        return

    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_split_qdisc import (
        SplitQdiscTopo,
        change_measure_qdisc,
        intf_toward,
        setup_measure_qdisc,
        setup_return_qdisc,
    )

    os.makedirs(RAW, exist_ok=True)
    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        if_measure = intf_toward(s1, "s2")
        setup_return_qdisc(intf_toward(s2, "s1"), DELAY_MS)
        setup_measure_qdisc(if_measure, REF[0], REF[1])
        current = REF
        t0 = time.time()

        for k, point in enumerate(todo, 1):
            if (point["bw"], point["q"]) != current:
                change_measure_qdisc(if_measure, point["bw"], point["q"])
                current = (point["bw"], point["q"])
                time.sleep(0.2)

            row = measure(net, point)
            row["gate_fail"] = gate(row)
            row["attempt"] = 1
            if row["gate_fail"]:
                print("      * fail: %s -> chay lai 1 lan" % ",".join(row["gate_fail"]))
                row2 = measure(net, point)
                row2["gate_fail"] = gate(row2)
                row2["attempt"] = 2
                row2["attempt1_fail"] = row["gate_fail"]
                row = row2

            state.setdefault("rows", []).append(row)
            state.setdefault("done_idx", []).append(point["idx"])
            if point["block"] == "E":
                state.setdefault("sentinels", []).append(
                    {
                        "idx": point["idx"],
                        "t": row["wall_utc"],
                        "q_mean_ms": row["q_mean_ms"],
                    }
                )
            save_state(state, args.state)

            tag = ""
            if point["block"] == "E":
                z = (row["q_mean_ms"] - SENTINEL_REF["mean_ms"]) / SENTINEL_REF["sd_ms"]
                tag = " [CANH z=%+.2f%s]" % (
                    z,
                    " *NGOAI KIEM SOAT" if abs(z) > 3.0 else "",
                )
            eta = (time.time() - t0) / k * (len(todo) - k) / 3600.0
            print(
                "[%4d/%4d] %-8s bw=%g q=%2d rho=%.3f s=%3d p=%2g | "
                "q=%7.3f p95=%7.3f loss=%.4f | %-4s (con %.1f h)%s"
                % (
                    k,
                    len(todo),
                    point["mode"],
                    point["bw"],
                    point["q"],
                    point["rho"],
                    point["seed"],
                    point["probe_pps"],
                    row["q_mean_ms"],
                    row["q_p95_ms"],
                    row["loss"],
                    "OK" if not row["gate_fail"] else "FAIL",
                    eta,
                    tag,
                )
            )
    finally:
        try:
            net.get("h1").cmd("pkill -f 'measurements.load_gen' 2>/dev/null")
            net.get("h2").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
        except Exception:
            pass
        net.stop()
        save_state(state, args.state)

    summary = campaign_summary(state, plan)
    print("\n=== TONG KET ===")
    print(
        "  da xong %d/%d diem | fail sau khi chay lai: %d"
        % (summary["n_done"], summary["n_plan"], summary["n_fail"])
    )
    sent = summary["sentinel"]
    if sent.get("n", 0) >= 2:
        print("\n  * BIEU DO KIEM SOAT -- DIEM CANH")
        print(
            "     tham chieu: %.3f +- %.3f ms | gioi han 3-sigma [%.2f, %.2f]"
            % (
                SENTINEL_REF["mean_ms"],
                SENTINEL_REF["sd_ms"],
                SENTINEL_REF["mean_ms"] - 3 * SENTINEL_REF["sd_ms"],
                SENTINEL_REF["mean_ms"] + 3 * SENTINEL_REF["sd_ms"],
            )
        )
        print(
            "     n=%d mean=%.3f sd=%s min=%.3f max=%.3f ngoai_3sigma=%d pass=%s"
            % (
                sent["n"],
                sent["mean_ms"],
                "%.3f" % sent["sd_ms"] if sent["sd_ms"] is not None else "NA",
                sent["min_ms"],
                sent["max_ms"],
                sent["n_outside_3sigma"],
                sent["pass"],
            )
        )
        if sent.get("slope_ms_per_sentinel") is not None:
            print(
                "     do doc theo thoi gian: %+.4f ms/diem-canh (%s)"
                % (
                    sent["slope_ms_per_sentinel"],
                    "CO XU HUONG" if sent["trend_flag"] else "khong dang ke",
                )
            )
    print("\n  state -> %s" % args.state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase L / L.6 campaign")
    parser.add_argument("--session", type=int, default=None, help="1..4; omit to run all remaining")
    parser.add_argument("--n-sessions", type=int, default=4)
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument("--state", default=STATE)
    parser.add_argument("--resume", action="store_true", help="accepted for readability; resume is default")
    parser.add_argument("--plan-only", action="store_true", help="print selected plan without Mininet")
    args = parser.parse_args()
    if args.session is not None and not (1 <= args.session <= args.n_sessions):
        raise SystemExit("--session phai nam trong 1..%d" % args.n_sessions)
    run_live(args)


if __name__ == "__main__":
    main()

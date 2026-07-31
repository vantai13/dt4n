#!/usr/bin/env python3
"""Phase T / T.5 -- step-response runner and T_relax estimator."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple


BW, Q = 6.0, 13
DT = 0.005
PORT = 5555
RAW = "results/phase-T/raw"
STATE = "results/phase-T/step_v2_state.json"
RG = "python3 -m measurements.rho_gen"
PB = "python3 -m measurements.owd_probe"
AMP_SIGNIFICANCE_K = 5.0


Point = Dict[str, Any]
State = Dict[str, Any]


def finite_mean(xs: Sequence[float]) -> float:
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    return sum(vals) / len(vals) if vals else float("nan")


def finite_sd(xs: Sequence[float]) -> float:
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    if len(vals) < 2:
        return float("nan")
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))


def amplitude_se(q_sd_ms: float, n_cycles: int, n_tail_bins: int) -> float:
    """Expected SE for the difference between the two plateau estimates."""
    q_sd = float(q_sd_ms)
    n = int(n_cycles)
    nb = int(n_tail_bins)
    if not math.isfinite(q_sd) or n <= 0 or nb <= 0:
        return float("nan")
    return q_sd * math.sqrt(2.0 / (n * nb))


def amplitude_significant(
    q_a_ms: float,
    q_b_ms: float,
    q_sd_ms: float,
    n_cycles: int,
    n_tail_bins: int,
    k: float = AMP_SIGNIFICANCE_K,
) -> bool:
    """Return True only when the two plateaus are separated above noise."""
    amp = abs(float(q_a_ms) - float(q_b_ms))
    se = amplitude_se(q_sd_ms, n_cycles, n_tail_bins)
    if not math.isfinite(se):
        return False
    if se <= 0.0:
        return amp > 1e-12
    return amp > float(k) * se


def T_area_v2(
    qbar: Sequence[float],
    binw: float,
    amp: float,
    c: float = 8.0,
    tail_frac: float = 0.15,
) -> float:
    """Area estimator with automatic window and plateau-referenced amplitude."""
    nb = len(qbar)
    if nb <= 1 or abs(float(amp)) < 1e-12:
        return float("nan")
    ntail = max(2, int(float(tail_frac) * nb))
    qinf = finite_mean(qbar[-ntail:])
    if not math.isfinite(qinf):
        return float("nan")

    integral = 0.0
    last = float("nan")
    for b, value in enumerate(qbar):
        if not math.isfinite(float(value)):
            continue
        integral += (float(value) - qinf) * float(binw)
        t_hat = integral / float(amp)
        last = t_hat
        if t_hat > 0.0 and (b + 1) * float(binw) >= float(c) * t_hat:
            return t_hat
    return last


def ensemble_average(
    owd_ms: Sequence[float],
    t_rel: Sequence[float],
    hold_s: float,
    n_cycles: int,
    binw: float,
    phase: str = "ab",
) -> Tuple[List[float], List[int]]:
    """Fold cycles and average one transition phase by bins.

    The generated trajectory repeats ``[rho_a]*hold + [rho_b]*hold``. Thus
    A->B lives in the second half of each cycle, while B->A lives in the first.
    """
    if phase not in ("ab", "ba"):
        raise ValueError("phase phai la 'ab' hoac 'ba'")
    period = 2.0 * float(hold_s)
    nb = int(round(float(hold_s) / float(binw)))
    acc = [0.0] * nb
    cnt = [0] * nb
    off = float(hold_s) if phase == "ab" else 0.0
    max_t = period * int(n_cycles)

    for q, t in zip(owd_ms, t_rel):
        tt = float(t)
        if tt < 0.0 or tt >= max_t:
            continue
        tau = (tt % period) - off
        if 0.0 <= tau < float(hold_s):
            b = int(tau / float(binw))
            if 0 <= b < nb:
                acc[b] += float(q)
                cnt[b] += 1
    return [a / c if c else float("nan") for a, c in zip(acc, cnt)], cnt


def estimate_from_cycles(
    owd_ms: Sequence[float],
    t_rel: Sequence[float],
    hold_s: float,
    n_cycles: int,
    binw: float,
) -> Dict[str, Any]:
    q_ab, cnt_ab = ensemble_average(owd_ms, t_rel, hold_s, n_cycles, binw, "ab")
    q_ba, cnt_ba = ensemble_average(owd_ms, t_rel, hold_s, n_cycles, binw, "ba")
    ntail = max(2, int(0.15 * len(q_ab)))
    q_b = finite_mean(q_ab[-ntail:])
    q_a = finite_mean(q_ba[-ntail:])
    q_sd = finite_sd(owd_ms)
    amp = q_a - q_b
    amp_abs = abs(amp)
    amp_se = amplitude_se(q_sd, n_cycles, ntail)
    amp_z = amp_abs / amp_se if amp_se > 0.0 else (float("inf") if amp_abs > 0 else 0.0)
    amp_ok = amplitude_significant(q_a, q_b, q_sd, n_cycles, ntail)
    t_ab = T_area_v2(q_ab, binw, amp) if amp_ok else float("nan")
    t_ba = T_area_v2(q_ba, binw, -amp) if amp_ok else float("nan")
    return {
        "T_ab_s": t_ab,
        "T_ba_s": t_ba,
        "T_mean_s": finite_mean([t_ab, t_ba]),
        "symmetry_ratio": (
            abs(t_ab - t_ba) / max(finite_mean([abs(t_ab), abs(t_ba)]), 1e-12)
            if math.isfinite(t_ab) and math.isfinite(t_ba)
            else float("nan")
        ),
        "q_a_ms": q_a,
        "q_b_ms": q_b,
        "amp_ms": amp_abs,
        "amp_se_ms": amp_se,
        "amp_z": amp_z,
        "amp_significant": amp_ok,
        "q_sd_all_ms": q_sd,
        "min_bin_count_ab": min(cnt_ab) if cnt_ab else 0,
        "min_bin_count_ba": min(cnt_ba) if cnt_ba else 0,
    }


def _pid(point: Point, idx: int) -> str:
    return "t5s2_%04d_%s_r%04d_%04d_h%04d_c%d_s%d_%s" % (
        idx,
        point["mode"],
        int(round(float(point["rho_a"]) * 1000)),
        int(round(float(point["rho_b"]) * 1000)),
        int(round(float(point["hold_s"]) * 100)),
        int(point["n_cycles"]),
        int(point["seed"]),
        point["block"],
    )


def build_plan() -> List[Point]:
    points: List[Point] = [
        {
            "mode": "h2",
            "rho_a": 0.80,
            "rho_b": 0.80,
            "hold_s": 0.6,
            "n_cycles": 262,
            "binw_s": 0.020,
            "seed": 11,
            "block": "S1",
        }
    ]
    configs = (
        ("h2", 0.60, 0.80, 262),
        ("h2", 0.80, 0.98, 398),
        ("poisson", 0.80, 0.98, 150),
        ("poisson", 0.60, 0.80, 766),
    )
    for mode, rho_a, rho_b, cycles in configs:
        for seed in (11, 12, 13):
            points.append(
                {
                    "mode": mode,
                    "rho_a": rho_a,
                    "rho_b": rho_b,
                    "hold_s": 0.6,
                    "n_cycles": cycles,
                    "binw_s": 0.020,
                    "seed": seed,
                    "block": "S23_v2",
                }
            )
    for idx, point in enumerate(points):
        point["idx"] = idx
        point["pid"] = _pid(point, idx)
        point["duration_s"] = 2.0 * point["hold_s"] * point["n_cycles"]
    return points


def load_state(path: str = STATE) -> State:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_idx": [], "rows": []}


def save_state(state: State, path: str = STATE) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def select_todo(
    plan: Sequence[Point],
    state: State,
    max_points: Optional[int] = None,
) -> List[Point]:
    done = set(int(i) for i in state.get("done_idx", []))
    todo = [p for p in plan if int(p["idx"]) not in done]
    return todo[: int(max_points)] if max_points is not None else todo


def _load_step_series(prefix: str) -> Tuple[List[float], List[float]]:
    from measurements.owd_analyze import REC_RX, load

    rows = load(prefix + "_bg.bin", REC_RX)
    if not rows:
        return [], []
    t0 = float(rows[0][1])
    owd_ms = [(float(r[2]) - float(r[1])) * 1000.0 for r in rows]
    t_rel = [float(r[1]) - t0 for r in rows]
    return owd_ms, t_rel


def measure(net: Any, point: Point) -> Dict[str, Any]:
    from measurements.owd_analyze import analyze

    h1, h2 = net.get("h1"), net.get("h2")
    cwd = os.getcwd()
    prefix = "%s/%s" % (RAW, point["pid"])
    duration = float(point["duration_s"])

    h1.cmd("pkill -f 'measurements.rho_gen' 2>/dev/null")
    h2.cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
    time.sleep(0.2)
    h2.cmd(
        "cd %s && %s recv --port %d --duration %g --out-prefix %s >/dev/null 2>&1 &"
        % (cwd, PB, PORT, duration + 6.0, prefix)
    )
    time.sleep(0.8)
    h1.cmd(
        "cd %s && %s --dst 10.0.0.2 --port %d --bw %g --mode %s "
        "--duration %g --seed %d --run-id %d --out-prefix %s "
        "--step-a %g --step-b %g --step-hold %g --step-cycles %d "
        ">/dev/null 2>&1"
        % (
            cwd,
            RG,
            PORT,
            BW,
            point["mode"],
            duration,
            point["seed"],
            point["idx"],
            prefix,
            point["rho_a"],
            point["rho_b"],
            point["hold_s"],
            point["n_cycles"],
        )
    )
    time.sleep(6.5)

    bg = analyze(prefix + "_bg.bin", prefix + "_bgtx.bin", warmup_s=0.0)
    owd_ms, t_rel = _load_step_series(prefix)
    est = estimate_from_cycles(
        owd_ms,
        t_rel,
        point["hold_s"],
        point["n_cycles"],
        point["binw_s"],
    )
    with open(prefix + "_tx.meta.json", "r", encoding="utf-8") as f:
        tx = json.load(f)
    with open(prefix + "_rx.meta.json", "r", encoding="utf-8") as f:
        rx = json.load(f)

    total_sent = max(tx["counts"]["n_bg_sent"] + tx["counts"]["n_probe_sent"], 1)
    return {
        **point,
        **est,
        "q_mean_ms": bg["owd_ms"]["mean"],
        "loss": bg["loss_rate"],
        "n_late_ratio": tx["counts"]["n_late"] / total_sent,
        "max_late_ms": tx["counts"]["max_late_ms"],
        "socket_drops": rx["socket_drops_delta"],
        "n_foreign": rx["n_foreign_packets"],
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run_live(args: argparse.Namespace) -> None:
    plan = build_plan()
    state = load_state(args.state)
    todo = select_todo(plan, state, args.max_points)
    print(
        "Step plan %d diem | da xong %d | phien nay %d diem (~%.1f gio)"
        % (
            len(plan),
            len(set(int(i) for i in state.get("done_idx", []))),
            len(todo),
            sum(float(p["duration_s"]) + 12.0 for p in todo) / 3600.0,
        )
    )
    if args.plan_only:
        for point in todo:
            print(
                "%04d %-7s %.3f->%.3f hold=%g cycles=%d seed=%d block=%s"
                % (
                    point["idx"],
                    point["mode"],
                    point["rho_a"],
                    point["rho_b"],
                    point["hold_s"],
                    point["n_cycles"],
                    point["seed"],
                    point["block"],
                )
            )
        return

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
    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        setup_return_qdisc(intf_toward(s2, "s1"), 3.0)
        setup_measure_qdisc(intf_toward(s1, "s2"), BW, Q)
        t0 = time.time()
        for k, point in enumerate(todo, 1):
            row = measure(net, point)
            state.setdefault("rows", []).append(row)
            state.setdefault("done_idx", []).append(point["idx"])
            save_state(state, args.state)
            eta = (time.time() - t0) / k * (len(todo) - k) / 3600.0
            print(
                "[%3d/%3d] %-7s %.3f->%.3f T_ab=%s T_ba=%s sym=%s (con %.1f h)"
                % (
                    k,
                    len(todo),
                    point["mode"],
                    point["rho_a"],
                    point["rho_b"],
                    _fmt(row["T_ab_s"]),
                    _fmt(row["T_ba_s"]),
                    _fmt(row["symmetry_ratio"]),
                    eta,
                )
            )
    finally:
        try:
            net.get("h1").cmd("pkill -f 'measurements.rho_gen' 2>/dev/null")
            net.get("h2").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
        except Exception:
            pass
        net.stop()
        save_state(state, args.state)


def _fmt(x: float) -> str:
    return "nan" if not math.isfinite(float(x)) else "%.4f" % float(x)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase T / T.5 step response")
    parser.add_argument("--state", default=STATE)
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    run_live(args)


if __name__ == "__main__":
    main()

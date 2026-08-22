#!/usr/bin/env python3
"""Measure routing AoI, utilization error, and du/dt.

Lesson 9.0c checks whether delta sync makes AoI content-dependent:

* static load should have low du/dt and potentially high AoI,
* step load should reset AoI around real changes,
* ramp load should keep changing utilization and force frequent patches.

Run this while Ditto, the collector/pusher, and the routing topology are up.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import time
from typing import Iterable, List, Tuple

from bridge.ditto_reader import make_session
from measurements.aoi_probe import KernelUtilMeter, read_ditto_link


def run_in_ns(pid: int, cmd: str, timeout: float = 20.0) -> str:
    """Run a shell command inside a Mininet host namespace."""
    proc = subprocess.run(
        ["mnexec", "-a", str(pid), "sh", "-lc", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def stop_iperf(pid: int | None) -> None:
    if pid is None:
        return
    # Match executable name only. ``pkill -f iperf`` can kill parent scripts
    # whose argv contains this source text.
    run_in_ns(pid, "pkill -x iperf 2>/dev/null || true")


def start_sink_if_requested(sink_pid: int | None) -> None:
    if sink_pid is None:
        return
    stop_iperf(sink_pid)
    run_in_ns(
        sink_pid,
        "iperf -s -u -p 5001 >/tmp/dt4n_aoi_iperf_server.log 2>&1 &",
    )
    time.sleep(0.3)


def start_load(load_pid: int, sink_ip: str, rate_mbps: float, duration_s: float) -> None:
    stop_iperf(load_pid)
    run_in_ns(
        load_pid,
        (
            "iperf -c %s -u -b %gM -p 5001 -t %d -l 1470 "
            ">/tmp/dt4n_aoi_iperf_client.log 2>&1 &"
        )
        % (sink_ip, float(rate_mbps), max(int(duration_s), 1)),
    )


def load_schedule(mode: str, bw_mbps: float, duration_s: float) -> List[Tuple[float, float]]:
    """Return ``[(relative_time_s, offered_mbps), ...]`` for one mode."""
    bw = float(bw_mbps)
    duration = float(duration_s)
    if mode == "static":
        return [(0.0, 0.5 * bw)]

    if mode == "step":
        sched = []
        t = 0.0
        use_high = True
        while t < duration:
            sched.append((t, (0.8 if use_high else 0.3) * bw))
            use_high = not use_high
            t += 5.0
        return sched or [(0.0, 0.5 * bw)]

    if mode == "ramp":
        sched = []
        t = 0.0
        while t < duration:
            phase = (t % 5.0) / 4.0
            frac = 0.3 + 0.5 * min(phase, 1.0)
            sched.append((t, frac * bw))
            t += 1.0
        return sched or [(0.0, 0.3 * bw)]

    raise ValueError("unknown mode: %s" % mode)


def _fmt(value, pattern="%.3f") -> str:
    if value is None:
        return "NA"
    return pattern % value


def run_mode(args, mode: str, session, writer: csv.DictWriter, out_file) -> None:
    """Run one controlled-load mode and append samples to ``writer``."""
    meter = KernelUtilMeter(args.ifname, args.bw)
    sched = load_schedule(mode, args.bw, args.duration)
    print("\n=== MODE %s | %d load points ===" % (mode.upper(), len(sched)))

    start_sink_if_requested(args.sink_pid)
    stop_iperf(args.load_pid)
    time.sleep(0.3)

    t_start = time.time()
    schedule_index = 0
    current_rate = sched[0][1]
    start_load(
        args.load_pid,
        args.sink_ip,
        current_rate,
        args.duration + args.iperf_grace,
    )

    prev_kernel_util = None
    prev_ts = None
    n_rows = 0

    try:
        while time.time() - t_start < args.duration:
            t_rel = time.time() - t_start

            if (
                schedule_index + 1 < len(sched)
                and t_rel >= sched[schedule_index + 1][0]
            ):
                schedule_index += 1
                current_rate = sched[schedule_index][1]
                remaining = max(args.duration - t_rel + args.iperf_grace, 1.0)
                start_load(args.load_pid, args.sink_ip, current_rate, remaining)

            uk1, tk1 = meter.sample()
            ud, t_source, t_read, aoi, ok = read_ditto_link(
                session,
                args.node_a,
                args.node_b,
            )
            uk2, tk2 = meter.sample()

            if uk1 is None or uk2 is None:
                time.sleep(args.interval)
                continue

            kernel_util = (uk1 + uk2) / 2.0
            read_gap = tk2 - tk1

            err = (ud - kernel_util) if ok and ud is not None else None
            du_dt = None
            if prev_kernel_util is not None and prev_ts is not None:
                dt = tk2 - prev_ts
                if dt > 0.0:
                    du_dt = abs(kernel_util - prev_kernel_util) / dt
            prev_kernel_util, prev_ts = kernel_util, tk2

            err_pred = (
                aoi * du_dt
                if aoi is not None and du_dt is not None
                else None
            )

            writer.writerow(
                {
                    "mode": mode,
                    "t_rel": round(t_rel, 3),
                    "offered_mbps": round(current_rate, 5),
                    "util_kernel": round(kernel_util, 5),
                    "util_ditto": round(ud, 5) if ud is not None else None,
                    "aoi_s": round(aoi, 4) if aoi is not None else None,
                    "error": round(err, 5) if err is not None else None,
                    "abs_error": round(abs(err), 5) if err is not None else None,
                    "du_dt": round(du_dt, 5) if du_dt is not None else None,
                    "error_pred": round(err_pred, 5) if err_pred is not None else None,
                    "read_gap_s": round(read_gap, 4),
                    "ditto_ok": int(bool(ok)),
                    "t_source": round(t_source, 3) if t_source is not None else None,
                    "t_read": round(t_read, 3),
                    "ts": round(tk2, 3),
                }
            )
            out_file.flush()
            n_rows += 1

            if n_rows % 20 == 0:
                print(
                    "  [%s] t=%5.1fs uk=%s ud=%s aoi=%s err=%s du_dt=%s"
                    % (
                        mode,
                        t_rel,
                        _fmt(kernel_util),
                        _fmt(ud),
                        _fmt(aoi),
                        _fmt(err, "%+.3f"),
                        _fmt(du_dt),
                    )
                )

            time.sleep(args.interval)
    finally:
        stop_iperf(args.load_pid)
        stop_iperf(args.sink_pid)

    print("  -> wrote %d samples" % n_rows)


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_args(argv: Iterable[str] | None = None):
    ap = argparse.ArgumentParser(description="Lesson 9.0c routing AoI calibration")
    ap.add_argument("--node-a", required=True, help="Link endpoint, e.g. sC")
    ap.add_argument("--node-b", required=True, help="Link endpoint, e.g. sE")
    ap.add_argument(
        "--ifname",
        required=True,
        help="TX interface in root namespace, e.g. sC-eth3",
    )
    ap.add_argument("--bw", type=float, required=True, help="Link bandwidth Mbps")
    ap.add_argument(
        "--load-pid",
        type=int,
        required=True,
        help="PID of the Mininet host that sends load, e.g. py hload_e.pid",
    )
    ap.add_argument(
        "--sink-pid",
        type=int,
        default=None,
        help="Optional PID of sink host; when set, starts iperf -s there",
    )
    ap.add_argument("--sink-ip", default="10.0.0.12")
    ap.add_argument("--mode", choices=["static", "step", "ramp", "all"], default="all")
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("--iperf-grace", type=float, default=5.0)
    ap.add_argument("--out", default="results/SUPERSEDED/calib/raw_aoi_routing.csv")
    return ap.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    modes = ["static", "step", "ramp"] if args.mode == "all" else [args.mode]
    fields = [
        "mode",
        "t_rel",
        "offered_mbps",
        "util_kernel",
        "util_ditto",
        "aoi_s",
        "error",
        "abs_error",
        "du_dt",
        "error_pred",
        "read_gap_s",
        "ditto_ok",
        "t_source",
        "t_read",
        "ts",
    ]

    ensure_parent(args.out)
    session = make_session()
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for mode in modes:
            run_mode(args, mode, session, writer, f)
            time.sleep(2.0)

    print("\nWrote -> %s" % args.out)


if __name__ == "__main__":
    main()

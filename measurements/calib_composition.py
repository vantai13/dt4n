#!/usr/bin/env python3
"""Run Lesson 9.0 measurement B: path-composition validation.

This compatibility entry point matches the command used in the Lesson notes:

    sudo -E env PYTHONPATH="$PWD" python3 measurements/calib_composition.py \
        --repeats 8 --duration 8 --out results/SUPERSEDED/calib/raw_composition.csv

It starts the routing Ryu controller in the ``sdn_net`` conda environment,
runs several path loads through the 8-node routing topology, writes raw CSV
rows, and stops the controller when done.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import time
from datetime import datetime
from typing import Iterable, List

from mininet.log import setLogLevel

from measurements.calib_topo_validate import run_once, write_rows
from mininet.topology_routing import (
    DEFAULT_ROUTING_PATH,
    ROUTING_PORT_MAP_PATH,
    ROUTING_SPEC_PATH,
    ROUTING_TABLE_PATH,
    write_routing_artifacts,
)


DEFAULT_RYU_MANAGER = "/home/ubuntu/miniforge3/envs/sdn_net/bin/ryu-manager"


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_csv_floats(text: str) -> List[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def wait_tcp(host: str, port: int, timeout_s: float) -> bool:
    deadline = time.monotonic() + float(timeout_s)
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, int(port)), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def resolve_ryu_manager(path: str) -> str:
    if path and os.path.exists(path):
        return path
    found = shutil.which("ryu-manager")
    if found:
        return found
    raise SystemExit(
        "Cannot find ryu-manager. Expected %s or a ryu-manager in PATH."
        % DEFAULT_RYU_MANAGER
    )


def start_controller(args):
    ryu_manager = resolve_ryu_manager(args.ryu_manager)
    ensure_parent(args.controller_log)
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": os.getcwd(),
            "DT4N_TOPOLOGY_SPEC": args.spec,
            "DT4N_ROUTING_TABLE": args.routes,
            "DT4N_PORT_MAP": args.port_map,
        }
    )
    log_f = open(args.controller_log, "a", encoding="utf-8")
    log_f.write("\n=== start %s ===\n" % datetime.now().isoformat(timespec="seconds"))
    log_f.flush()
    proc = subprocess.Popen(
        [
            ryu_manager,
            "mininet.controller_static",
            "--ofp-tcp-listen-port",
            str(args.controller_port),
        ],
        cwd=os.getcwd(),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
    )
    if not wait_tcp(args.controller_ip, args.controller_port, args.controller_timeout):
        proc.poll()
        if proc.returncode is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        log_f.close()
        raise SystemExit(
            "Ryu controller did not open %s:%s. See %s"
            % (args.controller_ip, args.controller_port, args.controller_log)
        )
    return proc, log_f


def stop_controller(proc, log_f) -> None:
    if proc is not None and proc.poll() is None:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    if log_f is not None:
        log_f.write("=== stop %s ===\n" % datetime.now().isoformat(timespec="seconds"))
        log_f.close()


def parse_args(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="Lesson 9.0 measurement B composition")
    p.add_argument("--out", default="results/SUPERSEDED/calib/raw_composition.csv")
    p.add_argument("--rates", default="1.5,3.2,4.4",
                   help="comma-separated offered Mbps values")
    p.add_argument("--repeats", type=int, default=8)
    p.add_argument("--duration", type=float, default=8.0)
    p.add_argument("--ping-count", type=int, default=10)
    p.add_argument("--ping-interval", type=float, default=0.2)
    p.add_argument("--spec", default=ROUTING_SPEC_PATH)
    p.add_argument("--routes", default=ROUTING_TABLE_PATH)
    p.add_argument("--port-map", default=ROUTING_PORT_MAP_PATH)
    p.add_argument("--controller-ip", default="127.0.0.1")
    p.add_argument("--controller-port", type=int, default=6653)
    p.add_argument("--controller-timeout", type=float, default=8.0)
    p.add_argument("--controller-log", default="logs/calib/B_ryu_controller.log")
    p.add_argument("--ryu-manager", default=DEFAULT_RYU_MANAGER)
    p.add_argument("--keep-controller", action="store_true")
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    setLogLevel("warning")
    rates = parse_csv_floats(args.rates)

    print("Writing routing artifacts: %s, %s" % (args.spec, args.routes), flush=True)
    write_routing_artifacts(spec_path=args.spec, route_path=args.routes)

    proc = log_f = None
    rows_total = 0
    try:
        print("Starting Ryu controller -> %s" % args.controller_log, flush=True)
        proc, log_f = start_controller(args)

        for rep in range(int(args.repeats)):
            for rate in rates:
                print(
                    "[B rep=%d/%d rate=%.3gMbps] start"
                    % (rep + 1, args.repeats, rate),
                    flush=True,
                )
                rows = run_once(
                    path=DEFAULT_ROUTING_PATH,
                    rate_mbps=rate,
                    duration_s=args.duration,
                    ping_count=args.ping_count,
                    ping_interval=args.ping_interval,
                )
                write_rows(args.out, rows, append=(rows_total > 0 or os.path.exists(args.out)))
                rows_total += len(rows)
                qsum = rows[0].get("path_queue_delay_sum_ms") if rows else None
                rtt = rows[0].get("path_rtt_avg_ms") if rows else None
                print(
                    "[B rep=%d/%d rate=%.3gMbps] wrote=%d qsum=%s rtt=%s"
                    % (
                        rep + 1,
                        args.repeats,
                        rate,
                        len(rows),
                        "%.3fms" % qsum if qsum is not None else "n/a",
                        "%.3fms" % rtt if rtt is not None else "n/a",
                    ),
                    flush=True,
                )
    finally:
        if args.keep_controller:
            print("Keeping Ryu controller alive (pid=%s)" % (proc.pid if proc else "n/a"))
            if log_f is not None:
                log_f.close()
        else:
            stop_controller(proc, log_f)

    print("Ghi %d dòng -> %s" % (rows_total, args.out), flush=True)


if __name__ == "__main__":
    main()

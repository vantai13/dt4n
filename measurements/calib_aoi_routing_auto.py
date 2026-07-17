#!/usr/bin/env python3
"""Run Lesson 9.0 measurement C end-to-end.

This automates the manual recipe:

1. start Ryu static controller in the ``sdn_net`` conda env,
2. start the routing Mininet topology,
3. bootstrap routing Things into Ditto,
4. start sync_agent,
5. run ``calib_aoi_routing`` against hload_e -> hsink_e.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import threading
import time
from types import SimpleNamespace
from typing import Iterable

from mininet.log import setLogLevel

from bridge.bootstrap import bootstrap_all, entities_from_spec
from bridge.ditto_reader import make_session
from bridge.sync_agent import run as sync_run
from measurements.calib_aoi_routing import run_mode
from measurements.calib_composition import (
    DEFAULT_RYU_MANAGER,
    start_controller,
    stop_controller,
)
from mininet.topology_routing import (
    DEFAULT_QUEUE_TARGET_MS,
    ROUTING_PORT_MAP_PATH,
    ROUTING_SPEC_PATH,
    ROUTING_TABLE_PATH,
    build_routing_net,
    start_routing_net,
    write_routing_artifacts,
)


FIELDS = [
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


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_args(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="Lesson 9.0 measurement C AoI auto-runner")
    p.add_argument("--out", default="results/calib/raw_aoi_routing.csv")
    p.add_argument("--mode", choices=["static", "step", "ramp", "all"], default="all")
    p.add_argument("--duration", type=float, default=60.0)
    p.add_argument("--interval", type=float, default=0.2)
    p.add_argument("--period", type=float, default=1.0,
                   help="sync_agent collection period")
    p.add_argument("--tol", type=float, default=0.5)
    p.add_argument("--reconcile-every", type=int, default=30)
    p.add_argument("--node-a", default="sC")
    p.add_argument("--node-b", default="sE")
    p.add_argument("--ifname", default="sC-eth3")
    p.add_argument("--bw", type=float, default=4.0)
    p.add_argument("--sink-ip", default="10.0.0.12")
    p.add_argument("--iperf-grace", type=float, default=5.0)
    p.add_argument("--spec", default=ROUTING_SPEC_PATH)
    p.add_argument("--routes", default=ROUTING_TABLE_PATH)
    p.add_argument("--port-map", default=ROUTING_PORT_MAP_PATH)
    p.add_argument("--policy", default="ditto/policy.json")
    p.add_argument("--queue", type=int, default=None)
    p.add_argument("--queue-target-ms", type=float, default=DEFAULT_QUEUE_TARGET_MS)
    p.add_argument("--controller-ip", default="127.0.0.1")
    p.add_argument("--controller-port", type=int, default=6653)
    p.add_argument("--controller-timeout", type=float, default=8.0)
    p.add_argument("--controller-log", default="logs/calib/C_ryu_controller.log")
    p.add_argument("--ryu-manager", default=DEFAULT_RYU_MANAGER)
    p.add_argument("--convergence-timeout", type=float, default=8.0)
    p.add_argument("--startup-wait", type=float, default=4.0)
    p.add_argument("--append", action="store_true")
    p.add_argument("--keep-controller", action="store_true")
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    setLogLevel("warning")
    ensure_parent(args.out)

    print("Writing routing artifacts: %s, %s" % (args.spec, args.routes), flush=True)
    write_routing_artifacts(
        spec_path=args.spec,
        route_path=args.routes,
        queue_pkts=args.queue,
        queue_target_ms=args.queue_target_ms,
    )

    with open(args.policy, encoding="utf-8") as f:
        policy = json.load(f)

    proc = log_f = None
    net = None
    sync_thread = None
    stop_event = threading.Event()
    net_lock = threading.RLock()

    try:
        print("Starting Ryu controller -> %s" % args.controller_log, flush=True)
        proc, log_f = start_controller(args)

        print("Starting routing Mininet topology", flush=True)
        net = build_routing_net(
            queue_pkts=args.queue,
            queue_target_ms=args.queue_target_ms,
            controller_ip=args.controller_ip,
            controller_port=args.controller_port,
        )
        start_routing_net(
            net,
            convergence_timeout=args.convergence_timeout,
            do_ping=True,
            port_map_path=args.port_map,
        )

        print("Bootstrap routing Things in Ditto", flush=True)
        bootstrap_all(entities_from_spec(args.spec), policy, mode="create")

        print("Starting sync_agent period=%.3fs" % args.period, flush=True)
        sync_thread = threading.Thread(
            target=sync_run,
            args=(net,),
            kwargs={
                "period": args.period,
                "tol": args.tol,
                "ping_every": 0,
                "reconcile_every": args.reconcile_every,
                "net_lock": net_lock,
                "stop_event": stop_event,
            },
            daemon=True,
        )
        sync_thread.start()
        time.sleep(max(args.startup_wait, args.period * 3.0))

        hload = net.get("hload_e")
        hsink = net.get("hsink_e")
        probe_args = SimpleNamespace(
            node_a=args.node_a,
            node_b=args.node_b,
            ifname=args.ifname,
            bw=args.bw,
            load_pid=hload.pid,
            sink_pid=hsink.pid,
            sink_ip=args.sink_ip,
            mode=args.mode,
            duration=args.duration,
            interval=args.interval,
            iperf_grace=args.iperf_grace,
            out=args.out,
        )
        modes = ["static", "step", "ramp"] if args.mode == "all" else [args.mode]
        session = make_session()

        mode = "a" if args.append and os.path.exists(args.out) else "w"
        with open(args.out, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if mode == "w" or os.path.getsize(args.out) == 0:
                writer.writeheader()
            for item in modes:
                run_mode(probe_args, item, session, writer, f)
                time.sleep(2.0)

        print("Ghi -> %s" % args.out, flush=True)
    finally:
        stop_event.set()
        if sync_thread is not None:
            sync_thread.join(timeout=5.0)
        if net is not None:
            try:
                net.stop()
            except Exception:
                pass
        if args.keep_controller:
            print("Keeping Ryu controller alive (pid=%s)" % (proc.pid if proc else "n/a"))
            if log_f is not None:
                log_f.close()
        else:
            stop_controller(proc, log_f)


if __name__ == "__main__":
    main()

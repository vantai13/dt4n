#!/usr/bin/env python3
"""Run the Lesson 9.0 routing topology with Ditto sync enabled.

The older ``mininet.run_sync`` entry point owns the Phase 1/2 triangle
topology. Lesson 9.0c needs the 8-node routing topology, so this runner keeps
that topology alive, bootstraps routing Things in Ditto, starts ``sync_agent``,
and then opens the Mininet CLI.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import threading
import time

from mininet.cli import CLI
from mininet.log import info, setLogLevel

from bridge.bootstrap import bootstrap_all, entities_from_spec
from bridge.differ import DEFAULT_TOL
from bridge.sync_agent import run as sync_run
from mininet.topology_routing import (
    DEFAULT_QUEUE_TARGET_MS,
    ROUTING_SPEC_PATH,
    ROUTING_TABLE_PATH,
    build_routing_net,
    start_routing_net,
    write_routing_artifacts,
)


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def configure_logging(path: str, append: bool = False) -> None:
    ensure_parent(path)
    logging.basicConfig(
        filename=path,
        filemode="a" if append else "w",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


class LockedCLI(CLI):
    """Serialize CLI commands with the collector's Mininet reads."""

    def __init__(self, net, net_lock, *args, **kwargs):
        self.net_lock = net_lock
        super().__init__(net, *args, **kwargs)

    def do_link(self, line):
        with self.net_lock:
            return super().do_link(line)

    def do_switch(self, line):
        with self.net_lock:
            return super().do_switch(line)


def parse_args():
    p = argparse.ArgumentParser(description="Run routing topology with Ditto sync")
    p.add_argument("--period", type=float, default=1.0)
    p.add_argument("--tol", type=float, default=DEFAULT_TOL)
    p.add_argument("--ping-every", type=int, default=0)
    p.add_argument("--reconcile-every", type=int, default=30)
    p.add_argument("--queue", type=int, default=None)
    p.add_argument("--queue-target-ms", type=float, default=DEFAULT_QUEUE_TARGET_MS)
    p.add_argument("--controller-ip", default="127.0.0.1")
    p.add_argument("--controller-port", type=int, default=6653)
    p.add_argument("--convergence-timeout", type=float, default=8.0)
    p.add_argument("--spec", default=ROUTING_SPEC_PATH)
    p.add_argument("--routes", default=ROUTING_TABLE_PATH)
    p.add_argument("--policy", default="ditto/policy.json")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--log-path", default="logs/run_sync_routing.log")
    p.add_argument("--append-log", action="store_true")
    p.add_argument("--no-cli", action="store_true",
                   help="start sync, wait --duration, then exit")
    p.add_argument("--duration", type=float, default=30.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_path, append=args.append_log)
    setLogLevel("info")

    if args.write_artifacts:
        write_routing_artifacts(
            spec_path=args.spec,
            route_path=args.routes,
            queue_pkts=args.queue,
            queue_target_ms=args.queue_target_ms,
        )
        info("*** Wrote routing artifacts: %s, %s\n" % (args.spec, args.routes))

    with open(args.policy, encoding="utf-8") as f:
        policy = json.load(f)

    net_lock = threading.RLock()
    stop_event = threading.Event()
    sync_thread = None
    net = build_routing_net(
        queue_pkts=args.queue,
        queue_target_ms=args.queue_target_ms,
        controller_ip=args.controller_ip,
        controller_port=args.controller_port,
    )

    try:
        start_routing_net(
            net,
            convergence_timeout=args.convergence_timeout,
            do_ping=True,
        )

        info("*** Bootstrap routing Things in Ditto\n")
        bootstrap_all(entities_from_spec(args.spec), policy, mode="create")

        info("*** Start routing Sync Agent\n")
        sync_thread = threading.Thread(
            target=sync_run,
            args=(net,),
            kwargs={
                "period": args.period,
                "tol": args.tol,
                "ping_every": args.ping_every,
                "reconcile_every": args.reconcile_every,
                "net_lock": net_lock,
                "stop_event": stop_event,
            },
            daemon=True,
        )
        sync_thread.start()
        time.sleep(max(2.0, args.period * 3.0))

        if args.no_cli:
            info("*** Sync running for %.1fs\n" % args.duration)
            time.sleep(max(float(args.duration), 0.0))
        else:
            info("*** CLI ready. Useful commands: py hload_e.pid ; py hsink_e.pid\n")
            LockedCLI(net, net_lock)
    finally:
        stop_event.set()
        if sync_thread is not None:
            sync_thread.join(timeout=5.0)
        net.stop()


if __name__ == "__main__":
    main()

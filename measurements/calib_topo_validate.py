#!/usr/bin/env python3
"""Validate link-model composition on the 8-node routing topology.

This script configures one static SRC->DST path in the Linux-router testbed,
runs UDP traffic from hsrc to hdst, samples each path edge, and writes raw CSV
rows. It is intentionally separate from fitting.
"""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import time
import uuid
from datetime import datetime, timezone

from mininet.log import setLogLevel

from mininet.calib_probe import ping_probe, sample_link
from mininet.topology_routing import (
    DEFAULT_ROUTING_PATH,
    build_routing_net,
    find_link,
    link_intf_for_node,
    path_edges,
    parse_path,
    start_routing_net,
)
from mininet.traffic import run_host_shell, stop_all_iperf


IPERF_PORT = 5102
CSV_FIELDS = [
    "run_id",
    "timestamp_utc",
    "path",
    "edge_src",
    "edge_dst",
    "bw_mbps",
    "delay_ms",
    "offered_mbps",
    "duration_s",
    "throughput_mbps",
    "utilization",
    "mean_backlog_bytes",
    "q_delay_ms",
    "drops_delta",
    "loss_rate",
    "path_forward_base_delay_ms",
    "path_queue_delay_sum_ms",
    "path_rtt_avg_ms",
    "path_packet_loss_pct",
    "rtt_minus_2base_minus_qsum_ms",
]


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_rows(path: str, rows, append: bool = False) -> None:
    ensure_parent(path)
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    mode = "a" if append else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not append or not exists:
            writer.writeheader()
        writer.writerows(rows)


def start_traffic(net, rate_mbps: float, duration_s: float) -> None:
    hsrc = net.get("hsrc")
    hdst = net.get("hdst")
    stop_all_iperf(hsrc, hdst)
    run_host_shell(
        hdst,
        "iperf -s -u -p %d > /tmp/dt4n_topo_validate_server.log 2>&1 &" % IPERF_PORT,
    )
    time.sleep(0.5)
    run_host_shell(
        hsrc,
        "iperf -c %s -u -b %gM -p %d -t %d "
        "> /tmp/dt4n_topo_validate_client.log 2>&1 &"
        % (shlex.quote(hdst.IP()), float(rate_mbps), IPERF_PORT, int(duration_s)),
    )


def run_once(path, rate_mbps: float, duration_s: float, ping_count: int, ping_interval: float):
    net = build_routing_net()
    try:
        start_routing_net(net, path=path, ping=True)
        ping_s = float(ping_count) * float(ping_interval) + 2.0
        traffic_s = duration_s * max(len(path_edges(path)), 1) + ping_s + 4.0
        start_traffic(net, rate_mbps=rate_mbps, duration_s=traffic_s)
        hsrc = net.get("hsrc")
        hdst = net.get("hdst")
        ping = ping_probe(
            hsrc,
            hdst.IP(),
            count=ping_count,
            interval_s=ping_interval,
        )
        rows = []
        run_id = uuid.uuid4().hex[:12]
        for src, dst in path_edges(path):
            link = find_link(net, src, dst)
            intf = link_intf_for_node(link, src)
            bw_mbps = float(getattr(link, "dt4n_bw", 0.0) or 0.0)
            delay_text = str(getattr(link, "dt4n_delay", "0ms")).replace("ms", "")
            delay_ms = float(delay_text)
            sample = sample_link(intf.node, intf.name, bw_mbps=bw_mbps, duration_s=duration_s)
            util = sample["throughput_mbps"] / bw_mbps if bw_mbps else 0.0
            rows.append(
                {
                    "run_id": run_id,
                    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "path": "->".join(path),
                    "edge_src": src,
                    "edge_dst": dst,
                    "bw_mbps": bw_mbps,
                    "delay_ms": delay_ms,
                    "offered_mbps": rate_mbps,
                    "duration_s": round(sample["duration_s"], 6),
                    "throughput_mbps": round(sample["throughput_mbps"], 6),
                    "utilization": round(util, 6),
                    "mean_backlog_bytes": round(sample["mean_backlog_bytes"], 3),
                    "q_delay_ms": round(sample["q_delay_ms"], 6),
                    "drops_delta": sample["drops_delta"],
                    "loss_rate": round(sample["loss_rate"], 8),
                    "path_forward_base_delay_ms": None,
                    "path_queue_delay_sum_ms": None,
                    "path_rtt_avg_ms": (
                        round(ping["rtt_avg_ms"], 6)
                        if ping.get("rtt_avg_ms") is not None else None
                    ),
                    "path_packet_loss_pct": (
                        round(ping["packet_loss_pct"], 6)
                        if ping.get("packet_loss_pct") is not None else None
                    ),
                    "rtt_minus_2base_minus_qsum_ms": None,
                }
            )

        base_delay = sum(float(row["delay_ms"]) for row in rows)
        queue_delay = sum(float(row["q_delay_ms"]) for row in rows)
        residual = None
        if ping.get("rtt_avg_ms") is not None:
            residual = float(ping["rtt_avg_ms"]) - 2.0 * base_delay - queue_delay
        for row in rows:
            row["path_forward_base_delay_ms"] = round(base_delay, 6)
            row["path_queue_delay_sum_ms"] = round(queue_delay, 6)
            row["rtt_minus_2base_minus_qsum_ms"] = (
                round(residual, 6) if residual is not None else None
            )
        return rows
    finally:
        try:
            stop_all_iperf(*net.hosts)
        finally:
            net.stop()


def parse_args():
    p = argparse.ArgumentParser(description="Lesson 9.0 topology composition validation")
    p.add_argument("--out", default="results/calib/raw_topo_validate.csv")
    p.add_argument("--path", default=",".join(DEFAULT_ROUTING_PATH))
    p.add_argument("--rate-mbps", type=float, default=2.0)
    p.add_argument("--duration", type=float, default=5.0)
    p.add_argument("--ping-count", type=int, default=10)
    p.add_argument("--ping-interval", type=float, default=0.2)
    p.add_argument("--append", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    setLogLevel("warning")
    path = parse_path(args.path)
    rows = run_once(
        path,
        rate_mbps=args.rate_mbps,
        duration_s=args.duration,
        ping_count=args.ping_count,
        ping_interval=args.ping_interval,
    )
    write_rows(args.out, rows, append=args.append)
    total_q = sum(float(row["q_delay_ms"]) for row in rows)
    rtt = rows[0].get("path_rtt_avg_ms") if rows else None
    print(
        "wrote %d link rows -> %s; path queueing delay %.3f ms; ping RTT %s ms"
        % (len(rows), args.out, total_q, "%.3f" % rtt if rtt is not None else "n/a")
    )


if __name__ == "__main__":
    main()

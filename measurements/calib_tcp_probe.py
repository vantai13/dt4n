#!/usr/bin/env python3
"""Probe TCP behavior on one shaped Mininet link.

This is Lesson 9.0 measurement D: it measures the measurement instrument. The
link calibration sweep uses UDP because UDP lets us control offered load; this
script shows how TCP behaves on the same shaped link so the UDP-vs-TCP
limitation has numbers attached to it.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
import uuid
from datetime import datetime, timezone

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import OVSBridge

from mininet.calib_probe import (
    _run_in_ns,
    backlog_to_delay_ms,
    parse_ping,
    read_bottleneck_qdisc,
    read_ifstats,
)
from measurements.calib_link_sweep import TwoNodeTopo, find_intf, parse_targets
from mininet.topology_routing import queue_pkts_for


CSV_FIELDS = [
    "run_id",
    "timestamp_utc",
    "rep",
    "cfg_bw_mbps",
    "cfg_delay_ms",
    "cfg_queue_pkts",
    "cfg_queue_target_ms",
    "t_rel_s",
    "window_s",
    "throughput_mbps",
    "rho_measured",
    "backlog_bytes",
    "q_delay_ms",
    "drops_delta",
    "tx_packets_delta",
    "loss_rate",
    "qdisc_kind",
    "qdisc_layers",
    "rtt_idle_ms",
    "rtt_ms",
    "bloat_ms",
    "ping_rtt_avg_ms",
    "ping_packet_loss_pct",
    "tcp_throughput_mbps",
    "rho_tcp",
]


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def append_rows(path: str, rows) -> None:
    ensure_parent(path)
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)
        f.flush()


def queue_configs(args):
    if args.queue is not None:
        return [(int(args.queue), "")]
    if args.queues:
        return [(int(item.strip()), "") for item in args.queues.split(",") if item.strip()]
    return [
        (queue_pkts_for(args.bw, target_ms), float(target_ms))
        for target_ms in parse_targets(args.queue_targets)
    ]


def stop_background(h1, h2) -> None:
    for host in (h1, h2):
        _run_in_ns(host.pid, "pkill -x iperf 2>/dev/null || true")
        _run_in_ns(host.pid, "pkill -x ping 2>/dev/null || true")


def run_ping(h1, dst_ip: str, count: int = 3, interval_s: float = 0.2):
    text = _run_in_ns(
        h1.pid,
        "ping -c %d -i %g -q %s" % (int(count), float(interval_s), dst_ip),
        timeout=max(5.0, int(count) * float(interval_s) + 3.0),
    )
    return parse_ping(text)


def parse_iperf_tcp_mbps(text: str):
    """Return the last TCP throughput reported by iperf v2, in Mbps."""
    matches = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s+([KMG])bits/sec", text or "")
    if not matches:
        return None
    value, unit = matches[-1]
    scale = {"K": 1e-3, "M": 1.0, "G": 1e3}[unit]
    return float(value) * scale


def start_tcp(h1, h2, duration_s: float) -> None:
    stop_background(h1, h2)
    _run_in_ns(h2.pid, "iperf -s -p 5001 >/tmp/dt4n_tcp_probe_server.log 2>&1 &")
    time.sleep(0.5)
    _run_in_ns(
        h1.pid,
        (
            "iperf -c %s -p 5001 -t %d -i 1 >/tmp/dt4n_tcp_probe_client.log 2>&1 &"
            % (h2.IP(), max(int(duration_s), 1))
        ),
    )


def sample_tcp_run(net, args, rep: int, queue_pkts: int, queue_target_ms):
    h1, h2 = net.get("h1"), net.get("h2")
    s1 = net.get("s1")
    intf = find_intf(s1, "s2")
    if intf is None:
        raise RuntimeError("cannot find s1 interface connected to s2")

    run_id = uuid.uuid4().hex[:12]
    idle_ping = run_ping(
        h1,
        h2.IP(),
        count=args.idle_ping_count,
        interval_s=args.ping_interval,
    )
    rtt_idle = idle_ping.get("rtt_avg_ms")
    print(
        "\n=== q=%s | idle RTT = %s ms ==="
        % (queue_pkts, "%.3f" % rtt_idle if rtt_idle is not None else "n/a")
    )

    total_duration = float(args.duration) + float(args.settle) + 2.0
    start_tcp(h1, h2, duration_s=total_duration)
    time.sleep(float(args.settle))

    prev_stats = read_ifstats(s1, intf)
    prev_qdisc = read_bottleneck_qdisc(s1, intf)
    prev_t = time.time()
    start_t = prev_t
    if prev_stats is None or prev_qdisc is None:
        raise RuntimeError("cannot read initial counters on %s" % intf)

    rows = []
    while time.time() - start_t < float(args.duration):
        time.sleep(float(args.interval))
        now = time.time()
        stats = read_ifstats(s1, intf)
        qdisc = read_bottleneck_qdisc(s1, intf)
        if stats is None or qdisc is None:
            continue

        dt = max(now - prev_t, 1e-6)
        tx_bytes = max(0, stats["tx_bytes"] - prev_stats["tx_bytes"])
        tx_pkts = max(0, stats["tx_packets"] - prev_stats["tx_packets"])
        drops = max(0, qdisc["drops"] - prev_qdisc["drops"])
        throughput = tx_bytes * 8.0 / dt / 1e6
        total_pkts = tx_pkts + drops
        ping = run_ping(
            h1,
            h2.IP(),
            count=args.loaded_ping_count,
            interval_s=args.ping_interval,
        )
        rtt = ping.get("rtt_avg_ms")
        bloat = (rtt - rtt_idle) if rtt is not None and rtt_idle is not None else None

        rows.append(
            {
                "run_id": run_id,
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "rep": rep,
                "cfg_bw_mbps": float(args.bw),
                "cfg_delay_ms": float(args.delay),
                "cfg_queue_pkts": int(queue_pkts),
                "cfg_queue_target_ms": queue_target_ms,
                "t_rel_s": round(now - start_t, 6),
                "window_s": round(dt, 6),
                "throughput_mbps": round(throughput, 6),
                "rho_measured": round(throughput / float(args.bw), 6),
                "backlog_bytes": int(qdisc["backlog_bytes"]),
                "q_delay_ms": round(
                    backlog_to_delay_ms(qdisc["backlog_bytes"], args.bw),
                    6,
                ),
                "drops_delta": int(drops),
                "tx_packets_delta": int(tx_pkts),
                "loss_rate": round(float(drops) / total_pkts, 8) if total_pkts else 0.0,
                "qdisc_kind": qdisc.get("kind", ""),
                "qdisc_layers": str(qdisc.get("all_layers", {})),
                "rtt_idle_ms": round(rtt_idle, 6) if rtt_idle is not None else None,
                "rtt_ms": round(rtt, 6) if rtt is not None else None,
                "bloat_ms": round(bloat, 6) if bloat is not None else None,
                "ping_rtt_avg_ms": round(rtt, 6) if rtt is not None else None,
                "ping_packet_loss_pct": (
                    round(ping["packet_loss_pct"], 6)
                    if ping.get("packet_loss_pct") is not None else None
                ),
                "tcp_throughput_mbps": None,
                "rho_tcp": None,
            }
        )

        latest = rows[-1]
        print(
            "  t=%4.1fs rho=%.3f backlog=%6dB qdel=%6.2fms rtt=%s bloat=%s"
            % (
                latest["t_rel_s"],
                latest["rho_measured"],
                latest["backlog_bytes"],
                latest["q_delay_ms"],
                "%.3f" % rtt if rtt is not None else "n/a",
                "%+.3f" % bloat if bloat is not None else "n/a",
            )
        )

        prev_stats = stats
        prev_qdisc = qdisc
        prev_t = now

    iperf_text = _run_in_ns(h1.pid, "cat /tmp/dt4n_tcp_probe_client.log 2>/dev/null")
    tcp_bw = parse_iperf_tcp_mbps(iperf_text)
    if tcp_bw is None and rows:
        tcp_bw = sum(float(row["throughput_mbps"]) for row in rows) / len(rows)
    for row in rows:
        row["tcp_throughput_mbps"] = round(tcp_bw, 6) if tcp_bw is not None else None
        row["rho_tcp"] = round(tcp_bw / float(args.bw), 6) if tcp_bw is not None else None

    stop_background(h1, h2)
    return rows


def parse_args():
    p = argparse.ArgumentParser(description="Lesson 9.0 TCP instrument probe")
    p.add_argument("--bw", type=float, default=4.0, help="Mbps")
    p.add_argument("--delay", type=float, default=2.0, help="one-way ms")
    p.add_argument("--queues", default="4,13",
                   help="comma list of explicit queue packet counts")
    p.add_argument("--queue", type=int, default=None,
                   help="single explicit queue packets; overrides --queues")
    p.add_argument(
        "--queue-targets",
        default="",
        help="optional comma list of full-queue delay targets in ms; used only when --queues is empty",
    )
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--duration", type=float, default=25.0)
    p.add_argument("--settle", type=float, default=3.0)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--ping-interval", type=float, default=0.2)
    p.add_argument("--idle-ping-count", type=int, default=10)
    p.add_argument("--loaded-ping-count", type=int, default=3)
    p.add_argument("--out", default="results/calib/raw_tcp_probe.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    total = 0
    for queue_pkts, queue_target_ms in queue_configs(args):
        topo = TwoNodeTopo(bw=args.bw, delay_ms=args.delay, queue_pkts=queue_pkts)
        net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None)
        net.start()
        try:
            net.pingAll()
            for rep in range(int(args.repeats)):
                rows = sample_tcp_run(net, args, rep, queue_pkts, queue_target_ms)
                append_rows(args.out, rows)
                total += len(rows)
                if rows:
                    rho_mean = sum(float(r["rho_measured"]) for r in rows) / len(rows)
                    q_max = max(float(r["q_delay_ms"]) for r in rows)
                    bloat_values = [
                        float(r["bloat_ms"]) for r in rows
                        if r.get("bloat_ms") is not None
                    ]
                    bloat_max = max(bloat_values) if bloat_values else None
                    rho_tcp = rows[0].get("rho_tcp")
                    print(
                        "[q=%s target=%s rep=%d/%d] samples=%d rho_mean=%.3f rho_tcp=%s qdelay_max=%.2fms bloat_max=%s"
                        % (
                            queue_pkts,
                            queue_target_ms,
                            rep + 1,
                            args.repeats,
                            len(rows),
                            rho_mean,
                            "%.3f" % rho_tcp if rho_tcp is not None else "n/a",
                            q_max,
                            "%.2fms" % bloat_max if bloat_max is not None else "n/a",
                        )
                    )
        finally:
            try:
                stop_background(net.get("h1"), net.get("h2"))
            finally:
                net.stop()

    print("Ghi %d dòng -> %s" % (total, args.out))


if __name__ == "__main__":
    main()

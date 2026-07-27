#!/usr/bin/env python3
"""Sweep delay(rho) and loss(rho) on one real shaped Mininet link.

This is the raw-data side of Lesson 9.0. It deliberately does not fit or
interpret the data; ``twin.link_model_fit`` does that later.
"""

from __future__ import annotations

import argparse
import csv
import os
import time

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.topo import Topo

from mininet.calib_probe import (
    _run_in_ns,
    backlog_to_delay_ms,
    read_bottleneck_qdisc,
    read_ifstats,
)
from mininet.topology_routing import QUEUE_SWEEP_TARGET_MS, queue_pkts_for


class TwoNodeTopo(Topo):
    """h1 -- s1 == shaped link == s2 -- h2."""

    def build(self, bw, delay_ms, queue_pkts):
        self.addHost("h1", ip="10.0.0.1/8")
        self.addHost("h2", ip="10.0.0.2/8")
        self.addSwitch("s1")
        self.addSwitch("s2")
        self.addLink("h1", "s1", bw=1000)
        self.addLink("h2", "s2", bw=1000)
        self.addLink(
            "s1",
            "s2",
            bw=float(bw),
            delay="%gms" % float(delay_ms),
            max_queue_size=int(queue_pkts),
            use_htb=True,
        )


def find_intf(node, peer_name):
    """Return the interface name on ``node`` connected to ``peer_name``."""
    for intf in node.intfList():
        if intf.link is None:
            continue
        other = intf.link.intf2 if intf.link.intf1 == intf else intf.link.intf1
        if other.node.name == peer_name:
            return intf.name
    return None


def measure_point(net, offered_mbps, bw_mbps, duration_s, settle_s=2.0):
    """Run UDP at a fixed offered rate and sample the shaped s1->s2 link."""
    h1, h2 = net.get("h1"), net.get("h2")
    s1 = net.get("s1")
    intf = find_intf(s1, "s2")
    if intf is None:
        raise RuntimeError("cannot find s1 interface connected to s2")

    # Match the executable name only. ``pkill -f iperf`` can kill an inline
    # Python parent whose argv contains the source text "iperf".
    _run_in_ns(h1.pid, "pkill -x iperf 2>/dev/null")
    _run_in_ns(h2.pid, "pkill -x iperf 2>/dev/null")
    time.sleep(0.3)

    _run_in_ns(h2.pid, "iperf -s -u -p 5001 >/tmp/dt4n_calib_isrv.log 2>&1 &")
    time.sleep(0.5)

    iperf_duration = int(float(duration_s) + float(settle_s) + 3)
    _run_in_ns(
        h1.pid,
        (
            "iperf -c 10.0.0.2 -u -b %gM -p 5001 -t %d -l 1470 "
            ">/tmp/dt4n_calib_icli.log 2>&1 &"
        )
        % (float(offered_mbps), iperf_duration),
    )

    time.sleep(float(settle_s))

    q0 = read_bottleneck_qdisc(s1, intf)
    if q0 is None:
        raise RuntimeError("no qdisc found on %s" % intf)
    a = read_ifstats(s1, intf)
    if a is None:
        raise RuntimeError("no /proc/net/dev counters for %s" % intf)
    t0 = time.time()

    backlogs = []
    n_polls = max(int(float(duration_s) / 0.05), 1)
    for _ in range(n_polls):
        q = read_bottleneck_qdisc(s1, intf)
        if q is not None:
            backlogs.append(q["backlog_bytes"])
        time.sleep(0.05)

    b = read_ifstats(s1, intf)
    if b is None:
        raise RuntimeError("no /proc/net/dev counters for %s after sample" % intf)
    t1 = time.time()
    q1 = read_bottleneck_qdisc(s1, intf)
    if q1 is None:
        raise RuntimeError("qdisc disappeared on %s" % intf)

    _run_in_ns(h1.pid, "pkill -x iperf 2>/dev/null")
    _run_in_ns(h2.pid, "pkill -x iperf 2>/dev/null")

    dt = max(t1 - t0, 1e-6)
    tx_bytes = max(0, b["tx_bytes"] - a["tx_bytes"])
    tx_pkts = max(0, b["tx_packets"] - a["tx_packets"])
    d_drops = max(0, q1["drops"] - q0["drops"])

    throughput = tx_bytes * 8.0 / dt / 1e6
    mean_backlog = sum(backlogs) / len(backlogs) if backlogs else 0.0
    total_pkts = tx_pkts + d_drops

    return {
        "offered_mbps": float(offered_mbps),
        "rho_offered": float(offered_mbps) / float(bw_mbps),
        "throughput_mbps": throughput,
        "rho_measured": throughput / float(bw_mbps),
        "q_delay_ms": backlog_to_delay_ms(mean_backlog, bw_mbps),
        "mean_backlog_bytes": mean_backlog,
        "max_backlog_bytes": max(backlogs) if backlogs else 0,
        "drops": d_drops,
        "tx_packets": tx_pkts,
        "loss_rate": (float(d_drops) / total_pkts) if total_pkts else 0.0,
        "qdisc_kind": q1["kind"],
        "qdisc_layers": str(q1.get("all_layers")),
        "duration_s": dt,
    }


def ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_targets(text):
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def queue_configs(args):
    if args.queue is not None:
        return [(int(args.queue), "")]
    return [
        (queue_pkts_for(args.bw, target_ms), float(target_ms))
        for target_ms in parse_targets(args.queue_targets)
    ]


def append_row(path, row):
    ensure_parent(path)
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new_file:
            writer.writeheader()
        writer.writerow(row)
        f.flush()


def parse_args():
    ap = argparse.ArgumentParser(description="Lesson 9.0 isolated-link sweep")
    ap.add_argument("--bw", type=float, required=True, help="Mbps")
    ap.add_argument("--delay", type=float, required=True, help="one-way ms")
    ap.add_argument("--queue", type=int, default=None,
                    help="explicit queue packets; disables --queue-targets")
    ap.add_argument(
        "--queue-targets",
        default=",".join("%g" % item for item in QUEUE_SWEEP_TARGET_MS),
        help="comma list of full-queue delay targets in ms",
    )
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--duration", type=float, default=10.0)
    ap.add_argument("--settle", type=float, default=2.0)
    ap.add_argument("--out", default="results/calib/raw_sweep_2node.csv")
    return ap.parse_args()


def main():
    args = parse_args()
    fracs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.1, 1.3]

    n_rows = 0
    for queue_pkts, queue_target_ms in queue_configs(args):
        topo = TwoNodeTopo(bw=args.bw, delay_ms=args.delay, queue_pkts=queue_pkts)
        net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None)
        net.start()
        try:
            net.pingAll()
            for rep in range(int(args.repeats)):
                for frac in fracs:
                    row = measure_point(
                        net,
                        offered_mbps=frac * args.bw,
                        bw_mbps=args.bw,
                        duration_s=args.duration,
                        settle_s=args.settle,
                    )
                    row.update(
                        {
                            "rep": rep,
                            "cfg_bw_mbps": args.bw,
                            "cfg_delay_ms": args.delay,
                            "cfg_queue_pkts": queue_pkts,
                            "cfg_queue_target_ms": queue_target_ms,
                            "ts": time.time(),
                        }
                    )
                    append_row(args.out, row)
                    n_rows += 1
                    print(
                        "[q=%s target=%s rep=%d/%d] offered=%.2f rho_m=%.3f qdel=%.2fms loss=%.3f qdisc=%s"
                        % (
                            queue_pkts,
                            queue_target_ms,
                            rep + 1,
                            args.repeats,
                            row["offered_mbps"],
                            row["rho_measured"],
                            row["q_delay_ms"],
                            row["loss_rate"],
                            row["qdisc_kind"],
                        )
                    )
        finally:
            _run_in_ns(net.get("h1").pid, "pkill -x iperf 2>/dev/null")
            _run_in_ns(net.get("h2").pid, "pkill -x iperf 2>/dev/null")
            net.stop()

    print("Ghi %d dòng -> %s" % (n_rows, args.out))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure qdisc backlog density on one real Mininet/TCLink queue.

This probe is intentionally different from the earlier calibration sweep: it
does not average backlog first. It samples the qdisc repeatedly and records the
packet-count distribution, so we can distinguish a real smooth delay law from a
0/1-packet quantization artifact below saturation.
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import time
import uuid
from datetime import datetime, timezone

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import OVSBridge

from measurements.calib_link_sweep import TwoNodeTopo, find_intf
from mininet.calib_probe import _run_in_ns, read_ifstats, read_qdisc_all


SUMMARY_FIELDS = [
    "run_id",
    "timestamp_utc",
    "cfg_bw_mbps",
    "cfg_delay_ms",
    "cfg_queue_pkts",
    "offered_mbps",
    "rho_offered",
    "throughput_mbps",
    "rho_measured",
    "loss_rate",
    "samples",
    "mean_netem_pkts",
    "max_netem_pkts",
    "p0",
    "p1",
    "p_full",
    "netem_distribution",
    "htb_distribution",
]

RAW_FIELDS = [
    "run_id",
    "timestamp_utc",
    "cfg_bw_mbps",
    "cfg_delay_ms",
    "cfg_queue_pkts",
    "offered_mbps",
    "rho_offered",
    "sample_idx",
    "t_rel_s",
    "netem_backlog_bytes",
    "netem_backlog_pkts",
    "htb_backlog_bytes",
    "htb_backlog_pkts",
]


BACKLOG_PKTS_RE = re.compile(r"\bbacklog\s+\S+\s+(\d+)p\b")


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_rates(text: str):
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def append_rows(path: str, rows, fields) -> None:
    if not rows:
        return
    ensure_parent(path)
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)
        f.flush()


def qdisc_backlog_pkts(qdisc) -> int:
    if not qdisc:
        return 0
    raw = qdisc.get("raw", "")
    match = BACKLOG_PKTS_RE.search(raw)
    if not match:
        return 0
    return int(match.group(1))


def compact_distribution(values, min_frac: float = 0.01) -> str:
    if not values:
        return ""
    counts = collections.Counter(int(v) for v in values)
    n = float(len(values))
    parts = []
    for pkts in sorted(counts):
        frac = counts[pkts] / n
        if frac >= min_frac or pkts == max(counts):
            parts.append("%dp:%.3f" % (pkts, frac))
    return " ".join(parts)


def stop_iperf(h1, h2) -> None:
    _run_in_ns(h1.pid, "pkill -x iperf 2>/dev/null || true")
    _run_in_ns(h2.pid, "pkill -x iperf 2>/dev/null || true")


def start_udp_load(h1, h2, offered_mbps: float, duration_s: float) -> None:
    stop_iperf(h1, h2)
    time.sleep(0.2)
    _run_in_ns(h2.pid, "iperf -s -u -p 5001 >/tmp/dt4n_qdisc_density_srv.log 2>&1 &")
    time.sleep(0.4)
    _run_in_ns(
        h1.pid,
        (
            "iperf -c %s -u -b %gM -p 5001 -t %d -l 1470 "
            ">/tmp/dt4n_qdisc_density_cli.log 2>&1 &"
        )
        % (h2.IP(), float(offered_mbps), max(int(duration_s), 1)),
    )


def sample_rate(net, args, offered_mbps: float):
    h1, h2 = net.get("h1"), net.get("h2")
    s1 = net.get("s1")
    intf = find_intf(s1, "s2")
    if intf is None:
        raise RuntimeError("cannot find s1 interface connected to s2")

    run_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total_runtime = float(args.settle) + int(args.samples) * float(args.interval) + 3.0
    start_udp_load(h1, h2, offered_mbps=offered_mbps, duration_s=total_runtime)
    time.sleep(float(args.settle))

    q0_layers = read_qdisc_all(s1, intf)
    stats0 = read_ifstats(s1, intf)
    if "netem" not in q0_layers:
        raise RuntimeError("no netem qdisc found on %s; layers=%s" % (intf, sorted(q0_layers)))
    if stats0 is None:
        raise RuntimeError("cannot read interface counters for %s" % intf)

    t0 = time.time()
    raw_rows = []
    netem_pkts = []
    htb_pkts = []
    for sample_idx in range(int(args.samples)):
        now = time.time()
        layers = read_qdisc_all(s1, intf)
        netem = layers.get("netem", {})
        htb = layers.get("htb", {})
        n_pkts = qdisc_backlog_pkts(netem)
        h_pkts = qdisc_backlog_pkts(htb)
        netem_pkts.append(n_pkts)
        htb_pkts.append(h_pkts)
        raw_rows.append(
            {
                "run_id": run_id,
                "timestamp_utc": timestamp,
                "cfg_bw_mbps": float(args.bw),
                "cfg_delay_ms": float(args.delay),
                "cfg_queue_pkts": int(args.queue),
                "offered_mbps": float(offered_mbps),
                "rho_offered": float(offered_mbps) / float(args.bw),
                "sample_idx": sample_idx,
                "t_rel_s": round(now - t0, 6),
                "netem_backlog_bytes": int(netem.get("backlog_bytes", 0)),
                "netem_backlog_pkts": int(n_pkts),
                "htb_backlog_bytes": int(htb.get("backlog_bytes", 0)),
                "htb_backlog_pkts": int(h_pkts),
            }
        )
        time.sleep(float(args.interval))

    stats1 = read_ifstats(s1, intf)
    q1_layers = read_qdisc_all(s1, intf)
    stop_iperf(h1, h2)

    dt = max(time.time() - t0, 1e-6)
    tx_bytes = 0
    tx_pkts = 0
    if stats1 is not None:
        tx_bytes = max(0, stats1["tx_bytes"] - stats0["tx_bytes"])
        tx_pkts = max(0, stats1["tx_packets"] - stats0["tx_packets"])
    q0 = q0_layers.get("netem", {})
    q1 = q1_layers.get("netem", {})
    drops = max(0, int(q1.get("drops", 0)) - int(q0.get("drops", 0)))
    total_pkts = tx_pkts + drops
    throughput = tx_bytes * 8.0 / dt / 1e6
    p0 = netem_pkts.count(0) / float(len(netem_pkts)) if netem_pkts else 0.0
    p1 = netem_pkts.count(1) / float(len(netem_pkts)) if netem_pkts else 0.0
    pfull = netem_pkts.count(int(args.queue)) / float(len(netem_pkts)) if netem_pkts else 0.0

    summary = {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "cfg_bw_mbps": float(args.bw),
        "cfg_delay_ms": float(args.delay),
        "cfg_queue_pkts": int(args.queue),
        "offered_mbps": float(offered_mbps),
        "rho_offered": float(offered_mbps) / float(args.bw),
        "throughput_mbps": round(throughput, 6),
        "rho_measured": round(throughput / float(args.bw), 6),
        "loss_rate": round(float(drops) / total_pkts, 8) if total_pkts else 0.0,
        "samples": int(len(netem_pkts)),
        "mean_netem_pkts": round(sum(netem_pkts) / float(len(netem_pkts)), 6)
        if netem_pkts else 0.0,
        "max_netem_pkts": max(netem_pkts) if netem_pkts else 0,
        "p0": round(p0, 6),
        "p1": round(p1, 6),
        "p_full": round(pfull, 6),
        "netem_distribution": compact_distribution(netem_pkts),
        "htb_distribution": compact_distribution(htb_pkts),
    }
    return summary, raw_rows


def parse_args():
    p = argparse.ArgumentParser(description="Measure qdisc backlog packet-density")
    p.add_argument("--bw", type=float, default=4.0, help="shaped link Mbps")
    p.add_argument("--delay", type=float, default=2.0, help="one-way netem delay ms")
    p.add_argument("--queue", type=int, default=13, help="netem queue packet limit")
    p.add_argument(
        "--rates",
        default="1.2,2.0,2.8,3.2,3.6,3.7,3.8,4.0,5.2",
        help="comma-separated offered Mbps values",
    )
    p.add_argument("--samples", type=int, default=200)
    p.add_argument("--interval", type=float, default=0.05)
    p.add_argument("--settle", type=float, default=3.0)
    p.add_argument("--out", default="results/SUPERSEDED/calib/qdisc_density.csv")
    p.add_argument("--raw-out", default="results/SUPERSEDED/calib/qdisc_density_raw.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    topo = TwoNodeTopo(bw=args.bw, delay_ms=args.delay, queue_pkts=args.queue)
    net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None)
    net.start()
    total_raw = 0
    try:
        net.pingAll()
        for offered_mbps in parse_rates(args.rates):
            summary, raw_rows = sample_rate(net, args, offered_mbps)
            append_rows(args.out, [summary], SUMMARY_FIELDS)
            append_rows(args.raw_out, raw_rows, RAW_FIELDS)
            total_raw += len(raw_rows)
            print(
                (
                    "rho_off=%.3f offered=%.2fM rho_m=%.3f loss=%.3f "
                    "mean=%.2fp max=%dp p0=%.2f p1=%.2f pfull=%.2f | %s"
                )
                % (
                    summary["rho_offered"],
                    summary["offered_mbps"],
                    summary["rho_measured"],
                    summary["loss_rate"],
                    summary["mean_netem_pkts"],
                    summary["max_netem_pkts"],
                    summary["p0"],
                    summary["p1"],
                    summary["p_full"],
                    summary["netem_distribution"],
                ),
                flush=True,
            )
    finally:
        try:
            stop_iperf(net.get("h1"), net.get("h2"))
        finally:
            net.stop()

    print("Wrote %s and %s (%d raw samples)" % (args.out, args.raw_out, total_raw))


if __name__ == "__main__":
    main()

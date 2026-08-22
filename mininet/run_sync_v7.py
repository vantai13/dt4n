#!/usr/bin/env python3
"""Run Phase 20 butterfly topology with flow-level traffic and rho logging."""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import os
import subprocess
import sys
import threading
import time
from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.topo import Topo

from mininet.tc_filter import install_tc_warning_filter
from mininet.traffic_v7 import (
    default_rho_targets,
    link_caps_from_topology,
    print_profile,
    start_all,
    stop_traffic_for_v7_hosts,
    traffic_profile,
)
from bridge.bootstrap import bootstrap_all, entities_from_spec
from bridge.differ import DEFAULT_TOL
from bridge import pusher as PUSH
from bridge.sync_agent import run as sync_run
from measurements.aoi_probe_v7 import run as aoi_probe_run
from twin import cost_v2 as C
from twin import topology_v7 as T7


install_tc_warning_filter()


SWITCHES = ("sSRC", "sA", "sB", "sC", "sD", "sDST")
SWITCH_DPIDS = {
    "sSRC": "1",
    "sA": "2",
    "sB": "3",
    "sC": "4",
    "sD": "5",
    "sDST": "6",
}
HOST_ATTACHMENTS = {
    "hsrc": "sSRC",
    "hA": "sA",
    "hB": "sB",
    "hC": "sC",
    "hD": "sD",
    "hdst": "sDST",
}
HOST_IPS = {
    "hsrc": "10.20.0.1",
    "hA": "10.20.0.2",
    "hB": "10.20.0.3",
    "hC": "10.20.0.4",
    "hD": "10.20.0.5",
    "hdst": "10.20.0.6",
}
HOST_MACS = {
    "hsrc": "00:00:00:00:20:01",
    "hA": "00:00:00:00:20:02",
    "hB": "00:00:00:00:20:03",
    "hC": "00:00:00:00:20:04",
    "hD": "00:00:00:00:20:05",
    "hdst": "00:00:00:00:20:06",
}
LINK_ENDPOINTS = {
    "uA": ("sSRC", "sA"),
    "uB": ("sSRC", "sB"),
    "ac": ("sA", "sC"),
    "ad": ("sA", "sD"),
    "bc": ("sB", "sC"),
    "bd": ("sB", "sD"),
    "vC": ("sC", "sDST"),
    "vD": ("sD", "sDST"),
}
ACCESS_BW_MBPS = 1000.0
ACCESS_DELAY_MS = 0.1
V7_SPEC = "ditto/topology_v7_spec.json"
TRAFFIC_RHO_CEILING = 0.995

MEASURED_CSV_FIELDS = (
    "sample_index",
    "timestamp_s",
    "link",
    "rho",
    "throughput_mbps",
    "tx_bytes_delta",
    "dt_s",
)


def feasible_traffic_rho_targets(rho_bar: float) -> Dict[str, float]:
    """Project model rho offsets into the physical generator domain.

    ``cost_v2.rho_vector`` intentionally permits overload up to 1.05, whereas
    the stationary flow generator requires every target to be below one.  Use
    the closest common-shift/clipping projection while preserving ``rho_bar``.
    """
    raw = C.rho_vector(float(rho_bar))
    target_sum = float(rho_bar) * len(T7.LINK_NAMES)
    low, high = -2.0, 2.0
    for _ in range(100):
        shift = (low + high) / 2.0
        total = sum(
            min(TRAFFIC_RHO_CEILING, max(1e-6, raw[name] + shift))
            for name in T7.LINK_NAMES
        )
        if total < target_sum:
            low = shift
        else:
            high = shift
    shift = (low + high) / 2.0
    return {
        name: min(TRAFFIC_RHO_CEILING, max(1e-6, raw[name] + shift))
        for name in T7.LINK_NAMES
    }
OFFERED_CSV_FIELDS = (
    "sample_index",
    "timestamp_s",
    "link",
    "rho",
    "rho_offered",
    "n_active",
    "rate_sum_bps",
    "dt_s",
    "source",
)


class Phase20V7Topo(Topo):
    """Mininet realization of ``twin.topology_v7``."""

    def build(self) -> None:
        for sw in SWITCHES:
            self.addSwitch(
                sw,
                protocols="OpenFlow13",
                dpid=SWITCH_DPIDS[sw],
            )

        for host, sw in HOST_ATTACHMENTS.items():
            self.addHost(
                host,
                ip="%s/24" % HOST_IPS[host],
                mac=HOST_MACS[host],
            )
            self.addLink(
                host,
                sw,
                bw=ACCESS_BW_MBPS,
                delay="%gms" % ACCESS_DELAY_MS,
                use_htb=True,
            )

        for link_name in T7.LINK_NAMES:
            a, b = LINK_ENDPOINTS[link_name]
            bw_mbps, delay_ms, queue_pkts = T7.LINKS[link_name]
            self.addLink(
                a,
                b,
                bw=float(bw_mbps),
                delay="%gms" % float(delay_ms),
                max_queue_size=int(queue_pkts),
                use_htb=True,
            )


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _other_intf(link, node_name: str):
    if link.intf1.node.name == node_name:
        return link.intf2
    if link.intf2.node.name == node_name:
        return link.intf1
    return None


def find_link(net, a: str, b: str):
    want = {a, b}
    for link in net.links:
        if {link.intf1.node.name, link.intf2.node.name} == want:
            return link
    raise KeyError("link %s-%s not found" % (a, b))


def link_intf_for_node(net, a: str, b: str, node_name: str):
    link = find_link(net, a, b)
    if link.intf1.node.name == node_name:
        return link.intf1
    if link.intf2.node.name == node_name:
        return link.intf2
    raise KeyError("%s is not on link %s-%s" % (node_name, a, b))


def _stamp_link_metadata(net) -> None:
    for link_name, (a, b) in LINK_ENDPOINTS.items():
        link = find_link(net, a, b)
        bw_mbps, delay_ms, queue_pkts = T7.LINKS[link_name]
        link.dt4n_name = link_name
        link.dt4n_bw = float(bw_mbps)
        link.dt4n_delay_ms = float(delay_ms)
        link.dt4n_queue_pkts = int(queue_pkts)


def _port_to_neighbor(net, switch: str, neighbor: str) -> int:
    link = find_link(net, switch, neighbor)
    intf = link_intf_for_node(net, switch, neighbor, switch)
    return int(intf.name.split("-eth", 1)[1])


def _graph() -> Dict[str, Dict[str, int]]:
    graph: Dict[str, Dict[str, int]] = defaultdict(dict)
    for host, sw in HOST_ATTACHMENTS.items():
        graph[host][sw] = 1
        graph[sw][host] = 1
    for a, b in LINK_ENDPOINTS.values():
        graph[a][b] = 1
        graph[b][a] = 1
    return graph


def _dijkstra_from(graph: Mapping[str, Mapping[str, int]], src: str):
    dist = {src: 0}
    prev = {}
    pq = [(0, src)]
    seen = set()

    while pq:
        cur_dist, node = heapq.heappop(pq)
        if node in seen:
            continue
        seen.add(node)
        for neighbor in sorted(graph.get(node, {})):
            new_dist = cur_dist + graph[node][neighbor]
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))
    return dist, prev


def next_hop_table() -> Dict[str, Dict[str, str]]:
    """Return switch -> destination host -> next hop."""
    graph = _graph()
    table = {sw: {} for sw in SWITCHES}
    for host in HOST_ATTACHMENTS:
        _dist, prev = _dijkstra_from(graph, host)
        for sw in SWITCHES:
            if sw in prev:
                table[sw][host] = prev[sw]
    return table


def _run_ovs(args: Sequence[str]) -> None:
    subprocess.run(
        ["ovs-ofctl", "-O", "OpenFlow13"] + list(args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def install_static_flows(net) -> Dict[str, Dict[str, str]]:
    """Install destination-MAC forwarding rules and no flood table miss."""
    table = next_hop_table()
    for sw in SWITCHES:
        _run_ovs(["del-flows", sw])
        for dst_host, next_hop in sorted(table[sw].items()):
            port = _port_to_neighbor(net, sw, next_hop)
            flow = "priority=100,dl_dst=%s,actions=output:%d" % (
                HOST_MACS[dst_host],
                port,
            )
            _run_ovs(["add-flow", sw, flow])
        _run_ovs(["add-flow", sw, "priority=0,actions=drop"])
    return table


def build_v7_net() -> Mininet:
    net = Mininet(
        topo=Phase20V7Topo(),
        link=TCLink,
        switch=OVSSwitch,
        controller=None,
        autoSetMacs=False,
        waitConnected=False,
    )
    _stamp_link_metadata(net)
    return net


def start_v7_net(net, do_ping: bool = False) -> None:
    net.start()
    net.staticArp()
    routes = install_static_flows(net)
    net.dt4n_v7_routes = routes
    if do_ping:
        loss = net.pingAll()
        info("*** pingAll packet loss = %.0f%%\n" % loss)


def _proc_net_dev() -> str:
    with open("/proc/net/dev", encoding="utf-8") as f:
        return f.read()


def _parse_proc_stats(text: str, ifnames: Iterable[str]) -> Dict[str, Dict[str, int]]:
    wanted = set(ifnames)
    out: Dict[str, Dict[str, int]] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        name = name.strip()
        if name not in wanted:
            continue
        cols = rest.split()
        if len(cols) <= 11:
            continue
        out[name] = {
            "rx_bytes": int(cols[0]),
            "rx_packets": int(cols[1]),
            "rx_drop": int(cols[3]),
            "tx_bytes": int(cols[8]),
            "tx_packets": int(cols[9]),
            "tx_drop": int(cols[11]),
        }
    return out


class RhoLogger(threading.Thread):
    """Sample upstream switch TX counters and write a long CSV trace."""

    def __init__(
        self,
        net,
        out_path: str,
        dt_s: float,
        duration_s: float,
        stop_event: Optional[threading.Event] = None,
    ) -> None:
        super().__init__(daemon=True)
        self.net = net
        self.out_path = out_path
        self.dt_s = float(dt_s)
        self.duration_s = float(duration_s)
        self.stop_event = stop_event or threading.Event()
        self.samples_written = 0
        self.error: Optional[BaseException] = None

    def link_interfaces(self) -> Dict[str, Tuple[str, float]]:
        out = {}
        for link_name, (upstream, downstream) in LINK_ENDPOINTS.items():
            intf = link_intf_for_node(self.net, upstream, downstream, upstream)
            bw_mbps = float(T7.LINKS[link_name][0])
            out[link_name] = (intf.name, bw_mbps)
        return out

    def run(self) -> None:
        try:
            self._run()
        except BaseException as exc:  # pragma: no cover - surfaced by runner.
            self.error = exc

    def _run(self) -> None:
        if self.dt_s <= 0:
            raise ValueError("dt_s must be positive")
        ensure_parent(self.out_path)
        link_ifaces = self.link_interfaces()
        ifnames = [item[0] for item in link_ifaces.values()]

        start = time.monotonic()
        prev_t = start
        prev = _parse_proc_stats(_proc_net_dev(), ifnames)
        missing = sorted(set(ifnames) - set(prev))
        if missing:
            raise RuntimeError("interfaces missing from /proc/net/dev: %s" % missing)

        with open(self.out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=MEASURED_CSV_FIELDS)
            writer.writeheader()
            deadline = start + self.duration_s
            sample_index = 0
            next_t = start

            while not self.stop_event.is_set():
                next_t += self.dt_s
                now = time.monotonic()
                if now >= deadline:
                    return
                self.stop_event.wait(max(0.0, next_t - now))
                if self.stop_event.is_set():
                    return

                now = time.monotonic()
                if now >= deadline:
                    return
                stats = _parse_proc_stats(_proc_net_dev(), ifnames)
                dt = max(now - prev_t, 1e-9)
                for link in T7.LINK_NAMES:
                    ifname, bw_mbps = link_ifaces[link]
                    cur = stats.get(ifname)
                    old = prev.get(ifname)
                    if cur is None or old is None:
                        continue
                    tx_delta = max(0, cur["tx_bytes"] - old["tx_bytes"])
                    throughput_mbps = tx_delta * 8.0 / dt / 1e6
                    writer.writerow(
                        {
                            "sample_index": sample_index,
                            "timestamp_s": "%.6f" % (now - start),
                            "link": link,
                            "rho": "%.8f" % (throughput_mbps / bw_mbps),
                            "throughput_mbps": "%.8f" % throughput_mbps,
                            "tx_bytes_delta": tx_delta,
                            "dt_s": "%.8f" % dt,
                        }
                    )
                f.flush()
                self.samples_written += 1
                sample_index += 1
                prev = stats
                prev_t = now


def write_metadata(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def _start_ditto_sync(net, args, net_lock):
    """Bootstrap topology_v7 Things and start the filtered sync loop."""
    info("*** Bootstrap topology_v7 Things in Ditto\n")
    with open(args.policy, encoding="utf-8") as handle:
        policy = json.load(handle)
    entities = entities_from_spec(V7_SPEC)
    bootstrap_all(entities, policy, mode="create")
    allowed_ids = {
        entity["thing_id"]
        for entity in entities
        if entity["kind"] in {"host", "switch", "link"}
    }
    if args.cycle_trace:
        ensure_parent(args.cycle_trace)
        open(args.cycle_trace, "w", encoding="utf-8").close()
    if args.push_trace:
        ensure_parent(args.push_trace)
        open(args.push_trace, "w", encoding="utf-8").close()
        PUSH.PUSH_TRACE_PATH = args.push_trace

    stop_event = threading.Event()
    thread = threading.Thread(
        target=sync_run,
        kwargs={
            "net": net,
            "period": args.sync_period,
            "tol": args.tol,
            "measurement_mode": args.measurement_mode,
            "reconcile_every": args.reconcile_every,
            "ping_every": 0,
            "net_lock": net_lock,
            "stop_event": stop_event,
            "cycle_trace_path": args.cycle_trace,
            "thing_ids": allowed_ids,
        },
        daemon=True,
        name="sync-agent-v7",
    )
    thread.start()
    return stop_event, thread


def _start_aoi_probe(args, stop_event):
    errors = []

    def _target():
        try:
            aoi_probe_run(
                duration_s=args.duration,
                interval_s=args.aoi_probe_interval,
                out_path=args.aoi_probe_out,
                meta={
                    "mode": args.measurement_mode,
                    "rho_bar": float(args.rho_bar),
                    "repeat": int(args.repeat),
                    "sync_period_s": float(args.sync_period),
                    "tol": 0.0 if args.measurement_mode == "clean" else float(args.tol),
                    "reconcile_every": 1 if args.measurement_mode == "clean" else int(args.reconcile_every),
                    "probe_interval_s": float(args.aoi_probe_interval),
                    "duration_s": float(args.duration),
                },
                stop_event=stop_event,
            )
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=_target, daemon=True, name="aoi-probe-v7")
    thread.start()
    return thread, errors


def wait_for_generator_summaries(gens, timeout_s: float = 8.0) -> None:
    deadline = time.monotonic() + float(timeout_s)
    paths = [gen.run_summary_path for gen in gens]
    while time.monotonic() < deadline:
        if all(os.path.exists(path) for path in paths):
            return
        time.sleep(0.1)


def aggregate_offered_logs(gens, out_path: str, dt_s: float) -> int:
    """Merge per-channel FlowEngine logs into the standard long rho CSV."""
    ensure_parent(out_path)
    rows_written = 0
    with open(out_path, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=OFFERED_CSV_FIELDS)
        writer.writeheader()
        for gen in gens:
            with open(gen.rho_log_path, newline="", encoding="utf-8") as in_f:
                for row in csv.DictReader(in_f):
                    rho = float(row["rho_offered"])
                    writer.writerow(
                        {
                            "sample_index": row["sample_index"],
                            "timestamp_s": row["timestamp_s"],
                            "link": gen.link,
                            "rho": "%.8f" % rho,
                            "rho_offered": "%.8f" % rho,
                            "n_active": row["n_active"],
                            "rate_sum_bps": row["rate_sum_bps"],
                            "dt_s": "%.8f" % float(dt_s),
                            "source": "offered",
                        }
                    )
                    rows_written += 1
    return rows_written


def _series_by_link(path: str) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {link: [] for link in T7.LINK_NAMES}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            link = row.get("link")
            if link in out:
                out[link].append(float(row["rho"]))
    return out


def _drop_warmup(xs: List[float], frac: float = 0.2) -> List[float]:
    start = int(len(xs) * float(frac))
    return xs[start:]


def _within_factor(value: float, target: float, factor: float) -> bool:
    if value <= 0.0 or target <= 0.0:
        return False
    return abs(math.log2(value / target)) <= math.log2(factor)


def quick_check_offered(path: str) -> bool:
    """Print and evaluate prereg C1-C3 using offered-load trace."""
    by_link = _series_by_link(path)
    low, high = T7.JUMPS
    core = {"ac", "ad", "bc", "bd"}
    ok = True

    print("\n=== quick check C1-C3 on rho_offered ===")
    for link in T7.LINK_NAMES:
        xs = _drop_warmup(by_link.get(link, []))
        if not xs:
            print("  %s: MISS no samples" % link)
            ok = False
            continue
        mean = sum(xs) / len(xs)
        p_below = sum(1 for x in xs if x < low) / len(xs)
        p_over_low = sum(1 for x in xs if x > low) / len(xs)
        p_above = sum(1 for x in xs if x > high) / len(xs)
        c1 = _within_factor(mean, T7.LOAD_MEAN[link], 1.05)
        if link in core:
            c23 = p_below >= 0.15 and p_above >= 0.15
            label = "core"
        else:
            c23 = p_over_low <= 0.05
            label = "edge"
        passed = c1 and c23
        ok = ok and passed
        print(
            "  %s %-4s mean=%.4f target=%.4f p<%.4f=%.3f p>%.4f=%.3f p>%.4f=%.3f %s"
            % (
                link,
                label,
                mean,
                T7.LOAD_MEAN[link],
                low,
                p_below,
                low,
                p_over_low,
                high,
                p_above,
                "OK" if passed else "MISS",
            )
        )
    return ok


def parse_args():
    p = argparse.ArgumentParser(
        description="Run Phase 20 v7 Mininet traffic and log rho(t)."
    )
    p.add_argument("--traffic", choices=["none", "v7"], default="v7")
    p.add_argument(
        "--log-rho",
        "--log-dt",
        dest="log_dt",
        type=float,
        default=0.010,
        help="offered rho sample period in seconds",
    )
    p.add_argument(
        "--measured-window",
        type=float,
        default=0.200,
        help="counter-based measured rho window in seconds",
    )
    p.add_argument("--duration", type=float, default=300.0)
    p.add_argument("--rho-bar", type=float, default=sum(T7.LOAD_MEAN.values()) / len(T7.LOAD_MEAN))
    p.add_argument("--out", default=None, help="legacy alias for --offered-out")
    p.add_argument("--offered-out", default="results/phase-20/rho_offered.csv")
    p.add_argument("--measured-out", default="results/phase-20/rho_measured.csv")
    p.add_argument("--meta-out", default="results/phase-20/rho_trace_meta.json")
    p.add_argument("--flow-log-dir", default="results/phase-20/flow_logs")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--sigma", "--core-sigma", dest="core_sigma", type=float, default=0.10)
    p.add_argument("--edge-sigma", type=float, default=0.03)
    p.add_argument("--kappa", type=float, default=2.5)
    p.add_argument("--size-min-kb", type=float, default=20.0)
    p.add_argument("--payload-bytes", type=int, default=1400)
    p.add_argument("--python-bin", default=sys.executable)
    p.add_argument("--ping", action="store_true")
    p.add_argument("--quick-check", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="print predicted profile only")
    p.add_argument("--ditto", action="store_true", help="enable topology_v7 Digital Twin sync")
    p.add_argument("--policy", default="ditto/policy.json")
    p.add_argument("--sync-period", type=float, default=0.5)
    p.add_argument("--tol", type=float, default=DEFAULT_TOL)
    p.add_argument("--reconcile-every", type=int, default=30)
    p.add_argument("--measurement-mode", choices=("clean", "prod"), default=None)
    p.add_argument("--cycle-trace", default=None)
    p.add_argument("--push-trace", default=None)
    p.add_argument("--aoi-probe-out", default=None)
    p.add_argument("--aoi-probe-interval", type=float, default=0.1)
    p.add_argument("--repeat", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    setLogLevel("info")
    offered_out = args.out or args.offered_out

    link_caps = link_caps_from_topology()
    rho_targets = feasible_traffic_rho_targets(float(args.rho_bar))
    profile = traffic_profile(
        link_caps=link_caps,
        rho_targets=rho_targets,
        sigma_target=args.core_sigma,
        edge_sigma_target=args.edge_sigma,
        kappa=args.kappa,
        size_min_kb=args.size_min_kb,
    )
    if args.dry_run:
        print_profile(profile)
        return

    stop_event = threading.Event()
    sync_stop_event = None
    sync_thread = None
    probe_stop_event = threading.Event()
    probe_thread = None
    probe_errors = []
    gens = []
    logger = None
    net = build_v7_net()
    net_lock = threading.RLock()

    try:
        info("*** Starting Phase 20 v7 topology\n")
        start_v7_net(net, do_ping=args.ping)

        if args.ditto:
            sync_stop_event, sync_thread = _start_ditto_sync(net, args, net_lock)
            # Let the first full sync replace bootstrap tSource=0 before probing.
            time.sleep(max(0.1, min(1.0, args.sync_period * 2.0)))
        elif args.aoi_probe_out:
            raise ValueError("--aoi-probe-out requires --ditto")

        if args.traffic == "v7":
            info("*** Starting flow-level v7 load\n")
            with net_lock:
                gens = list(start_all(
                    net,
                    link_caps=link_caps,
                    rho_targets=rho_targets,
                    seed=args.seed,
                    duration_s=args.duration,
                    sigma_target=args.core_sigma,
                    edge_sigma_target=args.edge_sigma,
                    kappa=args.kappa,
                    size_min_kb=args.size_min_kb,
                    python_bin=args.python_bin,
                    repo_root=os.getcwd(),
                    log_dt_s=args.log_dt,
                    log_dir=args.flow_log_dir,
                    payload_bytes=args.payload_bytes,
                    stop_event=stop_event,
                ))

        if args.aoi_probe_out:
            probe_thread, probe_errors = _start_aoi_probe(args, probe_stop_event)

        info(
            "*** Logging measured rho every %.3fs -> %s\n"
            % (args.measured_window, args.measured_out)
        )
        logger = RhoLogger(
            net=net,
            out_path=args.measured_out,
            dt_s=args.measured_window,
            duration_s=args.duration,
            stop_event=stop_event,
        )
        logger.start()
        logger.join()

        if logger.error is not None:
            raise RuntimeError("measured rho logger failed: %s" % logger.error)

        offered_rows = 0
        summaries = {}
        if gens:
            wait_for_generator_summaries(gens)
            info("*** Aggregating offered rho -> %s\n" % offered_out)
            offered_rows = aggregate_offered_logs(gens, offered_out, dt_s=args.log_dt)
            summaries = {gen.link: gen.summary() for gen in gens}

        quick_ok = None
        if args.quick_check and gens:
            quick_ok = quick_check_offered(offered_out)

        write_metadata(
            args.meta_out,
            {
                "duration_s": float(args.duration),
                "offered_dt_s": float(args.log_dt),
                "measured_window_s": float(args.measured_window),
                "seed": int(args.seed),
                "rho_bar": float(args.rho_bar),
                "core_sigma_target": float(args.core_sigma),
                "edge_sigma_target": float(args.edge_sigma),
                "kappa": float(args.kappa),
                "size_min_kb": float(args.size_min_kb),
                "payload_bytes": int(args.payload_bytes),
                "rho_targets": rho_targets,
                "profile": {link: cfg.as_dict() for link, cfg in profile.items()},
                "flow_engine": summaries,
                "offered_out": offered_out,
                "measured_out": args.measured_out,
                "offered_rows": int(offered_rows),
                "measured_samples_written": logger.samples_written if logger else 0,
                "quick_check_ok": quick_ok,
                "ditto": bool(args.ditto),
                "measurement_mode": args.measurement_mode,
                "sync_period_s": float(args.sync_period),
                "reconcile_every": int(args.reconcile_every),
                "cycle_trace": args.cycle_trace,
                "push_trace": args.push_trace,
                "aoi_probe_out": args.aoi_probe_out,
            },
        )
        if probe_thread is not None:
            probe_thread.join(timeout=max(5.0, args.aoi_probe_interval * 4.0))
            if probe_thread.is_alive():
                raise RuntimeError("AoI probe did not stop after duration")
            if probe_errors:
                raise RuntimeError("AoI probe failed: %s" % probe_errors[0])
        info("*** Done. Metadata -> %s\n" % args.meta_out)
        if quick_ok is False:
            raise SystemExit(2)
    finally:
        stop_event.set()
        probe_stop_event.set()
        if sync_stop_event is not None:
            sync_stop_event.set()
        if sync_thread is not None:
            sync_thread.join(timeout=5.0)
        try:
            stop_traffic_for_v7_hosts(net)
        finally:
            net.stop()


if __name__ == "__main__":
    main()

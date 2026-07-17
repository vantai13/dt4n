#!/usr/bin/env python3
"""Lesson 9.0 routing calibration topology for the existing OpenFlow stack.

The simulator topology uses semantic nodes ``SRC, A, B, C, D, E, F, DST``.
This Mininet realization maps:

* ``SRC`` and ``DST`` to hosts: ``hsrc`` and ``hdst``.
* ``A`` through ``F`` to OpenFlow switches: ``sA`` through ``sF``.

The important property is the same decision structure, especially the choice at
``C``/``D`` between the narrow-fast E path and the wider-slower F path.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Dict, Iterable, List, Sequence, Tuple

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSBridge, OVSSwitch, RemoteController
from mininet.topo import Topo

from mininet.gen_routes import generate as generate_routes
from mininet.tc_filter import install_tc_warning_filter
from mininet.topology import dump_port_map, remove_stale_port_map


install_tc_warning_filter()


PACKET_BYTES_FOR_QUEUE = 1500
DEFAULT_QUEUE_TARGET_MS = 15.0
QUEUE_SWEEP_TARGET_MS = [5.0, 15.0, 40.0]
ROUTING_SPEC_PATH = "ditto/topology_routing_spec.json"
ROUTING_TABLE_PATH = "ditto/routing_table_routing.json"
ROUTING_PORT_MAP_PATH = "ditto/port_map_routing.json"

SWITCH_DPIDS = {
    "sA": "1",
    "sB": "2",
    "sC": "3",
    "sD": "4",
    "sE": "5",
    "sF": "6",
}

# [endpoint A, endpoint B, one-way delay ms, bandwidth Mbps]
EDGES_V2 = [
    ("hsrc", "sA", 2.0, 8.0),
    ("hsrc", "sB", 2.5, 8.0),
    ("sA", "sC", 3.0, 6.0),
    ("sA", "sD", 4.0, 6.0),
    ("sB", "sC", 4.0, 6.0),
    ("sB", "sD", 3.0, 6.0),
    ("sC", "sE", 2.0, 4.0),
    ("sD", "sE", 2.0, 4.0),
    ("sE", "sF", 1.0, 8.0),
    ("sC", "sF", 6.0, 8.0),
    ("sD", "sF", 5.5, 8.0),
    ("sF", "hdst", 1.5, 8.0),
]

# Extra hosts create real background traffic on C<->E.
LOAD_INJECTORS = [
    ("hload_e", "sE", 1.0, 20.0),
    ("hsink_e", "sC", 1.0, 20.0),
]

ROUTING_PATH_VIA_E = ["hsrc", "sA", "sC", "sE", "sF", "hdst"]
ROUTING_PATH_VIA_F = ["hsrc", "sA", "sC", "sF", "hdst"]
DEFAULT_ROUTING_PATH = ROUTING_PATH_VIA_F


def _host_params(name: str, octet: int, role: str) -> Dict[str, str]:
    return {
        "name": name,
        "ip": "10.0.0.%d" % octet,
        "role": role,
    }


HOSTS = [
    _host_params("hsrc", 1, "client"),
    _host_params("hdst", 2, "server"),
    _host_params("hload_e", 11, "load"),
    _host_params("hsink_e", 12, "sink"),
]


class RoutingTopo8(Topo):
    """8-node decision topology using OVS switches and TCLink shaping."""

    def build(self, queue_pkts=None, queue_target_ms=DEFAULT_QUEUE_TARGET_MS):
        for name in ("sA", "sB", "sC", "sD", "sE", "sF"):
            self.addSwitch(
                name,
                protocols="OpenFlow13",
                dpid=SWITCH_DPIDS[name],
            )

        self.addHost("hsrc", ip="10.0.0.1/8", mac="00:00:00:00:00:01")
        self.addHost("hdst", ip="10.0.0.2/8", mac="00:00:00:00:00:02")
        self.addHost("hload_e", ip="10.0.0.11/8", mac="00:00:00:00:00:0b")
        self.addHost("hsink_e", ip="10.0.0.12/8", mac="00:00:00:00:00:0c")

        for a, b, delay_ms, bw_mbps in EDGES_V2 + LOAD_INJECTORS:
            link_queue_pkts = _queue_pkts_for_link(
                bw_mbps,
                queue_pkts=queue_pkts,
                queue_target_ms=queue_target_ms,
            )
            self.addLink(
                a,
                b,
                bw=float(bw_mbps),
                delay="%gms" % float(delay_ms),
                max_queue_size=int(link_queue_pkts),
                use_htb=True,
            )


class CalibLinkTopo(Topo):
    """Isolated h1--s1==s2--h2 link for quick manual probing."""

    def build(self, bw_mbps=6.0, delay_ms=3.0, queue_pkts=None):
        self.addHost("h1", ip="10.0.0.1/8")
        self.addHost("h2", ip="10.0.0.2/8")
        self.addSwitch("s1")
        self.addSwitch("s2")
        self.addLink("h1", "s1", bw=1000)
        self.addLink("h2", "s2", bw=1000)
        self.addLink(
            "s1",
            "s2",
            bw=float(bw_mbps),
            delay="%gms" % float(delay_ms),
            max_queue_size=int(queue_pkts),
            use_htb=True,
        )


def queue_pkts_for(bw_mbps, target_qdelay_ms, packet_bytes=PACKET_BYTES_FOR_QUEUE):
    """Return queue packets so a full queue drains in target_qdelay_ms.

    This sets the observable consequence first, then derives the tc parameter:
    full_queue_delay = queue_pkts * packet_bytes * 8 / bw.
    """
    packets = float(target_qdelay_ms) * float(bw_mbps) * 1e6
    packets /= 8.0 * float(packet_bytes) * 1000.0
    return max(int(packets), 4)


def _queue_pkts_for_link(bw_mbps, queue_pkts=None, queue_target_ms=DEFAULT_QUEUE_TARGET_MS):
    if queue_pkts is not None:
        return int(queue_pkts)
    return queue_pkts_for(bw_mbps, queue_target_ms)


def routing_spec(queue_pkts=None, queue_target_ms=DEFAULT_QUEUE_TARGET_MS) -> Dict[str, object]:
    """Return a spec JSON body compatible with controller_static/gen_routes."""
    links = []
    for a, b, delay_ms, bw_mbps in EDGES_V2 + LOAD_INJECTORS:
        link_queue_pkts = _queue_pkts_for_link(
            bw_mbps,
            queue_pkts=queue_pkts,
            queue_target_ms=queue_target_ms,
        )
        links.append(
            {
                "endpoints": [a, b],
                "bwMbps": float(bw_mbps),
                "delayMs": float(delay_ms),
                "queueTargetMs": float(queue_target_ms) if queue_pkts is None else None,
                "maxQueuePkts": int(link_queue_pkts),
            }
        )

    return {
        "_comment": (
            "Lesson 9.0 routing calibration topology. Use with "
            "DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json, "
            "DT4N_ROUTING_TABLE=ditto/routing_table_routing.json, and "
            "DT4N_PORT_MAP=ditto/port_map_routing.json."
        ),
        "hosts": HOSTS,
        "switches": [
            {"name": name, "dpid": dpid}
            for name, dpid in sorted(SWITCH_DPIDS.items(), key=lambda item: item[1])
        ],
        "links": links,
        "pathProbes": [["hsrc", "hdst"]],
    }


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_routing_artifacts(
    spec_path: str = ROUTING_SPEC_PATH,
    route_path: str = ROUTING_TABLE_PATH,
    queue_pkts=None,
    queue_target_ms=DEFAULT_QUEUE_TARGET_MS,
):
    """Write the 8-node spec and generated static route table."""
    spec = routing_spec(queue_pkts=queue_pkts, queue_target_ms=queue_target_ms)
    write_json(spec_path, spec)
    write_json(route_path, generate_routes(spec))
    return spec


def _stamp_link_metadata(net, queue_pkts=None, queue_target_ms=DEFAULT_QUEUE_TARGET_MS):
    meta = {
        frozenset((a, b)): (float(delay_ms), float(bw_mbps))
        for a, b, delay_ms, bw_mbps in EDGES_V2 + LOAD_INJECTORS
    }
    for link in net.links:
        a, b = link.intf1.node.name, link.intf2.node.name
        values = meta.get(frozenset((a, b)))
        if values is None:
            continue
        delay_ms, bw_mbps = values
        link.dt4n_delay_ms = delay_ms
        link.dt4n_delay = "%gms" % delay_ms
        link.dt4n_bw = bw_mbps
        link.dt4n_queue_target_ms = float(queue_target_ms)
        link.dt4n_queue_pkts = _queue_pkts_for_link(
            bw_mbps,
            queue_pkts=queue_pkts,
            queue_target_ms=queue_target_ms,
        )


def build_routing_net(
    queue_pkts=None,
    queue_target_ms=DEFAULT_QUEUE_TARGET_MS,
    controller_ip="127.0.0.1",
    controller_port=6653,
):
    """Build, but do not start, the 8-node OpenFlow routing net."""
    topo = RoutingTopo8(queue_pkts=queue_pkts, queue_target_ms=queue_target_ms)
    net = Mininet(
        topo=topo,
        link=TCLink,
        switch=OVSSwitch,
        controller=None,
        autoSetMacs=False,
        waitConnected=True,
    )
    net.addController(
        "c0",
        controller=RemoteController,
        ip=controller_ip,
        port=controller_port,
    )
    _stamp_link_metadata(net, queue_pkts=queue_pkts, queue_target_ms=queue_target_ms)
    return net


def build_calib_link_net(
    bw_mbps=6.0,
    delay_ms=3.0,
    queue_pkts=None,
    queue_target_ms=DEFAULT_QUEUE_TARGET_MS,
):
    """Build, but do not start, the isolated calibration link net."""
    link_queue_pkts = _queue_pkts_for_link(
        bw_mbps,
        queue_pkts=queue_pkts,
        queue_target_ms=queue_target_ms,
    )
    topo = CalibLinkTopo(bw_mbps=bw_mbps, delay_ms=delay_ms, queue_pkts=link_queue_pkts)
    net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None)
    for link in net.links:
        if {link.intf1.node.name, link.intf2.node.name} == {"s1", "s2"}:
            link.dt4n_delay_ms = float(delay_ms)
            link.dt4n_delay = "%gms" % float(delay_ms)
            link.dt4n_bw = float(bw_mbps)
            link.dt4n_queue_target_ms = float(queue_target_ms)
            link.dt4n_queue_pkts = int(link_queue_pkts)
    return net


def wait_routing_convergence(net, timeout=8.0, poll=0.3):
    """Wait until hsrc can ping hdst under controller_static routes."""
    deadline = time.monotonic() + float(timeout)
    hsrc = net.get("hsrc")
    hdst = net.get("hdst")
    while time.monotonic() < deadline:
        out = hsrc.cmd("ping -c 1 -W 1 %s" % hdst.IP())
        if "1 received" in out or "0% packet loss" in out:
            elapsed = float(timeout) - (deadline - time.monotonic())
            info("*** Routing topology converged after %.2fs\n" % elapsed)
            return True, elapsed
        time.sleep(float(poll))
    info("*** WARNING: routing topology did not converge after %.1fs\n" % float(timeout))
    return False, float(timeout)


def start_routing_net(
    net,
    path=None,
    convergence_timeout=8.0,
    do_ping=True,
    ping=None,
    dump_ports=True,
    port_map_path=ROUTING_PORT_MAP_PATH,
):
    """Start routing net, write port_map, and optionally verify hsrc->hdst."""
    # ``path`` is kept as a compatibility no-op for the earlier LinuxRouter
    # draft. The OpenFlow topology follows the generated controller routes.
    if ping is not None:
        do_ping = ping
    if dump_ports:
        remove_stale_port_map(port_map_path)
    net.start()
    if dump_ports:
        dump_port_map(net, port_map_path)

    ok, secs = wait_routing_convergence(net, timeout=convergence_timeout)
    net.dt4n_convergence_ok = ok
    net.dt4n_convergence_sec = secs

    if do_ping:
        info("*** pingAll kiểm tra thông mạng\n")
        loss_pct = net.pingAll()
        info("*** pingAll packet loss = %.0f%%\n" % loss_pct)
    return net


def find_link(net, a: str, b: str):
    """Return the Mininet link connecting node ``a`` and node ``b``."""
    want = {a, b}
    for link in net.links:
        if {link.intf1.node.name, link.intf2.node.name} == want:
            return link
    raise KeyError("link %s-%s not found" % (a, b))


def link_intf_for_node(link, node_name: str):
    """Return the interface for ``node_name`` on ``link``."""
    if link.intf1.node.name == node_name:
        return link.intf1
    if link.intf2.node.name == node_name:
        return link.intf2
    raise KeyError(
        "%s is not on link %s-%s"
        % (node_name, link.intf1.node.name, link.intf2.node.name)
    )


def path_edges(path: Sequence[str]) -> List[Tuple[str, str]]:
    return list(zip(path[:-1], path[1:]))


def parse_path(text: str) -> List[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def enumerate_paths(source="hsrc", destination="hdst") -> Iterable[List[str]]:
    """Enumerate simple directed SRC->DST paths from EDGES_V2."""
    adj: Dict[str, List[str]] = {}
    for src, dst, _delay, _bw in EDGES_V2:
        adj.setdefault(src, []).append(dst)

    stack = [(source, [source])]
    while stack:
        node, path = stack.pop()
        if node == destination:
            yield path
            continue
        for nxt in reversed(adj.get(node, [])):
            if nxt not in path:
                stack.append((nxt, path + [nxt]))


def run_cli(args):
    if args.write_artifacts:
        write_routing_artifacts(
            spec_path=args.spec_out,
            route_path=args.routes_out,
            queue_pkts=args.queue,
            queue_target_ms=args.queue_target_ms,
        )
        info("*** Wrote routing artifacts: %s, %s\n" % (args.spec_out, args.routes_out))
        if args.artifacts_only:
            return

    if args.mode == "link":
        net = build_calib_link_net(
            args.bw,
            args.delay,
            queue_pkts=args.queue,
            queue_target_ms=args.queue_target_ms,
        )
        try:
            net.start()
            if args.ping:
                net.pingAll()
            CLI(net)
        finally:
            net.stop()
        return

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
            do_ping=args.ping,
            port_map_path=args.port_map,
        )
        CLI(net)
    finally:
        net.stop()


def parse_args():
    p = argparse.ArgumentParser(description="Lesson 9.0 routing calibration topology")
    p.add_argument("--mode", choices=["routing", "link"], default="routing")
    p.add_argument("--queue", type=int, default=None,
                   help="explicit queue packets for every shaped link")
    p.add_argument("--queue-target-ms", type=float, default=DEFAULT_QUEUE_TARGET_MS,
                   help="derive per-link queue packets from this full-queue delay")
    p.add_argument("--bw", type=float, default=6.0, help="isolated link bw for --mode link")
    p.add_argument("--delay", type=float, default=3.0, help="isolated link delay for --mode link")
    p.add_argument("--controller-ip", default="127.0.0.1")
    p.add_argument("--controller-port", type=int, default=6653)
    p.add_argument("--convergence-timeout", type=float, default=8.0)
    p.add_argument("--port-map", default=os.environ.get("DT4N_PORT_MAP", ROUTING_PORT_MAP_PATH))
    p.add_argument("--spec-out", default=ROUTING_SPEC_PATH)
    p.add_argument("--routes-out", default=ROUTING_TABLE_PATH)
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--artifacts-only", action="store_true",
                   help="write spec/routes and exit without starting Mininet")
    p.add_argument("--ping", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    setLogLevel("info")
    run_cli(parse_args())

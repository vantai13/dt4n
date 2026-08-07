#!/usr/bin/env python3
"""Phase 20R.6 -- three measured links in tandem.

The measured links deliberately start without TCLink ``bw``/``delay`` params.
After ``net.start()``, ``configure_qdiscs`` installs the exact Phase L split
qdisc stack with ``setup_measure_qdisc`` and ``setup_return_qdisc``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from mininet.topo import Topo


TANDEM_LINKS: Tuple[Tuple[str, str, float, int, float], ...] = (
    ("L1", "uA", 8.0, 18, 1.107),
    ("L2", "ac", 6.0, 13, 1.712),
    ("L3", "ad", 4.0, 10, 2.436),
)
TANDEM_BY_IDX = {idx: row for idx, row in enumerate(TANDEM_LINKS, start=1)}
TANDEM_BY_NAME = {row[0]: row for row in TANDEM_LINKS}


class TandemTopo(Topo):
    """Linear path with independent load and per-link probe hosts."""

    def build(self) -> None:
        n = len(TANDEM_LINKS)
        for i in range(n + 1):
            self.addSwitch("s%d" % i, failMode="standalone")

        self.addHost("hsrc", ip="10.0.0.1/8")
        self.addHost("hdst", ip="10.0.0.2/8")
        self.addLink("hsrc", "s0")
        self.addLink("hdst", "s%d" % n)

        for i in range(1, n + 1):
            self.addHost("hload%d" % i, ip="10.0.%d.11/8" % i)
            self.addHost("hsink%d" % i, ip="10.0.%d.12/8" % i)
            self.addHost("hpa%d" % i, ip="10.0.%d.21/8" % i)
            self.addHost("hpb%d" % i, ip="10.0.%d.22/8" % i)

            self.addLink("hload%d" % i, "s%d" % (i - 1))
            self.addLink("hsink%d" % i, "s%d" % i)
            self.addLink("hpa%d" % i, "s%d" % (i - 1))
            self.addLink("hpb%d" % i, "s%d" % i)
            self.addLink("s%d" % (i - 1), "s%d" % i)


def _raise_if_hidden(info: Dict[str, Any]) -> Dict[str, Any]:
    if not info.get("ok"):
        raise AssertionError("hidden queue tren %s: %s" % (info.get("ifname"), info.get("raw")))
    return info


def _assert_host_no_hidden_queue(node: Any, ifname: str) -> Dict[str, Any]:
    raw = node.cmd("tc qdisc show dev %s 2>&1" % ifname).strip()
    ok = ("noqueue" in raw) or ("pfifo_fast" in raw) or ("qdisc mq" in raw)
    return _raise_if_hidden({"ifname": ifname, "raw": raw, "ok": ok})


def configure_qdiscs(net: Any, check_access: bool = True) -> Dict[str, Any]:
    """Install Phase L qdiscs and assert the measured stack on all links."""
    from mininet.topology_split_qdisc import (
        intf_toward,
        setup_and_verify_measure_qdisc,
        setup_return_qdisc,
    )

    measured: List[Dict[str, Any]] = []
    access: List[Dict[str, Any]] = []
    reinstall_log: List[Dict[str, Any]] = []
    for i, (name, t7_link, bw, q, base_ms) in enumerate(TANDEM_LINKS, start=1):
        a = net.get("s%d" % (i - 1))
        b = net.get("s%d" % i)
        fwd = intf_toward(a, b.name)
        rev = intf_toward(b, a.name)
        setup_return_qdisc(rev, base_ms)
        proof = setup_and_verify_measure_qdisc(fwd, bw, q, log_sink=reinstall_log)
        measured.append(
            {
                "idx": int(i),
                "link": name,
                "topology_v7_link": t7_link,
                "if_fwd": fwd,
                "if_rev": rev,
                "bw": float(bw),
                "q": int(q),
                "base_ms": float(base_ms),
                "measure_assert": proof,
            }
        )

    if check_access:
        for host in ("hsrc", "hdst") + tuple("hload%d" % i for i in range(1, 4)) + tuple("hsink%d" % i for i in range(1, 4)) + tuple("hpa%d" % i for i in range(1, 4)) + tuple("hpb%d" % i for i in range(1, 4)):
            node = net.get(host)
            for intf in node.intfList():
                if intf.name == "lo":
                    continue
                access.append(_assert_host_no_hidden_queue(node, intf.name))

    return {"measured": measured, "access": access, "qdisc_reinstall_log": reinstall_log}

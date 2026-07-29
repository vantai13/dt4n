#!/usr/bin/env python3
"""Phase L -- two-node topology with split qdiscs installed by hand.

Each qdisc has exactly one job:

* measured direction s1 -> s2: HTB shapes rate, bfifo owns the byte buffer.
* return direction s2 -> s1: netem owns propagation delay.

Do not use TCLink params here. Mininet's default HTB burst and netem-backed
``max_queue_size`` are the artifacts Lesson L.1 is designed to avoid.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional

from mininet.topo import Topo


FRAME_BYTES_1470 = 1512
DEFAULT_BURST_BYTES = 1600

H_ROOT = "1:"
H_CLASS = "1:10"
H_LEAF = "10:"


class SplitQdiscTopo(Topo):
    """h1 --- s1 == measured link == s2 --- h2.

    No TCLink, no bw/delay/max_queue_size params. The qdiscs are installed
    explicitly after net.start().
    """

    def build(self) -> None:
        self.addHost("h1", ip="10.0.0.1/8")
        self.addHost("h2", ip="10.0.0.2/8")
        self.addSwitch("s1")
        self.addSwitch("s2")

        self.addLink("h1", "s1")
        self.addLink("h2", "s2")
        self.addLink("s1", "s2")


def sh(cmd: str, timeout: float = 10.0) -> str:
    """Run a command in the root namespace, where switch interfaces live."""
    p = subprocess.run(
        ["sh", "-lc", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )
    return p.stdout or ""


def intf_toward(node: Any, peer_name: str) -> str:
    """Return the interface on ``node`` connected to ``peer_name``."""
    for intf in node.intfList():
        if intf.link is None:
            continue
        other = intf.link.intf2 if intf.link.intf1 == intf else intf.link.intf1
        if other.node.name == peer_name:
            return intf.name
    raise RuntimeError("khong tim thay interface tu %s toi %s" % (node.name, peer_name))


def queue_bytes(queue_pkts: int, frame_bytes: int = FRAME_BYTES_1470) -> int:
    """Convert the topology language (packets) to the bfifo language (bytes)."""
    return int(queue_pkts) * int(frame_bytes)


def queue_ceiling_ms(
    queue_pkts: int,
    bw_mbps: float,
    frame_bytes: int = FRAME_BYTES_1470,
) -> float:
    """Full-buffer delay in ms for the explicit byte buffer."""
    return queue_bytes(queue_pkts, frame_bytes) * 8.0 / (float(bw_mbps) * 1e6) * 1000.0


def setup_measure_qdisc(
    ifname: str,
    bw_mbps: float,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
) -> List[str]:
    """Measured direction: HTB for rate plus bfifo for byte buffer; no netem."""
    limit_b = queue_bytes(queue_pkts, frame_bytes)
    dev = shlex.quote(ifname)
    cmds = [
        "tc qdisc del dev %s root" % dev,
        "tc qdisc add dev %s root handle %s htb default 10" % (dev, H_ROOT),
        (
            "tc class add dev %s parent %s classid %s htb "
            "rate %gmbit burst %db cburst %db"
        )
        % (dev, H_ROOT, H_CLASS, float(bw_mbps), int(burst_bytes), int(burst_bytes)),
        "tc qdisc add dev %s parent %s handle %s bfifo limit %d"
        % (dev, H_CLASS, H_LEAF, limit_b),
    ]
    for i, cmd in enumerate(cmds):
        out = sh(cmd + (" 2>/dev/null" if i == 0 else ""))
        if i > 0 and out.strip():
            raise RuntimeError("lenh tc bao loi/canh bao:\n  %s\n  -> %s" % (cmd, out.strip()))
    return cmds


def change_measure_qdisc(
    ifname: str,
    bw_mbps: float,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
) -> List[str]:
    """Change rate/buffer without restarting Mininet."""
    limit_b = queue_bytes(queue_pkts, frame_bytes)
    dev = shlex.quote(ifname)
    cmds = [
        (
            "tc class change dev %s parent %s classid %s htb "
            "rate %gmbit burst %db cburst %db"
        )
        % (dev, H_ROOT, H_CLASS, float(bw_mbps), int(burst_bytes), int(burst_bytes)),
        "tc qdisc change dev %s parent %s handle %s bfifo limit %d"
        % (dev, H_CLASS, H_LEAF, limit_b),
    ]
    for cmd in cmds:
        out = sh(cmd)
        if out.strip():
            raise RuntimeError("lenh tc bao loi/canh bao:\n  %s\n  -> %s" % (cmd, out.strip()))
    return cmds


def setup_return_qdisc(ifname: str, delay_ms: float) -> List[str]:
    """Return direction: only netem propagation delay."""
    dev = shlex.quote(ifname)
    cmds = [
        "tc qdisc del dev %s root" % dev,
        "tc qdisc add dev %s root handle %s netem delay %gms" % (dev, H_ROOT, float(delay_ms)),
    ]
    for i, cmd in enumerate(cmds):
        out = sh(cmd + (" 2>/dev/null" if i == 0 else ""))
        if i > 0 and out.strip():
            raise RuntimeError("lenh tc bao loi/canh bao:\n  %s\n  -> %s" % (cmd, out.strip()))
    return cmds


def show_qdisc(ifname: str, stats: bool = True) -> str:
    return sh("tc %sqdisc show dev %s" % ("-s " if stats else "", shlex.quote(ifname)))


def show_class(ifname: str, stats: bool = True) -> str:
    return sh("tc %sclass show dev %s" % ("-s " if stats else "", shlex.quote(ifname)))


def _parse_bytes_token(text: str, key: str) -> Optional[int]:
    m = re.search(r"%s\s+(\d+)\s*(?:b|bytes?)\b" % re.escape(key), text)
    return int(m.group(1)) if m else None


def parse_qdisc_tree(text: str) -> List[Dict[str, Any]]:
    """Split ``tc qdisc show`` output into qdisc blocks.

    Stats such as ``Sent`` and ``backlog`` live on continuation lines, so parse
    those from the whole block rather than just the headline.
    """
    layers: List[Dict[str, Any]] = []
    for block in re.split(r"\n(?=qdisc\s)", text.strip()):
        if not block.startswith("qdisc"):
            continue
        head = block.splitlines()[0]
        m = re.match(r"qdisc\s+(\S+)\s+(\S+)\s*(.*)", head)
        if not m:
            continue
        kind, handle, rest = m.group(1), m.group(2), m.group(3)

        def from_head(pat: str, cast: Any = float) -> Optional[Any]:
            mm = re.search(pat, rest)
            return cast(mm.group(1)) if mm else None

        def from_block(pat: str, cast: Any = float) -> Optional[Any]:
            mm = re.search(pat, block)
            return cast(mm.group(1)) if mm else None

        limit_bytes = _parse_bytes_token(rest, "limit")
        layers.append(
            {
                "kind": kind,
                "handle": handle,
                "is_root": " root " in (" " + rest + " ") or rest.startswith("root"),
                "limit_bytes": limit_bytes,
                "limit_pkts": from_head(r"limit\s+(\d+)p\b", int),
                "delay_ms": from_head(r"delay\s+([0-9.]+)ms"),
                "backlog_bytes": _parse_bytes_token(block, "backlog"),
                "backlog_pkts": from_block(r"backlog\s+\d+\s*(?:b|bytes?)\s+(\d+)p\b", int),
                "sent_bytes": from_block(r"Sent\s+(\d+)\s+bytes", int),
                "dropped": from_block(r"dropped\s+(\d+)", int),
                "overlimits": from_block(r"overlimits\s+(\d+)", int),
                "raw": block,
            }
        )
    return layers


def read_sysfs_tx_bytes(ifname: str) -> Optional[int]:
    path = "/sys/class/net/%s/statistics/tx_bytes" % ifname
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="ascii") as f:
        return int(f.read().strip())


def find_layer(layers: List[Dict[str, Any]], kind: str) -> Optional[Dict[str, Any]]:
    for layer in layers:
        if layer["kind"] == kind:
            return layer
    return None


def assert_measure_qdisc(
    ifname: str,
    bw_mbps: float,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
) -> Dict[str, Any]:
    """Assert that the measured direction matches the Phase L design."""
    qtext = show_qdisc(ifname)
    ctext = show_class(ifname)
    layers = parse_qdisc_tree(qtext)
    kinds = [layer["kind"] for layer in layers]

    htb = find_layer(layers, "htb")
    assert htb is not None, "V-L1a FAIL: khong thay qdisc htb tren %s\n%s" % (ifname, qtext)
    assert htb["is_root"], "V-L1a FAIL: htb khong o root tren %s\n%s" % (ifname, qtext)

    assert "netem" not in kinds, (
        "V-L1b FAIL: CO netem tren chieu DO (%s). Day la loi E8 quay lai.\n%s"
        % (ifname, qtext)
    )

    bfifo = find_layer(layers, "bfifo")
    assert bfifo is not None, (
        "V-L1c FAIL: khong co bfifo. HTB co the dang dung leaf mac dinh "
        "pfifo limit=txqueuelen=1000 goi = 2016 ms dem o 6 Mbps.\n%s" % qtext
    )
    want_b = queue_bytes(queue_pkts, frame_bytes)
    assert bfifo["limit_bytes"] == want_b, (
        "V-L1c FAIL: bfifo limit = %s b, mong doi %d b (= %d goi x %d B)\n%s"
        % (bfifo["limit_bytes"], want_b, queue_pkts, frame_bytes, qtext)
    )

    assert re.search(r"burst\s+%d[bB]?\b" % int(burst_bytes), ctext) or re.search(
        r"burst\s+%db" % int(burst_bytes), ctext
    ), "V-L1d FAIL: khong thay burst %db trong class.\n%s" % (int(burst_bytes), ctext)

    return {
        "ifname": ifname,
        "qdisc_raw": qtext,
        "class_raw": ctext,
        "kinds": kinds,
        "bfifo_limit_bytes": bfifo["limit_bytes"],
        "ceiling_ms": queue_ceiling_ms(queue_pkts, bw_mbps, frame_bytes),
    }


def assert_no_hidden_queue(ifname: str) -> Dict[str, Any]:
    """Check host-switch links for hidden queueing."""
    qtext = show_qdisc(ifname, stats=False)
    ok = ("noqueue" in qtext) or ("pfifo_fast" in qtext)
    return {"ifname": ifname, "raw": qtext.strip(), "ok": ok}

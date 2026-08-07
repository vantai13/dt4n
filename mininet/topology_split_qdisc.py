#!/usr/bin/env python3
"""Phase L -- live two-node topology with split qdiscs.

Pure qdisc math/text lives in ``mininet.tc_spec``. This module is the live side:
Topo construction, subprocess calls, interface discovery, and assertions
against the running kernel.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from typing import Any, Dict, List, Optional

from mininet.tc_spec import (
    CONFIGS,
    DEFAULT_BURST_BYTES,
    FRAME_BYTES_1470,
    H_CLASS,
    H_LEAF,
    H_ROOT,
    capacity_pps,
    check_measure_text,
    fit_staircase,
    measure_cmds,
    parse_qdisc_tree,
    queue_bytes,
    queue_ceiling_ms,
    return_cmds,
    staircase_delays_ms,
)
from mininet.topo import Topo

MAX_QDISC_INSTALL_ATTEMPTS = 3
QDISC_SETTLE_S = 0.5


class SplitQdiscTopo(Topo):
    """h1 --- s1 == measured link == s2 --- h2."""

    def build(self) -> None:
        self.addHost("h1", ip="10.0.0.1/8")
        self.addHost("h2", ip="10.0.0.2/8")
        self.addSwitch("s1")
        self.addSwitch("s2")

        self.addLink("h1", "s1")
        self.addLink("h2", "s2")
        self.addLink("s1", "s2")


def sh(cmd: str, timeout: float = 10.0) -> str:
    """Run a command in the root namespace, where switch interfaces live.

    Use ``sh -c`` rather than a login shell: ``sh -lc`` reads profile scripts
    on every call and widens the race window between qdisc setup commands.
    """
    p = subprocess.run(
        ["sh", "-c", cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )
    return p.stdout or ""


def sh_tc_batch(cmds: List[str], timeout: float = 10.0) -> str:
    """Run several tc commands in one process with ``tc -batch``."""
    lines = []
    for cmd in cmds:
        c = cmd.strip()
        lines.append(c[3:].strip() if c.startswith("tc ") else c)
    p = subprocess.run(
        ["tc", "-batch", "-"],
        input="\n".join(lines) + "\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(
            "tc -batch that bai (rc=%d):\n%s\n---\n%s"
            % (p.returncode, "\n".join(lines), p.stdout or "")
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


def setup_measure_qdisc(
    ifname: str,
    bw_mbps: float,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
) -> List[str]:
    """Measured direction: HTB for rate plus bfifo for byte buffer; no netem."""
    dev = shlex.quote(ifname)
    del_cmd = "tc qdisc del dev %s root" % dev
    add_cmds = measure_cmds(
        dev,
        bw_mbps,
        queue_pkts,
        burst_bytes=burst_bytes,
        frame_bytes=frame_bytes,
    )
    sh(del_cmd + " 2>/dev/null")
    out = sh_tc_batch(add_cmds)
    if out.strip():
        raise RuntimeError("lenh tc bao loi/canh bao:\n  %s\n  -> %s" % ("\n  ".join(add_cmds), out.strip()))
    return [del_cmd] + add_cmds


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
    cmds = ["tc qdisc del dev %s root" % dev] + return_cmds(dev, delay_ms)
    for i, cmd in enumerate(cmds):
        out = sh(cmd + (" 2>/dev/null" if i == 0 else ""))
        if i > 0 and out.strip():
            raise RuntimeError("lenh tc bao loi/canh bao:\n  %s\n  -> %s" % (cmd, out.strip()))
    return cmds


def show_qdisc(ifname: str, stats: bool = True) -> str:
    return sh("tc %sqdisc show dev %s" % ("-s " if stats else "", shlex.quote(ifname)))


def show_class(ifname: str, stats: bool = True) -> str:
    return sh("tc %sclass show dev %s" % ("-s " if stats else "", shlex.quote(ifname)))


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


def read_direct_packets(ifname: str) -> int:
    """Read HTB ``direct_packets_stat`` for a measured interface."""
    layers = parse_qdisc_tree(show_qdisc(ifname))
    htb = find_layer(layers, "htb")
    if htb is None:
        raise RuntimeError("khong tim thay htb tren %s" % ifname)
    return int(htb.get("direct_packets_stat") or 0)


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
    errs = check_measure_text(
        qtext,
        ctext,
        queue_pkts=queue_pkts,
        burst_bytes=burst_bytes,
        frame_bytes=frame_bytes,
    )
    assert not errs, "V-L1 FAIL tren %s:\n%s\n\n%s" % (ifname, "\n".join(errs), qtext)

    layers = parse_qdisc_tree(qtext)
    htb = find_layer(layers, "htb")
    bfifo = find_layer(layers, "bfifo")
    assert htb is not None and bfifo is not None
    return {
        "ifname": ifname,
        "qdisc_raw": qtext,
        "class_raw": ctext,
        "kinds": [layer["kind"] for layer in layers],
        "direct_packets_stat": htb["direct_packets_stat"],
        "direct_qlen": htb["direct_qlen"],
        "bfifo_limit_bytes": bfifo["limit_bytes"],
        "ceiling_ms": queue_ceiling_ms(queue_pkts, bw_mbps, frame_bytes),
    }


def setup_and_verify_measure_qdisc(
    ifname: str,
    bw_mbps: float,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
    log_sink: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Install measured qdisc and retry only pre-run setup validation."""
    attempts: List[str] = []
    for attempt in range(1, MAX_QDISC_INSTALL_ATTEMPTS + 1):
        setup_measure_qdisc(ifname, bw_mbps, queue_pkts, burst_bytes=burst_bytes, frame_bytes=frame_bytes)
        time.sleep(QDISC_SETTLE_S)
        try:
            proof = assert_measure_qdisc(ifname, bw_mbps, queue_pkts, burst_bytes=burst_bytes, frame_bytes=frame_bytes)
            proof["install_attempts"] = int(attempt)
            proof["install_history"] = list(attempts)
            return proof
        except AssertionError as exc:
            lines = str(exc).splitlines()
            reason = lines[1] if len(lines) > 1 else str(exc)
            attempts.append(reason)
            if attempt < MAX_QDISC_INSTALL_ATTEMPTS:
                if log_sink is not None:
                    log_sink.append(
                        {
                            "event": "qdisc_reinstall",
                            "ifname": ifname,
                            "attempt": int(attempt + 1),
                            "reason": reason,
                        }
                    )
                continue
            raise RuntimeError(
                "V-L1 khong sach sau %d lan cai tren %s. Dieu tra truoc khi chay tiep.\nLich su:\n%s"
                % (MAX_QDISC_INSTALL_ATTEMPTS, ifname, "\n".join(attempts))
            ) from exc


def assert_no_hidden_queue(ifname: str) -> Dict[str, Any]:
    """Check host-switch links for hidden queueing."""
    qtext = show_qdisc(ifname, stats=False)
    ok = ("noqueue" in qtext) or ("pfifo_fast" in qtext)
    return {"ifname": ifname, "raw": qtext.strip(), "ok": ok}

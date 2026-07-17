#!/usr/bin/env python3
"""Kernel-backed probes for Mininet calibration runs.

The functions in this module deliberately read Linux counters instead of using
the simulator's queueing formulas. They are the measurement side of Lesson 9.0:

* ``tc -s qdisc`` gives real qdisc backlog and drops.
* ``/proc/net/dev`` gives real RX/TX byte and packet counters.
* backlog bytes are converted to queueing delay by serialization time.

The probe uses ``mnexec`` when a Mininet node PID is available so it does not
compete for the node's interactive shell.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import time
from typing import Any, Dict, Optional


def _run_in_ns(pid: Optional[int], cmd: str, timeout: float = 5) -> str:
    """Run ``cmd`` in a Mininet node namespace when ``pid`` is available."""
    argv = ["sh", "-lc", cmd]
    if pid:
        argv = ["mnexec", "-a", str(pid)] + argv

    try:
        p = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.stdout or ""
    except subprocess.TimeoutExpired as exc:
        out = exc.output or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        return out
    except OSError:
        return ""


def _run_on_node(node: Any, cmd: str, timeout: float = 5) -> str:
    """Run a shell command for a Mininet host/switch-like object."""
    pid = getattr(node, "pid", None)
    out = _run_in_ns(pid, cmd, timeout=timeout)
    if out:
        return out

    # Switch interfaces usually live in the root namespace. Mininet switch
    # objects still expose cmd(), so keep that as a fallback for portability.
    try:
        return node.cmd(cmd)
    except Exception:
        pass

    return _run_in_ns(None, cmd, timeout=timeout)


def _parse_size_bytes(text: str) -> int:
    """Parse tc size strings such as ``4500b``, ``12Kb`` or ``1M``."""
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)([KMG]?)(?:[bB])?\s*$", text)
    if not m:
        return 0
    value = float(m.group(1))
    unit = m.group(2)
    mult = {"": 1, "K": 1000, "M": 1000**2, "G": 1000**3}[unit]
    return int(value * mult)


def parse_qdisc(text: str) -> Dict[str, Any]:
    """Parse the fields Lesson 9.0 needs from ``tc -s qdisc`` output."""
    backlog = 0
    m = re.search(r"\bbacklog\s+([0-9]+(?:\.[0-9]+)?[KMG]?[bB]?)", text)
    if m:
        backlog = _parse_size_bytes(m.group(1))

    drops = 0
    m = re.search(r"\bdropped\s+(\d+)", text)
    if m:
        drops = int(m.group(1))

    overlimits = 0
    m = re.search(r"\boverlimits\s+(\d+)", text)
    if m:
        overlimits = int(m.group(1))

    sent_bytes = 0
    m = re.search(r"\bSent\s+(\d+)\s+bytes", text)
    if m:
        sent_bytes = int(m.group(1))

    return {
        "backlog_bytes": backlog,
        "drops": drops,
        "overlimits": overlimits,
        "sent_bytes": sent_bytes,
        "raw": text,
    }


def read_qdisc(node: Any, ifname: str) -> Dict[str, Any]:
    """Read qdisc backlog/drop counters from ``ifname``."""
    out = _run_on_node(node, "tc -s qdisc show dev %s" % shlex.quote(ifname))
    return parse_qdisc(out)


def read_qdisc_all(node: Any, ifname: str) -> Dict[str, Dict[str, Any]]:
    """Read all qdisc layers from an interface.

    Mininet ``TCLink`` normally creates a stack: HTB for shaping and netem for
    fixed delay/loss. The congestion queue forms at the shaping layer, so
    callers must not blindly read the first backlog line from ``tc`` output.
    """
    out = _run_on_node(node, "tc -s qdisc show dev %s" % shlex.quote(ifname))
    blocks = re.split(r"\n(?=qdisc\s)", out.strip())
    result: Dict[str, Dict[str, Any]] = {}

    for block in blocks:
        m = re.match(r"qdisc\s+(\S+)\s+(\S+)", block)
        if not m:
            continue
        kind, handle = m.group(1), m.group(2)
        parsed = parse_qdisc(block)
        parsed.update({"kind": kind, "handle": handle})
        result[kind] = parsed

    return result


def read_bottleneck_qdisc(node: Any, ifname: str) -> Optional[Dict[str, Any]]:
    """Return the qdisc layer where bottleneck queueing should be measured."""
    layers = read_qdisc_all(node, ifname)
    for kind in ("htb", "tbf", "netem"):
        if kind in layers:
            qdisc = dict(layers[kind])
            qdisc["all_layers"] = {
                name: item.get("backlog_bytes", 0)
                for name, item in layers.items()
            }
            return qdisc
    return None


def backlog_to_delay_ms(backlog_bytes: float, bw_mbps: float) -> float:
    """Convert backlog bytes to queueing delay by link serialization time."""
    if bw_mbps <= 0:
        return 0.0
    return (float(backlog_bytes) * 8.0) / (float(bw_mbps) * 1e6) * 1000.0


def parse_proc_net_dev(text: str, ifname: str) -> Optional[Dict[str, int]]:
    """Return full interface counters from ``/proc/net/dev`` text."""
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        if name.strip() != ifname:
            continue
        cols = rest.split()
        if len(cols) <= 11:
            return None
        try:
            return {
                "rx_bytes": int(cols[0]),
                "rx_packets": int(cols[1]),
                "rx_drop": int(cols[3]),
                "tx_bytes": int(cols[8]),
                "tx_packets": int(cols[9]),
                "tx_drop": int(cols[11]),
            }
        except (ValueError, IndexError):
            return None
    return None


def read_ifstats(node: Any, ifname: str) -> Optional[Dict[str, int]]:
    """Read byte/packet/drop counters for ``ifname``."""
    out = _run_on_node(node, "cat /proc/net/dev")
    return parse_proc_net_dev(out, ifname)


def sample_link(node: Any, ifname: str, bw_mbps: float, duration_s: float = 1.0) -> Dict[str, Any]:
    """Sample throughput, qdisc backlog and qdisc drops over one window."""
    start_stats = read_ifstats(node, ifname)
    if start_stats is None:
        raise RuntimeError("interface %s not found in /proc/net/dev" % ifname)

    q_start = read_bottleneck_qdisc(node, ifname) or read_qdisc(node, ifname)
    t0 = time.time()

    backlogs = []
    n_polls = max(int(float(duration_s) / 0.05), 1)
    sleep_s = max(float(duration_s) / n_polls, 0.001)
    for _ in range(n_polls):
        q = read_bottleneck_qdisc(node, ifname) or read_qdisc(node, ifname)
        backlogs.append(q["backlog_bytes"])
        time.sleep(sleep_s)

    end_stats = read_ifstats(node, ifname)
    if end_stats is None:
        raise RuntimeError("interface %s disappeared from /proc/net/dev" % ifname)
    t1 = time.time()
    q_end = read_bottleneck_qdisc(node, ifname) or read_qdisc(node, ifname)

    dt = max(t1 - t0, 1e-6)
    tx_bytes = max(0, end_stats["tx_bytes"] - start_stats["tx_bytes"])
    tx_pkts = max(0, end_stats["tx_packets"] - start_stats["tx_packets"])
    drops = max(0, q_end["drops"] - q_start["drops"])

    mean_backlog = sum(backlogs) / len(backlogs) if backlogs else 0.0
    offered_pkts = tx_pkts + drops

    return {
        "throughput_mbps": tx_bytes * 8.0 / dt / 1e6,
        "mean_backlog_bytes": mean_backlog,
        "max_backlog_bytes": max(backlogs) if backlogs else 0,
        "q_delay_ms": backlog_to_delay_ms(mean_backlog, bw_mbps),
        "tx_packets": tx_pkts,
        "drops_delta": drops,
        "loss_rate": (float(drops) / offered_pkts) if offered_pkts else 0.0,
        "duration_s": dt,
        "qdisc_kind": q_end.get("kind", ""),
        "qdisc_layers": q_end.get("all_layers", {}),
        "qdisc_start": q_start,
        "qdisc_end": q_end,
    }


def parse_ping(text: str) -> Dict[str, Optional[float]]:
    """Parse average RTT and loss percentage from ping output."""
    result: Dict[str, Optional[float]] = {"rtt_avg_ms": None, "packet_loss_pct": None}
    for line in text.splitlines():
        if "packet loss" in line:
            for token in line.split(","):
                if "packet loss" not in token:
                    continue
                try:
                    result["packet_loss_pct"] = float(token.strip().split("%")[0])
                except ValueError:
                    pass
        if "min/avg/max" in line and "=" in line:
            nums = line.split("=", 1)[1].strip().split()[0]
            parts = nums.split("/")
            if len(parts) >= 2:
                try:
                    result["rtt_avg_ms"] = float(parts[1])
                except ValueError:
                    pass
    return result


def ping_probe(src: Any, dst_ip: str, count: int = 10, interval_s: float = 0.2) -> Dict[str, Optional[float]]:
    """Run a foreground ping probe and parse its summary."""
    cmd = "ping -i %g -c %d %s" % (float(interval_s), int(count), shlex.quote(dst_ip))
    return parse_ping(_run_on_node(src, cmd, timeout=max(count * interval_s + 5, 5)))

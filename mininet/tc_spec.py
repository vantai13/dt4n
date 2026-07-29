#!/usr/bin/env python3
"""Phase L -- pure qdisc specification.

No Mininet import and no I/O here: only numbers and text transformations. This
lets regression tests run without root, kernel modules, or a Mininet install.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


FRAME_BYTES_1470 = 1512
DEFAULT_BURST_BYTES = 1600
H_ROOT, H_CLASS, H_LEAF = "1:", "1:10", "10:"
CONFIGS = ((8.0, 18), (6.0, 13), (4.0, 10))


def queue_bytes(queue_pkts: int, frame_bytes: int = FRAME_BYTES_1470) -> int:
    return int(queue_pkts) * int(frame_bytes)


def queue_ceiling_ms(
    queue_pkts: int,
    bw_mbps: float,
    frame_bytes: int = FRAME_BYTES_1470,
) -> float:
    return queue_bytes(queue_pkts, frame_bytes) * 8.0 / (float(bw_mbps) * 1e6) * 1000.0


def capacity_pps(bw_mbps: float, frame_bytes: int = FRAME_BYTES_1470) -> float:
    """Packet/s capacity in the accounting units HTB uses."""
    return float(bw_mbps) * 1e6 / (8.0 * int(frame_bytes))


def measure_cmds(
    ifname: str,
    bw_mbps: float,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
) -> List[str]:
    limit_b = queue_bytes(queue_pkts, frame_bytes)
    return [
        "tc qdisc add dev %s root handle %s htb default 10" % (ifname, H_ROOT),
        (
            "tc class add dev %s parent %s classid %s htb "
            "rate %gmbit burst %db cburst %db"
        )
        % (ifname, H_ROOT, H_CLASS, float(bw_mbps), int(burst_bytes), int(burst_bytes)),
        "tc qdisc add dev %s parent %s handle %s bfifo limit %d"
        % (ifname, H_CLASS, H_LEAF, limit_b),
    ]


def return_cmds(ifname: str, delay_ms: float) -> List[str]:
    return [
        "tc qdisc add dev %s root handle %s netem delay %gms"
        % (ifname, H_ROOT, float(delay_ms))
    ]


def _num(text: str, pat: str, cast: Any = float) -> Optional[Any]:
    m = re.search(pat, text)
    return cast(m.group(1)) if m else None


def parse_qdisc_tree(text: str) -> List[Dict[str, Any]]:
    layers: List[Dict[str, Any]] = []
    for block in re.split(r"\n(?=qdisc\s)", (text or "").strip()):
        if not block.startswith("qdisc"):
            continue
        head = block.splitlines()[0]
        m = re.match(r"qdisc\s+(\S+)\s+(\S+)\s*(.*)", head)
        if not m:
            continue
        kind, handle, rest = m.group(1), m.group(2), m.group(3)

        limit_b = _num(rest, r"limit\s+(\d+)b\b", int)
        limit_p = _num(rest, r"limit\s+(\d+)p\b", int)
        if limit_b is None and limit_p is None:
            limit_p = _num(rest, r"limit\s+(\d+)(?![bp\d])", int)

        layers.append(
            {
                "kind": kind,
                "handle": handle,
                "is_root": " root " in (" " + rest + " ") or rest.startswith("root"),
                "limit_bytes": limit_b,
                "limit_pkts": limit_p,
                "delay_ms": _num(rest, r"delay\s+([0-9.]+)ms"),
                "backlog_bytes": _num(block, r"backlog\s+(\d+)\s*(?:b|bytes?)\b", int),
                "backlog_pkts": _num(block, r"backlog\s+\d+\s*(?:b|bytes?)\s+(\d+)p\b", int),
                "sent_bytes": _num(block, r"Sent\s+(\d+)\s+bytes", int),
                "dropped": _num(block, r"dropped\s+(\d+)", int),
                "overlimits": _num(block, r"overlimits\s+(\d+)", int),
                "direct_packets_stat": _num(rest, r"direct_packets_stat\s+(\d+)", int),
                "direct_qlen": _num(rest, r"direct_qlen\s+(\d+)", int),
                "raw": block,
            }
        )
    return layers


def check_measure_text(
    qdisc_text: str,
    class_text: str,
    queue_pkts: int,
    burst_bytes: int = DEFAULT_BURST_BYTES,
    frame_bytes: int = FRAME_BYTES_1470,
) -> List[str]:
    """Return errors for measured-direction qdisc text; empty means valid."""
    errs: List[str] = []
    layers = parse_qdisc_tree(qdisc_text)
    kinds = [layer["kind"] for layer in layers]

    htb = next((layer for layer in layers if layer["kind"] == "htb"), None)
    if htb is None or not htb["is_root"]:
        errs.append("V-L1a: khong co htb o root")
    if "netem" in kinds:
        errs.append("V-L1b: CO netem o chieu DO (loi E8 quay lai)")

    bfifo = next((layer for layer in layers if layer["kind"] == "bfifo"), None)
    if bfifo is None:
        pfifo = next((layer for layer in layers if layer["kind"] == "pfifo"), None)
        if pfifo is not None:
            errs.append(
                "V-L1c: dung pfifo (gioi han theo GOI) thay vi bfifo "
                "(theo BYTE)"
            )
        else:
            errs.append(
                "V-L1c: khong co leaf qdisc -> HTB dung pfifo mac dinh "
                "limit=txqueuelen=1000 goi = bufferbloat"
            )
    else:
        want = queue_bytes(queue_pkts, frame_bytes)
        if bfifo["limit_bytes"] != want:
            errs.append("V-L1c: bfifo limit=%s b, mong doi %d b" % (bfifo["limit_bytes"], want))

    if htb is not None and htb.get("direct_packets_stat") not in (0, None):
        errs.append(
            "V-L1g: direct_packets_stat=%s != 0 -> co goi BO QUA shaping"
            % htb["direct_packets_stat"]
        )

    if not re.search(r"burst\s+%db\b" % int(burst_bytes), class_text or ""):
        errs.append("V-L1d: khong thay burst %db trong class" % int(burst_bytes))
    return errs


def staircase_delays_ms(
    n: int,
    bw_mbps: float,
    frame_bytes: int = FRAME_BYTES_1470,
    burst_bytes: int = DEFAULT_BURST_BYTES,
) -> List[float]:
    """Theory for n back-to-back packets entering an empty HTB bucket."""
    C = float(bw_mbps) * 1e6 / 8.0
    out = []
    for k in range(1, int(n) + 1):
        delay_s = ((k - 1) * int(frame_bytes) - int(burst_bytes)) / C
        out.append(max(0.0, delay_s) * 1000.0)
    return out


def fit_staircase(
    delays_ms: List[float],
    k_start: int = 3,
    frame_bytes: int = FRAME_BYTES_1470,
) -> Dict[str, float]:
    """Recover shaper rate and token-bucket burst from measured staircase."""
    ks = list(range(int(k_start), len(delays_ms) + 1))
    ys = [delays_ms[k - 1] * 1e-3 for k in ks]
    n = len(ks)
    if n < 2:
        raise ValueError("can it nhat 2 diem")
    mean_k = sum(ks) / n
    mean_y = sum(ys) / n
    sxx = sum((k - mean_k) ** 2 for k in ks)
    sxy = sum((k - mean_k) * (y - mean_y) for k, y in zip(ks, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_k
    C = float(frame_bytes) / slope
    B = -intercept * C - float(frame_bytes)
    yhat = [slope * k + intercept for k in ks]
    ss_res = sum((y - h) ** 2 for y, h in zip(ys, yhat))
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "C_bytes_per_s": C,
        "C_mbps": C * 8.0 / 1e6,
        "burst_bytes": B,
        "r2": r2,
        "slope_s_per_pkt": slope,
        "intercept_s": intercept,
    }

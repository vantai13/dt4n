#!/usr/bin/env python3
"""Shared UDP packet player for Phase L and Phase T load generators."""

from __future__ import annotations

import os
import socket
import time
from typing import Any, Dict, List, Sequence, Tuple

from measurements.owd_probe import (
    KIND_BG,
    KIND_PROBE,
    REC_TX,
    pack_packet,
    sleep_until,
)
from mininet.load_spec import PAYLOAD_BG, PAYLOAD_PROBE, cv


def _interarrival_cv(times: Sequence[float]) -> float:
    return cv([b - a for a, b in zip(times, times[1:])])


def play_events(
    events: Sequence[Tuple[float, bool]],
    dst_ip: str,
    port: int,
    duration_s: float,
    run_id: int,
    out_prefix: str,
) -> Dict[str, Any]:
    """Send sorted ``(relative_time, is_probe)`` events and write tx raw files."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 21)
    addr = (dst_ip, int(port))

    rec_bg: List[bytes] = []
    rec_pr: List[bytes] = []
    ts_bg: List[float] = []
    seq_bg = 0
    seq_pr = 0
    n_late = 0
    max_late = 0.0

    t0 = time.monotonic()
    t_end = t0 + float(duration_s)
    try:
        for t_rel, is_probe in events:
            t_target = t0 + float(t_rel)
            if t_target > t_end:
                break
            now = time.monotonic()
            if now > t_target + 0.001:
                n_late += 1
                max_late = max(max_late, now - t_target)
            else:
                sleep_until(t_target)
            t_send = time.monotonic()
            if is_probe:
                sock.sendto(
                    pack_packet(KIND_PROBE, seq_pr, t_send, run_id, PAYLOAD_PROBE),
                    addr,
                )
                rec_pr.append(REC_TX.pack(seq_pr, t_send))
                seq_pr += 1
            else:
                sock.sendto(
                    pack_packet(KIND_BG, seq_bg, t_send, run_id, PAYLOAD_BG),
                    addr,
                )
                rec_bg.append(REC_TX.pack(seq_bg, t_send))
                ts_bg.append(t_send)
                seq_bg += 1
        if time.monotonic() < t_end:
            sleep_until(t_end)
    finally:
        t1 = time.monotonic()
        sock.close()

    out_dir = os.path.dirname(os.path.abspath(out_prefix)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(out_prefix + "_bgtx.bin", "wb") as f:
        f.write(b"".join(rec_bg))
    with open(out_prefix + "_prtx.bin", "wb") as f:
        f.write(b"".join(rec_pr))

    return {
        "n_bg_sent": seq_bg,
        "n_probe_sent": seq_pr,
        "n_late": n_late,
        "max_late_ms": max_late * 1e3,
        "duration_s_actual": max(t1 - t0, 1e-9),
        "c_a_actual_bg": _interarrival_cv(ts_bg),
    }

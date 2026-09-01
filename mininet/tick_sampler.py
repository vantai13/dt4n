#!/usr/bin/env python3
"""Shared-tick ledger snapshot primitives for the Phase-G emitter."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Sequence

from mininet.modulated_emitter import SPIN_THRESHOLD_S, sleep_until


@dataclass(frozen=True)
class TickSnapshot:
    window_index: int
    deadline_s: float
    target_cumulative_packets: tuple[float, ...]
    sent_cumulative_packets: tuple[int, ...]
    measured_cumulative_packets: tuple[int, ...]
    snapshot_span_s: float


def parse_proc_net_dev(
    text: str,
    interfaces: Sequence[str],
    *,
    direction: str = "tx",
) -> dict[str, tuple[int, int]]:
    """Return ``{ifname: (bytes, packets)}`` from Linux proc-net-dev text."""
    if direction not in {"rx", "tx"}:
        raise ValueError("direction must be 'rx' or 'tx'")
    wanted = set(interfaces)
    found: dict[str, tuple[int, int]] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        name, fields_text = raw_line.split(":", 1)
        name = name.strip()
        if name not in wanted:
            continue
        fields = fields_text.split()
        if len(fields) < 16:
            raise ValueError(f"malformed /proc/net/dev row for {name}")
        offset = 0 if direction == "rx" else 8
        found[name] = (int(fields[offset]), int(fields[offset + 1]))
    missing = wanted - found.keys()
    if missing:
        raise KeyError(f"interfaces missing from /proc/net/dev: {sorted(missing)}")
    return found


def read_proc_packet_counters(
    interfaces: Sequence[str],
    *,
    direction: str = "tx",
    path: str = "/proc/net/dev",
) -> tuple[int, ...]:
    with open(path, encoding="utf-8") as handle:
        parsed = parse_proc_net_dev(
            handle.read(), interfaces, direction=direction
        )
    return tuple(parsed[name][1] for name in interfaces)


def sample_at(
    window_index: int,
    deadline_s: float,
    target_cumulative_packets: Sequence[float],
    shared_sent_cumulative: Sequence[int],
    counter_reader: Callable[[], Sequence[int]],
    *,
    spin_threshold_s: float = SPIN_THRESHOLD_S,
    clock: Callable[[], float] = time.perf_counter,
    sleeper: Callable[[float], None] = time.sleep,
) -> TickSnapshot:
    """Capture L2 then L3 on one absolute tick and record snapshot width."""
    sleep_until(
        deadline_s,
        spin_threshold_s=spin_threshold_s,
        clock=clock,
        sleeper=sleeper,
    )
    snapshot_start = clock()
    sent = tuple(int(value) for value in shared_sent_cumulative)
    measured = tuple(int(value) for value in counter_reader())
    snapshot_end = clock()
    target = tuple(float(value) for value in target_cumulative_packets)
    if not (len(target) == len(sent) == len(measured)):
        raise ValueError("target/sent/measured ledgers have different widths")
    return TickSnapshot(
        window_index=window_index,
        deadline_s=deadline_s,
        target_cumulative_packets=target,
        sent_cumulative_packets=sent,
        measured_cumulative_packets=measured,
        snapshot_span_s=max(0.0, snapshot_end - snapshot_start),
    )

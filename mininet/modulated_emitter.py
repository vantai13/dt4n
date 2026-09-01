#!/usr/bin/env python3
"""Absolute-deadline packet emitter for Phase-G mechanism A.

This module deliberately owns no Mininet objects.  It can drive a connected
datagram socket on a bench and later the same send contract inside a namespace.
Every window independently rounds its requested packet count; missed packets
are recorded and never carried into a later window.
"""
from __future__ import annotations

import ctypes
import gc
import math
import os
import time
from dataclasses import dataclass
from multiprocessing.sharedctypes import RawArray
from typing import Callable, MutableSequence, Protocol


SPIN_THRESHOLD_S = 200e-6
NATIVE_INT64_BYTES = ctypes.sizeof(ctypes.c_longlong)


class SendSocket(Protocol):
    def send(self, payload: bytes) -> int: ...


@dataclass
class EmitterState:
    target_cum_packets: float = 0.0
    sent_cum_packets: int = 0
    windows: int = 0
    overrun_windows: int = 0
    overrun_max_s: float = 0.0
    deadline_lateness_max_s: float = 0.0


@dataclass(frozen=True)
class WindowResult:
    window_index: int
    target_packets: float
    sent_packets: int
    max_deadline_lateness_s: float
    overrun_s: float


def sleep_until(
    deadline: float,
    *,
    spin_threshold_s: float = SPIN_THRESHOLD_S,
    clock: Callable[[], float] = time.perf_counter,
    sleeper: Callable[[float], None] = time.sleep,
) -> None:
    """Wait for an absolute perf-counter deadline by coarse sleep then spin."""
    if not math.isfinite(deadline):
        raise ValueError("deadline must be finite")
    if not 0.0 <= spin_threshold_s < 0.01:
        raise ValueError("spin_threshold_s must be in [0, 0.01)")
    while True:
        remaining = deadline - clock()
        if remaining <= 0.0:
            return
        if remaining > spin_threshold_s:
            sleeper(remaining - spin_threshold_s)


def pin_current_process(cpu: int) -> None:
    """Pin the calling process and verify the kernel accepted the affinity."""
    if not isinstance(cpu, int) or cpu < 0:
        raise ValueError("cpu must be a non-negative integer")
    if not hasattr(os, "sched_setaffinity"):
        raise RuntimeError("CPU affinity is unavailable on this platform")
    os.sched_setaffinity(0, {cpu})
    actual = os.sched_getaffinity(0)
    if actual != {cpu}:
        raise RuntimeError(f"CPU pin failed: requested {cpu}, got {sorted(actual)}")


def atomic_int64_array(size: int) -> MutableSequence[int]:
    """Allocate an aligned lock-free int64 shared array for single-writer slots."""
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    values = RawArray(ctypes.c_longlong, size)
    address = ctypes.addressof(values)
    if NATIVE_INT64_BYTES != 8 or address % 8 != 0:
        raise RuntimeError("native aligned atomic int64 storage is unavailable")
    return values


def emit_window(
    window_index: int,
    epoch_s: float,
    dt_s: float,
    rate_pps: float,
    sock: SendSocket,
    payload: bytes,
    shared_cumulative: MutableSequence[int],
    emitter_index: int,
    state: EmitterState,
    *,
    spin_threshold_s: float = SPIN_THRESHOLD_S,
    clock: Callable[[], float] = time.perf_counter,
    sleeper: Callable[[float], None] = time.sleep,
) -> WindowResult:
    """Emit one independently rounded window without deficit compensation."""
    if window_index < 0 or dt_s <= 0.0 or rate_pps < 0.0:
        raise ValueError("window_index/rate/dt outside physical domain")
    if not payload:
        raise ValueError("payload must not be empty")
    target_packets = float(rate_pps * dt_s)
    n_target = int(round(target_packets))
    t_start = float(epoch_s + window_index * dt_s)
    t_end = t_start + dt_s
    state.target_cum_packets += target_packets
    max_lateness = 0.0

    for packet_index in range(n_target):
        deadline = t_start + (packet_index + 0.5) * dt_s / n_target
        sleep_until(
            deadline,
            spin_threshold_s=spin_threshold_s,
            clock=clock,
            sleeper=sleeper,
        )
        sent_bytes = int(sock.send(payload))
        if sent_bytes != len(payload):
            raise RuntimeError(
                f"partial datagram send: {sent_bytes}/{len(payload)} bytes"
            )
        state.sent_cum_packets += 1
        shared_cumulative[emitter_index] = state.sent_cum_packets
        max_lateness = max(max_lateness, max(0.0, clock() - deadline))

    overrun = max(0.0, clock() - t_end)
    state.windows += 1
    state.deadline_lateness_max_s = max(
        state.deadline_lateness_max_s, max_lateness
    )
    if overrun > 0.0:
        state.overrun_windows += 1
        state.overrun_max_s = max(state.overrun_max_s, overrun)
    return WindowResult(
        window_index=window_index,
        target_packets=target_packets,
        sent_packets=n_target,
        max_deadline_lateness_s=max_lateness,
        overrun_s=overrun,
    )


def emit_series(
    rates_pps: list[float],
    epoch_s: float,
    dt_s: float,
    sock: SendSocket,
    payload: bytes,
    shared_cumulative: MutableSequence[int],
    emitter_index: int,
    *,
    cpu: int | None = None,
    spin_threshold_s: float = SPIN_THRESHOLD_S,
    window_sent: MutableSequence[int] | None = None,
    window_lateness_ns: MutableSequence[int] | None = None,
) -> EmitterState:
    """Run an absolute-grid series and optionally publish per-window ledgers."""
    if cpu is not None:
        pin_current_process(cpu)
    state = EmitterState()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for window_index, rate_pps in enumerate(rates_pps):
            result = emit_window(
                window_index,
                epoch_s,
                dt_s,
                float(rate_pps),
                sock,
                payload,
                shared_cumulative,
                emitter_index,
                state,
                spin_threshold_s=spin_threshold_s,
            )
            if window_sent is not None:
                window_sent[window_index] = result.sent_packets
            if window_lateness_ns is not None:
                window_lateness_ns[window_index] = int(round(
                    result.max_deadline_lateness_s * 1e9
                ))
    finally:
        if gc_was_enabled:
            gc.enable()
    return state

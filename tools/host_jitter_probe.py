#!/usr/bin/env python3
"""Measure shared-stall probability directly with emitter pacing and no socket."""
from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path

import numpy as np

from mininet.modulated_emitter import (
    SPIN_THRESHOLD_S,
    pin_current_process,
    sleep_until,
)
from tools.g1_quant_model import WIRE_BYTES_DEFAULT
from tools.g2_topology import CAP_BPS
from tools.g3_emitter_dryrun import DT_S, git_hash, sha256


RHO_ANCHOR = 0.857
STALL_THRESHOLD_S = 1e-3
WARMUP_S = 0.5


def read_psi_totals(path: str = "/proc/pressure/cpu") -> dict[str, int]:
    """Return cumulative PSI stall microseconds for each available class."""
    totals: dict[str, int] = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                fields = line.split()
                if not fields:
                    continue
                values = dict(
                    field.split("=", 1) for field in fields[1:] if "=" in field
                )
                if "total" in values:
                    totals[fields[0]] = int(values["total"])
    except (OSError, ValueError):
        return {}
    return totals


def read_steal_ticks(path: str = "/proc/stat") -> int | None:
    """Return the cumulative guest steal counter from the aggregate CPU row."""
    try:
        with open(path, encoding="utf-8") as handle:
            fields = handle.readline().split()
        if fields and fields[0] == "cpu" and len(fields) > 8:
            return int(fields[8])
    except (OSError, ValueError):
        pass
    return None


def _psi_delta_rate(
    before: dict[str, int], after: dict[str, int], elapsed_s: float
) -> dict[str, float]:
    if elapsed_s <= 0.0:
        raise ValueError("elapsed_s must be positive")
    return {
        key: (after[key] - before[key]) / (elapsed_s * 1e6)
        for key in sorted(before.keys() & after.keys())
        if after[key] >= before[key]
    }


def _wilson_upper_95(successes: int, trials: int) -> float:
    """One-sided-ish 95% Wilson upper endpoint, reported as finite-N context."""
    if not 0 <= successes <= trials or trials <= 0:
        raise ValueError("invalid binomial counts")
    z = 1.96
    p = successes / trials
    denominator = 1.0 + z * z / trials
    center = p + z * z / (2.0 * trials)
    radius = z * np.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials**2))
    return float((center + radius) / denominator)


def probe(cpu: int, duration_s: float, rate_pps: float) -> dict[str, object]:
    """Reproduce pacing deadlines and record each lateness without sending."""
    if not np.isfinite(duration_s) or duration_s <= 0.0:
        raise ValueError("duration_s must be finite and positive")
    if not np.isfinite(rate_pps) or rate_pps <= 0.0:
        raise ValueError("rate_pps must be finite and positive")
    pin_current_process(cpu)
    packets_per_window = int(round(rate_pps * DT_S))
    windows = int(duration_s / DT_S)
    if packets_per_window < 1 or windows < 2:
        raise ValueError("probe needs at least one packet and two windows")

    lateness = np.empty((windows, packets_per_window), dtype=float)
    gap = DT_S / packets_per_window
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        sleep_until(time.perf_counter() + WARMUP_S)
        psi_before = read_psi_totals()
        steal_before = read_steal_ticks()
        epoch = time.perf_counter()
        for window in range(windows):
            t_start = epoch + window * DT_S
            for packet in range(packets_per_window):
                deadline = t_start + (packet + 0.5) * gap
                sleep_until(deadline, spin_threshold_s=SPIN_THRESHOLD_S)
                lateness[window, packet] = max(
                    0.0, time.perf_counter() - deadline
                )
        observed_end = time.perf_counter()
        psi_after = read_psi_totals()
        steal_after = read_steal_ticks()
    finally:
        if gc_was_enabled:
            gc.enable()

    elapsed_s = observed_end - epoch
    window_max = lateness.max(axis=1)
    stall_windows = int(np.count_nonzero(window_max >= STALL_THRESHOLD_S))
    steal_delta = (
        None
        if steal_before is None or steal_after is None
        else steal_after - steal_before
    )
    return {
        "cpu": cpu,
        "rate_pps": rate_pps,
        "packets_per_window": packets_per_window,
        "windows": windows,
        "scheduled_duration_s": windows * DT_S,
        "observed_elapsed_s": elapsed_s,
        "lateness_median_s": float(np.median(lateness)),
        "lateness_p99_s": float(np.quantile(lateness, 0.99)),
        "lateness_p999_s": float(np.quantile(lateness, 0.999)),
        "lateness_max_s": float(lateness.max()),
        "window_max_median_s": float(np.median(window_max)),
        "window_max_p99_s": float(np.quantile(window_max, 0.99)),
        "p_stall_1ms": stall_windows / windows,
        "p_stall_1ms_wilson_upper_95": _wilson_upper_95(
            stall_windows, windows
        ),
        "stall_threshold_s": STALL_THRESHOLD_S,
        "stall_windows": stall_windows,
        "psi_total_us_before": psi_before,
        "psi_total_us_after": psi_after,
        "psi_delta_rate": _psi_delta_rate(psi_before, psi_after, elapsed_s),
        "steal_ticks_before": steal_before,
        "steal_ticks_after": steal_after,
        "steal_ticks_delta": steal_delta,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--cpu", type=int, default=0)
    parser.add_argument("--duration-s", type=float, default=60.0)
    parser.add_argument(
        "--label",
        choices=("before_quiesce", "after_quiesce"),
        required=True,
    )
    args = parser.parse_args()
    rate_pps = (
        RHO_ANCHOR * float(CAP_BPS.max()) / (WIRE_BYTES_DEFAULT * 8.0)
    )
    started = time.perf_counter()
    loadavg_at_start = float(os.getloadavg()[0])
    result = probe(args.cpu, args.duration_s, rate_pps)
    artifact = {
        "schema": "dt4n.phase_g.host_jitter_probe.v1",
        "status": "NO_SOCKET_HOST_MEASUREMENT",
        "scenario": args.label,
        "git_hash": git_hash(),
        "tool_path": "tools/host_jitter_probe.py",
        "tool_sha256": sha256(Path(__file__)),
        "loadavg_at_start": loadavg_at_start,
        **result,
        "runtime_s": time.perf_counter() - started,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        "p_stall(>=1ms) = {p_stall_1ms:.6f}  stalls={stall_windows}/{windows}  "
        "window_max_p99={window_max_p99_s:.6f}s".format(**artifact)
    )
    print("psi_delta_rate =", artifact["psi_delta_rate"])
    print("steal_ticks_delta =", artifact["steal_ticks_delta"])
    print("artifact =", args.out)


if __name__ == "__main__":
    main()

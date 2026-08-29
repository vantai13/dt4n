#!/usr/bin/env python3
"""Record host-infrastructure state alongside an experiment run.

The output is JSONL: one header followed by samples.  Durations are measured
with CLOCK_MONOTONIC; CLOCK_REALTIME is retained only to detect wall-clock
adjustments while a run is in progress.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import psutil


def _net_counters() -> dict[str, int]:
    counters = psutil.net_io_counters()
    return {
        "drop_in": int(counters.dropin),
        "drop_out": int(counters.dropout),
        "err_in": int(counters.errin),
        "err_out": int(counters.errout),
    }


def monitor(out: Path, duration_s: float, interval_s: float, tag: str = "") -> int:
    if duration_s <= 0:
        raise ValueError("duration must be positive")
    if interval_s <= 0:
        raise ValueError("interval must be positive")

    out.parent.mkdir(parents=True, exist_ok=True)
    t0_real = time.time()
    t0_mono = time.monotonic()
    deadline = t0_mono + duration_s
    previous_ctx = int(psutil.cpu_stats().ctx_switches)
    psutil.cpu_percent(interval=None, percpu=True)  # prime the counters

    n_rows = 0
    with out.open("w", encoding="utf-8") as handle:
        header = {
            "_header": True,
            "schema": "dt4n.infra_monitor.v1",
            "tag": tag,
            "interval_s": interval_s,
            "duration_requested_s": duration_s,
            "n_cpu": psutil.cpu_count(),
            "boot_time": psutil.boot_time(),
            "total_mem_gb": round(psutil.virtual_memory().total / 1e9, 2),
        }
        handle.write(json.dumps(header, sort_keys=True) + "\n")

        sample_index = 0
        while True:
            sample_started = time.monotonic()
            if sample_started >= deadline:
                break

            cpu_by_core = psutil.cpu_percent(interval=None, percpu=True)
            stats = psutil.cpu_stats()
            current_ctx = int(stats.ctx_switches)
            elapsed_mono = sample_started - t0_mono
            elapsed_real = time.time() - t0_real
            row = {
                "i": sample_index,
                "t_mono_s": round(elapsed_mono, 6),
                "cpu_percent": round(float(sum(cpu_by_core) / max(len(cpu_by_core), 1)), 3),
                "cpu_percent_max_core": round(float(max(cpu_by_core, default=0.0)), 3),
                "load_1m": float(os.getloadavg()[0]),
                "ctx_switches_delta": current_ctx - previous_ctx,
                "mem_percent": float(psutil.virtual_memory().percent),
                "swap_percent": float(psutil.swap_memory().percent),
                "clock_skew_ms": round((elapsed_real - elapsed_mono) * 1e3, 6),
                **_net_counters(),
            }
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            previous_ctx = current_ctx
            sample_index += 1
            n_rows += 1

            remaining = interval_s - (time.monotonic() - sample_started)
            if remaining > 0:
                time.sleep(remaining)

    return n_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--tag", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = monitor(args.out, args.duration, args.interval, args.tag)
    print(json.dumps({"out": str(args.out), "samples": rows}, sort_keys=True))


if __name__ == "__main__":
    main()

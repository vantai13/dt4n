#!/usr/bin/env python3
"""Summarize a ``tools.infra_monitor`` JSONL file and emit warning flags."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def summarize(path: Path) -> dict[str, object]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    headers = [row for row in records if row.get("_header")]
    rows = [row for row in records if not row.get("_header")]
    if len(headers) != 1 or not rows:
        raise ValueError("infra JSONL must contain one header and at least one sample")

    interval_s = float(headers[0]["interval_s"])
    cpu = np.asarray([row["cpu_percent"] for row in rows], dtype=float)
    cpu_core = np.asarray([row["cpu_percent_max_core"] for row in rows], dtype=float)
    ctx = np.asarray([row["ctx_switches_delta"] for row in rows], dtype=float)
    skew = np.asarray([row["clock_skew_ms"] for row in rows], dtype=float)
    drop_delta = (
        int(rows[-1]["drop_in"]) + int(rows[-1]["drop_out"])
        - int(rows[0]["drop_in"]) - int(rows[0]["drop_out"])
    )
    clock_jump = float(np.max(np.abs(np.diff(skew)))) if len(skew) > 1 else 0.0
    swap_max = float(max(row["swap_percent"] for row in rows))

    return {
        "schema": "dt4n.infra_summary.v1",
        "source": str(path),
        "samples": len(rows),
        "interval_s": interval_s,
        "cpu_p50": round(float(np.percentile(cpu, 50)), 3),
        "cpu_p95": round(float(np.percentile(cpu, 95)), 3),
        "cpu_max": round(float(cpu.max()), 3),
        "cpu_max_core_p95": round(float(np.percentile(cpu_core, 95)), 3),
        "ctx_per_s": round(float(ctx.mean() / interval_s), 3),
        "load_1m_max": round(float(max(row["load_1m"] for row in rows)), 3),
        "swap_max_pct": swap_max,
        "net_drops": drop_delta,
        "clock_skew_ms_p95": round(float(np.percentile(np.abs(skew), 95)), 6),
        "clock_jump_ms_max": round(clock_jump, 6),
        "flag_cpu_saturated": bool(np.percentile(cpu, 95) > 85.0),
        "flag_swapping": bool(swap_max > 1.0),
        "flag_packet_drops": bool(drop_delta > 0),
        "flag_clock_jump": bool(clock_jump > 5.0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = summarize(args.input)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Analyze TCP instrument-probe output."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from typing import Iterable, Mapping

import numpy as np


def _float(row: Mapping[str, str], key: str, default=None):
    value = row.get(key)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_groups(path: str):
    groups = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            run_id = row.get("run_id") or "%s:%s:%s" % (
                row.get("cfg_queue_pkts", ""),
                row.get("rep", ""),
                row.get("timestamp_utc", ""),
            )
            groups[run_id].append(row)
    return groups


def pct(values, q):
    if not values:
        return float("nan")
    return float(np.percentile(np.asarray(values, dtype=float), q))


def parse_args(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="Analyze Lesson 9.0 TCP probe")
    p.add_argument("--csv", default="results/calib/raw_tcp_probe.csv")
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    groups = read_groups(args.csv)
    if not groups:
        raise SystemExit("no usable rows in %s" % args.csv)

    print("=" * 116)
    print("TCP Probe Summary")
    print("=" * 116)
    print(
        "run_id        q  target  n   rho_mean rho_p95 rho_max rho_tcp  "
        "q_ms_mean q_ms_p95 q_ms_max  rtt_idle rtt_mean bloat_max"
    )
    print("-" * 116)
    all_rho = []
    all_q = []
    all_bloat = []
    for run_id, rows in sorted(groups.items()):
        rho = [_float(row, "rho_measured", 0.0) for row in rows]
        q_ms = [_float(row, "q_delay_ms", 0.0) for row in rows]
        rtt = [
            _float(row, "rtt_ms", _float(row, "ping_rtt_avg_ms"))
            for row in rows
        ]
        rtt = [value for value in rtt if value is not None]
        bloat = [_float(row, "bloat_ms") for row in rows]
        bloat = [value for value in bloat if value is not None]
        all_rho.extend(rho)
        all_q.extend(q_ms)
        all_bloat.extend(bloat)
        first = rows[0]
        rho_tcp = _float(first, "rho_tcp")
        rtt_idle = _float(first, "rtt_idle_ms")
        print(
            "%-12s %2.0f %7s %3d   %7.3f %7.3f %7.3f %7s  "
            "%8.3f %7.3f %8.3f  %8s %8s %9s"
            % (
                run_id,
                _float(first, "cfg_queue_pkts", 0.0),
                (
                    "%.0f" % _float(first, "cfg_queue_target_ms")
                    if _float(first, "cfg_queue_target_ms") is not None
                    else "explicit"
                ),
                len(rows),
                float(np.mean(rho)) if rho else float("nan"),
                pct(rho, 95),
                max(rho) if rho else float("nan"),
                "%.3f" % rho_tcp if rho_tcp is not None else "n/a",
                float(np.mean(q_ms)) if q_ms else float("nan"),
                pct(q_ms, 95),
                max(q_ms) if q_ms else float("nan"),
                "%.3f" % rtt_idle if rtt_idle is not None else "n/a",
                "%.3f" % float(np.mean(rtt)) if rtt else "n/a",
                "%.3f" % max(bloat) if bloat else "n/a",
            )
        )

    print()
    print("=" * 116)
    print("Instrument-Effect Questions")
    print("=" * 116)
    print("TCP rho mean/max       = %.3f / %.3f" % (float(np.mean(all_rho)), max(all_rho)))
    print("TCP qdelay mean/p95/max= %.3f / %.3f / %.3f ms" % (
        float(np.mean(all_q)),
        pct(all_q, 95),
        max(all_q),
    ))
    if all_bloat:
        print("TCP bloat mean/p95/max = %.3f / %.3f / %.3f ms" % (
            float(np.mean(all_bloat)),
            pct(all_bloat, 95),
            max(all_bloat),
        ))
    print()
    print("Interpretation:")
    print("  rho_max well below 1.0 -> UDP sweep covers a region TCP rarely reaches")
    print("  high q_ms_p95/max      -> TCP can fill buffers; bufferbloat is present")
    print("  high q_ms variance     -> TCP creates sawtooth, not steady utilization")


if __name__ == "__main__":
    main()

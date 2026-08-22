#!/usr/bin/env python3
"""Freeze a hand-validated L.2 result as the Phase L golden fixture."""

from __future__ import annotations

import json
import os
import sys


def main(src: str) -> None:
    checks = json.load(open(src, "r", encoding="utf-8"))["checks"]
    golden = {
        "source": os.path.basename(src),
        "note": "Dong bang sau khi kiem chung bang tay. Sua = phai viet amendment.",
        "floor": {key: checks["V-L0_floor"][key] for key in ("mean_ms", "sd_ms", "p50_ms", "p99_ms")},
        "zero_load_mean_ms": {
            "bw%g" % bw: checks["V-L2"]["bw%g" % bw]["mean_ms"]
            for bw in (4.0, 6.0, 8.0)
        },
        "staircase_ms": {
            "bw%g" % bw: checks["V-L2b"]["bw%g" % bw]["measured_ms"]
            for bw in (4.0, 6.0, 8.0)
        },
    }
    os.makedirs("results/RAW/phase-L/golden", exist_ok=True)
    dst = "results/RAW/phase-L/golden/l2_staircase_golden.json"
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(golden, f, indent=2, sort_keys=True)
    print("-> %s" % dst)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 tools/freeze_l2_golden.py results/SUPERSEDED/phase-L/l2_probe_XXXX.json")
    main(sys.argv[1])

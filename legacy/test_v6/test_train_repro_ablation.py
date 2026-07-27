#!/usr/bin/env python3
"""Golden reproducibility check for Phase 11.2 ablation training.

Run directly:
    python test/routing/test_train_repro_ablation.py

It trains the same short run twice and compares the full train_return sequence.
If this fails, do not launch the 10-run ablation.
"""

from __future__ import annotations

import csv
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path


CFG = os.environ.get(
    "ROUTE_REPRO_CONFIG",
    "rl/routing/configs/train_r_ablation_aoi.yaml",
)
ROOT_PREFIX = os.environ.get("ROUTE_REPRO_ROOT_PREFIX", "results/repro")


def run_short(tag: str) -> list[str]:
    """Run a 30-episode training smoke test and return train_return values."""
    out = Path(f"{ROOT_PREFIX}_{tag}")
    if out.exists():
        shutil.rmtree(out)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "rl.routing_2path.train_r",
            "--config",
            CFG,
            "--seed",
            "0",
            "--episodes",
            "30",
            "--out-root",
            str(out),
            "--print-every",
            "30",
        ],
        check=True,
    )

    [episodes_csv] = glob.glob(str(out / "*" / "episodes.csv"))
    with open(episodes_csv, newline="") as handle:
        return [row["train_return"] for row in csv.DictReader(handle)]


def main() -> int:
    first = run_short("A")
    second = run_short("B")
    print(f"\nrun A[:5] = {first[:5]}")
    print(f"run B[:5] = {second[:5]}")
    if first != second:
        raise AssertionError(
            "FAIL: same seed produced different train_return sequences"
        )
    print("PASS - same seed -> identical train_return sequence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

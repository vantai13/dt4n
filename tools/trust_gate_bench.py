#!/usr/bin/env python3
"""Microbenchmark the current scalar trust-gate decision path.

The benchmark deliberately calls ``cert.usefulness_v2._thresholds`` on one
representative row.  This includes the pandas age-bin lookup used by the
analysis code, rather than timing only a floating-point comparison.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from cert.usefulness_v2 import _thresholds


DEFAULT_QHAT = {0: 3.1843101978302, 1: 4.277664661407471, 2: 5.3734636306762695, 3: 6.711788177490234}


def decision(row: pd.DataFrame, qhat: dict[int, float], kappa: float) -> bool:
    threshold = _thresholds(row, qhat, "z_bin", kappa)
    return bool(row["m_hat"].to_numpy(np.float64)[0] >= threshold[0])


def run_benchmark(n_warm: int, n: int, m_hat: float, z_bin: int, kappa: float) -> dict[str, object]:
    row = pd.DataFrame({"m_hat": [float(m_hat)], "z_bin": [int(z_bin)]})
    for _ in range(n_warm):
        decision(row, DEFAULT_QHAT, kappa)

    latency_ms = np.empty(n, dtype=float)
    accepted = False
    for index in range(n):
        started = time.perf_counter_ns()
        accepted = decision(row, DEFAULT_QHAT, kappa)
        latency_ms[index] = (time.perf_counter_ns() - started) / 1e6

    return {
        "schema": "dt4n.trust_gate_benchmark.v1",
        "implementation": "cert.usefulness_v2._thresholds + scalar comparison",
        "n": n,
        "warmup": n_warm,
        "input": {"m_hat": m_hat, "z_bin": z_bin, "kappa": kappa},
        "accepted": accepted,
        "p50_ms": round(float(np.percentile(latency_ms, 50)), 6),
        "p95_ms": round(float(np.percentile(latency_ms, 95)), 6),
        "p99_ms": round(float(np.percentile(latency_ms, 99)), 6),
        "max_ms": round(float(latency_ms.max()), 6),
        "mean_ms": round(float(latency_ms.mean()), 6),
        "gate_p99_le_10ms": bool(np.percentile(latency_ms, 99) <= 10.0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=200)
    parser.add_argument("--n", type=int, default=5000)
    parser.add_argument("--m-hat", type=float, default=8.0)
    parser.add_argument("--z-bin", type=int, default=2, choices=sorted(DEFAULT_QHAT))
    parser.add_argument("--kappa", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_benchmark(args.warmup, args.n, args.m_hat, args.z_bin, args.kappa)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

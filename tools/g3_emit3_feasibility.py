#!/usr/bin/env python3
"""Synthetic feasibility check for max-per-window timing correlation."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from tools.g3_emitter_dryrun import git_hash, mean_correlation_then_max, sha256


SEED = 11
WINDOWS = 300
REPLICATES = 16
LINKS = 8
PACKETS_PER_WINDOW = 119
STALL_AMPLITUDE_S = 1e-3
PRIVATE_MEAN_S = 50e-6
PROBABILITIES = (0.0, 0.0005, 0.001, 0.005, 0.02, 0.05, 0.10, 0.50)


def _statistic(rng: np.random.Generator, p_stall: float) -> float:
    replicates = np.empty((REPLICATES, LINKS, WINDOWS), dtype=float)
    for replicate in range(REPLICATES):
        private = rng.exponential(
            PRIVATE_MEAN_S, (LINKS, WINDOWS, PACKETS_PER_WINDOW)
        ).max(axis=2)
        hit = rng.random(WINDOWS) < p_stall
        shared = np.where(
            hit, rng.exponential(STALL_AMPLITUDE_S, WINDOWS), 0.0
        )
        replicates[replicate] = np.maximum(private, shared[None, :])
    return mean_correlation_then_max(replicates)[0]


def simulate(*, repeats: int = 3, seed: int = SEED) -> dict[str, object]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    rows = []
    for probability in PROBABILITIES:
        values = [_statistic(rng, probability) for _ in range(repeats)]
        rows.append({
            "p_stall_per_window": probability,
            "mean_emit3": float(np.mean(values)),
            "replicate_statistics": values,
            "mean_seconds_between_stalls": (
                None if probability == 0.0 else 0.2 / probability
            ),
        })
    return {
        "schema": "dt4n.phase_g.g3_emit3_feasibility.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "tool_sha256": sha256(Path(__file__)),
        "seed": seed,
        "repeats": repeats,
        "windows": WINDOWS,
        "replicates": REPLICATES,
        "packets_per_window": PACKETS_PER_WINDOW,
        "stall_amplitude_s": STALL_AMPLITUDE_S,
        "legacy_gate": 0.10,
        "rows": rows,
        "runtime_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    artifact = simulate(repeats=args.repeats)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    for row in artifact["rows"]:
        print(
            "p_stall=%7.4f  EMIT-3=%.4f"
            % (row["p_stall_per_window"], row["mean_emit3"])
        )
    print("runtime_s = %.3f" % artifact["runtime_s"])
    if args.out:
        print("artifact =", args.out)


if __name__ == "__main__":
    main()

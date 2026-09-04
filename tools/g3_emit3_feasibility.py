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


def _statistic(
    rng: np.random.Generator,
    p_stall: float,
    *,
    replicates: int,
    windows: int,
    measured_threshold_input: bool,
) -> float:
    values = np.empty((replicates, LINKS, windows), dtype=float)
    for replicate in range(replicates):
        private = rng.exponential(
            PRIVATE_MEAN_S, (LINKS, windows, PACKETS_PER_WINDOW)
        ).max(axis=2)
        hit = rng.random(windows) < p_stall
        amplitude = rng.exponential(STALL_AMPLITUDE_S, windows)
        if measured_threshold_input:
            # The probe measures P(max lateness >= 1 ms). Conditional on a
            # measured hit, injected amplitude must therefore be >= 1 ms;
            # the legacy illustration instead used an unconditional
            # exponential whose hit probability had a different meaning.
            amplitude += STALL_AMPLITUDE_S
        shared = np.where(hit, amplitude, 0.0)
        values[replicate] = np.maximum(private, shared[None, :])
    return mean_correlation_then_max(values)[0]


def simulate(
    *,
    repeats: int = 3,
    seed: int = SEED,
    probabilities: tuple[float, ...] = PROBABILITIES,
    replicates: int = REPLICATES,
    windows: int = WINDOWS,
    measured_threshold_input: bool = False,
) -> dict[str, object]:
    if min(repeats, replicates, windows) <= 0:
        raise ValueError("repeats, replicates, and windows must be positive")
    if not probabilities or any(not 0.0 <= p <= 1.0 for p in probabilities):
        raise ValueError("probabilities must be a non-empty subset of [0,1]")
    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    rows = []
    for probability in probabilities:
        values = [
            _statistic(
                rng,
                probability,
                replicates=replicates,
                windows=windows,
                measured_threshold_input=measured_threshold_input,
            )
            for _ in range(repeats)
        ]
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
        "tool_path": "tools/g3_emit3_feasibility.py",
        "tool_sha256": sha256(Path(__file__)),
        "seed": seed,
        "repeats": repeats,
        "windows": windows,
        "replicates": replicates,
        "packets_per_window": PACKETS_PER_WINDOW,
        "stall_amplitude_s": STALL_AMPLITUDE_S,
        "p_stall_definition": (
            "fraction of windows with injected shared lateness >= 1 ms"
            if measured_threshold_input
            else "legacy probability of an unconditional exponential event"
        ),
        "measured_threshold_input": measured_threshold_input,
        "legacy_gate": 0.10,
        "rows": rows,
        "runtime_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--p-stall", type=float, action="append")
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    parser.add_argument("--windows", type=int, default=WINDOWS)
    args = parser.parse_args()
    measured_input = args.p_stall is not None
    probabilities = (
        tuple(args.p_stall) if measured_input else PROBABILITIES
    )
    artifact = simulate(
        repeats=args.repeats,
        probabilities=probabilities,
        replicates=args.replicates,
        windows=args.windows,
        measured_threshold_input=measured_input,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    for row in artifact["rows"]:
        print(
            "p_stall=%7.4f  EMIT-3=%.4f"
            % (row["p_stall_per_window"], row["mean_emit3"])
        )
    print("p_stall_definition =", artifact["p_stall_definition"])
    print("runtime_s = %.3f" % artifact["runtime_s"])
    if args.out:
        print("artifact =", args.out)


if __name__ == "__main__":
    main()

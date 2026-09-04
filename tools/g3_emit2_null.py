#!/usr/bin/env python3
"""Calibrate the exact EMIT-2 max-over-16-rows operator under its null."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from tools.g1_quant_model import WIRE_BYTES_DEFAULT, acf1_predicted_mechanism_a
from tools.g2_topology import CAP_BPS, DEGREE, INCIDENCE, LINKS, a0_from_sigma_at
from tools.g3_dryrun import (
    RHO_MAX,
    RHO_MIN,
    component_baselines,
    quantization_step_packets,
)
from tools.g3_emitter_dryrun import (
    CELLS, DT_S, N_WINDOWS, REPLICATES, git_hash, sha256,
)


TRIALS = 800
SEED = 50000
SAFETY_FACTOR = 1.957


def _acf1(values: np.ndarray) -> np.ndarray:
    centered = values - values.mean(axis=-1, keepdims=True)
    denominator = np.sum(centered * centered, axis=-1)
    numerator = np.sum(centered[..., :-1] * centered[..., 1:], axis=-1)
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan),
        where=denominator > 0.0,
    )


def _ar1(
    rng: np.random.Generator, tau_s: float, n_processes: int = len(LINKS)
) -> np.ndarray:
    phi = float(np.exp(-DT_S / tau_s))
    innovation_scale = float(np.sqrt(1.0 - phi * phi))
    innovations = rng.standard_normal((n_processes, N_WINDOWS))
    values = np.empty_like(innovations)
    values[:, 0] = innovations[:, 0]
    for window in range(1, N_WINDOWS):
        values[:, window] = (
            phi * values[:, window - 1]
            + innovation_scale * innovations[:, window]
        )
    return values


def _trial_maximum(
    seed: int,
    precomputed: list[tuple[dict[str, object], float, np.ndarray]],
) -> float:
    """Implement one complete 16-row EMIT-2 null world."""
    rng = np.random.default_rng(seed)
    errors = []
    for design, a0, predicted in precomputed:
        path_base, private_base, _ = component_baselines(a0)
        replicate_acfs = np.empty((REPLICATES, len(LINKS)), dtype=float)
        for replicate in range(REPLICATES):
            path_rate = np.maximum(path_base[:, None], 0.0)
            private_rate = np.maximum(
                private_base[:, None]
                + (a0 * np.sqrt(DEGREE))[:, None]
                * _ar1(rng, float(design["tau_s"])),
                0.0,
            )
            rho = np.clip(
                (INCIDENCE @ path_rate + private_rate) / CAP_BPS[:, None],
                RHO_MIN,
                RHO_MAX,
            )
            target_packets = (
                rho * CAP_BPS[:, None] * DT_S
                / (WIRE_BYTES_DEFAULT * 8.0)
            )
            replicate_acfs[replicate] = _acf1(
                np.round(target_packets) - target_packets
            )
        observed = np.median(replicate_acfs, axis=0)
        errors.extend(np.abs(observed - predicted))
    return float(np.max(errors))


def calibrate(*, trials: int = TRIALS, seed: int = SEED, batch_size: int = 20):
    if min(trials, batch_size) <= 0:
        raise ValueError("trials and batch_size must be positive")
    started = time.perf_counter()
    maxima = np.empty(trials, dtype=float)
    precomputed = []
    for design in CELLS:
        a0 = a0_from_sigma_at("uA", design["sigma_ref"])
        predicted = np.asarray([
            acf1_predicted_mechanism_a(step)
            for step in quantization_step_packets(
                a0, 0.0, design["tau_s"], design["tau_s"]
            )
        ])
        precomputed.append((design, a0, predicted))
    for trial in range(trials):
        maxima[trial] = _trial_maximum(seed + trial, precomputed)
    quantiles = np.quantile(maxima, [0.50, 0.90, 0.95, 0.99])
    p99 = float(quantiles[3])
    return {
        "schema": "dt4n.phase_g.g3_emit2_null.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "tool_sha256": sha256(Path(__file__)),
        "seed": seed,
        "seed_last": seed + trials - 1,
        "trials": trials,
        "replicates": REPLICATES,
        "windows": N_WINDOWS,
        "comparisons": len(CELLS) * len(LINKS),
        "median": float(quantiles[0]),
        "p90": float(quantiles[1]),
        "p95": float(quantiles[2]),
        "p99": p99,
        "max": float(maxima.max()),
        "probability_over_legacy_gate": float(np.mean(maxima > 0.05)),
        "probability_over_observed_0_057771": float(
            np.mean(maxima > 0.057771)
        ),
        "safety_factor": SAFETY_FACTOR,
        "calibrated_gate": SAFETY_FACTOR * p99,
        "runtime_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    artifact = calibrate(
        trials=args.trials, seed=args.seed, batch_size=args.batch_size
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        "EMIT-2 null: median={median:.5f} p90={p90:.5f} "
        "p95={p95:.5f} p99={p99:.5f} max={max:.5f}".format(**artifact)
    )
    print("P(>0.05) = %.4f" % artifact["probability_over_legacy_gate"])
    print("calibrated_gate = %.5f" % artifact["calibrated_gate"])
    print("runtime_s = %.3f" % artifact["runtime_s"])
    if args.out:
        print("artifact =", args.out)


if __name__ == "__main__":
    main()

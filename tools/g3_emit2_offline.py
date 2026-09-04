#!/usr/bin/env python3
"""Reproduce EMIT-2 from the signed generator without sockets or scheduling."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from tools.g1_quant_model import WIRE_BYTES_DEFAULT, acf1_predicted_mechanism_a
from tools.g2_topology import CAP_BPS, LINKS, a0_from_sigma_at
from tools.g3_dryrun import acf, physical_trace, quantization_step_packets
from tools.g3_emitter_dryrun import (
    CELLS, DT_S, N_WINDOWS, REPLICATES, SEED, git_hash, sha256,
)


def calculate() -> dict[str, object]:
    """Consume the original RNG stream and replace UDP with its count identity."""
    started = time.perf_counter()
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, object]] = []
    for level in ("L0", "L1", "L2"):
        designs = CELLS if level == "L0" else (CELLS[1],)
        for design in designs:
            a0 = a0_from_sigma_at("uA", design["sigma_ref"])
            replicate_acfs = []
            for _replicate in range(REPLICATES):
                trace = physical_trace(
                    0.0,
                    design["tau_s"],
                    design["tau_s"],
                    N_WINDOWS,
                    rng,
                    a0=a0,
                )
                target_packets = (
                    trace["rho_target"]
                    * CAP_BPS[:, None]
                    * DT_S
                    / (WIRE_BYTES_DEFAULT * 8.0)
                )
                sent_packets = np.round(target_packets)
                replicate_acfs.append([
                    acf(sent_packets[index] - target_packets[index])
                    for index in range(len(LINKS))
                ])
            observed = np.median(np.asarray(replicate_acfs), axis=0)
            steps = quantization_step_packets(
                a0, 0.0, design["tau_s"], design["tau_s"]
            )
            predicted = np.asarray([
                acf1_predicted_mechanism_a(step) for step in steps
            ])
            for index, link in enumerate(LINKS):
                rows.append({
                    "level": level,
                    "cell": design["name"],
                    "link": link,
                    "acf1_observed": float(observed[index]),
                    "acf1_predicted": float(predicted[index]),
                    "prediction_abs_error": float(abs(
                        observed[index] - predicted[index]
                    )),
                })

    l0_rows = [row for row in rows if row["level"] == "L0"]
    value = max(float(row["prediction_abs_error"]) for row in l0_rows)
    return {
        "schema": "dt4n.phase_g.g3_emit2_offline.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "tool_sha256": sha256(Path(__file__)),
        "seed": SEED,
        "replicates": REPLICATES,
        "windows": N_WINDOWS,
        "emit2": value,
        "legacy_gate": 0.05,
        "legacy_verdict": "PASS" if value <= 0.05 else "FAIL",
        "rows": rows,
        "runtime_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    artifact = calculate()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print("EMIT-2 offline = %.18f  legacy=%s" % (
        artifact["emit2"], artifact["legacy_verdict"]
    ))
    print("runtime_s = %.3f" % artifact["runtime_s"])
    if args.out:
        print("artifact =", args.out)


if __name__ == "__main__":
    main()

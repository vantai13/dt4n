#!/usr/bin/env python3
"""Write the signed EMIT-3' null calibration for the reduced G-A016 bench."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from tools.g3_emitter_dryrun import (
    A016_N_WINDOWS,
    A016_REPLICATES,
    EMIT3_PRIME_NULL_SEED,
    EMIT3_PRIME_NULL_TRIALS,
    git_hash,
    sha256,
    simulate_emit3_prime_null,
)


def calibrate() -> dict[str, object]:
    started = time.perf_counter()
    result = simulate_emit3_prime_null(
        trials=EMIT3_PRIME_NULL_TRIALS,
        replicates=A016_REPLICATES,
        windows=A016_N_WINDOWS - 1,
        seed=EMIT3_PRIME_NULL_SEED,
    )
    return {
        "schema": "dt4n.phase_g.g3_emit3_prime_null.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "tool_sha256": sha256(Path(__file__)),
        **result,
        "runtime_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    artifact = calibrate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        "EMIT-3' null: median={median:.6f} p95={p95:.6f} "
        "p99={p99:.6f} gate={gate:.6f}".format(**artifact)
    )
    print("runtime_s = %.3f" % artifact["runtime_s"])
    print("artifact =", args.out)


if __name__ == "__main__":
    main()

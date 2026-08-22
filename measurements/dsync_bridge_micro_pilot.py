#!/usr/bin/env python3
"""Range-setting micro-pilot for the inherited ``d_sync`` sensitivity study.

The pilot deliberately uses synthetic Things and does not read any certificate
outcome.  One measured cycle covers the complete software path used to motivate
``d_sync``: create a collector-like snapshot, PATCH all Things, wait for Ditto's
HTTP acknowledgement, and GET all Things back while verifying the cycle token.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import platform
import subprocess
import time
import uuid
from typing import Any, Dict, Sequence

import numpy as np
import requests

from bridge.ditto_common import DITTO_AUTH, DITTO_BASE_URL, HTTP_TIMEOUT, POLICY_ID
from bridge.ditto_reader import fetch_all_things
from bridge.pusher import push_changes


DEFAULT_OUTPUT = "results/SUPERSEDED/phase-23/dsync_bridge_micro_pilot.json"


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _summary_ms(values_s: Sequence[float]) -> Dict[str, float]:
    values_ms = np.asarray(values_s, dtype=np.float64) * 1000.0
    return {
        "min": float(values_ms.min()),
        "p05": float(np.percentile(values_ms, 5)),
        "p50": float(np.percentile(values_ms, 50)),
        "mean": float(values_ms.mean()),
        "p95": float(np.percentile(values_ms, 95)),
        "max": float(values_ms.max()),
    }


def _thing_body(thing_id: str, token: int = -1) -> Dict[str, Any]:
    return {
        "thingId": thing_id,
        "policyId": POLICY_ID,
        "features": {
            "pilot": {
                "properties": {
                    "cycleToken": int(token),
                    "tSource": 0.0,
                    "sample": 0.0,
                }
            }
        },
    }


def run_pilot(n_things: int, warmup_cycles: int, measured_cycles: int) -> Dict[str, Any]:
    if n_things <= 0 or warmup_cycles < 0 or measured_cycles <= 0:
        raise ValueError("n_things/measured_cycles must be positive and warmup non-negative")

    run_id = uuid.uuid4().hex[:12]
    namespace = POLICY_ID.split(":", 1)[0]
    thing_ids = [f"{namespace}:dsync-pilot-{run_id}-{i:02d}" for i in range(n_things)]
    push_session = requests.Session()
    push_session.auth = DITTO_AUTH
    read_session = requests.Session()
    read_session.auth = DITTO_AUTH

    created = []
    total_s: list[float] = []
    push_s: list[float] = []
    read_s: list[float] = []
    try:
        for thing_id in thing_ids:
            url = f"{DITTO_BASE_URL}/things/{thing_id}"
            existing = push_session.get(url, timeout=HTTP_TIMEOUT)
            if existing.status_code != 404:
                raise RuntimeError(f"refusing to overwrite existing pilot Thing {thing_id}: HTTP {existing.status_code}")
            response = push_session.put(url, json=_thing_body(thing_id), timeout=HTTP_TIMEOUT)
            if response.status_code not in (201, 204):
                raise RuntimeError(f"cannot create {thing_id}: HTTP {response.status_code} {response.text[:200]}")
            created.append(thing_id)

        n_total = warmup_cycles + measured_cycles
        for cycle in range(n_total):
            token = cycle + 1
            t_source = time.time()
            # This is the collector-like snapshot and adapter output for 20 fake entities.
            changes = {
                thing_id: {
                    "features": {
                        "pilot": {
                            "properties": {
                                "cycleToken": token,
                                "tSource": t_source,
                                "sample": float((token + index) % 101) / 100.0,
                            }
                        }
                    }
                }
                for index, thing_id in enumerate(thing_ids)
            }

            t0 = time.perf_counter()
            tp0 = time.perf_counter()
            n_ok, n_attempted = push_changes(changes, session=push_session)
            tp1 = time.perf_counter()
            things, read_meta = fetch_all_things(read_session, thing_ids)
            t1 = time.perf_counter()

            if n_ok != n_attempted or read_meta["n_fail"] != 0:
                raise RuntimeError(
                    f"incomplete cycle {token}: push={n_ok}/{n_attempted}, read_fail={read_meta['n_fail']}"
                )
            stale = [
                thing_id
                for thing_id in thing_ids
                if int(things[thing_id]["features"]["pilot"]["properties"]["cycleToken"]) != token
            ]
            if stale:
                raise RuntimeError(f"Ditto read-back did not observe token {token}: {stale[:3]}")

            if cycle >= warmup_cycles:
                total_s.append(t1 - t0)
                push_s.append(tp1 - tp0)
                read_s.append(float(read_meta["fetch_ms"]) / 1000.0)

        return {
            "schema": "dt4n.dsync_bridge_micro_pilot.v1",
            "status": "RANGE_SETTING_ONLY",
            "certificate_outcomes_read": False,
            "run_id": run_id,
            "n_things": int(n_things),
            "warmup_cycles": int(warmup_cycles),
            "n_cycle": int(measured_cycles),
            "path": "synthetic collector snapshot -> sequential pusher PATCH -> Ditto acknowledgement -> sequential direct GET read-back",
            "cycle_ms": _summary_ms(total_s),
            "push_ms": _summary_ms(push_s),
            "read_ms": _summary_ms(read_s),
            "all_cycle_tokens_verified": True,
            "all_http_operations_succeeded": True,
            "environment": {
                "ditto_base_url": DITTO_BASE_URL,
                "host": platform.node(),
                "python": platform.python_version(),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "git_hash_before_prereg": _git("git", "rev-parse", "HEAD"),
                "git_dirty_during_pilot": bool(_git("git", "status", "--porcelain")),
            },
        }
    finally:
        cleanup_failures = []
        for thing_id in created:
            try:
                response = push_session.delete(
                    f"{DITTO_BASE_URL}/things/{thing_id}", timeout=HTTP_TIMEOUT
                )
                if response.status_code not in (204, 404):
                    cleanup_failures.append(f"{thing_id}:HTTP{response.status_code}")
            except requests.RequestException as exc:
                cleanup_failures.append(f"{thing_id}:{type(exc).__name__}")
        push_session.close()
        read_session.close()
        if cleanup_failures:
            raise RuntimeError("pilot cleanup failed: " + ", ".join(cleanup_failures))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--things", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--out", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = run_pilot(args.things, args.warmup, args.cycles)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

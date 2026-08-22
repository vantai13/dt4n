#!/usr/bin/env python3
"""Lesson 23.8[A3] -- counterbalanced AoI probe for topology_v7 links."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import subprocess
import time
from typing import Any, Dict, Mapping

from bridge.ditto_common import DITTO_BASE_URL
from bridge.ditto_reader import _get_one, extract_t_source, make_session
from bridge.topology_v7_map import SPEC_PATH, link_thing_ids
from twin.util_spec import UTIL_DIRECTION, utilization_from_rate
from twin import topology_v7 as T7


SCHEMA = "dt4n.aoi.v7.v1"


def _feature_properties(body: Mapping[str, Any], feature: str) -> Mapping[str, Any]:
    value = body.get("features", {}).get(feature, {})
    if not isinstance(value, dict):
        return {}
    properties = value.get("properties")
    return properties if isinstance(properties, dict) else value


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def probe_once(session, ids: Mapping[str, str], k: int) -> Dict[str, Any]:
    """Read all 8 links, reversing order on odd probes."""
    order = list(T7.LINK_NAMES)
    probe_order = "fwd"
    if int(k) % 2:
        order.reverse()
        probe_order = "rev"

    out: Dict[str, Any] = {}
    t_probe_start = time.time()
    for pos, logical in enumerate(order):
        thing_id = ids[logical]
        t0 = time.time()
        body, ok = _get_one(session, thing_id)
        t_obs = time.time()
        t_source = extract_t_source(body) if ok and body is not None else None
        rho = None
        if ok and body is not None:
            traffic = _feature_properties(body, "traffic")
            capacity = _feature_properties(body, "capacity")
            rate = traffic.get("%sRate" % UTIL_DIRECTION)
            bw_mbps = capacity.get("bwMbps")
            if rate is not None and bw_mbps not in (None, 0, 0.0):
                rho = utilization_from_rate(rate, bw_mbps)
        out[logical] = {
            "thing_id": thing_id,
            "t_source": t_source,
            "t_obs": t_obs,
            "aoi_s": None if t_source is None else t_obs - t_source,
            "get_ms": (t_obs - t0) * 1000.0,
            "read_pos": int(pos),
            "ok": bool(ok),
            "rho": rho,
            "util_direction": UTIL_DIRECTION,
        }
    return {
        "schema": SCHEMA,
        "record": "probe",
        "k": int(k),
        "probe_order": probe_order,
        "t_probe_start": t_probe_start,
        "links": out,
    }


def default_metadata(**overrides: Any) -> Dict[str, Any]:
    meta = {
        "git_hash": _git_hash(),
        "spec_sha256": _sha256(SPEC_PATH),
        "t_start_utc": datetime.now(timezone.utc).isoformat(),
        "host": platform.node(),
        "ditto_url": DITTO_BASE_URL,
    }
    meta.update(overrides)
    return meta


def run(
    duration_s: float,
    interval_s: float,
    out_path: str,
    meta: Mapping[str, Any],
    stop_event=None,
) -> int:
    session = make_session()
    ids = link_thing_ids()
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    end = time.monotonic() + float(duration_s)
    k = 0
    try:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "schema": SCHEMA,
                "record": "header",
                **default_metadata(**dict(meta)),
            }, sort_keys=True) + "\n")
            while time.monotonic() < end and not (
                stop_event is not None and stop_event.is_set()
            ):
                t0 = time.monotonic()
                handle.write(json.dumps(probe_once(session, ids, k), sort_keys=True) + "\n")
                handle.flush()
                k += 1
                wait = max(0.0, float(interval_s) - (time.monotonic() - t0))
                if stop_event is not None:
                    stop_event.wait(wait)
                else:
                    time.sleep(wait)
    finally:
        session.close()
    return k


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--out", required=True)
    parser.add_argument("--mode", choices=("clean", "prod"), required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()
    count = run(
        args.duration,
        args.interval,
        args.out,
        {
            "mode": args.mode,
            "rho_bar": args.rho_bar,
            "repeat": args.repeat,
            "sync_period_s": 0.5,
            "tol": 0.0 if args.mode == "clean" else 0.5,
            "reconcile_every": 1 if args.mode == "clean" else 30,
            "probe_interval_s": args.interval,
            "duration_s": args.duration,
        },
    )
    print("wrote %d probes -> %s" % (count, args.out))


if __name__ == "__main__":
    main()

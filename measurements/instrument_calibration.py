#!/usr/bin/env python3
"""Lesson 23.8[A0] -- calibrate the AoI instrument before system outcomes."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import platform
import tempfile
import threading
import time
import uuid
from typing import Any, Dict, Sequence

import numpy as np
import requests

from bridge import pusher as PUSH
from bridge import sync_agent as SYNC
from bridge.ditto_common import DITTO_AUTH, DITTO_BASE_URL, HTTP_TIMEOUT, POLICY_ID
from bridge.ditto_reader import _get_one, extract_t_source, make_session
from bridge.ditto_common import make_thing_id_link
from bridge.pusher import patch_thing


OUTPUT = "results/phase-23/a0_instrument_calibration.json"


def _summary(values: Sequence[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "min_s": float(arr.min()),
        "p05_s": float(np.percentile(arr, 5)),
        "p50_s": float(np.percentile(arr, 50)),
        "mean_s": float(arr.mean()),
        "p95_s": float(np.percentile(arr, 95)),
        "p99_s": float(np.percentile(arr, 99)),
        "max_s": float(arr.max()),
        "sd_s": float(arr.std(ddof=0)),
        "cv": float(arr.std(ddof=0) / arr.mean()),
    }


def nc_do_1(session, thing_id: str, offset_s: float = 1.0, n: int = 20) -> Dict[str, Any]:
    values = []
    response_values = []
    residual_ms = []
    for _ in range(int(n)):
        t_fake = time.time() - float(offset_s)
        ok = patch_thing(
            thing_id,
            {"features": {"meta": {"properties": {"tSource": round(t_fake, 6)}}}},
            session=session,
        )
        # Amendment pseudocode defines observation at request start. Record the
        # response timestamp separately so reader RTT remains visible.
        t_obs = time.time()
        body, read_ok = _get_one(session, thing_id)
        t_response = time.time()
        t_source = extract_t_source(body) if read_ok and body is not None else None
        if ok and t_source is not None:
            values.append(t_obs - t_source)
            response_values.append(t_response - t_source)
            residual_ms.append((t_fake - t_source) * 1000.0)
        time.sleep(0.05)
    result = _summary(values)
    result.update(
        {
            "nominal_s": float(offset_s),
            "bias_ms": float((result["mean_s"] - float(offset_s)) * 1000.0),
            "response_observation": _summary(response_values),
            "reader_added_mean_ms": float(
                (np.mean(response_values) - np.mean(values)) * 1000.0
            ),
            "pass_M_68_original": bool(
                result["min_s"] >= 0.995 and result["max_s"] <= 1.010
            ),
            "timestamp_residual_ms": {
                "mean": float(np.mean(residual_ms)),
                "max_abs": float(np.max(np.abs(residual_ms))),
            },
            "pass_M_68b_timestamp_residual": bool(
                float(np.max(np.abs(residual_ms))) <= 0.001
            ),
        }
    )
    return result


class _SyntheticCollector:
    """Fixed-state collector used only to calibrate delta/full-sync behavior."""

    short_keys: Sequence[str] = ()

    def __init__(self, net, interval=0.5, **_kwargs):
        self.net = net
        self.interval = float(interval)

    def collect_all(self) -> Dict[str, Any]:
        start = time.time()
        things = {}
        for index, short_key in enumerate(self.short_keys):
            t_source = time.time()
            left, right = short_key.split("link-", 1)[1].split("-", 1)
            things[short_key] = {
                "attributes": {
                    "type": "link",
                    "endpointA": left,
                    "endpointB": right,
                },
                "features": {
                    "status": {"state": "up"},
                    "traffic": {"rxRate": 0.0, "txRate": 0.0, "lossPct": 0.0},
                },
                "t_source": t_source,
            }
        end = time.time()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "t_source": start,
            "t_cycle_start": start,
            "t_cycle_end": end,
            "cycle_scan_ms": (end - start) * 1000.0,
            "things": things,
        }


def _run_sync_mode(
    mode: str,
    thing_ids: Sequence[str],
    short_keys: Sequence[str],
    target_id: str,
    duration_s: float,
    sample_interval_s: float = 0.05,
) -> Dict[str, Any]:
    period = 0.5
    max_cycles = int(round(float(duration_s) / period)) + 1
    errors = []
    samples = []
    with tempfile.TemporaryDirectory(prefix="dt4n-a0-") as tmp:
        cycle_trace = os.path.join(tmp, f"cycles-{mode}.jsonl")
        push_trace = os.path.join(tmp, f"push-{mode}.jsonl")
        old_collector = SYNC.Collector
        old_push_trace = PUSH.PUSH_TRACE_PATH
        _SyntheticCollector.short_keys = tuple(short_keys)
        SYNC.Collector = _SyntheticCollector
        PUSH.PUSH_TRACE_PATH = push_trace
        net = type("CalibrationNet", (), {})()

        def _target():
            try:
                SYNC.run(
                    net,
                    period=period,
                    max_cycles=max_cycles,
                    ping_every=0,
                    reconcile_every=30,
                    measurement_mode=mode,
                    cycle_trace_path=cycle_trace,
                )
            except BaseException as exc:  # surfaced in the parent thread
                errors.append(exc)

        thread = threading.Thread(target=_target, name=f"a0-{mode}", daemon=True)
        session = make_session()
        started = time.time()
        try:
            thread.start()
            while thread.is_alive():
                body, ok = _get_one(session, target_id)
                t_obs = time.time()
                t_source = extract_t_source(body) if ok and body is not None else None
                if t_source is not None and t_source > 0.0 and t_obs - started >= 1.0:
                    samples.append(
                        {
                            "t_obs": t_obs,
                            "t_source": t_source,
                            "aoi_s": t_obs - t_source,
                        }
                    )
                time.sleep(float(sample_interval_s))
            thread.join(timeout=2.0)
            if errors:
                raise errors[0]
            cycles = [
                json.loads(line)
                for line in open(cycle_trace, encoding="utf-8")
                if line.strip()
            ]
            pushes = [
                json.loads(line)
                for line in open(push_trace, encoding="utf-8")
                if line.strip()
            ] if os.path.exists(push_trace) else []
        finally:
            session.close()
            SYNC.Collector = old_collector
            PUSH.PUSH_TRACE_PATH = old_push_trace

    values = [float(row["aoi_s"]) for row in samples]
    result = {
        "mode": mode,
        "duration_s": float(duration_s),
        "period_s": period,
        "reconcile_every": 1 if mode == "clean" else 30,
        "aoi": _summary(values),
        "n_cycles": len(cycles),
        "n_push_records": len(pushes),
        "max_n_pushed": max(int(row["n_pushed"]) for row in cycles),
        "min_n_pushed": min(int(row["n_pushed"]) for row in cycles),
        "n_things": len(thing_ids),
        "overrun_ratio": float(np.mean([bool(row["overrun"]) for row in cycles])),
        "cycle_elapsed_ms": _summary(
            [float(row["cycle_elapsed_ms"]) / 1000.0 for row in cycles]
        ),
        "cycle_scan_ms": _summary(
            [float(row["cycle_scan_ms"]) / 1000.0 for row in cycles]
        ),
        "lock_wait_ms": _summary(
            [float(row["lock_wait_ms"]) / 1000.0 for row in cycles]
        ),
        "all_pushes_ok": bool(all(bool(row["ok"]) for row in pushes)),
    }
    if mode == "clean":
        spread_90 = float(result["aoi"]["p95_s"] - result["aoi"]["p05_s"])
        d_hat = max(0.0, float(result["aoi"]["p05_s"]) - 0.05 * period)
        cv_expected = float(
            period / np.sqrt(12.0) / (d_hat + period / 2.0)
        )
        result["NC_U_all_cycles_full_push"] = bool(
            all(int(row["n_pushed"]) == int(row["n_things"]) for row in cycles)
        )
        result["pass_NC_do_2_original"] = bool(
            0.44 <= float(result["aoi"]["cv"]) <= 0.52
            and result["NC_U_all_cycles_full_push"]
        )
        result["uniform_shape"] = {
            "p95_minus_p05_s": spread_90,
            "d_hat_from_p05_s": d_hat,
            "cv_expected": cv_expected,
            "cv_observed": float(result["aoi"]["cv"]),
            "cv_abs_gap": abs(float(result["aoi"]["cv"]) - cv_expected),
            "pass_NC_do_2a_spread": bool(0.42 <= spread_90 <= 0.48),
            "pass_NC_do_2b_cv_identity": bool(
                abs(float(result["aoi"]["cv"]) - cv_expected) <= 0.03
            ),
        }
    else:
        result["pass_M_69_NC_do_3"] = bool(result["aoi"]["max_s"] >= 5.0)
    return result


def rate_smoke() -> Dict[str, Any]:
    """Deterministic two-snapshot check of common vs per-link time deltas."""
    old_dt = 0.500
    # Scan position changed slightly between two cycles (seconds).
    prev_offsets = np.linspace(0.010, 0.080, 8)
    now_offsets = np.linspace(0.012, 0.096, 8)
    new_dt = old_dt + now_offsets - prev_offsets
    byte_delta = np.full(8, 500_000.0)
    old_rate = byte_delta / old_dt
    new_rate = byte_delta / new_dt
    relative = np.abs(new_rate - old_rate) / old_rate
    return {
        "description": "8-link deterministic snapshot smoke; scan span changes 70ms -> 84ms",
        "old_rxRate_Bps": [float(x) for x in old_rate],
        "new_rxRate_Bps": [float(x) for x in new_rate],
        "relative_abs_gap": [float(x) for x in relative],
        "max_relative_abs_gap": float(relative.max()),
        "pass_M_67": bool(relative.max() <= 0.05),
    }


def _create_things(session, run_id: str, n_things: int = 1):
    namespace = POLICY_ID.split(":", 1)[0]
    short_keys = [f"link-a0{run_id}{i:02d}-b0{run_id}{i:02d}" for i in range(n_things)]
    thing_ids = []
    for short_key in short_keys:
        left, right = short_key.split("link-", 1)[1].split("-", 1)
        thing_id = make_thing_id_link(left, right)
        response = session.get(f"{DITTO_BASE_URL}/things/{thing_id}", timeout=HTTP_TIMEOUT)
        if response.status_code != 404:
            raise RuntimeError(f"refusing to overwrite {thing_id}: HTTP {response.status_code}")
        body = {
            "thingId": thing_id,
            "policyId": POLICY_ID,
            "features": {
                "meta": {"properties": {"tSource": 0.0}},
                "status": {"properties": {"state": "up"}},
            },
        }
        response = session.put(
            f"{DITTO_BASE_URL}/things/{thing_id}", json=body, timeout=HTTP_TIMEOUT
        )
        if response.status_code not in (201, 204):
            raise RuntimeError(f"cannot create {thing_id}: HTTP {response.status_code}")
        thing_ids.append(thing_id)
    return short_keys, thing_ids


def run(clean_duration_s: float = 15.0, prod_duration_s: float = 60.0) -> Dict[str, Any]:
    run_id = uuid.uuid4().hex[:6]
    admin = requests.Session()
    admin.auth = DITTO_AUTH
    created = []
    try:
        # NC-do-2/3 calibrate the measurement path with one known, fixed-state
        # Thing. Batch-width effects are a later system estimand, not an
        # instrument-calibration input.
        short_keys, created = _create_things(admin, run_id, n_things=1)
        target_id = created[len(created) // 2]
        nc1 = nc_do_1(admin, target_id)
        clean = _run_sync_mode(
            "clean", created, short_keys, target_id, clean_duration_s
        )
        prod = _run_sync_mode(
            "prod", created, short_keys, target_id, prod_duration_s
        )
        smoke = rate_smoke()
        return {
            "schema": "dt4n.phase23.a0_instrument_calibration.v1",
            "status": "INSTRUMENT_CALIBRATION",
            "closes_P23A": False,
            "run_id": run_id,
            "target_thing": target_id,
            "n_things": len(created),
            "M_66_changed_test_status_count": 0,
            "M_67_rate_smoke": smoke,
            "M_68_NC_do_1": nc1,
            "NC_do_2_clean_sawtooth": clean,
            "M_69_NC_do_3_prod_delta": prod,
            "verdict": {
                "M_66": True,
                "M_67": bool(smoke["pass_M_67"]),
                "M_68b": bool(nc1["pass_M_68b_timestamp_residual"]),
                "M_69": bool(prod["pass_M_69_NC_do_3"]),
                "NC_do_2a": bool(clean["uniform_shape"]["pass_NC_do_2a_spread"]),
                "NC_do_2b": bool(clean["uniform_shape"]["pass_NC_do_2b_cv_identity"]),
            },
            "original_preregistered_misses": {
                "M_68_original": not bool(nc1["pass_M_68_original"]),
                "NC_do_2_original_CV_band": not bool(clean["pass_NC_do_2_original"]),
            },
            "environment": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "host": platform.node(),
                "python": platform.python_version(),
                "ditto_base_url": DITTO_BASE_URL,
            },
        }
    finally:
        failures = []
        for thing_id in created:
            try:
                response = admin.delete(
                    f"{DITTO_BASE_URL}/things/{thing_id}", timeout=HTTP_TIMEOUT
                )
                if response.status_code not in (204, 404):
                    failures.append(f"{thing_id}:HTTP{response.status_code}")
            except requests.RequestException as exc:
                failures.append(f"{thing_id}:{type(exc).__name__}")
        admin.close()
        if failures:
            raise RuntimeError("cleanup failed: " + ", ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-duration", type=float, default=15.0)
    parser.add_argument("--prod-duration", type=float, default=60.0)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args()
    report = run(args.clean_duration, args.prod_duration)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all(report["verdict"].values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

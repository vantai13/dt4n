#!/usr/bin/env python3
"""Phase L / L.4 -- send background traffic plus probe from one socket."""

from __future__ import annotations

import argparse
import json
import os
import socket
import time
from typing import Any, Dict

from measurements.owd_probe import (
    KIND_BG,
    KIND_PROBE,
    REC_TX,
    pack_packet,
    sleep_until,
)
from mininet.load_spec import (
    DESIGN_CA,
    FRAME_BG,
    FRAME_PROBE,
    MODES,
    ONOFF_DEFAULT,
    PAYLOAD_BG,
    PAYLOAD_PROBE,
    PROBE_PPS,
    aggregate_ca,
    background_pps,
    build_schedule,
    cv,
    merge_schedules,
    rho_from_rates,
    schedule_digest,
)


def _interarrival_cv(times):
    return cv([b - a for a, b in zip(times, times[1:])])


def run(
    dst_ip: str,
    port: int,
    bw_mbps: float,
    rho: float,
    mode: str,
    duration_s: float,
    seed: int,
    run_id: int,
    out_prefix: str,
    probe_pps: float = PROBE_PPS,
) -> Dict[str, Any]:
    bg_pps = background_pps(rho, bw_mbps, probe_pps)
    if bg_pps <= 0:
        raise ValueError("rho qua nho so voi toc do probe")
    mean_gap = 1.0 / bg_pps

    n_bg = max(1, int(bg_pps * float(duration_s)))
    n_pr = max(0, int(float(probe_pps) * float(duration_s))) if probe_pps > 0 else 0

    bg_gaps = build_schedule(mode, n_bg, mean_gap, seed)
    pr_gaps = (
        build_schedule("poisson", n_pr, 1.0 / float(probe_pps), int(seed) + 500000)
        if probe_pps > 0
        else []
    )
    events = merge_schedules(bg_gaps, pr_gaps)
    ca_schedule_bg = cv(bg_gaps)
    ca_schedule_agg = aggregate_ca(events)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 21)
    addr = (dst_ip, int(port))

    rec_bg = []
    rec_pr = []
    ts_bg = []
    seq_bg = 0
    seq_pr = 0
    n_late = 0
    max_late = 0.0

    t0 = time.monotonic()
    t_end = t0 + float(duration_s)
    try:
        for t_rel, is_probe in events:
            t_target = t0 + t_rel
            if t_target > t_end:
                break
            now = time.monotonic()
            if now > t_target + 0.001:
                n_late += 1
                max_late = max(max_late, now - t_target)
            else:
                sleep_until(t_target)
            t_send = time.monotonic()
            if is_probe:
                sock.sendto(
                    pack_packet(KIND_PROBE, seq_pr, t_send, run_id, PAYLOAD_PROBE),
                    addr,
                )
                rec_pr.append(REC_TX.pack(seq_pr, t_send))
                seq_pr += 1
            else:
                sock.sendto(
                    pack_packet(KIND_BG, seq_bg, t_send, run_id, PAYLOAD_BG),
                    addr,
                )
                rec_bg.append(REC_TX.pack(seq_bg, t_send))
                ts_bg.append(t_send)
                seq_bg += 1
        if time.monotonic() < t_end:
            sleep_until(t_end)
    finally:
        t1 = time.monotonic()
        sock.close()

    out_dir = os.path.dirname(os.path.abspath(out_prefix)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(out_prefix + "_bgtx.bin", "wb") as f:
        f.write(b"".join(rec_bg))
    with open(out_prefix + "_prtx.bin", "wb") as f:
        f.write(b"".join(rec_pr))

    dt = max(t1 - t0, 1e-9)
    bg_pps_actual = seq_bg / dt
    pr_pps_actual = seq_pr / dt
    meta: Dict[str, Any] = {
        "role": "load_gen",
        "config": {
            "bw_mbps": float(bw_mbps),
            "rho_nominal": float(rho),
            "mode": mode,
            "duration_s": float(duration_s),
            "seed": int(seed),
            "run_id": int(run_id),
            "probe_pps_nominal": float(probe_pps),
            "payload_bg": PAYLOAD_BG,
            "payload_probe": PAYLOAD_PROBE,
            "frame_bg": FRAME_BG,
            "frame_probe": FRAME_PROBE,
            "onoff_params": ONOFF_DEFAULT if mode == "onoff" else None,
        },
        "schedule": {
            "n_bg": n_bg,
            "n_probe": n_pr,
            "digest_bg": schedule_digest(bg_gaps),
            "digest_probe": schedule_digest(pr_gaps),
        },
        "c_a": {
            "design_target": DESIGN_CA[mode],
            "schedule_bg": ca_schedule_bg,
            "actual_bg": _interarrival_cv(ts_bg),
            "aggregate_schedule": ca_schedule_agg,
        },
        "c_s": 0.0,
        "rates": {
            "bg_pps_target": bg_pps,
            "bg_pps_actual": bg_pps_actual,
            "probe_pps_actual": pr_pps_actual,
            "rho_actual": rho_from_rates(bg_pps_actual, pr_pps_actual, bw_mbps),
            "rate_ratio": bg_pps_actual / bg_pps,
        },
        "counts": {
            "n_bg_sent": seq_bg,
            "n_probe_sent": seq_pr,
            "n_late": n_late,
            "max_late_ms": max_late * 1e3,
            "duration_s_actual": dt,
        },
    }
    with open(out_prefix + "_tx.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, sort_keys=True)
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase L load generator")
    ap.add_argument("--dst", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--bw", type=float, required=True)
    ap.add_argument("--rho", type=float, required=True)
    ap.add_argument("--mode", choices=list(MODES), required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--probe-pps", type=float, default=PROBE_PPS)
    ap.add_argument("--out-prefix", required=True)
    args = ap.parse_args()

    meta = run(
        args.dst,
        args.port,
        args.bw,
        args.rho,
        args.mode,
        args.duration,
        args.seed,
        args.run_id,
        args.out_prefix,
        args.probe_pps,
    )
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

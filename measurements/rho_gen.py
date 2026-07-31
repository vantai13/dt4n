#!/usr/bin/env python3
"""Phase T / T.5 -- live load generator for time-varying rho(t)."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from measurements.packet_player import play_events
from mininet.load_spec import (
    DESIGN_CA,
    FRAME_BG,
    FRAME_PROBE,
    PAYLOAD_BG,
    PAYLOAD_PROBE,
    PROBE_PPS,
)
from mininet.rho_schedule import (
    build_varying_schedule,
    ca_pooled_predicted,
    intensity,
    merge_with_probe,
)
from mininet.rho_spec import (
    DT_DEFAULT,
    ou_trajectory,
    sigma_from_a,
    step_trajectory,
)


def _build_traj(
    duration_s: Optional[float],
    seed: int,
    rho_bar: Optional[float],
    a: Optional[float],
    tau_rho: Optional[float],
    dt: float,
    step: Optional[Dict[str, float]],
):
    if step is not None:
        return step_trajectory(
            step["a"],
            step["b"],
            step["hold"],
            int(step["cycles"]),
            dt,
        )

    if duration_s is None:
        raise ValueError("duration_s bat buoc cho OU trajectory")
    if rho_bar is None or a is None:
        raise ValueError("rho_bar va a bat buoc cho OU trajectory")
    sigma = 0.0 if float(a) == 0.0 else sigma_from_a(rho_bar, a)
    n_steps = int(round(float(duration_s) / float(dt)))
    return ou_trajectory(rho_bar, sigma, tau_rho or 1.0, n_steps, seed, dt=dt)


def run(
    dst_ip: str,
    port: int,
    bw_mbps: float,
    mode: str,
    duration_s: Optional[float],
    seed: int,
    run_id: int,
    out_prefix: str,
    rho_bar: Optional[float] = None,
    a: Optional[float] = None,
    tau_rho: Optional[float] = None,
    dt: float = DT_DEFAULT,
    step: Optional[Dict[str, float]] = None,
    probe_pps: float = PROBE_PPS,
) -> Dict[str, Any]:
    traj = _build_traj(duration_s, seed, rho_bar, a, tau_rho, dt, step)
    duration = traj.duration_s if duration_s is None else float(duration_s)
    if abs(duration - traj.duration_s) > max(float(dt), 1e-9):
        raise ValueError("duration_s khong khop trajectory duration")

    sched = build_varying_schedule(mode, traj, bw_mbps, seed, probe_pps=probe_pps)
    events = merge_with_probe(sched, probe_pps, duration, seed)
    counts = play_events(events, dst_ip, port, duration, run_id, out_prefix)

    c_design = DESIGN_CA.get(mode)
    lam = intensity(traj, bw_mbps, probe_pps)
    pred = ca_pooled_predicted(lam, c_design) if c_design is not None else None
    meta: Dict[str, Any] = {
        "role": "rho_gen",
        "config": {
            "bw_mbps": float(bw_mbps),
            "mode": mode,
            "duration_s": duration,
            "seed": int(seed),
            "run_id": int(run_id),
            "dt": float(dt),
            "payload_bg": PAYLOAD_BG,
            "payload_probe": PAYLOAD_PROBE,
            "frame_bg": FRAME_BG,
            "frame_probe": FRAME_PROBE,
            "probe_pps_nominal": float(probe_pps),
            "rho_bar": rho_bar,
            "a": a,
            "tau_rho": tau_rho,
            "step": dict(step) if step is not None else None,
        },
        "trajectory": traj.as_dict(),
        "schedule": {
            **sched.as_dict(),
            "c_a_pooled_predicted": pred,
        },
        "counts": counts,
    }
    with open(out_prefix + "_tx.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, sort_keys=True)
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase T rho(t) load generator")
    parser.add_argument("--dst", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--bw", type=float, required=True)
    parser.add_argument("--mode", choices=("cbr", "poisson", "h2"), required=True)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--probe-pps", type=float, default=PROBE_PPS)
    parser.add_argument("--out-prefix", required=True)
    parser.add_argument("--rho-bar", type=float, default=None)
    parser.add_argument("--a", type=float, default=None)
    parser.add_argument("--tau-rho", type=float, default=None)
    parser.add_argument("--dt", type=float, default=DT_DEFAULT)
    parser.add_argument("--step-a", type=float, default=None)
    parser.add_argument("--step-b", type=float, default=None)
    parser.add_argument("--step-hold", type=float, default=None)
    parser.add_argument("--step-cycles", type=int, default=None)
    args = parser.parse_args()

    step = None
    if args.step_a is not None or args.step_b is not None:
        if args.step_a is None or args.step_b is None or args.step_hold is None or args.step_cycles is None:
            raise SystemExit("step can --step-a --step-b --step-hold --step-cycles")
        step = {
            "a": args.step_a,
            "b": args.step_b,
            "hold": args.step_hold,
            "cycles": args.step_cycles,
        }

    meta = run(
        args.dst,
        args.port,
        args.bw,
        args.mode,
        args.duration,
        args.seed,
        args.run_id,
        args.out_prefix,
        rho_bar=args.rho_bar,
        a=args.a,
        tau_rho=args.tau_rho,
        dt=args.dt,
        step=step,
        probe_pps=args.probe_pps,
    )
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

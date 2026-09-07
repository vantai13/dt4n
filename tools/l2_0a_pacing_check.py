#!/usr/bin/env python3
"""L2.0a -- reproduce docs/phase-L2/00a-addendum-F7-F8.md.

No root, no netns, no tc, no traffic. Arithmetic and a token-bucket model
written from the HTB algorithm, plus read-back of the Phase L campaign.

Separate from `tools.l2_0_audit_check` on purpose: doc 00 is signed under tag
`phase-L2-audit-signed` and its checker must keep reproducing what it claimed,
including the MAIN table this addendum retracts.

    python -m tools.l2_0a_pacing_check
    python -m tools.l2_0a_pacing_check --json OUT
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

C_BPS = 6_000_000.0
FRAME_BYTES = 1442.0                 # tools/g2_kill_test.py:50
PHASE_L_FRAME_BYTES = 1512.0         # docs/phase-L/02-probe-validation.md:44
STAGE2_BURST_BYTES = 1600.0          # docs/phase-L/01-infra.md:40
BFIFO_BYTES = 19_656.0               # docs/phase-L/01-infra.md:41
ZERO_LOAD_BW6_MS = 0.1407            # docs/phase-L/02-probe-validation.md:37

S_MS = FRAME_BYTES * 8.0 / C_BPS * 1000.0
S_PHASE_L_MS = PHASE_L_FRAME_BYTES * 8.0 / C_BPS * 1000.0


def tb_departures(rho: float, burst_frames: int, n_pkts: int = 60_000,
                  g_us: float = 0.0) -> np.ndarray:
    """Departure times (ms) of a BACKLOGGED source through one token bucket.

    Written from the HTB algorithm: tokens accrue at `r`, capped at `burst`;
    a backlogged class dequeues whenever tokens >= L, else arms a watchdog.

    The bucket starts FULL, which is the case most favourable to a burst. That
    is the whole point: even then the burst is a ONE-TIME transient, because a
    backlogged source never lets the bucket refill.
    """
    r = rho * C_BPS / 8.0
    cap = burst_frames * FRAME_BYTES
    tok, t = cap, 0.0
    g = g_us * 1e-6
    out = np.empty(n_pkts)
    for i in range(n_pkts):
        if tok < FRAME_BYTES:
            wait = (FRAME_BYTES - tok) / r
            if g > 0.0:
                wait = float(np.ceil(wait / g) * g)
            t += wait
            tok = min(cap, tok + r * wait)
        tok -= FRAME_BYTES
        out[i] = t * 1000.0
    return out


def gap_cv(departures: np.ndarray, skip: int = 500) -> tuple:
    gaps = np.diff(departures[skip:])
    return float(gaps.std() / gaps.mean()), float(gaps.mean())


def transient_frames(burst_frames: int) -> int:
    """Frames released back-to-back at t=0, before the bucket runs dry."""
    return int(burst_frames)


def watchdog_frames_per_wake(rho: float, g_us: float) -> float:
    return rho * C_BPS / 8.0 * g_us * 1e-6 / FRAME_BYTES


def g_us_needed_for_one_frame(rho: float) -> float:
    """Timer granularity at which HTB would release a whole frame per wake."""
    return FRAME_BYTES / (rho * C_BPS / 8.0) * 1e6


def residual_service_ms(rho: float, s_ms: float = S_MS) -> float:
    """The rho*s/2 term -- ONLY real if the server serialises. It does not here."""
    return rho * s_ms / 2.0


def stage2_queue_under_paced_input() -> float:
    """Stage 2 fed a paced stream at rho*C < C.

    Tokens accrue at C and are spent at rho*C, so the bucket saturates at its
    cap. `STAGE2_BURST_BYTES > FRAME_BYTES`, so every frame finds credit and
    leaves at once. Backlog is identically zero for every rho < 1.
    """
    assert STAGE2_BURST_BYTES > FRAME_BYTES
    return 0.0


def hybrid_overshoot(rho_bar: float, sigma_fast: float, dt_fast_ms: float = 10.0,
                     horizon_ms: float = 120_000.0, seed: int = 3) -> tuple:
    """Stage-1 rate modulated at `dt_fast`; stage 2 drains at C with a bfifo.

    Fluid model at window granularity -- enough for the mean, not for quantiles.
    Shows that F8 binds POINTWISE: a queue forms exactly when rho(t) > 1.
    """
    rng = np.random.default_rng(seed)
    n = int(horizon_ms / dt_fast_ms)
    rho_t = np.clip(rho_bar + sigma_fast * rng.standard_normal(n), 0.0, None)
    drain = C_BPS / 8.0 * dt_fast_ms / 1000.0
    q, delays = 0.0, np.empty(n)
    for k, r in enumerate(rho_t):
        q = min(BFIFO_BYTES, max(0.0, q + r * drain - drain))
        delays[k] = q * 8.0 / C_BPS * 1000.0
    return float(delays.mean()), float(np.mean(rho_t > 1.0))


def phase_l_cbr_excess(fit_path: str) -> dict:
    """cbr IS the paced regime (c_a = 0.004). What did it actually measure?"""
    with open(fit_path, "r", encoding="utf-8") as handle:
        fit = json.load(handle)
    rho_all = fit["rho_all"]
    y = fit["links"]["cbr|6|13"]["delay_observed"]
    out = {}
    for r in (0.60, 0.80, 0.90, 0.95):
        i = rho_all.index(r)
        out[str(r)] = {
            "measured_ms": y[i],
            "excess_over_floor_ms": y[i] - ZERO_LOAD_BW6_MS,
            "residual_service_prediction_ms": residual_service_ms(r, S_PHASE_L_MS),
        }
    i60, i95 = rho_all.index(0.60), rho_all.index(0.95)
    out["r_measured"] = y[i95] / y[i60]
    out["r_if_residual_service"] = 0.95 / 0.60
    return out


BURST_GRID = (1, 4, 12, 50)
RHO_GRID = (0.60, 0.90)
G_US_GRID = (1.0, 10.0, 50.0, 100.0, 1000.0, 4000.0)
SIGMA_FAST_GRID = (0.0, 0.05, 0.10, 0.20, 0.30)


def build_report(fit_path: str) -> dict:
    pacing = {}
    for bf in BURST_GRID:
        for rho in RHO_GRID:
            cv, mean_gap = gap_cv(tb_departures(rho, bf))
            pacing["b%d_rho%.2f" % (bf, rho)] = {
                "cv_gap": cv,
                "mean_gap_ms": mean_gap,
                "paced_gap_ms": S_MS / rho,
                "transient_frames": transient_frames(bf),
            }
    watchdog = {
        "g_us_needed_for_one_frame_rho090": g_us_needed_for_one_frame(0.90),
        "kernel": "6.8.0-1066-gcp, CONFIG_HZ=1000, CONFIG_HIGH_RES_TIMERS=y, "
                  "psched clock_res 1e9 ns",
        "grid": {str(g): {"frames_per_wake": watchdog_frames_per_wake(0.90, g),
                          "cv_gap": gap_cv(tb_departures(0.90, 12, 20_000, g))[0]}
                 for g in G_US_GRID},
    }
    hybrid = {}
    for sf in SIGMA_FAST_GRID:
        d60, _ = hybrid_overshoot(0.60, sf)
        d90, _ = hybrid_overshoot(0.90, sf)
        d95, frac = hybrid_overshoot(0.95, sf)
        hybrid[str(sf)] = {
            "delay_060_ms": d60, "delay_090_ms": d90, "delay_095_ms": d95,
            "frac_rho_over_one_at_095": frac,
            "r": d95 / d60 if d60 > 1e-9 else None,
        }
    return {
        "schema": "dt4n.phase_l2.pacing_check.v1",
        "constants": {"s_ms": S_MS, "s_phase_l_ms": S_PHASE_L_MS,
                      "stage2_burst_bytes": STAGE2_BURST_BYTES,
                      "frame_bytes": FRAME_BYTES},
        "f7_pacing": pacing,
        "f7_watchdog": watchdog,
        "f9_stage2_queue_under_paced_input_ms": stage2_queue_under_paced_input(),
        "f9_phase_l_cbr": phase_l_cbr_excess(fit_path),
        "f10_hybrid_overshoot": hybrid,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", default="results/LIVE/phase-L/link_model_v2_fit.json")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    rep = build_report(args.fit)

    print("L2.0a pacing check -- NO MEASUREMENT")
    print("\n[F7] backlogged source through a token bucket: is the output bursty?")
    print("     %-6s %5s %11s %13s %13s %11s"
          % ("burst", "rho", "CV(gap)", "mean gap ms", "paced s/rho", "transient"))
    for bf in BURST_GRID:
        for rho in RHO_GRID:
            v = rep["f7_pacing"]["b%d_rho%.2f" % (bf, rho)]
            print("     %-6d %5.2f %11.6f %13.5f %13.5f %11d"
                  % (bf, rho, v["cv_gap"], v["mean_gap_ms"], v["paced_gap_ms"],
                     v["transient_frames"]))

    w = rep["f7_watchdog"]
    print("\n[F7] watchdog granularity -- the only thing that could save ON-OFF")
    print("     need g >= %.0f us for one frame per wake at rho=0.90"
          % w["g_us_needed_for_one_frame_rho090"])
    print("     kernel: %s" % w["kernel"])
    print("     %-9s %16s %11s" % ("g (us)", "frames/wake", "CV(gap)"))
    for g, v in w["grid"].items():
        print("     %-9s %16.4f %11.6f" % (g, v["frames_per_wake"], v["cv_gap"]))

    print("\n[F9] does the residual-service term rho*s/2 exist here?")
    c = rep["f9_phase_l_cbr"]
    print("     stage-2 backlog under paced input = %.3f ms (bucket saturates)"
          % rep["f9_stage2_queue_under_paced_input_ms"])
    print("     %-6s %13s %17s %24s"
          % ("rho", "cbr measured", "excess over floor", "rho*s/2 would demand"))
    for r in ("0.6", "0.8", "0.9", "0.95"):
        v = c[r]
        print("     %-6s %13.4f %17.4f %24.4f"
              % (r, v["measured_ms"], v["excess_over_floor_ms"],
                 v["residual_service_prediction_ms"]))
    print("     R measured = %.4f | R if residual service = %.4f"
          % (c["r_measured"], c["r_if_residual_service"]))

    print("\n[F10] F8 binds POINTWISE: queue forms exactly when rho(t) > 1")
    print("     %-11s %13s %10s %10s %10s %10s"
          % ("sigma_fast", "%rho(t)>1", "d(0.60)", "d(0.90)", "d(0.95)", "R"))
    for sf, v in rep["f10_hybrid_overshoot"].items():
        r = v["r"]
        print("     %-11s %12.1f%% %10.4f %10.4f %10.4f %10s"
              % (sf, v["frac_rho_over_one_at_095"] * 100, v["delay_060_ms"],
                 v["delay_090_ms"], v["delay_095_ms"],
                 "undef" if r is None else "%.1f" % r))

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        print("\nwrote %s" % out)


if __name__ == "__main__":
    main()

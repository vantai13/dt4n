#!/usr/bin/env python3
"""L2.0 -- reproduce every derived number in docs/phase-L2/00-mechanism-gap-audit.md.

L2.0 is an AUDIT lesson: no root, no netns, no tc, no traffic. This module only
does arithmetic on constants that are quoted from files, plus a phase-average of
a deterministic sawtooth. It exists so the audit's numbers are reproducible
rather than asserted.

Constants are transcribed from source WITH the file:line they came from. Do not
retype them from memory; that is the failure this lesson is meant to catch.

    python -m tools.l2_0_audit_check            # print the audit tables
    python -m tools.l2_0_audit_check --json OUT # write the artifact
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

# --- Phase L stage-2 constants -------------------------------------------
# docs/phase-L/01-infra.md:40  "htb rate 6mbit burst 1600b cburst 1600b"
C_BPS = 6_000_000.0
STAGE2_BURST_BYTES = 1600.0
# docs/phase-L/01-infra.md:41  "bfifo limit 19656"  (= 13 x 1512 B, line 71)
BFIFO_BYTES = 19_656.0
# docs/phase-L/02-probe-validation.md:44  "8 goi 1470 B payload (= 1512 B tai qdisc)"
PHASE_L_FRAME_BYTES = 1512.0

# --- Phase G' constants ---------------------------------------------------
# tools/g2_kill_test.py:50  FRAME_BYTES = 1442
FRAME_BYTES = 1442.0
# tools/g2_kill_test.py:49  QDISC_LIMIT_FRAMES = 300
STAGE1_PFIFO_FRAMES = 300
# tools/g2_kill_test.py:92  burst = f"{FRAME_BYTES}b"  -> exactly one frame
G2_STAGE1_BURST_FRAMES = 1

# --- Phase L measured anchors --------------------------------------------
# docs/phase-L/02-probe-validation.md:25  V-L0 noise floor
FLOOR_MEAN_MS = 0.1453
FLOOR_SD_MS = 0.1186
# docs/phase-L/02-probe-validation.md:37  V-L2 zero-load OWD at bw=6, q=13
ZERO_LOAD_BW6_MS = 0.1407

S_MS = FRAME_BYTES * 8.0 / C_BPS * 1000.0            # 1.92267 ms per frame
BETA_MS = STAGE2_BURST_BYTES * 8.0 / C_BPS * 1000.0  # 2.13333 ms of burst credit

PROBE_PPS = 20.0          # docs/phase-L/99-gate-decision.md:48  V-L7
DURATION_S = 60.0
REPS = 3


def vmax_ms(n_frames: int) -> float:
    """Departure time of the LAST frame of a stage-1 batch of `n_frames`.

    The staircase is the one MEASURED in docs/phase-L/02-probe-validation.md:47-50:

        d_k = ((k - 1) * L - B2) / C     clamped at 0

    Note the `(k-1)`: HTB dequeues while tokens are still positive and lets them
    go negative, so a 1600 B bucket passes TWO 1512 B frames free, not one. That
    off-by-one is the difference between a prediction that matches the measured
    table and one that does not.
    """
    return max(0.0, (n_frames - 1) * S_MS - BETA_MS)


def delay_q_ms(rho: float, n_frames: int) -> float:
    """Time-average stage-2 queueing delay under DETERMINISTIC on-off input.

        delay_q(rho, n) = rho * max(0, (n-1)s - beta)^2 / (2 n s)

    Derivation: stage 1 emits `n` frames back-to-back every T = n*s/rho ms.
    Stage 2 drains them, so the virtual waiting time is the sawtooth
    V(t) = max(0, vmax - t) on [0, T). A Poisson probe sees its time average
    (PASTA), which is vmax^2 / (2T).

    The `beta` term is the stage-2 burst credit. Dropping it -- as the planning
    note did -- inflates the prediction by +152% at n=4 and +24% at n=12, while
    leaving the ratio R unchanged because beta sits in the rho-independent
    prefactor.
    """
    if n_frames <= 1:
        return 0.0
    return rho * vmax_ms(n_frames) ** 2 / (2.0 * n_frames * S_MS)


def amplification_ratio(delay_by_rho: dict) -> float:
    """R = delay_q(0.95) / delay_q(0.60), the discriminator of L2.0b.

    deterministic on-off -> 0.95/0.60           = 1.583   (beta cancels)
    M/D/1 Kingman        -> [.95/(2*.05)]/[.60/(2*.40)] = 12.667

    Returns nan, never 0, when the denominator is non-positive: a 0 here would
    make the gate `R <= 3.0` PASS by dividing by nothing.
    """
    lo = delay_by_rho.get(0.60, 0.0)
    hi = delay_by_rho.get(0.95, 0.0)
    if lo <= 0.0:
        return float("nan")
    return float(hi / lo)


def sawtooth_stats(rho: float, n_frames: int, horizon_ms: float = 1.2e6,
                   seed: int = 7) -> tuple:
    """Poisson-sample the sawtooth. Independent check on `delay_q_ms`, and the
    source of the SD used for the sampling-adequacy calculation."""
    vm = vmax_ms(n_frames)
    if vm <= 0.0:
        return 0.0, 0.0, 0
    rng = np.random.default_rng(seed)
    period = n_frames * S_MS / rho
    gaps = rng.exponential(1000.0 / PROBE_PPS, int(horizon_ms * PROBE_PPS / 1000.0))
    t = np.cumsum(gaps)
    t = t[t < horizon_ms]
    v = np.maximum(0.0, vm - np.mod(t, period))
    return float(v.mean()), float(v.std()), int(v.size)


def stage1_head_of_line_ms(rho: float, frames: int = STAGE1_PFIFO_FRAMES) -> float:
    """Delay a probe eats if it is injected BEHIND the backlogged blast source
    at stage 1. `blast_source.py:29` sets blocking sends, so the stage-1 pfifo
    (`g2_kill_test.py:95`, limit 300 frames) sits FULL for the whole run."""
    return frames * FRAME_BYTES * 8.0 / (rho * C_BPS) * 1000.0


def phase_l_measured_ratios(fit_path: str) -> dict:
    """R computed from the Phase L campaign that ALREADY RAN. No new measurement."""
    with open(fit_path, "r", encoding="utf-8") as handle:
        fit = json.load(handle)
    rho_all = fit["rho_all"]
    i60, i95 = rho_all.index(0.60), rho_all.index(0.95)
    out = {}
    for mode in ("cbr", "poisson", "h2", "onoff"):
        link = fit["links"]["%s|6|13" % mode]
        y = link["delay_observed"]
        loss = link["loss_observed"]
        lo, hi = y[i60], y[i95]
        excess_lo = lo - ZERO_LOAD_BW6_MS
        out[mode] = {
            "delay_060_ms": lo,
            "delay_095_ms": hi,
            "r_raw": hi / lo,
            "r_excess_over_floor": (hi - ZERO_LOAD_BW6_MS) / excess_lo
            if excess_lo > 1e-9 else float("nan"),
            "excess_over_floor_060_ms": excess_lo,
            "loss_095": loss[i95],
            "c_a": fit["ca_counterexample"][mode]["ca_mean"]
            if isinstance(fit.get("ca_counterexample"), dict)
            and mode in fit.get("ca_counterexample", {}) else None,
        }
    return out


R_DETERMINISTIC = 0.95 / 0.60
R_MD1 = (0.95 / (2 * 0.05)) / (0.60 / (2 * 0.40))

RHO_GRID = (0.60, 0.80, 0.90, 0.95)
BURST_GRID = (1, 2, 4, 8, 12)
BURST_OVF = 26


def build_report(fit_path: str = "results/LIVE/phase-L/link_model_v2_fit.json") -> dict:
    grid = {}
    for n in BURST_GRID:
        row = {}
        for rho in RHO_GRID:
            mean, sd, count = sawtooth_stats(rho, n)
            se = sd / np.sqrt(PROBE_PPS * DURATION_S * REPS) if sd > 0 else 0.0
            row[str(rho)] = {
                "analytic_ms": delay_q_ms(rho, n),
                "sim_ms": mean,
                "sim_sd_ms": sd,
                "se_3reps_ms": float(se),
                "planning_note_ms": 0.0 if n <= 1
                else rho * (n - 1) ** 2 * S_MS / (2.0 * n),
            }
        grid[str(n)] = row

    r_by_burst = {}
    for n in BURST_GRID:
        d = {r: delay_q_ms(r, n) for r in (0.60, 0.95)}
        r_by_burst[str(n)] = amplification_ratio(d)

    peak = {str(n): (n - 1) * FRAME_BYTES for n in list(BURST_GRID) + [BURST_OVF]}
    return {
        "schema": "dt4n.phase_l2.audit_check.v1",
        "constants": {
            "c_bps": C_BPS,
            "frame_bytes": FRAME_BYTES,
            "s_ms": S_MS,
            "stage2_burst_bytes": STAGE2_BURST_BYTES,
            "beta_ms": BETA_MS,
            "bfifo_bytes": BFIFO_BYTES,
            "bfifo_frames_at_1442": int(BFIFO_BYTES // FRAME_BYTES),
            "floor_mean_ms": FLOOR_MEAN_MS,
            "zero_load_bw6_ms": ZERO_LOAD_BW6_MS,
        },
        "grid": grid,
        "r_by_burst": r_by_burst,
        "r_reference": {"deterministic": R_DETERMINISTIC, "md1_kingman": R_MD1,
                        "separation": R_MD1 / R_DETERMINISTIC},
        "stage1_head_of_line_ms": {str(r): stage1_head_of_line_ms(r)
                                   for r in RHO_GRID},
        "peak_stage2_backlog_bytes": peak,
        "phase_l_measured": phase_l_measured_ratios(fit_path),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", default="results/LIVE/phase-L/link_model_v2_fit.json")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    rep = build_report(args.fit)

    print("L2.0 audit check -- NO MEASUREMENT, arithmetic only")
    c = rep["constants"]
    print("  s = %.5f ms/frame   beta = %.5f ms   bfifo holds %d frames of %d B"
          % (c["s_ms"], c["beta_ms"], c["bfifo_frames_at_1442"], c["frame_bytes"]))

    print("\n[1] Phase L MEASURED R = delay(0.95)/delay(0.60), bw=6 q=13")
    print("    (source: results/LIVE/phase-L/link_model_v2_fit.json, no new run)")
    print("    %-8s %9s %9s %8s %9s" % ("mode", "d(0.60)", "d(0.95)", "R", "loss@.95"))
    for mode, v in rep["phase_l_measured"].items():
        print("    %-8s %9.4f %9.4f %8.3f %9.4f"
              % (mode, v["delay_060_ms"], v["delay_095_ms"], v["r_raw"], v["loss_095"]))
    print("    reference: deterministic %.3f | M/D/1 %.3f | separation %.1fx"
          % (rep["r_reference"]["deterministic"], rep["r_reference"]["md1_kingman"],
             rep["r_reference"]["separation"]))

    print("\n[2] Predicted stage-2 delay under deterministic on-off (MAIN arm)")
    print("    %-3s %5s %10s %9s %14s" % ("n", "rho", "corrected", "sim", "planning note"))
    for n in BURST_GRID:
        for rho in RHO_GRID:
            cell = rep["grid"][str(n)][str(rho)]
            print("    %-3d %5.2f %10.4f %9.4f %14.4f"
                  % (n, rho, cell["analytic_ms"], cell["sim_ms"],
                     cell["planning_note_ms"]))

    print("\n[3] R by stage-1 burst (beta cancels -> constant)")
    for n, r in rep["r_by_burst"].items():
        print("    n=%-3s R = %s" % (n, "nan" if r != r else "%.4f" % r))

    print("\n[4] Probe injected behind the blast source at stage 1 would measure")
    for rho, ms in rep["stage1_head_of_line_ms"].items():
        print("    rho=%s -> %.1f ms of STAGE-1 queue" % (rho, ms))

    print("\n[5] Peak stage-2 backlog vs bfifo %d B" % int(c["bfifo_bytes"]))
    for n, b in rep["peak_stage2_backlog_bytes"].items():
        print("    n=%-3s peak=%8.0f B  %s"
              % (n, b, "OVERFLOW" if b > c["bfifo_bytes"] else "fits"))

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        print("\nwrote %s" % out)


if __name__ == "__main__":
    main()

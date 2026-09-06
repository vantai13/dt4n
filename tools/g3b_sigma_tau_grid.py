#!/usr/bin/env python3
"""G'.3b -- sigma/tau round-trip and ORTHOGONALITY on the live path.

Preregistered in `docs/phase-G/65-prereg-g3b-sigma-tau-roundtrip.md`,
tag `phase-G2-g3b-prereg`, signed before any data.

WHY THIS EXISTS
    `G'.2` bounded contamination at omega = 0 (nothing manufactured).
    `G'.3a` recovered a known omega (claim A transported).
    NEITHER touched claim B (tau) or claim C (sigma), and neither asked the
    question the whole phase rests on: are sigma and tau INDEPENDENT KNOBS
    once the signal has crossed kernel, qdisc, NIC and /proc/net/dev?

    The generator makes them independent BY DEFINITION -- sigma multiplies,
    tau lives inside phi. That is a statement about `rate_modulator`, not
    about the measured path. This tool measures the path.

DESIGN
    omega = 0 at every cell, so the eight links are INDEPENDENT replicates
    of the same (sigma, tau) measurement: one run yields eight estimates.
    dt = 0.1 s at every cell, so the G'.4 certificate stays valid (NT 55);
    the lag window is scaled by tau instead (gate T-5).

Run as root, through the sdn_rl interpreter:

    sudo -n /home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m tools.g3b_sigma_tau_grid --dry
    sudo -n ... -m tools.g3b_sigma_tau_grid --setup
    sudo -n ... -m tools.g3b_sigma_tau_grid --run
    sudo -n ... -m tools.g3b_sigma_tau_grid --teardown
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from mininet.byte_sampler import sample
from mininet.rate_controller import drive
from tools.artifact_guard import write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools import g3_dryrun
from tools.g2_kill_test import (
    BacklogMonitor, IFACE, chown_back, peer_rx_bytes,
    setup, start_traffic, teardown,
)
from tools.g3_dryrun import CAP_BPS, LINKS, physical_trace
from tools.g2_topology import a0_from_sigma_at
from tools.g3b_bias_sim import LAG_LO, LAG_SPAN, V_NUGGET, n_lags_for
from tools.measurement_path_calib import estimate_nugget

OUTDIR = Path("results/SMOKE/phase-G2")
SCHEMA = "dt4n.phase_g2.g3b_sigma_tau.v1"

DT_S = 0.1
OMEGA = 0.0
T_OVER_TAU = 205.0
FRAME_BYTES = 1442
SEED = 2026_09_06

#            (tau_s, sigma_ref, n_replicates)
GRID = ((2.0, 0.028, 2), (2.0, 0.045, 2),
        (5.0, 0.028, 2), (5.0, 0.045, 2),
        (30.0, 0.036, 1))

GATE_SIGMA = 0.10       # RT-C1, claim C
GATE_TAU = 0.20         # RT-B1, claim B
GATE_ORTHO_TAU = 0.10   # RT-O1
GATE_ORTHO_SIGMA = 0.05 # RT-O2
GATE_CLIP = 0.01        # C-1
GATE_SF_MIN = 0.8264    # B-1a
GATE_SINK = 0.02        # S-1
GATE_UNDERRUN = 0.001   # K-2
GATE_LAG_SPAN = 0.30    # T-5

# ★ `g3_dryrun.ar1` reads the MODULE-level DT_S, not a caller argument
#   (`G-L101`; it invalidated run 1 of the kill test). Bind it once, then
#   VERIFY the realised phi rather than trusting the binding.
g3_dryrun.DT_S = DT_S


def assert_realised_tau(tau_s: float) -> None:
    """Probe the actual recurrence without finite-sample ACF uncertainty."""
    class ImpulseRng:
        first = True

        def standard_normal(self, size):
            value = np.ones(size) if self.first else np.zeros(size)
            self.first = False
            return value

    probe = g3_dryrun.ar1(1, tau_s, 4, ImpulseRng())[0]
    phi = float(probe[1] / probe[0])
    tau_eff = -DT_S / np.log(phi)
    if not np.isclose(tau_eff, tau_s, rtol=1e-10):
        raise RuntimeError(
            f"G-L101 guard: generator realises tau_eff={tau_eff:.3f} s for a "
            f"requested {tau_s:.3f} s. The dt binding did not take effect.")


def run_cell(tau_s: float, sigma_ref: float, n_rep: int, rng,
             checkpoint_dir: Path | None = None) -> dict:
    n_link = len(LINKS)
    n_win = int(round(T_OVER_TAU * tau_s / DT_S))
    n_lags = n_lags_for(tau_s, DT_S)
    a0 = a0_from_sigma_at("uA", sigma_ref)
    assert_realised_tau(tau_s)

    reps = []
    for rep in range(n_rep):
        print(f"START tau={tau_s:g} sigma={sigma_ref:g} rep={rep+1}/{n_rep} "
              f"duration={n_win * DT_S:g}s UTC={datetime.now(timezone.utc).isoformat()}",
              flush=True)
        trace = physical_trace(OMEGA, tau_s, tau_s, n_win, rng, a0=a0)
        rho_target = trace["rho_target"].T                  # (n_win, n_link)

        monitor = BacklogMonitor(IFACE)
        rx0 = [peer_rx_bytes(i) for i in range(n_link)]
        out: dict = {}

        def controller() -> None:
            out["ctl"] = drive(rho_target, IFACE, CAP_BPS, FRAME_BYTES, DT_S)

        def sampler() -> None:
            rho, late, span = sample(IFACE, n_win, DT_S, CAP_BPS)
            out["rho"] = rho
            out["smp"] = {
                "delta_p95_s": float(np.percentile(late, 95)),
                "delta_rms_s": float(np.sqrt((late ** 2).mean())),
                "read_span_p95_s": float(np.percentile(span, 95)),
            }

        monitor.start()
        t_ctl = threading.Thread(target=controller)
        t_smp = threading.Thread(target=sampler)
        t0 = time.perf_counter()
        t_ctl.start(); t_smp.start()
        t_ctl.join(); t_smp.join()
        wall = time.perf_counter() - t0
        monitor.stop_flag.set(); monitor.join(timeout=2)
        rx1 = [peer_rx_bytes(i) for i in range(n_link)]

        rho = out["rho"]
        fits = [estimate_nugget(rho[:, i], DT_S, n_lags, lag_lo=LAG_LO)
                for i in range(n_link)]
        set_mean = rho_target.mean(axis=0) * CAP_BPS
        reps.append({
            "replicate": rep,
            "wall_s": wall,
            "controller": out["ctl"],
            "sampler": out["smp"],
            "backlog": monitor.summary(IFACE),
            "clip_fractions": {k: float(trace[k]) for k in
                               ("component_clip_fraction", "path_clip_fraction",
                                "private_clip_fraction", "target_clip_fraction")},
            "sink_rate_ratio": [float((rx1[i] - rx0[i]) * 8.0 / wall / set_mean[i])
                                for i in range(n_link)],
            "tau_hat_per_link": [f.get("tau_from_fit_s", np.nan) for f in fits],
            "sigma_hat_per_link": [f.get("sigma_true", np.nan) for f in fits],
            "sf_per_link": [f.get("sf", np.nan) for f in fits],
            "estimator_fits": fits,
            "sigma_target_per_link": (
                a0 * np.sqrt(g3_dryrun.DEGREE) / CAP_BPS).tolist(),
            "_rho": rho,
            "_target": rho_target,
        })
        if checkpoint_dir is not None:
            stem = checkpoint_dir / f"t{tau_s:g}_s{sigma_ref:g}_rep{rep}"
            save_series(Path(str(stem) + ".npz"), rho=rho, target=rho_target,
                        tau_s=tau_s, sigma_ref=sigma_ref, dt_s=DT_S)
            write_contract_artifact(Path(str(stem) + ".json"),
                                    {k: v for k, v in reps[-1].items()
                                     if not k.startswith("_")})
        print(f"DONE tau={tau_s:g} sigma={sigma_ref:g} rep={rep+1} "
              f"tau_hat={np.median(reps[-1]['tau_hat_per_link']):.5f} "
              f"wall={wall:.1f}s", flush=True)

    tau_all = np.array([r["tau_hat_per_link"] for r in reps], float)
    sig_all = np.array([r["sigma_hat_per_link"] for r in reps], float)
    sig_tgt = np.array(reps[0]["sigma_target_per_link"], float)
    sf_all = np.array([r["sf_per_link"] for r in reps], float)

    # ★ sigma is PER LINK (sigma_l = a0*sqrt(d_l)/C_l), so the ratio must be
    #   formed per link BEFORE aggregating. Comparing a pooled sigma_hat to a
    #   single sigma_ref would mix a factor-1.5 design spread into the error.
    sigma_ratio = sig_all / sig_tgt[None, :]

    return {
        "tau_s": tau_s, "sigma_ref": sigma_ref, "omega": OMEGA,
        "n_replicates": n_rep, "n_windows": n_win, "n_lags": n_lags,
        "lag_span_over_tau": n_lags * DT_S / tau_s,
        "quantisation_headroom_min": float(np.min(
            sig_tgt / ((8 * FRAME_BYTES) / (CAP_BPS * DT_S * np.sqrt(12))))),
        "all_estimates_finite": bool(np.isfinite(tau_all).all()
                                     and np.isfinite(sig_all).all()
                                     and np.isfinite(sf_all).all()),
        "T_run_s": n_win * DT_S,
        "tau_hat_median": float(np.nanmedian(tau_all)),
        "tau_rel_error": float(np.nanmedian(tau_all) / tau_s - 1.0),
        "tau_hat_per_link_median": np.nanmedian(tau_all, axis=0).tolist(),
        "sigma_ratio_median": float(np.nanmedian(sigma_ratio)),
        "sigma_rel_error": float(np.nanmedian(sigma_ratio) - 1.0),
        "sigma_ratio_per_link_median": np.nanmedian(sigma_ratio, axis=0).tolist(),
        "sf_min_over_links": float(np.nanmin(np.nanmedian(sf_all, axis=0))),
        "sf_per_link_median": np.nanmedian(sf_all, axis=0).tolist(),
        "max_target_clip": max(r["clip_fractions"]["target_clip_fraction"]
                               for r in reps),
        "max_abs_sink_error": max(abs(x - 1.0) for r in reps
                                  for x in r["sink_rate_ratio"]),
        "max_underrun": max(r["backlog"]["underrun_fraction"] for r in reps),
        "max_delta_rms_s": max(r["controller"]["delta_rms_s"] for r in reps),
        "replicates": [{k: v for k, v in r.items() if not k.startswith("_")}
                       for r in reps],
        "_series": np.stack([r["_rho"] for r in reps]),
        "_targets": np.stack([r["_target"] for r in reps]),
    }


def orthogonality(cells: list[dict]) -> dict:
    """Sensitivity of each estimate to the OTHER axis, on the 2x2 sub-grid.

    Reported as a log-log slope so it is dimensionless and comparable to the
    relative-error budgets that set the gates.
    """
    grid = {(c["tau_s"], c["sigma_ref"]): c for c in cells}
    taus, sigmas = (2.0, 5.0), (0.028, 0.045)
    if not all((t, s) in grid for t in taus for s in sigmas):
        return {"available": False}

    d_log_sigma = np.log(sigmas[1] / sigmas[0])
    d_log_tau = np.log(taus[1] / taus[0])

    # RT-O1: tau_hat trôi bao nhiêu khi ĐỔI sigma, trung bình trên hai mức tau
    slope_tau = float(np.mean([
        np.log(grid[(t, sigmas[1])]["tau_hat_median"]
               / grid[(t, sigmas[0])]["tau_hat_median"]) / d_log_sigma
        for t in taus]))
    # RT-O2: sigma_hat/sigma trôi bao nhiêu khi ĐỔI tau
    slope_sigma = float(np.mean([
        np.log(grid[(taus[1], s)]["sigma_ratio_median"]
               / grid[(taus[0], s)]["sigma_ratio_median"]) / d_log_tau
        for s in sigmas]))
    return {
        "available": True,
        "d_log_tau_hat_d_log_sigma": slope_tau,
        "d_log_sigma_ratio_d_log_tau": slope_sigma,
    }


def adjudicate(cells: list[dict], ortho: dict) -> dict:
    small = [c for c in cells if c["tau_s"] <= 5.0]
    gates = {
        "complete_grid": len(cells) == len(GRID),
        "finite_estimates": all(c.get("all_estimates_finite", False) for c in cells),
        "RT-C1": all(abs(c["sigma_rel_error"]) <= GATE_SIGMA for c in cells),
        "RT-B1_small_tau": all(abs(c["tau_rel_error"]) <= GATE_TAU
                               for c in small),
        "RT-B1_tau30": all(abs(c["tau_rel_error"]) <= GATE_TAU
                           for c in cells if c["tau_s"] > 5.0),
        "RT-O1": (abs(ortho.get("d_log_tau_hat_d_log_sigma", np.inf))
                  <= GATE_ORTHO_TAU),
        "RT-O2": (abs(ortho.get("d_log_sigma_ratio_d_log_tau", np.inf))
                  <= GATE_ORTHO_SIGMA),
        "T-5": all(c["lag_span_over_tau"] >= GATE_LAG_SPAN for c in cells),
        "Q-1": all(c["quantisation_headroom_min"] >= 4.36 for c in cells),
        "C-1": all(c["max_target_clip"] <= GATE_CLIP for c in cells),
        "B-1a": all(c["sf_min_over_links"] >= GATE_SF_MIN for c in cells),
        "S-1": all(c["max_abs_sink_error"] <= GATE_SINK for c in cells),
        "K-2": all(c["max_underrun"] <= GATE_UNDERRUN for c in cells),
    }
    # Quy tắc dừng của prereg mục 4, áp dụng NGUYÊN VĂN.
    if not gates["finite_estimates"]:
        verdict = "INVALID_ESTIMATES"
    elif not (gates["RT-C1"] and gates["RT-B1_small_tau"]):
        verdict = "STOP_MECHANISM"
    elif ortho.get("available") and not (gates["RT-O1"] and gates["RT-O2"]):
        verdict = "STOP_NOT_ORTHOGONAL"
    elif not gates["complete_grid"]:
        verdict = "INCOMPLETE"
    elif not gates["RT-B1_tau30"]:
        verdict = "LIMIT_TAU_CEILING"
    elif all(gates.values()):
        verdict = "GO"
    else:
        verdict = "GO_STAR"          # gate phụ trợ fail, ghi limit
    return {**gates, "verdict": verdict}


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--setup", action="store_true")
    mode.add_argument("--teardown", action="store_true")
    mode.add_argument("--dry", action="store_true",
                    help="analysis path only, synthetic series, no network")
    mode.add_argument("--run", action="store_true")
    ap.add_argument("--out", default=str(OUTDIR / "g3b_sigma_tau.json"))
    args = ap.parse_args()

    if args.setup:
        setup(); return
    if args.teardown:
        teardown(); return
    if args.dry:
        _dry_run(Path(args.out).with_name("g3b_dry_run.json")); return

    out = Path(args.out)
    npz = out.with_name(out.stem + "_series.npz")
    checkpoint_dir = out.with_name(out.stem + "_checkpoints")
    for path in (out, npz, checkpoint_dir):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite previous run: {path}")
    prereg_commit = subprocess.check_output(
        ["git", "rev-parse", "phase-G2-g3b-prereg^{commit}"], text=True).strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", prereg_commit, "HEAD"],
                   check=True)
    run_provenance = provenance()
    if run_provenance["worktree_dirty_at_execution"]:
        raise RuntimeError("Commit tracked changes before running preregistered data")
    bias = json.loads((OUTDIR / "g3b_bias_sim.json").read_text())
    if not bias["summary"]["all_cells_feasible"]:
        raise RuntimeError("Bias simulation has failed")
    for tau, _, _ in GRID:
        assert_realised_tau(tau)
    checkpoint_dir.mkdir(parents=True)
    chown_back(checkpoint_dir)
    started_utc = datetime.now(timezone.utc).isoformat()
    rng = np.random.default_rng(SEED)
    procs = start_traffic(sys.executable, len(LINKS))
    try:
        cells = []
        for tau, sigma, n_rep in GRID:
            cell = run_cell(tau, sigma, n_rep, rng, checkpoint_dir)
            cells.append(cell)
            interim = adjudicate(cells, orthogonality(cells))
            print(f"CELL tau={tau:g} sigma={sigma:g} "
                  f"tau_error={cell['tau_rel_error']:+.5f} "
                  f"sigma_error={cell['sigma_rel_error']:+.5f} "
                  f"interim={interim['verdict']}", flush=True)
            if interim["verdict"] in {"STOP_MECHANISM", "STOP_NOT_ORTHOGONAL",
                                      "INVALID_ESTIMATES"}:
                print("Signed stop rule reached; remaining cells not run.", flush=True)
                break
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    ortho = orthogonality(cells)
    payload = {
        "schema": SCHEMA,
        "status": "MEASURED",
        "prereg": "docs/phase-G/65-prereg-g3b-sigma-tau-roundtrip.md",
        "prereg_tag": "phase-G2-g3b-prereg",
        "provenance": run_provenance,
        "prereg_commit": prereg_commit,
        "started_utc": started_utc,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "design": {
            "dt_s": DT_S, "omega": OMEGA, "T_over_tau": T_OVER_TAU,
            "lag_lo": LAG_LO, "lag_span": LAG_SPAN, "seed": SEED,
            "grid": [list(g) for g in GRID], "host_quiesced": False,
            "estimator": "measurement_path_calib.estimate_nugget lag_lo=2",
            "bias_sim": "results/SMOKE/phase-G2/g3b_bias_sim.json",
        },
        "cells": [{k: v for k, v in c.items() if not k.startswith("_")}
                  for c in cells],
        "orthogonality": ortho,
        "gates": adjudicate(cells, ortho),
    }
    write_contract_artifact(out, payload)

    # ★ RAW SERIES: the same decision that paid for itself twice already
    #   (doc 61 found the MA(1) nugget in them; doc 64 re-adjudicated P-7
    #   off them with no rerun). Cost: a few MB.
    save_series(
        npz,
        **{f"rho_t{c['tau_s']:g}_s{c['sigma_ref']:g}": c["_series"] for c in cells},
        **{f"tgt_t{c['tau_s']:g}_s{c['sigma_ref']:g}": c["_targets"] for c in cells},
        ifaces=np.array(IFACE), cap_bps=np.asarray(CAP_BPS),
        dt_s=DT_S, omega=OMEGA, seed=SEED,
    )
    chown_back(npz)

    print(f"{'tau':>5} {'sigma':>7} {'nlag':>5} {'tau_hat':>9} {'tau_err':>9} "
          f"{'sig_ratio':>10} {'sf_min':>7} {'clip':>9}")
    for c in payload["cells"]:
        print(f"{c['tau_s']:>5.0f} {c['sigma_ref']:>7.3f} {c['n_lags']:>5} "
              f"{c['tau_hat_median']:>9.3f} {c['tau_rel_error']:>+9.3f} "
              f"{c['sigma_ratio_median']:>10.4f} {c['sf_min_over_links']:>7.4f} "
              f"{c['max_target_clip']:>9.2e}")
    print(f"\n{npz}\n{out}")
    print(json.dumps(payload["orthogonality"], indent=2))
    print(json.dumps(payload["gates"], indent=2))


def save_series(path: Path, **arrays) -> None:
    """Exclusive creation protects raw observations as well as JSON artifacts."""
    with path.open("xb") as handle:
        np.savez_compressed(handle, **arrays)
    chown_back(path)


def _dry_run(out: Path) -> None:
    """NT 52: exercise the ANALYSIS path on synthetic series, no root needed.

    This catches shape bugs, per-link sigma bugs and orthogonality-slope sign
    errors in seconds. Every one of those would otherwise be discovered after
    3.3 hours of network time.
    """
    rng = np.random.default_rng(SEED)
    cells = []
    for tau_s, sigma_ref, n_rep in GRID:
        assert_realised_tau(tau_s)
        a0 = a0_from_sigma_at("uA", sigma_ref)
        sig_tgt = a0 * np.sqrt(g3_dryrun.DEGREE) / CAP_BPS
        n_win = int(round(T_OVER_TAU * tau_s / DT_S))
        n_lags = n_lags_for(tau_s, DT_S)
        phi = np.exp(-DT_S / tau_s)
        tau_all, sig_all, sf_all = [], [], []
        for _ in range(n_rep):
            u = np.empty((n_win, len(LINKS)))
            u[0] = rng.standard_normal(len(LINKS))
            for k in range(1, n_win):
                u[k] = phi * u[k - 1] + np.sqrt(1 - phi * phi) * \
                    rng.standard_normal(len(LINKS))
            w = rng.standard_normal((n_win + 1, len(LINKS))) * np.sqrt(V_NUGGET / 2)
            rho = 0.857 + sig_tgt * u + (w[1:] - w[:-1])
            fits = [estimate_nugget(rho[:, i], DT_S, n_lags, lag_lo=LAG_LO)
                    for i in range(len(LINKS))]
            tau_all.append([f.get("tau_from_fit_s", np.nan) for f in fits])
            sig_all.append([f.get("sigma_true", np.nan) for f in fits])
            sf_all.append([f.get("sf", np.nan) for f in fits])
        ratio = np.array(sig_all) / sig_tgt[None, :]
        cells.append({
            "tau_s": tau_s, "sigma_ref": sigma_ref, "n_lags": n_lags,
            "lag_span_over_tau": n_lags * DT_S / tau_s,
            "quantisation_headroom_min": float(np.min(
                sig_tgt / ((8 * FRAME_BYTES) / (CAP_BPS * DT_S * np.sqrt(12))))),
            "all_estimates_finite": bool(np.isfinite(tau_all).all()
                                         and np.isfinite(sig_all).all()
                                         and np.isfinite(sf_all).all()),
            "tau_hat_median": float(np.nanmedian(tau_all)),
            "tau_rel_error": float(np.nanmedian(tau_all) / tau_s - 1.0),
            "sigma_ratio_median": float(np.nanmedian(ratio)),
            "sigma_rel_error": float(np.nanmedian(ratio) - 1.0),
            "sf_min_over_links": float(np.nanmin(np.nanmedian(sf_all, axis=0))),
            "max_target_clip": 0.0, "max_abs_sink_error": 0.0,
            "max_underrun": 0.0,
        })
    ortho = orthogonality(cells)
    write_contract_artifact(out, {
        "schema": "dt4n.phase_g2.g3b_dry_run.v1",
        "status": "SYNTHETIC_NO_NETWORK", "cells": cells,
        "orthogonality": ortho, "gates": adjudicate(cells, ortho),
        "provenance": provenance(),
        "note": "clip/sink/underrun are synthetic placeholders; no network evidence",
    })
    print("DRY RUN -- synthetic series, analysis path only, NO NETWORK\n")
    print(f"{'tau':>5} {'sigma':>7} {'nlag':>5} {'span/tau':>9} "
          f"{'tau_err':>9} {'sig_err':>9}")
    for c in cells:
        print(f"{c['tau_s']:>5.0f} {c['sigma_ref']:>7.3f} {c['n_lags']:>5} "
              f"{c['lag_span_over_tau']:>9.2f} {c['tau_rel_error']:>+9.3f} "
              f"{c['sigma_rel_error']:>+9.3f}")
    print()
    print(json.dumps(ortho, indent=2))
    print(json.dumps(adjudicate(cells, ortho), indent=2))


if __name__ == "__main__":
    main()

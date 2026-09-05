#!/usr/bin/env python3
"""G'.3a omega positive control: sweep omega and test whether the mechanism
TRANSPORTS a known coupling.

Preregistered in `docs/phase-G/63-prereg-g3a-omega-positive-control.md`, tagged
`phase-G2-g3a-prereg` before any data.

    sudo -n /home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m tools.g3a_omega_sweep --setup
    sudo -n ... -m tools.g3a_omega_sweep --run
    sudo -n ... -m tools.g3a_omega_sweep --teardown
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np

from tools import g3_dryrun
from tools.artifact_guard import write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_kill_test import (
    CAP_BPS, DT_S, FRAME_BYTES, IFACE, LINKS, TAU_S, T_RUN_S,
    BacklogMonitor, drive, peer_rx_bytes, sample, setup, start_traffic, teardown,
)
from tools.g3_dryrun import INCIDENCE, physical_trace
from tools.g3a_omega_estimator import design_matrix, fit_omega, rho_eps_from_series

OUT = Path("results/SMOKE/phase-G2/g3a_omega_sweep.json")
SERIES = Path("results/SMOKE/phase-G2/g3a_omega_series.npz")
SCHEMA = "dt4n.phase_g2.g3a_omega_sweep.v1"

OMEGA_GRID = (0.00, 0.25, 0.50, 0.75, 1.00)
N_REPLICATES = 3
FIT_LAGS = 8
FIT_LAG_LO = 2          # G-A019/G-L103
SEED = 2026_09_05

g3_dryrun.DT_S = DT_S   # G-L101


def sf_from_series(x: np.ndarray) -> float:
    """Intercept of the lag 2..8 log-ACF fit (the signed estimator)."""
    c = x - x.mean()
    denom = float(c @ c)
    if denom <= 0:
        return float("nan")
    r = np.array([float(c[:-k] @ c[k:]) / denom for k in range(1, FIT_LAGS + 1)])
    lags = np.arange(1, FIT_LAGS + 1)
    keep = (r > 0) & (lags >= FIT_LAG_LO)
    if keep.sum() < 3:
        return float("nan")
    slope, intercept = np.polyfit(lags[keep], np.log(r[keep]), 1)
    return float(np.exp(intercept))


def run_level(omega: float, n_win: int, rng) -> dict:
    n_link = len(LINKS)
    reps = []
    for rep in range(N_REPLICATES):
        trace = physical_trace(omega, TAU_S, TAU_S, n_win, rng)
        rho_target = trace["rho_target"].T
        monitor = BacklogMonitor(IFACE)
        rx0 = [peer_rx_bytes(i) for i in range(n_link)]
        out: dict = {}

        import threading
        t_ctl = threading.Thread(
            target=lambda: out.__setitem__(
                "controller", drive(rho_target, IFACE, CAP_BPS, FRAME_BYTES, DT_S)))

        def _sample():
            rho, late, span = sample(IFACE, n_win, DT_S, CAP_BPS)
            out["rho"] = rho
            out["sampler"] = {
                "delta_p95_s": float(np.percentile(late, 95)),
                "delta_rms_s": float(np.sqrt((late ** 2).mean())),
                "read_span_p95_s": float(np.percentile(span, 95)),
            }

        t_smp = threading.Thread(target=_sample)
        monitor.start()
        t0 = time.perf_counter()
        t_ctl.start(); t_smp.start(); t_ctl.join(); t_smp.join()
        wall = time.perf_counter() - t0
        monitor.stop_flag.set(); monitor.join(timeout=2)
        rx1 = [peer_rx_bytes(i) for i in range(n_link)]

        set_mean = rho_target.mean(axis=0) * CAP_BPS
        reps.append({
            "replicate": rep,
            "rho": out["rho"],
            "rho_target": rho_target,
            "controller": out["controller"],
            "sampler": out["sampler"],
            "backlog": monitor.summary(IFACE),
            "clip_fractions": {k: float(trace[k]) for k in
                               ("target_clip_fraction", "component_clip_fraction")},
            "sink_rate_ratio": [
                float((rx1[i] - rx0[i]) * 8.0 / wall / set_mean[i])
                for i in range(n_link)],
        })
        print(f"    omega={omega:.2f} rep {rep}: wall {wall:.1f}s "
              f"underrun {reps[-1]['backlog']['underrun_fraction']}")
    return {"omega": omega, "reps": reps}


def analyse_level(level: dict, k_tilde: np.ndarray) -> dict:
    reps = level["reps"]
    n_link = len(LINKS)
    iu = np.triu_indices(n_link, 1)
    mats = [np.corrcoef(r["rho"].T) for r in reps]
    pooled = np.tanh(np.mean(
        [np.arctanh(np.clip(m, -0.999999, 0.999999)) for m in mats], axis=0))
    np.fill_diagonal(pooled, 1.0)
    sf = np.array([np.median([sf_from_series(r["rho"][:, i]) for r in reps])
                   for i in range(n_link)])
    fit = fit_omega(pooled, k_tilde, sf)

    a_pair = np.sqrt(np.outer(sf, sf))[iu]
    rc = pooled[iu] / a_pair
    k = k_tilde[iu]
    hi, lo = k > 0.6, (k > 0.3) & (k < 0.6)
    fit["level_ratio_corrected"] = (
        float(rc[hi].mean() / rc[lo].mean())
        if abs(rc[lo].mean()) > 1e-9 else float("nan"))

    eps_stats = [rho_eps_from_series(r["rho"], r["rho_target"]) for r in reps]
    return {
        "omega": level["omega"],
        "sf_per_link": sf.tolist(),
        "sf_min_over_links": float(np.nanmin(sf)),
        "R_hat_upper": pooled[iu].tolist(),
        **fit,
        "rho_eps_max_abs": float(max(e["rho_eps_max_abs"] for e in eps_stats)),
        "rho_eps_median_abs": float(np.median(
            [e["rho_eps_median_abs"] for e in eps_stats])),
        "eps_acf1_median": float(np.median(
            [np.median(e["eps_acf1_per_link"]) for e in eps_stats])),
        "underrun_fraction": float(max(r["backlog"]["underrun_fraction"]
                                       for r in reps)),
        "max_abs_sink_ratio_error": float(max(
            abs(x - 1.0) for r in reps for x in r["sink_rate_ratio"])),
        "delta_rms_controller_s": float(np.sqrt(np.mean(
            [r["controller"]["delta_rms_s"] ** 2 for r in reps]))),
        "target_clip_fraction": float(max(
            r["clip_fractions"]["target_clip_fraction"] for r in reps)),
    }


def gates(levels: list[dict]) -> dict:
    omegas = [l["omega"] for l in levels]
    oh = [l["omega_hat"] for l in levels]
    p1 = all(oh[i] < oh[i + 1] for i in range(len(oh) - 1))
    p2 = max(abs(o - w) for o, w in zip(oh, omegas))
    p3 = max(abs(l["intercept"]) for l in levels)
    p4 = max(abs(l["null_pairs_mean_r"]) for l in levels)
    top = [l for l in levels if l["omega"] == 1.00][0]
    p5 = top["level_ratio_corrected"]
    p6 = max(l["residual_rms"] for l in levels)
    p7 = max(l["rho_eps_max_abs"] for l in levels)
    result = {
        "P1_monotonic": bool(p1),
        "P2_max_omega_err": p2, "P2": bool(p2 <= 0.20),
        "P3_max_abs_intercept": p3, "P3": bool(p3 <= 0.08),
        "P4_max_abs_null_mean": p4, "P4": bool(p4 <= 0.08),
        "P5_ratio_corrected_at_omega1": p5, "P5": bool(1.28 <= p5 <= 1.55),
        "P6_max_residual_rms": p6, "P6": bool(p6 <= 0.08),
        "P7_max_rho_eps": p7, "P7": bool(p7 <= 0.040),
    }
    result["all_pass"] = all(result[k] for k in
                             ("P1_monotonic", "P2", "P3", "P4", "P5", "P6", "P7"))
    result["verdict"] = "GO" if result["all_pass"] else "FAIL"
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--teardown", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.setup:
        setup(); return
    if args.teardown:
        teardown(); return

    n_win = int(round(T_RUN_S / DT_S))
    python_bin = os.environ.get("G2_PYTHON", "python3")
    procs = start_traffic(python_bin, len(LINKS))
    rng = np.random.default_rng(SEED)
    k_tilde = design_matrix(INCIDENCE)
    try:
        levels = [run_level(w, n_win, rng) for w in OMEGA_GRID]
    finally:
        for p in procs:
            p.terminate()
        subprocess.run(["pkill", "-f", "mininet/udp_sink.py"], capture_output=True)
        subprocess.run(["pkill", "-f", "mininet/blast_source.py"], capture_output=True)

    np.savez_compressed(
        SERIES,
        rho_measured=np.stack([[r["rho"] for r in l["reps"]] for l in levels]),
        rho_target=np.stack([[r["rho_target"] for r in l["reps"]] for l in levels]),
        omega_grid=np.array(OMEGA_GRID), dt_s=DT_S, tau_s=TAU_S, seed=SEED,
        ifaces=np.array(IFACE))
    name = os.environ.get("SUDO_USER")
    if name:
        import pwd
        info = pwd.getpwnam(name)
        os.chown(SERIES, info.pw_uid, info.pw_gid)

    analysed = [analyse_level(l, k_tilde) for l in levels]
    payload = {
        "schema": SCHEMA, "status": "MEASURED",
        "prereg": "docs/phase-G/63-prereg-g3a-omega-positive-control.md",
        "prereg_tag": "phase-G2-g3a-prereg",
        "provenance": provenance(),
        "design": {"omega_grid": list(OMEGA_GRID), "tau_s": TAU_S, "dt_s": DT_S,
                   "T_run_s": T_RUN_S, "n_windows": n_win,
                   "n_replicates": N_REPLICATES, "n_links": len(LINKS),
                   "host_quiesced": False, "fit_lag_lo": FIT_LAG_LO,
                   "seed": SEED},
        "levels": analysed,
        "gates": gates(analysed),
    }
    print(write_contract_artifact(OUT, payload)[:16] + f"  -> {OUT}")
    print(json.dumps(payload["gates"], indent=2))


if __name__ == "__main__":
    main()

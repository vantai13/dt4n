#!/usr/bin/env python3
"""G'.2 kill test -- try to FALSIFY the kernel-shaping escape from G-L98.

Preregistered in `docs/phase-G/58-prereg-g2-kill-test.md`, tagged
`phase-G2-kill-test-prereg` before any data was taken. This tool adjudicates
nothing on its own; it produces the artifact that doc 59 reads.

Topology: one veth pair per link. The root end carries an HTB class whose rate
is rewritten every window; the peer end lives in its own netns and runs a
blocking sink. The source is backlogged and blocking, so the SHAPER, not the
source, decides when packets leave.

Must run as root (tc and netns). Run it through the sdn_rl interpreter:

    sudo -n /home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m tools.g2_kill_test --setup
    sudo -n ... -m tools.g2_kill_test --smoke
    sudo -n ... -m tools.g2_kill_test --run
    sudo -n ... -m tools.g2_kill_test --teardown
"""
from __future__ import annotations

import argparse
import json
import os
import pwd
import subprocess
import threading
import time
from pathlib import Path

import numpy as np

from mininet.byte_sampler import read_counters, sample
from mininet.rate_controller import drive
from tools.g1_estimator_bias_sim import provenance
from tools import g3_dryrun
from tools.g3_dryrun import CAP_BPS, LINKS, physical_trace
from tools.measurement_path_calib import estimate_nugget

OUTDIR = Path("results/SMOKE/phase-G2")
SCHEMA = "dt4n.phase_g2.kill_test.v1"

TAU_S = 2.0
DT_S = 0.1
T_RUN_S = 410.0
N_REPLICATES = 4
OMEGA = 0.0
QDISC_LIMIT_FRAMES = 300
FRAME_BYTES = 1442
PORT = 9000
SEED = 2026_09_05
N_FIT_LAGS = 8

IFACE = [f"g2v{i}" for i in range(len(LINKS))]
NETNS = [f"g2link{i}" for i in range(len(LINKS))]
PEER = [f"g2p{i}" for i in range(len(LINKS))]
ADDR_ROOT = [f"10.90.{i}.1" for i in range(len(LINKS))]
ADDR_PEER = [f"10.90.{i}.2" for i in range(len(LINKS))]

# ★ `tools.g3_dryrun.ar1` reads the module-level `DT_S` (0.2 s) rather than a
# caller-supplied step, so `physical_trace(tau_s=...)` silently generates
# `phi = exp(-DT_S/tau)`. Driving that series at a different `dt` realises
# `tau_eff = -dt/log(phi)`, not `tau`. Run 1 of the kill test was executed at
# `tau_eff = 1.0 s` instead of the signed 2.0 s for exactly this reason, and
# was recorded invalid. Bind the constant to the step actually used, and put
# the value in the artifact so the realised tau is never implicit again.
g3_dryrun.DT_S = DT_S


def sh(*cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def setup() -> None:
    teardown(quiet=True)
    for i in range(len(LINKS)):
        sh("ip", "netns", "add", NETNS[i])
        sh("ip", "link", "add", IFACE[i], "type", "veth", "peer", "name", PEER[i])
        sh("ip", "link", "set", PEER[i], "netns", NETNS[i])
        sh("ip", "addr", "add", f"{ADDR_ROOT[i]}/24", "dev", IFACE[i])
        sh("ip", "link", "set", IFACE[i], "up")
        sh("ip", "netns", "exec", NETNS[i], "ip", "addr", "add",
           f"{ADDR_PEER[i]}/24", "dev", PEER[i])
        sh("ip", "netns", "exec", NETNS[i], "ip", "link", "set", PEER[i], "up")
        sh("ip", "netns", "exec", NETNS[i], "ip", "link", "set", "lo", "up")
        rate_kbit = max(8, int(CAP_BPS[i] / 1000.0))
        sh("tc", "qdisc", "add", "dev", IFACE[i], "root", "handle", "1:",
           "htb", "default", "10")
        sh("tc", "class", "add", "dev", IFACE[i], "parent", "1:", "classid",
           "1:10", "htb", "rate", f"{rate_kbit}kbit", "ceil",
           f"{rate_kbit}kbit", "burst", f"{FRAME_BYTES}b", "cburst",
           f"{FRAME_BYTES}b")
        sh("tc", "qdisc", "add", "dev", IFACE[i], "parent", "1:10", "handle",
           "10:", "pfifo", "limit", str(QDISC_LIMIT_FRAMES))
    print(f"setup: {len(LINKS)} links, qdisc limit {QDISC_LIMIT_FRAMES} frames")


def teardown(quiet: bool = False) -> None:
    subprocess.run(["pkill", "-f", "mininet/udp_sink.py"], capture_output=True)
    subprocess.run(["pkill", "-f", "mininet/blast_source.py"], capture_output=True)
    for i in range(len(LINKS)):
        sh("ip", "netns", "del", NETNS[i], check=False)
        sh("ip", "link", "del", IFACE[i], check=False)
    if not quiet:
        print("teardown: done")


def start_traffic(python_bin: str, n_link: int) -> list[subprocess.Popen]:
    procs = []
    for i in range(n_link):
        procs.append(subprocess.Popen(
            ["ip", "netns", "exec", NETNS[i], python_bin, "mininet/udp_sink.py",
             ADDR_PEER[i], str(PORT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    time.sleep(1.0)
    for i in range(n_link):
        procs.append(subprocess.Popen(
            [python_bin, "mininet/blast_source.py", ADDR_PEER[i], str(PORT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    time.sleep(2.0)
    return procs


def peer_rx_bytes(i: int) -> int:
    out = sh("ip", "netns", "exec", NETNS[i], "cat", "/proc/net/dev").stdout
    for line in out.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        if name.strip() == PEER[i]:
            return int(rest.split()[0])
    return -1


class BacklogMonitor(threading.Thread):
    """Poll every qdisc in ONE `tc` call, so the probe costs one process."""

    def __init__(self, ifaces, hz: float = 5.0) -> None:
        super().__init__(daemon=True)
        self.ifaces, self.period = set(ifaces), 1.0 / hz
        self.stop_flag = threading.Event()
        self.samples: list[dict] = []

    def run(self) -> None:
        while not self.stop_flag.is_set():
            try:
                data = json.loads(sh("tc", "-s", "-j", "qdisc", "show").stdout)
                row = {q["dev"]: (q.get("backlog", 0), q.get("drops", 0))
                       for q in data
                       if q.get("dev") in self.ifaces and q.get("kind") == "pfifo"}
                if row:
                    self.samples.append(row)
            except Exception:
                pass
            self.stop_flag.wait(self.period)

    def summary(self, ifaces) -> dict:
        if not self.samples:
            return {"n_samples": 0, "underrun_fraction": None, "drops_total": 0}
        counts = {name: 0 for name in ifaces}
        for row in self.samples:
            for name in ifaces:
                if name in row and row[name][0] == 0:
                    counts[name] += 1
        n = len(self.samples)
        drops = max((row[name][1] for row in self.samples
                     for name in ifaces if name in row), default=0)
        return {
            "n_samples": n,
            "underrun_fraction_per_link": {k: v / n for k, v in counts.items()},
            "underrun_fraction": max(counts.values()) / n,
            "drops_max": int(drops),
        }


def run_replicate(rep: int, n_link: int, n_win: int, rng) -> dict:
    ifaces, caps = IFACE[:n_link], CAP_BPS[:n_link]
    trace = physical_trace(OMEGA, TAU_S, TAU_S, n_win, rng)
    rho_target = trace["rho_target"][:n_link].T          # (n_win, n_link)

    monitor = BacklogMonitor(ifaces)
    rx0 = [peer_rx_bytes(i) for i in range(n_link)]
    result: dict = {}

    def controller() -> None:
        result["controller"] = drive(rho_target, ifaces, caps,
                                     FRAME_BYTES, DT_S)

    def sampler() -> None:
        rho, late, span = sample(ifaces, n_win, DT_S, caps)
        result["rho_measured"] = rho
        result["sampler"] = {
            "delta_mean_s": float(late.mean()),
            "delta_p50_s": float(np.percentile(late, 50)),
            "delta_p95_s": float(np.percentile(late, 95)),
            "delta_p99_s": float(np.percentile(late, 99)),
            "delta_max_s": float(late.max()),
            "delta_rms_s": float(np.sqrt((late ** 2).mean())),
            "read_span_p95_s": float(np.percentile(span, 95)),
        }

    monitor.start()
    t_ctl = threading.Thread(target=controller)
    t_smp = threading.Thread(target=sampler)
    t0 = time.perf_counter()
    t_ctl.start()
    t_smp.start()
    t_ctl.join()
    t_smp.join()
    wall = time.perf_counter() - t0
    monitor.stop_flag.set()
    monitor.join(timeout=2)
    rx1 = [peer_rx_bytes(i) for i in range(n_link)]

    rho_meas = result["rho_measured"]
    set_mean = rho_target.mean(axis=0) * caps                    # bps
    sink_mean = [(rx1[i] - rx0[i]) * 8.0 / wall for i in range(n_link)]
    return {
        "replicate": rep,
        "wall_s": wall,
        "controller": result["controller"],
        "sampler": result["sampler"],
        "backlog": monitor.summary(ifaces),
        "rho_target_mean": rho_target.mean(axis=0).tolist(),
        "rho_measured_mean": rho_meas.mean(axis=0).tolist(),
        "rho_measured_sd": rho_meas.std(axis=0, ddof=1).tolist(),
        "sink_rate_ratio": [float(sink_mean[i] / set_mean[i])
                            for i in range(n_link)],
        "_rho_measured": rho_meas,
    }


def analyse(reps: list[dict], n_link: int) -> dict:
    upper = np.triu_indices(n_link, 1)
    per_rep_r, fits = [], []
    for rep in reps:
        rho = rep["_rho_measured"]
        # A single-link smoke has no pairs; KILL-1 is undefined there.
        if n_link > 1:
            per_rep_r.append(np.corrcoef(rho.T)[upper])
        fits.append([estimate_nugget(rho[:, i], DT_S, N_FIT_LAGS)
                     for i in range(n_link)])
    if n_link > 1:
        r_stack = np.array(per_rep_r)
        pooled = np.tanh(
            np.arctanh(np.clip(r_stack, -0.999999, 0.999999)).mean(axis=0))
    else:
        r_stack = np.zeros((len(reps), 0))
        pooled = np.zeros(0)

    sf, v, tau_fit = [], [], []
    for rep_fits in fits:
        for fit in rep_fits:
            if np.isfinite(fit.get("sf", np.nan)):
                sf.append(float(fit["sf"]))
                v.append(float(fit["v"]))
            t = fit.get("tau_from_fit_s", np.nan)
            if np.isfinite(t) and t > 0:
                tau_fit.append(float(t))

    delta_rms = float(np.sqrt(np.mean([r["controller"]["delta_rms_s"] ** 2
                                       for r in reps])))
    sigma2 = float(np.mean([np.array(r["rho_measured_sd"]) ** 2 for r in reps]))
    v_meas = float(np.median(v)) if v else float("nan")
    v_pred_over_sigma2 = 2.0 * delta_rms ** 2 / (DT_S * TAU_S)
    v_pred = v_pred_over_sigma2 * sigma2
    ratio = v_meas / v_pred if v_pred > 0 else float("inf")

    return {
        "kill_1_max_abs_r": float(np.abs(pooled).max()) if pooled.size else None,
        "kill_1_median_abs_r": (float(np.median(np.abs(pooled)))
                                if pooled.size else None),
        "pooled_abs_r_sorted": np.sort(np.abs(pooled))[::-1].tolist(),
        "per_replicate_max_abs_r": (np.abs(r_stack).max(axis=1).tolist()
                                    if r_stack.shape[1] else []),
        "kill_2_underrun_fraction": max(r["backlog"]["underrun_fraction"]
                                        for r in reps),
        "kill_3_v_measured": v_meas,
        "kill_3_v_predicted": v_pred,
        "kill_3_ratio": ratio,
        "kill_4_max_abs_sink_ratio_error": max(
            abs(x - 1.0) for r in reps for x in r["sink_rate_ratio"]),
        "delta_rms_controller_s": delta_rms,
        "sigma2_measured": sigma2,
        "sf_hat_median": float(np.median(sf)) if sf else None,
        "tau_hat_median_s": float(np.median(tau_fit)) if tau_fit else None,
        "v_pred_over_sigma2": v_pred_over_sigma2,
    }


def verdict(a: dict) -> dict:
    k1 = a["kill_1_max_abs_r"] <= 0.20
    k1t = a["kill_1_max_abs_r"] <= 0.10
    k2 = a["kill_2_underrun_fraction"] <= 0.001
    k3 = 0.5 <= a["kill_3_ratio"] <= 3.0
    k4 = a["kill_4_max_abs_sink_ratio_error"] <= 0.05
    if k1 and k3:
        v = "GO"
    elif k1 and not k3:
        v = "GO_STAR"
    elif not k1 and k3:
        v = "DIAG"
    else:
        v = "STOP"
    return {"KILL_1_hard": k1, "KILL_1_target": k1t, "KILL_2": k2,
            "KILL_3": k3, "KILL_4": k4, "verdict": v}


def chown_back(path: Path) -> None:
    name = os.environ.get("SUDO_USER")
    if name:
        info = pwd.getpwnam(name)
        os.chown(path, info.pw_uid, info.pw_gid)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--teardown", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    if args.setup:
        setup()
        return
    if args.teardown:
        teardown()
        return

    smoke = args.smoke
    n_link = 1 if smoke else len(LINKS)
    n_rep = 1 if smoke else N_REPLICATES
    n_win = int(round((60.0 if smoke else T_RUN_S) / DT_S))
    out = OUTDIR / ("g2_pipeline_smoke.json" if smoke else "g2_kill_test.json")

    python_bin = os.environ.get("G2_PYTHON", "python3")
    procs = start_traffic(python_bin, n_link)
    rng = np.random.default_rng(SEED)
    try:
        reps = [run_replicate(k, n_link, n_win, rng) for k in range(n_rep)]
    finally:
        for proc in procs:
            proc.terminate()
        subprocess.run(["pkill", "-f", "mininet/udp_sink.py"], capture_output=True)
        subprocess.run(["pkill", "-f", "mininet/blast_source.py"], capture_output=True)

    stats = analyse(reps, n_link)
    payload = {
        "schema": SCHEMA,
        "status": "SMOKE_PIPELINE_CHECK" if smoke else "KILL_TEST_MEASURED",
        "prereg": "docs/phase-G/58-prereg-g2-kill-test.md",
        "prereg_tag": "phase-G2-kill-test-prereg",
        "provenance": provenance(),
        "design": {
            "omega": OMEGA, "tau_s": TAU_S, "dt_s": DT_S,
            "T_run_s": n_win * DT_S, "n_windows": n_win,
            "n_links": n_link, "n_replicates": n_rep,
            "qdisc_limit_frames": QDISC_LIMIT_FRAMES,
            "frame_bytes": FRAME_BYTES, "seed": SEED,
            "host_quiesced": False,
            "rate_path": "tools.g3_dryrun.physical_trace",
            "tau_estimator": "measurement_path_calib.estimate_nugget slope",
        },
        "analysis": stats,
        "gates": verdict(stats) if not smoke else None,
        "replicates": [{k: v for k, v in r.items() if not k.startswith("_")}
                       for r in reps],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    chown_back(out)
    print(f"{out}")
    print(json.dumps(stats, indent=2))
    if not smoke:
        print(json.dumps(payload["gates"], indent=2))


if __name__ == "__main__":
    main()

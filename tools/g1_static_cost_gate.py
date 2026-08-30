#!/usr/bin/env python3
"""Run eight static emitters without Mininet and enforce the CPU cost gate."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from mininet.run_sync_v7 import feasible_traffic_rho_targets
from mininet.traffic_v7 import link_caps_from_topology
from tools.infra_monitor import monitor
from tools.summarize_infra import summarize
from twin import topology_v7 as T7


def run_gate(raw_dir: Path, out: Path, duration_s: float, pace_tick_s: float, threshold: float) -> dict[str, object]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    caps = link_caps_from_topology()
    targets = feasible_traffic_rho_targets(0.857)
    processes = []
    for index, link in enumerate(T7.LINK_NAMES):
        command = [
            sys.executable, "-m", "mininet.static_emitter", "run",
            "--cap-mbps", str(caps[link]), "--rho-target", str(targets[link]),
            "--dst-ip", "127.0.0.1", "--dst-port", str(6200 + index),
            "--duration", str(duration_s), "--log-dt", "0.010",
            "--pace-tick", str(pace_tick_s),
            "--ledger", str(raw_dir / ("rho_offered_%s.csv" % link)),
            "--summary-out", str(raw_dir / ("flow_%s_summary.json" % link)),
        ]
        processes.append(subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    infra_path = raw_dir / "infra.jsonl"
    monitor(infra_path, duration_s, 0.1, tag="g1-static-v2-cost-gate")
    exit_codes = []
    for process in processes:
        try:
            exit_codes.append(process.wait(timeout=10.0))
        except subprocess.TimeoutExpired:
            process.terminate()
            exit_codes.append(process.wait(timeout=5.0))
    infra = summarize(infra_path)
    result = {
        "schema": "dt4n.phase_g.g1_static_v2_cost_gate.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": duration_s,
        "pace_tick_s": pace_tick_s,
        "n_emitters": len(processes),
        "cpu_p95_threshold": threshold,
        "infra": infra,
        "emitter_exit_codes": exit_codes,
        "pass": bool(float(infra["cpu_p95"]) < threshold and all(code == 0 for code in exit_codes)),
        "raw_dir": str(raw_dir),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("results/RAW/phase-G/g1-static-v2-cost"))
    parser.add_argument("--out", type=Path, default=Path("results/SMOKE/phase-G/g1_static_v2_cost_gate.json"))
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--pace-tick", type=float, default=0.002)
    parser.add_argument("--cpu-p95-threshold", type=float, default=25.0)
    args = parser.parse_args()
    result = run_gate(args.raw_dir, args.out, args.duration, args.pace_tick, args.cpu_p95_threshold)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

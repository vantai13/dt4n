#!/usr/bin/env python3
"""Run the preregistered topology_v7 AoI campaign in frozen random order."""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from typing import Any, Dict


MODES = ("clean", "prod")
RHOS = (0.700, 0.850, 0.900, 0.925, 0.960)
REPS = (1, 2, 3)
SEED = 23843
OUTDIR = "results/phase-23/aoi_v7_campaign"


def frozen_schedule() -> list[Dict[str, Any]]:
    canonical = list(itertools.product(MODES, RHOS, REPS))
    runs = list(canonical)
    random.Random(SEED).shuffle(runs)
    out = []
    for order, (mode, rho, rep) in enumerate(runs, 1):
        canonical_index = canonical.index((mode, rho, rep))
        out.append({
            "order": order,
            "mode": mode,
            "rho_bar": rho,
            "repeat": rep,
            "traffic_seed": SEED + canonical_index,
            "tag": f"{mode}_rho{rho:.3f}_rep{rep}",
            "status": "planned",
        })
    return out


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sanity(outdir: Path, run: Dict[str, Any], duration: float) -> Dict[str, Any]:
    probes = _read_jsonl(outdir / f"aoi_{run['tag']}.jsonl")
    cycles = _read_jsonl(outdir / f"cycles_{run['tag']}.jsonl")
    values = [
        float(value["aoi_s"])
        for row in probes[1:]
        if row.get("record") == "probe"
        for value in row["links"].values()
        if value.get("aoi_s") is not None
    ]
    expected_min = int(duration / 0.1 * 0.90) * 8
    negative = sum(value < 0.0 for value in values)
    clean_full = all(
        row.get("mode") != "clean" or row["n_pushed"] == row["n_things"]
        for row in cycles
    )
    if len(values) < expected_min:
        raise RuntimeError(f"probe completeness failed: {len(values)} < {expected_min}")
    if negative:
        raise RuntimeError(f"NC-S failed: {negative} negative AoI values")
    if not clean_full:
        raise RuntimeError("NC-U failed: CLEAN did not push every Thing")
    return {
        "n_aoi": len(values),
        "n_negative": negative,
        "n_cycles": len(cycles),
        "overrun_ratio": sum(bool(row["overrun"]) for row in cycles) / len(cycles),
        "clean_all_full_push": clean_full,
    }


def _write_manifest(path: Path, duration: float, runs: list[Dict[str, Any]]) -> None:
    body = {
        "schema": "dt4n.aoi.v7.campaign.v1",
        "order_seed": SEED,
        "duration_s": duration,
        "probe_interval_s": 0.1,
        "runs": runs,
    }
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--outdir", default=OUTDIR)
    parser.add_argument("--pause", type=float, default=5.0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    outdir = repo / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = outdir / "campaign_manifest.json"
    runs = frozen_schedule()
    if args.resume and manifest.exists():
        previous = json.loads(manifest.read_text(encoding="utf-8"))
        if previous["order_seed"] != SEED or previous["duration_s"] != args.duration:
            raise RuntimeError("existing manifest does not match the frozen design")
        runs = previous["runs"]
    _write_manifest(manifest, args.duration, runs)

    for run in runs:
        if args.resume and run.get("status") == "complete":
            print(f"[skip {run['order']:02d}/30] {run['tag']}", flush=True)
            continue
        tag = run["tag"]
        mode = run["mode"]
        print(f"[{run['order']:02d}/30] {tag}", flush=True)
        command = [
            "sudo", "-n", "env", f"PYTHONPATH={repo}", sys.executable,
            "-m", "mininet.run_sync_v7",
            "--ditto", "--traffic", "v7", "--measurement-mode", mode,
            "--sync-period", "0.5", "--tol", "0.0" if mode == "clean" else "0.5",
            "--reconcile-every", "1" if mode == "clean" else "30",
            "--rho-bar", str(run["rho_bar"]), "--repeat", str(run["repeat"]),
            "--seed", str(run["traffic_seed"]), "--duration", str(args.duration),
            "--cycle-trace", str(outdir / f"cycles_{tag}.jsonl"),
            "--push-trace", str(outdir / f"push_{tag}.jsonl"),
            "--aoi-probe-out", str(outdir / f"aoi_{tag}.jsonl"),
            "--offered-out", str(outdir / f"rho_offered_{tag}.csv"),
            "--measured-out", str(outdir / f"rho_measured_{tag}.csv"),
            "--meta-out", str(outdir / f"meta_{tag}.json"),
            "--flow-log-dir", str(outdir / f"flows_{tag}"),
        ]
        run["command"] = command
        run["status"] = "running"
        _write_manifest(manifest, args.duration, runs)
        try:
            subprocess.run(command, cwd=repo, check=True)
            run["sanity"] = sanity(outdir, run, args.duration)
            run["status"] = "complete"
        except BaseException:
            run["status"] = "failed"
            raise
        finally:
            _write_manifest(manifest, args.duration, runs)
            subprocess.run(["sudo", "-n", "mn", "-c"], cwd=repo, check=False)
        time.sleep(args.pause)

    print(f"campaign complete -> {manifest}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure the seed-to-seed noise floor for the marginalized Bayes policy.

This is an exploratory calibration tool for Phase 14. It does not train an
agent. It reuses the same oracle estimator as ``pilot_marginalized`` and reports
the standard deviation of Bayes-marginalized policy performance across seeds.
The intended threshold rule is still:

    gate_threshold = 2 * noise_floor
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from measurements.pilot_marginalized import Z_CHOICES, estimate_q_for_z
from measurements.samplers import build_sampler


def git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def file_sha(path, n_chars=12):
    try:
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None
    return digest[:int(n_chars)]


def eval_bayes_marginalized_policy(
    sampler,
    z_choices,
    p_z,
    n_cases,
    n_mc,
    rng,
    objective,
    cvar_alpha,
):
    """Evaluate the z-blind Bayes policy on sampled true z values."""
    actions = tuple(sampler.actions)
    returns = np.empty(int(n_cases), dtype=np.float64)

    for idx in range(int(n_cases)):
        obs, z_true = sampler.sample_observation(z_choices, rng)
        q_by_z = {}
        for z in z_choices:
            q_by_z[z] = estimate_q_for_z(
                sampler,
                obs,
                z,
                actions,
                int(n_mc),
                rng,
                objective,
                cvar_alpha,
            )

        def ev_marginal(action):
            return sum(float(p_z[z]) * q_by_z[z][action] for z in z_choices)

        a_marg = max(actions, key=ev_marginal)
        returns[idx] = q_by_z[int(z_true)][a_marg]

    return float(returns.mean())


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", default="routing3",
                        choices=("routing3", "routing_2path"))
    parser.add_argument("--load-cfg", default=None,
                        help="optional sampler load config name")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--cases", type=int, default=200)
    parser.add_argument("--mc-samples", type=int, default=100)
    parser.add_argument("--objective", default="mean", choices=("mean", "cvar"))
    parser.add_argument("--cvar-alpha", type=float, default=0.2)
    parser.add_argument("--out", default=None,
                        help="optional JSON result path")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.seeds < 2:
        raise ValueError("--seeds must be at least 2")
    if args.cases <= 0:
        raise ValueError("--cases must be positive")
    if args.mc_samples <= 0:
        raise ValueError("--mc-samples must be positive")
    if not (0.0 < float(args.cvar_alpha) <= 1.0):
        raise ValueError("--cvar-alpha must be in (0, 1]")

    z_choices = tuple(Z_CHOICES)
    p_z = {z: 1.0 / len(z_choices) for z in z_choices}
    perf = []
    load_cfg_name = args.load_cfg
    link_model_path = None
    reward_model_path = None
    dynamics_source_path = None

    for seed in range(int(args.seeds)):
        rng = np.random.default_rng(seed)
        sampler_kwargs = {}
        if args.load_cfg:
            sampler_kwargs["load_cfg_name"] = args.load_cfg
        sampler = build_sampler(args.topology, **sampler_kwargs)
        load_cfg_name = getattr(sampler, "load_cfg_name", load_cfg_name)
        link_model_path = getattr(sampler, "link_model_path", None)
        reward_model_path = getattr(sampler, "reward_model_path", None)
        dynamics_source_path = getattr(sampler, "dynamics_source_path", None)
        perf.append(
            eval_bayes_marginalized_policy(
                sampler,
                z_choices,
                p_z,
                int(args.cases),
                int(args.mc_samples),
                rng,
                args.objective,
                float(args.cvar_alpha),
            )
        )

    values = np.asarray(perf, dtype=np.float64)
    floor = float(values.std(ddof=1))
    threshold = 2.0 * floor

    objective_label = args.objective
    if args.objective == "cvar":
        objective_label = f"cvar (alpha={float(args.cvar_alpha):g})"

    print("=" * 62)
    print("  Bayes-marginalized policy noise floor")
    print("=" * 62)
    print(f"topology          : {args.topology}")
    print(f"load_cfg          : {load_cfg_name}")
    print(f"objective         : {objective_label}")
    print(f"seeds             : {args.seeds}")
    print(f"cases             : {args.cases}   (MC {args.mc_samples}/cell)")
    print(f"git               : {git_hash()}")
    print("-" * 62)
    print(f"performance mean  : {values.mean():.4f}")
    print(f"noise_floor       : {floor:.4f}")
    print(f"threshold = 2x    : {threshold:.4f}")
    print(f"per_seed          : {[round(float(v), 4) for v in values]}")
    print("-" * 62)
    print("reference         : Phase 9 std_agent=0.045, old threshold=0.10")
    print("=" * 62)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now().isoformat(),
            "git_hash": git_hash(),
            "topology": args.topology,
            "load_cfg": load_cfg_name,
            "objective": args.objective,
            "cvar_alpha": float(args.cvar_alpha),
            "seeds": int(args.seeds),
            "cases": int(args.cases),
            "mc_samples": int(args.mc_samples),
            "performance_mean": float(values.mean()),
            "noise_floor": floor,
            "threshold_2x": threshold,
            "per_seed": [float(v) for v in values],
            "link_model_path": link_model_path,
            "link_model_sha": file_sha(link_model_path) if link_model_path else None,
            "reward_model_path": reward_model_path,
            "reward_model_sha": file_sha(reward_model_path) if reward_model_path else None,
            "dynamics_source_path": dynamics_source_path,
            "dynamics_source_sha": (
                file_sha(dynamics_source_path) if dynamics_source_path else None
            ),
        }
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"-> wrote {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

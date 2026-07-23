#!/usr/bin/env python3
"""Probe the cost-of-blindness curve on SCENARIOS_ASYM.

This is a cheap Phase-10-style check before training. It compares the same
Dijkstra oracle with fresh state (clairvoyant) versus stale twin state (blind)
over several z values. No learning happens here.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.routing_2path.baselines import ospf_calibrated
from rl.routing_2path.metrics_r import make_env, run_episode
from rl.routing_2path.oracles import blind_dijkstra, clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing_2path.topology_r import ASYM_SCENARIO_WEIGHTS, LOAD_CFG_ASYM


DEFAULT_Z_VALUES = (0, 1, 3, 5, 8, 12)
def parse_ints(text: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in str(text).split(",") if item.strip())


def ci95(values) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) <= 1:
        return 0.0
    return float(1.96 * values.std(ddof=1) / math.sqrt(len(values)))


def build_load_cfg(drift_sigma: float, offered_load_max: float) -> dict:
    """Return LOAD_CFG_ASYM with optional parent drift/cap overrides."""
    cfg = dict(LOAD_CFG_ASYM)
    cfg["drift_sigma"] = float(drift_sigma)
    cfg["offered_load_max"] = float(offered_load_max)
    return cfg


def run_policy(policy_fn, z: int, seed: int, load_cfg: dict, max_steps: int) -> dict:
    env = make_env(z, seed=seed, load_cfg=load_cfg, max_steps=max_steps)
    return run_episode(
        env,
        policy_fn,
        seed=seed,
        target_fn=posthoc_dijkstra,
    ).as_dict()


def evaluate_z_paired(z: int, seeds: range, load_cfg: dict, max_steps: int) -> dict:
    clair_returns = []
    blind_returns = []
    ospf_returns = []
    clair_wrong = []
    blind_wrong = []
    aoi_values = []
    blind_safe = []
    clair_safe = []

    for seed in seeds:
        clair = run_policy(
            clairvoyant_dijkstra,
            z,
            seed,
            load_cfg,
            max_steps,
        )
        blind = run_policy(
            blind_dijkstra,
            z,
            seed,
            load_cfg,
            max_steps,
        )
        ospf = run_policy(
            ospf_calibrated,
            z,
            seed,
            load_cfg,
            max_steps,
        )

        clair_returns.append(float(clair["total_reward"]))
        blind_returns.append(float(blind["total_reward"]))
        ospf_returns.append(float(ospf["total_reward"]))
        clair_wrong.append(float(clair["wrong_rate"]))
        blind_wrong.append(float(blind["wrong_rate"]))
        aoi_values.append(float(blind["aoi_mean_s"]))
        blind_safe.append(float(blind["safe_path_freq"]))
        clair_safe.append(float(clair["safe_path_freq"]))

    clair_returns = np.asarray(clair_returns, dtype=float)
    blind_returns = np.asarray(blind_returns, dtype=float)
    ospf_returns = np.asarray(ospf_returns, dtype=float)
    clair_wrong = np.asarray(clair_wrong, dtype=float)
    blind_wrong = np.asarray(blind_wrong, dtype=float)
    cob = clair_returns - blind_returns
    wrong_excess = blind_wrong - clair_wrong

    return {
        "z_steps": int(z),
        "aoi_mean_s": float(np.mean(aoi_values)),
        "clair_return": float(clair_returns.mean()),
        "blind_return": float(blind_returns.mean()),
        "ospf_return": float(ospf_returns.mean()),
        "cost_of_blindness": float(cob.mean()),
        "cost_of_blindness_ci95": ci95(cob),
        "wrong_excess": float(wrong_excess.mean()),
        "wrong_excess_ci95": ci95(wrong_excess),
        "clair_wrong_rate": float(clair_wrong.mean()),
        "blind_wrong_rate": float(blind_wrong.mean()),
        "clair_safe_path_freq": float(np.mean(clair_safe)),
        "blind_safe_path_freq": float(np.mean(blind_safe)),
    }


def is_monotone(values, tol: float) -> bool:
    return all(values[idx] <= values[idx + 1] + tol
               for idx in range(len(values) - 1))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=80)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--z", default=",".join(str(z) for z in DEFAULT_Z_VALUES))
    parser.add_argument("--drift-sigma", type=float, default=0.15)
    parser.add_argument("--offered-load-max", type=float, default=1.60)
    parser.add_argument("--max-steps", type=int, default=15)
    parser.add_argument("--snr-gate", type=float, default=3.0)
    parser.add_argument("--std-agent", type=float, default=0.0450)
    parser.add_argument("--monotone-tol", type=float, default=0.02)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    z_values = parse_ints(args.z)
    seeds = range(int(args.seed_start), int(args.seed_start) + int(args.seeds))
    load_cfg = build_load_cfg(
        drift_sigma=args.drift_sigma,
        offered_load_max=args.offered_load_max,
    )

    print("Probe Phase 10 curve on SCENARIOS_ASYM")
    print(f"seeds={seeds.start}..{seeds.stop - 1} z={z_values}")
    print(
        "weights="
        + ", ".join(
            f"{name}:{weight:g}" for name, weight in ASYM_SCENARIO_WEIGHTS.items()
        )
    )
    print(
        f"drift_sigma={args.drift_sigma:.3f} "
        f"offered_load_max={args.offered_load_max:.2f}"
    )
    print(
        f"{'z':>3} {'AoI(s)':>7} {'clair':>9} {'blind':>9} "
        f"{'CoB':>9} {'CI95':>9} {'wrong_ex':>9} {'safe_b':>8}"
    )
    print("-" * 78)

    rows = []
    for z in z_values:
        row = evaluate_z_paired(
            z,
            seeds,
            load_cfg=load_cfg,
            max_steps=args.max_steps,
        )
        rows.append(row)
        print(
            f"{row['z_steps']:3d} {row['aoi_mean_s']:7.2f} "
            f"{row['clair_return']:9.4f} {row['blind_return']:9.4f} "
            f"{row['cost_of_blindness']:9.4f} "
            f"{row['cost_of_blindness_ci95']:9.4f} "
            f"{row['wrong_excess']:9.4f} "
            f"{row['blind_safe_path_freq']:8.4f}"
        )

    costs = [row["cost_of_blindness"] for row in rows]
    cost0 = float(costs[0])
    cost_max = float(max(costs))
    z_max = rows[int(np.argmax(costs))]["z_steps"]
    snr = cost_max / max(float(args.std_agent), 1e-12)
    monotone = is_monotone(costs, tol=float(args.monotone_tol))
    z0_ok = abs(cost0) <= max(0.05, rows[0]["cost_of_blindness_ci95"] * 2.0)
    pass_gate = z0_ok and monotone and snr >= float(args.snr_gate)

    print()
    print(f"CoB(z=0) = {cost0:+.4f}")
    print(f"CoB_max  = {cost_max:+.4f} at z={z_max}")
    print(f"SNR      = {snr:.2f} (CoB_max / std_agent {args.std_agent:.4f})")
    print(f"monotone = {monotone} (tol {args.monotone_tol:.3f})")
    print("PASS" if pass_gate else "FAIL")
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())

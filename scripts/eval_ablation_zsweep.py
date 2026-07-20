#!/usr/bin/env python3
"""Phase 11.3 - evaluate ablation checkpoints across fixed z values.

Each output row is one trained checkpoint averaged over fixed eval seeds:
    branch, agent_seed, z, return, wrong_rate, safe_path_freq

The eval seeds are shared across all checkpoints so later seed-level paired
tests compare like with like.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
from pathlib import Path

import numpy as np

from rl.agent.dqn_agent import DQNAgent
from rl.routing.oracles import posthoc_dijkstra
from rl.routing.state_r import R_STATE_DIM
from rl.routing.train_r import make_eval_env, run_agent_episode


BRANCHES = ("aoi", "mask")
Z_VALUES = (0, 1, 3, 5, 8, 12)
EVAL_SEEDS = tuple(range(200, 300))
OUT_DIR = Path("results/ablation")


def load_manifest(path: str) -> dict:
    """Load one train.json manifest and remember its path."""
    with open(path) as handle:
        payload = json.load(handle)
    payload["_path"] = path
    payload["_run_dir"] = str(Path(path).parent)
    return payload


def discover_runs(root: Path) -> list[dict]:
    """Return exactly one manifest per branch/agent_seed."""
    manifests = []
    for path in sorted(glob.glob(str(root / "*" / "r_seed*" / "train.json"))):
        payload = load_manifest(path)
        branch = payload.get("ablation_branch")
        if branch in BRANCHES:
            manifests.append(payload)

    if len(manifests) != 10:
        raise RuntimeError(
            f"expected 10 ablation manifests under {root}, found {len(manifests)}"
        )

    seen = set()
    for payload in manifests:
        key = (payload["ablation_branch"], int(payload["agent_seed"]))
        if key in seen:
            raise RuntimeError(f"duplicate manifest for {key}")
        seen.add(key)

    expected = {(branch, seed) for branch in BRANCHES for seed in range(5)}
    if seen != expected:
        raise RuntimeError(f"manifest set mismatch: expected {expected}, got {seen}")

    return sorted(
        manifests,
        key=lambda row: (BRANCHES.index(row["ablation_branch"]), int(row["agent_seed"])),
    )


def load_agent(manifest: dict) -> DQNAgent:
    """Load a trained DQNAgent from one manifest."""
    cfg = manifest["config"]
    agent = DQNAgent(R_STATE_DIM, 2, cfg)
    agent.load(os.path.join(manifest["_run_dir"], "model.pt"))
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def eval_agent_at_z(agent: DQNAgent, cfg: dict, z: int, eval_seeds: tuple[int, ...]):
    """Evaluate one checkpoint at one z over fixed eval seeds."""
    returns = []
    wrong_rates = []
    safe_freqs = []
    aoi_means = []
    arrivals = []
    steps = []

    for eval_seed in eval_seeds:
        env = make_eval_env(cfg, seed=eval_seed, z=z)
        stats = run_agent_episode(
            env,
            agent,
            seed=eval_seed,
            target_fn=posthoc_dijkstra,
        ).as_dict()
        returns.append(float(stats["total_reward"]))
        wrong_rates.append(float(stats["wrong_rate"]))
        safe_freqs.append(float(stats["safe_path_freq"]))
        aoi_means.append(float(stats["aoi_mean_s"]))
        arrivals.append(float(stats["arrived"]))
        steps.append(float(stats["steps"]))

    return {
        "aoi_mean_s": float(np.mean(aoi_means)),
        "return": float(np.mean(returns)),
        "wrong_rate": float(np.mean(wrong_rates)),
        "safe_path_freq": float(np.mean(safe_freqs)),
        "arrived": float(np.mean(arrivals)),
        "steps": float(np.mean(steps)),
    }


def write_csv(rows: list[dict], path: Path) -> None:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "branch",
        "seed",
        "z",
        "n_eval_seeds",
        "aoi_mean_s",
        "return",
        "wrong_rate",
        "safe_path_freq",
        "arrived",
        "steps",
        "run_dir",
    ]
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[CSV] wrote {path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(OUT_DIR))
    parser.add_argument("--out", default=str(OUT_DIR / "zsweep.csv"))
    parser.add_argument(
        "--eval-seeds",
        type=int,
        default=len(EVAL_SEEDS),
        help="number of eval seeds starting at 200",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    eval_seeds = tuple(range(200, 200 + int(args.eval_seeds)))
    manifests = discover_runs(root)

    print(f"[EVAL] runs={len(manifests)} z={Z_VALUES} eval_seeds={eval_seeds[0]}..{eval_seeds[-1]}")
    rows = []
    for manifest in manifests:
        branch = manifest["ablation_branch"]
        seed = int(manifest["agent_seed"])
        cfg = manifest["config"]
        agent = load_agent(manifest)
        for z in Z_VALUES:
            metrics = eval_agent_at_z(agent, cfg, z, eval_seeds)
            row = {
                "branch": branch,
                "seed": seed,
                "z": int(z),
                "n_eval_seeds": len(eval_seeds),
                "aoi_mean_s": round(metrics["aoi_mean_s"], 4),
                "return": round(metrics["return"], 6),
                "wrong_rate": round(metrics["wrong_rate"], 6),
                "safe_path_freq": round(metrics["safe_path_freq"], 6),
                "arrived": round(metrics["arrived"], 6),
                "steps": round(metrics["steps"], 6),
                "run_dir": manifest["_run_dir"],
            }
            rows.append(row)
            print(
                f"{branch:4s} seed{seed} z={z:>2} "
                f"aoi={metrics['aoi_mean_s']:.2f}s "
                f"return={metrics['return']:.3f} "
                f"wrong={metrics['wrong_rate']:.3f} "
                f"safe={metrics['safe_path_freq']:.3f}",
                flush=True,
            )

    write_csv(rows, Path(args.out))
    print(f"[DONE] wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Measure frozen-agent return std on LOAD_CFG_ABLATION.

This is optional support for Phase 11.2. The registered GO/NO-GO gate remains
the Phase-10 LOAD_CFG_SWEEP SNR, but this script tells us the noise scale on
the six-scenario training load.
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.metrics_r import summarize_episode_stats
from rl.routing_2path.oracles import posthoc_dijkstra
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.topology_r import LOAD_CFG_ABLATION, TOPO
from rl.routing_2path.train_r import run_agent_episode


FROZEN = "frozen_policies/v1"
SIGNAL_COB_MAX = 0.3283


def load_frozen(seed: int, cfg: dict) -> DQNAgent:
    """Load one frozen policy seed."""
    agent = DQNAgent(R_STATE_DIM, 2, cfg)
    agent.load(os.path.join(FROZEN, f"seed{seed}", "model.pt"))
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def eval_seed(agent: DQNAgent, n_eval_seeds: int) -> float:
    """Evaluate one frozen policy at z=0 over LOAD_CFG_ABLATION."""
    rows = []
    for eval_seed in range(int(n_eval_seeds)):
        base = RouteEnv(
            TOPO,
            load_cfg=LOAD_CFG_ABLATION,
            max_steps=15,
            seed=eval_seed,
        )
        env = StalenessWrapper(base, z_steps_choices=(0,))
        rows.append(
            run_agent_episode(
                env,
                agent,
                seed=eval_seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return float(summarize_episode_stats(rows)["return"])


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-frozen-seeds", type=int, default=5)
    parser.add_argument("--n-eval-seeds", type=int, default=50)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    with open(os.path.join(FROZEN, "config.json")) as handle:
        cfg = json.load(handle)

    per_seed = []
    for seed in range(int(args.n_frozen_seeds)):
        agent = load_frozen(seed, cfg)
        value = eval_seed(agent, args.n_eval_seeds)
        per_seed.append(value)
        print(f"seed{seed}: return={value:.4f}", flush=True)

    per_seed = np.array(per_seed, dtype=float)
    std = float(per_seed.std(ddof=1))
    mean = float(per_seed.mean())
    print("")
    print("return moi seed:", [round(float(v), 4) for v in per_seed])
    print(f"mean_return on LOAD_CFG_ABLATION = {mean:.4f}")
    print(f"std_agent on LOAD_CFG_ABLATION   = {std:.4f}")
    print(f"SNR if using this std            = {SIGNAL_COB_MAX / std:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 10.1 — Đo lại std_agent CHUẨN từ frozen_policies/v1/ hiện tại.

Đo return trung bình mỗi seed tại z=0, rồi std giữa 5 seed.
Đo trên CẢ HAI load để so sánh và chọn đúng cái sweep 10.2 sẽ dùng.
"""
import json
import os

import numpy as np

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.metrics_r import summarize_episode_stats
from rl.routing_2path.oracles import posthoc_dijkstra
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.topology_r import (
    LOAD_CFG_SWEEP,
    LOAD_CFG_TRAIN,
    SCENARIOS_TRAIN,
    TOPO,
)
from rl.routing_2path.train_r import run_agent_episode

FROZEN = "frozen_policies/v1"
N_SEEDS = 5
EVAL_SEEDS = range(50)      # 50 eval-seed mỗi frozen-seed
MAX_STEPS = 15

# Load config đúng như frozen được train (đọc từ config.json để khỏi hard-code sai)
with open(os.path.join(FROZEN, "config.json")) as f:
    CFG = json.load(f)


def load_frozen(seed):
    agent = DQNAgent(R_STATE_DIM, 2, CFG)
    agent.load(os.path.join(FROZEN, f"seed{seed}", "model.pt"))
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def eval_seed_at_z0(agent, load_cfg):
    """Return trung bình của MỘT frozen-seed qua EVAL_SEEDS, tại z=0."""
    rows = []
    for es in EVAL_SEEDS:
        base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=MAX_STEPS, seed=es)
        env = StalenessWrapper(base, z_steps_choices=(0,))  # z=0
        rows.append(
            run_agent_episode(
                env,
                agent,
                seed=es,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows)["return"]


def measure(load_cfg, label):
    per_seed = [eval_seed_at_z0(load_frozen(s), load_cfg) for s in range(N_SEEDS)]
    per_seed = np.array(per_seed, dtype=float)
    mean = float(per_seed.mean())
    std = float(per_seed.std(ddof=1))
    ci95 = float(1.96 * std / np.sqrt(N_SEEDS))
    print(f"\n=== std_agent trên {label} ===")
    print("return mỗi seed:", [round(float(r), 4) for r in per_seed])
    print(f"mean_return = {mean:.4f}")
    print(f"std_agent   = {std:.4f}")
    print(f"ci95        = {ci95:.4f}")
    return std


if __name__ == "__main__":
    load_train = {"scenarios": SCENARIOS_TRAIN,
                  "scenario_mix": tuple(SCENARIOS_TRAIN)}
    measure(load_train, "SCENARIOS_TRAIN (đúng load frozen được train)")
    measure(LOAD_CFG_TRAIN, "LOAD_CFG_TRAIN (tĩnh, Phase 9)")
    measure(LOAD_CFG_SWEEP, "LOAD_CFG_SWEEP (drift 0.15, đúng load sweep 10.2)")
    print("\n→ Ghi con số std_agent (theo load sweep 10.2 sẽ dùng) vào pre-registration.")

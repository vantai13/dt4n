#!/usr/bin/env python3
"""Lesson 11.2 bước 0 — xem 6 scenario: tải thế nào, cái nào động (drift)."""
import sys; sys.path.insert(0, '.')
import numpy as np
from rl.routing.route_env import RouteEnv
from rl.routing.topology_r import TOPO, SCENARIOS_TRAIN, SCENARIOS_DYNAMIC

ALL_SCENARIOS = {**SCENARIOS_TRAIN, **SCENARIOS_DYNAMIC}
CE, CF = ('C', 'E'), ('C', 'F')   # hai link quyết định tại node C

for name, scen in ALL_SCENARIOS.items():
    # Dựng env chỉ với 1 scenario này để quan sát riêng
    load_cfg = {'scenarios': {name: scen}, 'scenario_mix': (name,)}
    env = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=15, seed=7)
    env.reset(seed=7)
    sigma = env._drift_sigma()
    ce0, cf0 = env._rho_offered[CE], env._rho_offered[CF]
    # mô phỏng 5 bước drift để xem tải có đổi trong episode không
    traj_ce = [env._rho_offered[CE]]
    for _ in range(5):
        env._drift()
        traj_ce.append(env._rho_offered[CE])
    dong = "ĐỘNG" if sigma > 0 else "tĩnh"
    print(f"{name:18s} [{dong}] drift={sigma:.2f} | C→E khởi đầu={ce0:.3f} C→F={cf0:.3f}")
    print(f"    quỹ đạo C→E qua 5 bước: {[round(x,3) for x in traj_ce]}")
#!/usr/bin/env python3
"""Frozen-dimension diagnostic with RouteEnv wrapped by staleness."""

import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.state_r import R_DIM_NAMES
from rl.routing.topology_r import TOPO


def main():
    env = StalenessWrapper(
        RouteEnv(TOPO, seed=0),
        z_steps_choices=(0, 1, 2, 3, 5),
    )

    obs_all = []
    for ep in range(300):
        obs, info = env.reset(seed=ep)
        obs_all.append(obs)
        rng = np.random.default_rng(ep * 31)
        for _ in range(20):
            valid = np.flatnonzero(info['valid_mask'])
            if len(valid) == 0:
                break
            action = int(rng.choice(valid))
            obs, _reward, terminated, truncated, info = env.step(action)
            obs_all.append(obs)
            if terminated or truncated:
                break

    matrix = np.array(obs_all)
    print('=== FROZEN-DIM DIAGNOSTIC - WITH WRAPPER (z random) ===')
    for idx, name in enumerate(R_DIM_NAMES):
        std = matrix[:, idx].std()
        flag = '  <-- FROZEN' if std < 0.01 else ''
        print(f'  [{idx}] {name:14s} std={std:.4f}{flag}')
    print('\nNote: wrapper uses RouteEnv.STEP_DURATION_S as simulated time.')


if __name__ == '__main__':
    main()

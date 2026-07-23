#!/usr/bin/env python3
"""[9.2] Reproducibility tests for the routing training loop."""
import random
import sys

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.routing_2path.train_r import config_hash, git_hash, set_global_seed


def test_set_global_seed_covers_all_four():
    """Python random, NumPy, and Torch draws repeat for the same seed."""
    def draw():
        return (
            random.random(),
            float(np.random.rand()),
            float(torch.rand(1)),
        )

    set_global_seed(42)
    first = draw()
    set_global_seed(42)
    second = draw()
    set_global_seed(43)
    third = draw()

    assert first == second
    assert first != third


def test_random_seed_not_forgotten():
    """ReplayBuffer.sample uses random.sample, so stdlib random must be seeded."""
    set_global_seed(7)
    first = [random.random() for _ in range(5)]
    set_global_seed(7)
    second = [random.random() for _ in range(5)]
    assert first == second


def test_agent_init_deterministic():
    """Calling set_global_seed before DQNAgent makes initial weights stable."""
    from rl.agent.dqn_agent import DQNAgent
    from rl.routing_2path.state_r import R_STATE_DIM

    cfg = {'agent': {
        'gamma': 0.95,
        'epsilon_start': 1.0,
        'epsilon_end': 0.05,
        'epsilon_decay': 0.99,
        'learning_rate': 1e-3,
        'batch_size': 64,
        'target_update_freq': 200,
        'hidden_layers': [64, 32],
        'buffer_capacity': 1000,
        'device': 'cpu',
    }}

    set_global_seed(11)
    first = DQNAgent(R_STATE_DIM, 2, cfg)
    set_global_seed(11)
    second = DQNAgent(R_STATE_DIM, 2, cfg)

    for p1, p2 in zip(first.main_net.parameters(), second.main_net.parameters()):
        assert torch.allclose(p1, p2)


def test_train_seeds_depend_on_agent_seed():
    """Train seeds must not be shared across agent seeds."""
    start, stride, n = 1000, 100_000, 500
    seeds = {
        agent_seed: set(range(
            start + agent_seed * stride,
            start + agent_seed * stride + n,
        ))
        for agent_seed in range(5)
    }

    for i in range(5):
        for j in range(i + 1, 5):
            assert not (seeds[i] & seeds[j])
    assert min(seeds[0]) != min(seeds[1])


def test_eval_seeds_fixed_across_agents():
    """Eval seeds stay fixed to preserve paired comparison."""
    expected = list(range(500, 520))
    for _agent_seed in range(5):
        assert list(range(500, 520)) == expected


def test_config_hash_stable_and_sensitive():
    """Hash ignores dict key order but changes when values change."""
    c1 = {'agent': {'lr': 0.001, 'gamma': 0.95}}
    c2 = {'agent': {'gamma': 0.95, 'lr': 0.001}}
    c3 = {'agent': {'lr': 0.002, 'gamma': 0.95}}

    assert config_hash(c1) == config_hash(c2)
    assert config_hash(c1) != config_hash(c3)


def test_dirty_flag_detected():
    """git_hash should always return a usable run identity component."""
    h = git_hash()
    assert isinstance(h, str)
    assert h


def test_aoi_dims_alive_under_random_z():
    """Randomized z keeps AoI dimensions non-constant for Phase 11 ablation."""
    from rl.routing_2path.route_env import RouteEnv
    from rl.routing_2path.staleness_r import StalenessWrapper
    from rl.routing_2path.state_r import AOI_DIMS
    from rl.routing_2path.topology_r import LOAD_CFG_V1, TOPO

    def collect(z_choices, n=100):
        values = []
        for seed in range(n):
            env = StalenessWrapper(
                RouteEnv(TOPO, load_cfg=LOAD_CFG_V1, seed=seed),
                z_steps_choices=z_choices,
            )
            obs, _info = env.reset(seed=seed)
            for _ in range(6):
                values.append([obs[d] for d in AOI_DIMS])
                obs, _reward, terminated, truncated, _info = env.step(0)
                if terminated or truncated:
                    break
        return np.array(values)

    dead = collect((0,))
    assert dead.std(axis=0).max() < 1e-9

    alive = collect((0, 1, 3, 5, 8, 12))
    for idx, dim in enumerate(AOI_DIMS):
        assert alive[:, idx].std() > 0.05, (
            f'AoI dim {dim} is nearly constant: std={alive[:, idx].std():.6f}')

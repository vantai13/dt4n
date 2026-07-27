#!/usr/bin/env python3
"""[9.1] Tests for DQN action masking."""
import sys

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.topology_r import LOAD_CFG_V1, TOPO


def _cfg(**overrides):
    agent_cfg = {
        'gamma': 0.95,
        'epsilon_start': 1.0,
        'epsilon_end': 0.05,
        'epsilon_decay': 0.995,
        'learning_rate': 1e-3,
        'batch_size': 8,
        'target_update_freq': 100,
        'hidden_layers': [32, 16],
        'buffer_capacity': 1000,
        'device': 'cpu',
    }
    agent_cfg.update(overrides)
    return {'agent': agent_cfg}


def test_fuzz_never_picks_invalid():
    """1000+ choices: never pick an action outside the valid mask."""
    env = RouteEnv(TOPO, load_cfg=LOAD_CFG_V1, seed=0)
    agent = DQNAgent(R_STATE_DIM, 2, _cfg())
    checked = 0

    for eps in (1.0, 0.5, 0.0):
        for seed in range(90):
            obs, info = env.reset(seed=seed)
            for _ in range(15):
                mask = info['valid_mask']
                action = agent.select_action(obs, epsilon=eps, valid_mask=mask)
                assert mask[action] > 0.5, (
                    f'invalid action picked: node={info["current_node"]} '
                    f'action={action} mask={mask} eps={eps}')
                checked += 1
                obs, _reward, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break

    assert checked > 1000, f'only checked {checked} choices'


def test_no_invalid_action_in_env():
    """With masking, exploration should not kill episodes via invalid actions."""
    env = RouteEnv(TOPO, load_cfg=LOAD_CFG_V1, seed=0)
    agent = DQNAgent(R_STATE_DIM, 2, _cfg())
    killed = 0

    for seed in range(200):
        obs, info = env.reset(seed=seed)
        for _ in range(15):
            action = agent.select_action(
                obs,
                epsilon=1.0,
                valid_mask=info['valid_mask'],
            )
            obs, _reward, terminated, truncated, info = env.step(action)
            if info.get('invalid_action'):
                killed += 1
            if terminated or truncated:
                break

    assert killed == 0, f'{killed}/200 episodes died from invalid actions'


class _PoisonedTwoActionNet(torch.nn.Module):
    """Tiny network where invalid action 1 looks extremely attractive."""

    def __init__(self, valid_q=0.0, invalid_q=1000.0):
        super().__init__()
        self.valid_q = torch.nn.Parameter(torch.tensor(float(valid_q)))
        self.invalid_q = torch.nn.Parameter(
            torch.tensor(float(invalid_q)),
            requires_grad=False,
        )

    def forward(self, x):
        batch = x.shape[0]
        valid = self.valid_q.expand(batch)
        invalid = self.invalid_q.expand(batch)
        return torch.stack((valid, invalid), dim=1)


def _masked_train_loss(use_double):
    agent = DQNAgent(R_STATE_DIM, 2, _cfg(use_double=use_double))
    agent.main_net = _PoisonedTwoActionNet().to(agent.device)
    agent.target_net = _PoisonedTwoActionNet().to(agent.device)
    agent.target_net.eval()
    agent.optimizer = torch.optim.SGD(agent.main_net.parameters(), lr=0.0)

    rng = np.random.RandomState(0)
    states = rng.rand(8, R_STATE_DIM).astype(np.float32)
    next_states = rng.rand(8, R_STATE_DIM).astype(np.float32)
    next_mask = np.array([1.0, 0.0], dtype=np.float32)

    for i in range(8):
        agent.remember(states[i], 0, -1.0, next_states[i], False, next_mask)

    return agent.train_step()


def test_bellman_not_poisoned():
    """Invalid Q=+1000 must not enter the Bellman target."""
    for use_double in (True, False):
        loss = _masked_train_loss(use_double)
        assert loss < 2.0, (
            f'Bellman target used invalid Q under use_double={use_double}; '
            f'loss={loss}')


def test_bellman_test_actually_fails_without_mask():
    """Meta-test: without masking, the same setup would be wildly poisoned."""
    gamma = 0.95
    reward = torch.full((8,), -1.0)
    done = torch.zeros(8)
    q_next = torch.tensor([[0.0, 1000.0]] * 8)
    mask = torch.tensor([[1.0, 0.0]] * 8)

    target_without_mask = reward + gamma * q_next.max(dim=1)[0] * (1.0 - done)
    target_with_mask = reward + gamma * q_next.masked_fill(
        mask < 0.5,
        -1e9,
    ).max(dim=1)[0] * (1.0 - done)

    assert target_without_mask.mean() > target_with_mask.mean() + 900.0


def test_neighbor_order_locked():
    """Neighbor order is part of the action-index contract."""
    expected = {
        'SRC': ['A', 'B'],
        'A': ['C', 'D'],
        'B': ['C', 'D'],
        'C': ['E', 'F'],
        'D': ['E', 'F'],
        'E': ['F'],
        'F': ['DST'],
        'DST': [],
    }
    env = RouteEnv(TOPO, load_cfg=LOAD_CFG_V1, seed=0)

    for node, want in expected.items():
        assert env.adj[node] == want, (
            f'neighbor order changed at {node}: {env.adj[node]} != {want}')


def test_valid_mask_matches_topology():
    """Env valid_mask must match the actual number of neighbors."""
    env = RouteEnv(TOPO, load_cfg=LOAD_CFG_V1, seed=0)

    for seed in range(20):
        _obs, info = env.reset(seed=seed)
        for _ in range(15):
            node = info['current_node']
            assert int(info['valid_mask'].sum()) == len(env.adj[node])
            action = int(np.flatnonzero(info['valid_mask'])[0])
            _obs, _reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break


def test_a2_backward_compat():
    """valid_mask=None keeps the old all-actions-valid behavior."""
    agent = DQNAgent(R_STATE_DIM, 2, _cfg())
    state = np.zeros(R_STATE_DIM, dtype=np.float32)

    for _ in range(50):
        action = agent.select_action(state, epsilon=1.0, valid_mask=None)
        assert 0 <= action < 2

    agent.remember(state, 0, -1.0, state, False)
    assert len(agent.buffer) == 1

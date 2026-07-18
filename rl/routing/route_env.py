#!/usr/bin/env python3
"""Minimal routing environment for the AoI experiment.

This file contains no staleness logic. Staleness belongs in a wrapper so the
clean z=0 case is just ``RouteEnv`` itself, not a branch inside this class.

Contract for that future wrapper:
    - true_utils() returns true per-neighbor utilization at the current node.
    - true_losses() returns true per-neighbor loss at the current node.
    - info['neighbor_utils_true'] provides raw material so the wrapper can
      rebuild a state instead of patching obs[2:4].
    - reward is always computed from true measured delay and true loss.
"""

import copy

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    class _Env:
        metadata = {}

        def reset(self, seed=None, options=None):
            return None

    class _Discrete:
        def __init__(self, n):
            self.n = int(n)

        def __repr__(self):
            return f'Discrete({self.n})'

    class _Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = tuple(shape)
            self.dtype = dtype

        def __repr__(self):
            return f'Box({self.low}, {self.high}, {self.shape}, {self.dtype})'

    class _Spaces:
        Discrete = _Discrete
        Box = _Box

    class _Gym:
        Env = _Env

    gym = _Gym()
    spaces = _Spaces()

from rl.routing.link_model import (
    loss_rate,
    rho_measured_from_offered,
    total_delay_ms,
)
from rl.routing.reward_r import REWARD_VERSION, step_reward
from rl.routing.state_r import MAX_NEIGHBORS, R_STATE_DIM, build_route_state


class RouteEnv(gym.Env):
    """Route a flow from SRC to DST, one next-hop choice per step."""

    metadata = {'render_modes': []}
    # Legacy z-wrapper clock only. Physical time for new sync-period wrappers is
    # ``sim_time_s``, advanced by each traversed link's modeled delay.
    STEP_DURATION_S = 0.5

    def __init__(self, topo_cfg, load_cfg=None, max_steps=15, seed=None):
        super().__init__()
        self.nodes = list(topo_cfg['nodes'])
        self.node_to_idx = {name: idx for idx, name in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)
        self.source = topo_cfg['source']
        self.destination = topo_cfg['destination']

        self.adj = {node: [] for node in self.nodes}
        self.link = {}
        default_queue_pkts = topo_cfg.get('default_queue_pkts')
        for src, dst, delay, bw in topo_cfg['edges']:
            self.adj[src].append(dst)
            self.link[(src, dst)] = {
                'base_delay': float(delay),
                'base_bw': float(bw),
                'queue_pkts': default_queue_pkts,
            }
        for node in self.nodes:
            if len(self.adj[node]) > MAX_NEIGHBORS:
                raise ValueError(
                    f'node {node} has {len(self.adj[node])} neighbors > '
                    f'MAX_NEIGHBORS={MAX_NEIGHBORS}')

        self.load_cfg = load_cfg or {}
        self.max_steps = int(max_steps)

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(R_STATE_DIM,), dtype=np.float32)
        self.action_space = spaces.Discrete(MAX_NEIGHBORS)

        self._rng = np.random.default_rng(seed)
        self.reward_version = REWARD_VERSION

        self.current = None
        self.step_count = 0
        self.sim_time_s = 0.0
        self.path = []
        self._rho_offered = {}
        self._rho = {}
        self._loss = {}

    def _default_offered_max(self):
        base_hi = self.load_cfg.get('base_load', (0.25, 0.40))[1]
        e_hi = self.load_cfg.get('e_load', (0.60, 0.95))[1]
        return max(1.30, float(base_hi), float(e_hi))

    def _offered_max(self):
        return float(self.load_cfg.get(
            'offered_load_max',
            self._default_offered_max(),
        ))

    def _sync_observed_link_metrics(self):
        """Refresh deployable measured util/loss from offered load."""
        self._rho = {
            link: rho_measured_from_offered(rho_offered)
            for link, rho_offered in self._rho_offered.items()
        }
        self._loss = {
            link: loss_rate(rho_offered)
            for link, rho_offered in self._rho_offered.items()
        }

    def _sample_load(self):
        """Draw per-link offered load for one episode.

        Offered load is the traffic we try to inject. It may exceed 1.0. The
        deployable utilization exposed to the agent is derived separately and
        clipped by ``rho_measured_from_offered``.
        """
        base_lo, base_hi = self.load_cfg.get('base_load', (0.25, 0.40))
        e_lo, e_hi = self.load_cfg.get('e_load', (0.60, 0.95))
        hi = self._offered_max()
        rho = {}
        for link in self.link:
            rho[link] = float(np.clip(
                self._rng.uniform(base_lo, base_hi),
                0.02,
                hi,
            ))

        e_level = float(np.clip(self._rng.uniform(e_lo, e_hi), 0.02, hi))
        for link in (('C', 'E'), ('D', 'E')):
            if link in rho:
                rho[link] = e_level
        return rho

    def _drift(self):
        """Move congestion slightly so stale observations can become wrong."""
        sigma = float(self.load_cfg.get('drift_sigma', 0.05))
        hi = self._offered_max()
        for link in self._rho_offered:
            self._rho_offered[link] = float(np.clip(
                self._rho_offered[link] + self._rng.normal(0.0, sigma),
                0.02,
                hi,
            ))
        self._sync_observed_link_metrics()

    def peek_next_rho_offered(self):
        """Return the next offered-load snapshot without consuming env RNG."""
        sigma = float(self.load_cfg.get('drift_sigma', 0.05))
        hi = self._offered_max()
        rng = np.random.default_rng()
        rng.bit_generator.state = copy.deepcopy(self._rng.bit_generator.state)
        return {
            link: float(np.clip(rho + rng.normal(0.0, sigma), 0.02, hi))
            for link, rho in self._rho_offered.items()
        }

    def peek_next_rho(self):
        """Return the next measured rho snapshot without consuming env RNG.

        This is a measurement hook for post-hoc diagnostics, not policy input.
        It clones the RNG state so peeking cannot perturb the episode.
        """
        offered = self.peek_next_rho_offered()
        return {
            link: rho_measured_from_offered(rho_offered)
            for link, rho_offered in offered.items()
        }

    def peek_next_loss(self):
        """Return the next loss snapshot without consuming env RNG."""
        offered = self.peek_next_rho_offered()
        return {
            link: loss_rate(rho_offered)
            for link, rho_offered in offered.items()
        }

    def neighbors(self, node):
        return self.adj[node]

    def true_utils(self):
        """Return true per-neighbor utilization at the current node."""
        return [self._rho[(self.current, nb)] for nb in self.adj[self.current]]

    def true_losses(self):
        """Return true per-neighbor loss at the current node."""
        return [self._loss[(self.current, nb)] for nb in self.adj[self.current]]

    def valid_mask(self):
        mask = np.zeros(MAX_NEIGHBORS, dtype=np.float32)
        for idx in range(len(self.adj[self.current])):
            mask[idx] = 1.0
        return mask

    def _obs(self, utils_observed, losses_observed=None, aoi_s=0.0):
        return build_route_state(
            current_idx=self.node_to_idx[self.current],
            n_nodes=self.n_nodes,
            step=self.step_count,
            max_steps=self.max_steps,
            neighbor_utils=utils_observed,
            neighbor_valid=self.valid_mask(),
            neighbor_losses=losses_observed,
            aoi_s=aoi_s,
        )

    def _info(self):
        return {
            'current_node': self.current,
            'neighbor_utils_true': list(self.true_utils()),
            'neighbor_losses_true': list(self.true_losses()),
            'valid_mask': self.valid_mask().copy(),
            'path': list(self.path),
            'step': self.step_count,
            'sim_time_s': float(self.sim_time_s),
            'rho_offered_snapshot': dict(self._rho_offered),
            'rho_measured_snapshot': dict(self._rho),
            'rho_snapshot': dict(self._rho),
            'rho_snapshot_next': self.peek_next_rho(),
            'rho_offered_snapshot_next': self.peek_next_rho_offered(),
            'loss_snapshot': dict(self._loss),
            'loss_snapshot_next': self.peek_next_loss(),
            'reward_version': self.reward_version,
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        self.current = self.source
        self.step_count = 0
        self.sim_time_s = 0.0
        self.path = [self.current]
        self._rho_offered = self._sample_load()
        self._sync_observed_link_metrics()
        return self._obs(self.true_utils(), self.true_losses()), self._info()

    def step(self, action):
        action = int(action)
        neighbors = self.adj[self.current]
        self.step_count += 1

        if action >= len(neighbors):
            breakdown = step_reward(0.0, 0.0, failed=True)
            info = self._info()
            info.update({
                'invalid_action': True,
                'arrived': False,
                **breakdown.as_dict(),
            })
            return (
                self._obs(self.true_utils(), self.true_losses()),
                breakdown.total,
                False,
                True,
                info,
            )

        nxt = neighbors[action]
        link = (self.current, nxt)
        rho_offered = self._rho_offered[link]
        rho_measured = self._rho[link]
        base_delay = self.link[link]['base_delay']
        bw_mbps = self.link[link].get('base_bw')
        queue_pkts = self.link[link].get('queue_pkts')

        delay_ms = total_delay_ms(
            base_delay,
            rho_offered,
            bw_mbps=bw_mbps,
            queue_pkts=queue_pkts,
        )
        loss = loss_rate(rho_offered)

        self.sim_time_s += float(delay_ms) / 1000.0
        self.current = nxt
        self.path.append(nxt)
        self._drift()

        arrived = self.current == self.destination
        # Tripwire, not a live branch: topology_r is a DAG, so loops are
        # physically impossible unless a future topology change introduces a
        # cycle. Kept as a guard; do not read it as live experiment complexity.
        looped = self.path.count(self.current) > 1
        timeout = self.step_count >= self.max_steps and not arrived

        breakdown = step_reward(
            delay_ms,
            loss,
            arrived=arrived,
            failed=(looped or timeout),
        )
        terminated = arrived
        truncated = (timeout or looped) and not arrived

        info = self._info()
        info.update({
            'arrived': arrived,
            'loop': looped,
            'timeout': timeout,
            'invalid_action': False,
            'link_delay_ms': delay_ms,
            'link_loss': loss,
            'link_rho_true': rho_measured,
            'link_rho_measured': rho_measured,
            'link_rho_offered': rho_offered,
            **breakdown.as_dict(),
        })
        return (
            self._obs(self.true_utils(), self.true_losses()),
            breakdown.total,
            terminated,
            truncated,
            info,
        )

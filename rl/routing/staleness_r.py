#!/usr/bin/env python3
"""Controlled observation-staleness wrapper for RouteEnv.

Ported from ``rl/a2/staleness.py`` with one important routing-specific change:
we buffer full per-link utilization snapshots, not positional neighbor utils.

Why: in A2, demand is a global pair. In routing, ``neighbor_utils`` are local
to the current node. A stale positional buffer could hand the agent SRC link
utils while it is standing at C. A snapshot keyed by link preserves identity.
"""

from collections import deque

import numpy as np

from rl.routing.state_r import build_route_state, mask_aoi


class StalenessWrapper:
    """Wrap RouteEnv and return observations from stale rho snapshots."""

    def __init__(self, env, z_steps_choices=(0,), mask_aoi_dims=False,
                 history_cap=64, clock=None):
        self.env = env
        self.z_choices = tuple(int(z) for z in z_steps_choices)
        if not self.z_choices:
            raise ValueError('z_steps_choices is empty')
        if any(z < 0 for z in self.z_choices):
            raise ValueError('z_steps must be >= 0')

        self.mask_aoi_dims = bool(mask_aoi_dims)
        self._hist = deque(maxlen=max(int(history_cap), max(self.z_choices) + 1))
        self._z_steps = 0
        self._last_aoi_s = 0.0
        self._last_obs_utils = ()
        self._last_obs_snapshot = {}
        self._episode_seed = 0
        self._clock = clock  # accepted for older callers; sim-time is canonical

        self.action_space = env.action_space
        self.observation_space = env.observation_space

    def __getattr__(self, name):
        return getattr(self.env, name)

    def _pick_z(self, seed):
        """Choose z deterministically from seed."""
        if len(self.z_choices) == 1:
            return self.z_choices[0]
        rng = np.random.default_rng(int(seed) + 987_654)
        return int(rng.choice(self.z_choices))

    def _record(self):
        """Timestamp a full copy of the true per-link rho snapshot."""
        self._hist.append((self._sim_time_s(), dict(self.env._rho)))

    def _sim_time_s(self):
        """Nominal simulator time in seconds.

        The simulator does not sleep, so wall-clock AoI would be microseconds.
        This explicit clock puts AoI on the same scale as the real twin sync
        period and keeps Phase-11 AoI features alive.
        """
        return float(self.env.step_count) * float(self.env.STEP_DURATION_S)

    def _warmup(self):
        """Pre-fill history so large z is not clipped by short episodes.

        The real twin has history before a flow arrives. Build that past in a
        local copy only: calling env._drift() here would advance env._rng and
        break zero-divergence.
        """
        if self._z_steps <= 0:
            return

        sigma = float(self.env.load_cfg.get('drift_sigma', 0.05))
        rng = np.random.default_rng((int(self._episode_seed) + 555_111) % (2**32))
        depth = max(self.z_choices)
        past = dict(self.env._rho)
        chain = []
        for _ in range(depth):
            past = {
                link: float(np.clip(rho + rng.normal(0.0, sigma), 0.02, 1.10))
                for link, rho in past.items()
            }
            chain.append(dict(past))

        # _observed_snapshot indexes positionally with len(hist)-1-z, so the
        # deque must be ordered oldest -> newest. The past RNG is seeded from
        # the episode seed only, never z, so z changes only "how far back".
        for k in range(depth, 0, -1):
            t = self._sim_time_s() - k * float(self.env.STEP_DURATION_S)
            self._hist.append((t, chain[k - 1]))

    def _observed_snapshot(self):
        """Return ``(snapshot_seen_by_agent, measured_aoi_seconds)``."""
        if not self._hist:
            return dict(self.env._rho), 0.0

        idx = max(0, len(self._hist) - 1 - self._z_steps)
        t_rec, snap = self._hist[idx]
        if self._z_steps == 0:
            return snap, 0.0
        return snap, max(0.0, self._sim_time_s() - t_rec)

    def _rebuild_obs(self):
        """Rebuild state from a raw snapshot; never patch obs[2:4]."""
        snap, aoi_s = self._observed_snapshot()
        node = self.env.current

        utils_obs = []
        for nb in self.env.adj[node]:
            link = (node, nb)
            utils_obs.append(snap.get(link, self.env._rho[link]))

        self._last_aoi_s = aoi_s
        self._last_obs_utils = tuple(float(x) for x in utils_obs)
        self._last_obs_snapshot = dict(snap)

        obs = build_route_state(
            current_idx=self.env.node_to_idx[node],
            n_nodes=self.env.n_nodes,
            step=self.env.step_count,
            max_steps=self.env.max_steps,
            neighbor_utils=utils_obs,
            neighbor_valid=self.env.valid_mask(),
            aoi_s=aoi_s,
        )
        if self.mask_aoi_dims:
            obs = mask_aoi(obs)
        return obs

    def _augment_info(self, info):
        info = dict(info)
        true_utils = tuple(float(x) for x in self.env.true_utils())
        obs_utils_rounded = tuple(round(x, 9) for x in self._last_obs_utils)
        true_utils_rounded = tuple(round(x, 9) for x in true_utils)
        info['z_steps'] = int(self._z_steps)
        info['aoi_measured_s'] = round(float(self._last_aoi_s), 4)
        info['neighbor_utils_observed'] = list(self._last_obs_utils)
        info['rho_snapshot_observed'] = dict(self._last_obs_snapshot)
        info['util_is_stale'] = obs_utils_rounded != true_utils_rounded
        return info

    def reset(self, seed=None, options=None):
        _obs, info = self.env.reset(seed=seed, options=options)
        self._hist.clear()
        self._episode_seed = seed if seed is not None else 0
        self._z_steps = self._pick_z(self._episode_seed)
        self._warmup()
        self._record()
        obs = self._rebuild_obs()
        return obs, self._augment_info(info)

    def step(self, action):
        _obs, reward, terminated, truncated, info = self.env.step(action)
        self._record()
        obs = self._rebuild_obs()
        return obs, reward, terminated, truncated, self._augment_info(info)

    def close(self):
        if hasattr(self.env, 'close'):
            self.env.close()

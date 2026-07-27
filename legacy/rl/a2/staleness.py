#!/usr/bin/env python3
"""Controlled demand-staleness wrapper for A2.

The wrapper changes only what the agent observes: demand can be delayed by a
fixed number of environment steps while goodput and reward remain fresh.  This
isolates observation age from Mininet timing, sync CPU load, and goodput AoI.
"""

import time
from collections import deque

import numpy as np

from rl.a2.state_a2 import build_a2_state, mask_aoi


class StalenessWrapper:
    """Wrap ``TwinEnvA2`` and return observations with stale demand."""

    def __init__(self, env, z_steps_choices=(0,), mask_aoi_dims=False,
                 history_cap=64):
        self.env = env
        self.z_choices = tuple(int(z) for z in z_steps_choices)
        if not self.z_choices:
            raise ValueError('z_steps_choices is empty')
        if any(z < 0 for z in self.z_choices):
            raise ValueError('z_steps must be >= 0')

        self.mask_aoi_dims = bool(mask_aoi_dims)
        self._hist = deque(maxlen=int(history_cap))
        self._z_steps = 0
        self._last_aoi_s = 0.0
        self._last_obs_demand = (0.0, 0.0)

        self.action_space = env.action_space
        self.observation_space = env.observation_space

    def __getattr__(self, name):
        return getattr(self.env, name)

    def _pick_z(self, seed):
        if len(self.z_choices) == 1:
            return self.z_choices[0]
        rng = np.random.default_rng(int(seed) + 987_654)
        return int(rng.choice(self.z_choices))

    def _record(self, demand):
        self._hist.append((time.monotonic(), float(demand[0]), float(demand[1])))

    def _observed_demand(self):
        if not self._hist:
            demand = self.env.true_demand()
            return float(demand[0]), float(demand[1]), 0.0

        idx = max(0, len(self._hist) - 1 - self._z_steps)
        t_rec, demand_a, demand_b = self._hist[idx]
        aoi_s = max(0.0, time.monotonic() - t_rec)
        return demand_a, demand_b, aoi_s

    def _rebuild_obs(self, info):
        demand_a_obs, demand_b_obs, aoi_s = self._observed_demand()
        self._last_aoi_s = aoi_s
        self._last_obs_demand = (demand_a_obs, demand_b_obs)

        obs = build_a2_state(
            alloc_level_norm=info['alloc_level_norm'],
            goodput_A=info['goodput_A'],
            goodput_B=info['goodput_B'],
            demand_A=demand_a_obs,
            demand_B=demand_b_obs,
            c_total=self.env.c_total,
            step_progress=info['t'] / max(self.env.t_max, 1),
            last_action=self.env._last_action,
            n_actions=self.env.alloc.n_actions,
            aoi_s=aoi_s,
        )
        if self.mask_aoi_dims:
            obs = mask_aoi(obs)
        return obs

    def _augment_info(self, info):
        info = dict(info)
        info['z_steps'] = int(self._z_steps)
        info['aoi_measured_s'] = round(float(self._last_aoi_s), 4)
        info['demand_A_observed'] = self._last_obs_demand[0]
        info['demand_B_observed'] = self._last_obs_demand[1]
        true_demand = tuple(float(x) for x in self.env.true_demand())
        info['demand_is_stale'] = self._last_obs_demand != true_demand
        return info

    def reset(self, seed=None, options=None):
        _obs, info = self.env.reset(seed=seed, options=options)
        self._hist.clear()
        self._z_steps = self._pick_z(seed if seed is not None else 0)
        self._record(self.env.true_demand())
        obs = self._rebuild_obs(info)
        return obs, self._augment_info(info)

    def step(self, action):
        _obs, reward, terminated, truncated, info = self.env.step(action)
        self._record(self.env.true_demand())
        obs = self._rebuild_obs(info)
        return obs, reward, terminated, truncated, self._augment_info(info)

    def close(self):
        if hasattr(self.env, 'close'):
            self.env.close()

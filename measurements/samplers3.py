#!/usr/bin/env python3
"""Sampler adapter for the Phase 14 three-path topology.

Public observations contain only ``rho``. The event schedule, event phase, and
base levels are not returned to the meter or any future adversarial probe.
"""

from __future__ import annotations

import numpy as np

from rl.routing3 import link_model as link_model
from rl.routing3 import reward3
from rl.routing3 import topology3 as T3


class Sampler3Path:
    """Sampler for the three symmetric routing paths."""

    actions = T3.PATH_NAMES

    def __init__(self, episode_len=T3.EPISODE_LEN):
        self.episode_len = int(episode_len)
        self.link_cfg = T3.link_cfg()
        self.link_model_path = "rl/routing3/link_model.py"
        self.reward_model_path = "rl/routing3/reward3.py"
        self.dynamics_source_path = "rl/routing3/topology3.py"
        self.load_cfg_name = (
            f"EVENT_3PATH_V4_RATE_{T3.EVENT_RATE:g}"
            f"_PROFILE_{T3.LOAD_PROFILE}"
            f"_BIAS_{T3.CRASH_BIAS_TEMP:g}"
        )

    def sample_observation(self, z_choices, rng):
        """Return a public stale snapshot and independently sampled z."""
        levels = T3.sample_observation_levels(rng, self.episode_len)
        z_true = int(rng.choice(tuple(z_choices)))
        return {"rho": T3.levels_to_rho(levels)}, z_true

    def roll_forward(self, obs, z, rng):
        """Sample one possible true world z steps after public observation."""
        if int(z) <= 0:
            return {"rho": dict(obs["rho"])}
        levels = T3.rho_to_levels(obs["rho"])
        future = T3.advance_levels(levels, int(z), rng)
        return {"rho": T3.levels_to_rho(T3.observe_levels(future, rng))}

    def reward_of(self, action, true_world):
        """Score an action on the true world only."""
        if action not in T3.PATH_LINKS:
            raise ValueError(f"unknown action: {action!r}")
        rho = true_world["rho"]
        return float(self._path_reward(T3.PATH_LINKS[action], rho))

    def _path_reward(self, path, rho):
        total = 0.0
        last_idx = len(path) - 1
        for idx, link in enumerate(path):
            meta = self.link_cfg[link]
            rho_offered = float(rho[link])
            delay_ms = link_model.total_delay_ms(
                meta["base_delay"],
                rho_offered,
                bw_mbps=meta["base_bw"],
                queue_pkts=meta["queue_pkts"],
            )
            total += reward3.step_reward(
                delay_ms,
                link_model.loss_rate(rho_offered),
                arrived=(idx == last_idx),
            ).total
        return float(total)

#!/usr/bin/env python3
"""Heterogeneous-volatility sampler for the Phase 14 three-path topology.

This keeps the routing3 stage, link model, and reward model intact. The only
structural change from ``Sampler3Path`` is that each path can have its own
public volatility rate. Because ``vol`` is included in the observation, both the
z-aware and z-blind Bayes branches see it; the only difference remains whether
the branch knows the realized age z.
"""

from __future__ import annotations

from rl.routing3 import link_model as LM
from rl.routing3 import reward3
from rl.routing3 import topology3 as T3


class Sampler3PathHetero:
    """Routing3 sampler where path volatility is heterogeneous and public."""

    actions = T3.PATH_NAMES

    def __init__(self, rates=(0.0, 0.10, 0.35), coupling="by_load"):
        if coupling not in {"by_load", "random"}:
            raise ValueError("coupling must be 'by_load' or 'random'")

        self.rates = tuple(float(rate) for rate in rates)
        if len(self.rates) != len(T3.PATH_NAMES):
            raise ValueError("rates must contain one value per path")

        self.coupling = coupling
        self.link_cfg = T3.link_cfg()
        self.link_model_path = "rl/routing3/link_model.py"
        self.reward_model = "r_v2"
        self.reward_model_path = "rl/routing3/reward3.py"
        self.dynamics_source_path = "measurements/samplers3_hetero.py"
        self.load_cfg_name = (
            f"HETERO_{coupling}_"
            + "_".join(f"{rate:g}" for rate in self.rates)
        )

    def sample_observation(self, z_choices, rng):
        """Return a public stale snapshot with public path volatilities."""
        levels = T3.sample_observation_levels(rng, T3.EPISODE_LEN)

        if self.coupling == "random":
            perm = rng.permutation(len(T3.PATH_NAMES))
            vol = {
                T3.PATH_NAMES[idx]: self.rates[int(perm[idx])]
                for idx in range(len(T3.PATH_NAMES))
            }
        else:
            # The currently least-loaded path is most likely to attract traffic,
            # so it is modeled as the most volatile path.
            paths_by_load = sorted(T3.PATH_NAMES, key=lambda path: levels[path])
            rates_hi_to_lo = sorted(self.rates, reverse=True)
            vol = {
                path: rates_hi_to_lo[idx]
                for idx, path in enumerate(paths_by_load)
            }

        z_true = int(rng.choice(tuple(z_choices)))
        return {"rho": T3.levels_to_rho(levels), "vol": vol}, z_true

    def roll_forward(self, obs, z, rng):
        """Sample one possible true world z steps after the observation."""
        levels = T3.rho_to_levels(obs["rho"])
        vol = dict(obs["vol"])

        for _step in range(max(0, int(z))):
            for path in T3.PATH_NAMES:
                if float(rng.random()) < float(vol[path]):
                    load_band = T3.CRASH_LOAD if rng.random() < 0.5 else T3.FREE_LOAD
                    levels[path] = T3._u(rng, load_band)

        noisy = T3.observe_levels(levels, rng)
        return {"rho": T3.levels_to_rho(noisy), "vol": vol}

    def reward_of(self, action, true_world):
        """Score an action using the original routing3 reward."""
        if action not in T3.PATH_LINKS:
            raise ValueError(f"unknown action: {action!r}")

        rho = true_world["rho"]
        total = 0.0
        path = T3.PATH_LINKS[action]
        last_idx = len(path) - 1
        for idx, link in enumerate(path):
            meta = self.link_cfg[link]
            offered = float(rho[link])
            delay_ms = LM.total_delay_ms(
                meta["base_delay"],
                offered,
                bw_mbps=meta["base_bw"],
                queue_pkts=meta["queue_pkts"],
            )
            total += reward3.step_reward(
                delay_ms,
                LM.loss_rate(offered),
                arrived=(idx == last_idx),
            ).total
        return float(total)

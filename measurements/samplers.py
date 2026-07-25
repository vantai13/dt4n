#!/usr/bin/env python3
"""Topology adapters for the marginalized-gap measurement.

The measurement code talks only to this small interface:

    actions
    sample_observation(z_choices, rng)
    roll_forward(obs, z, rng)
    reward_of(action, true_world)

Keep reward_of deliberately narrow: it receives the true world only, not the
observation and not z. That makes stale-observation leakage hard to express.
"""

from __future__ import annotations

import numpy as np


class Sampler2Path:
    """Adapter for rl.routing_2path used as the Phase 14 negative control."""

    actions = ("E", "F")

    def __init__(self, load_cfg_name="LOAD_CFG_DYNAMIC", reward_model="default"):
        from rl.routing_2path import topology_r as topology
        from rl.routing_2path.link_model import loss_rate, total_delay_ms

        reward_model = "r_v2" if reward_model == "default" else str(reward_model)
        if reward_model == "r_v2":
            from rl.routing_2path.reward_r import step_reward

            reward_model_path = "rl/routing_2path/reward_r.py"
        elif reward_model == "r_v3":
            from rl.routing3.reward3_v3 import step_reward

            reward_model_path = "rl/routing3/reward3_v3.py"
        else:
            raise ValueError(f"unknown reward_model: {reward_model!r}")

        self.topology = topology
        self.load_cfg_name = load_cfg_name
        self.link_model_path = "rl/routing_2path/link_model.py"
        self.reward_model = reward_model
        self.reward_model_path = reward_model_path
        self.dynamics_source_path = "rl/routing_2path/route_env.py"
        self.loss_rate = loss_rate
        self.step_reward = step_reward
        self.total_delay_ms = total_delay_ms
        self.load_cfg = getattr(topology, load_cfg_name)

        self.link_keys = [
            (src, dst)
            for src, dst, _delay_ms, _bw_mbps in topology.TOPO_V2["edges"]
        ]
        self.link_cfg = {
            (src, dst): {
                "base_delay": float(delay_ms),
                "base_bw": float(bw_mbps),
                "queue_pkts": topology.TOPO_V2.get("default_queue_pkts"),
            }
            for src, dst, delay_ms, bw_mbps in topology.TOPO_V2["edges"]
        }

        self.e_links = tuple(topology.VIA_E_LINKS)
        self.f_links = tuple(topology.DIRECT_F_LINKS)
        self.path_links = {
            "E": (
                (("C", "E"), ("E", "F"), ("F", "DST")),
                (("D", "E"), ("E", "F"), ("F", "DST")),
            ),
            "F": (
                (("C", "F"), ("F", "DST")),
                (("D", "F"), ("F", "DST")),
            ),
        }

    def sample_observation(self, z_choices, rng):
        """Sample a public stale snapshot and its true age z.

        Scenario labels and resolved load config are intentionally discarded.
        They are generator context, not policy-visible observation.
        """
        rho, _scenario_name, _active_cfg = self.topology.sample_offered_load(
            self.link_keys,
            self.load_cfg,
            rng,
        )
        z_true = int(rng.choice(tuple(z_choices)))
        return {"rho": dict(rho)}, z_true

    def roll_forward(self, obs, z, rng):
        """Run the old RouteEnv offered-load dynamics forward z steps."""
        if int(z) <= 0:
            return {"rho": dict(obs["rho"])}
        cfg = self._sample_dynamics_cfg(obs, rng)
        return self._roll_forward_with_cfg(obs, z, cfg, rng)

    def _roll_forward_with_cfg(self, obs, z, cfg, rng):
        """Run dynamics with one resolved cfg.

        This is split out so tests can compare the adapter with RouteEnv's
        drift equation directly.
        """
        rho = dict(obs["rho"])
        steps = int(z)
        if steps <= 0:
            return {"rho": rho}

        sigma = float(cfg.get("drift_sigma", self.load_cfg.get("drift_sigma", 0.05)))
        lo = float(self.topology.OFFERED_LOAD_MIN)
        hi = float(
            cfg.get(
                "offered_load_max",
                self.topology.default_offered_load_max(self.load_cfg),
            )
        )

        for _ in range(steps):
            for link, value in list(rho.items()):
                delta = self._trend_for(link, cfg)
                if sigma > 0.0:
                    delta += float(rng.normal(0.0, sigma))
                rho[link] = float(np.clip(float(value) + delta, lo, hi))

        return {"rho": rho}

    def reward_of(self, action, true_world):
        """Score one action on the true world, never on the observation."""
        if action not in self.path_links:
            raise ValueError(f"unknown action: {action!r}")

        rho = true_world["rho"]
        rewards = [
            self._route_reward(path, rho)
            for path in self.path_links[action]
        ]
        return float(np.mean(rewards))

    def _trend_for(self, link, cfg):
        if link in self.e_links:
            return float(cfg.get("e_trend", 0.0))
        if link in self.f_links:
            return float(cfg.get("direct_trend", cfg.get("f_trend", 0.0)))
        return float(cfg.get("base_trend", 0.0))

    def _route_reward(self, path, rho):
        total = 0.0
        last_idx = len(path) - 1
        for idx, link in enumerate(path):
            meta = self.link_cfg[link]
            delay_ms = self.total_delay_ms(
                meta["base_delay"],
                float(rho[link]),
                bw_mbps=meta["base_bw"],
                queue_pkts=meta["queue_pkts"],
            )
            loss = self.loss_rate(float(rho[link]))
            total += self.step_reward(
                delay_ms,
                loss,
                arrived=(idx == last_idx),
            ).total
        return float(total)

    def _sample_dynamics_cfg(self, obs, rng):
        """Sample hidden dynamics from the posterior induced by public rho."""
        scenarios = self.load_cfg.get("scenarios")
        mix = self.load_cfg.get("scenario_mix")
        if not mix and isinstance(scenarios, dict):
            mix = tuple(scenarios)
        if not mix:
            return self.topology.choose_load_scenario(self.load_cfg, rng)[0]

        candidates = []
        weights = self.load_cfg.get("scenario_weights") or {}
        for scenario_name in mix:
            cfg, _name = self.topology.resolve_load_scenario(
                self.load_cfg,
                scenario_name,
            )
            likelihood = self._obs_likelihood_under_cfg(obs, cfg)
            weight = float(weights.get(scenario_name, 1.0)) * likelihood
            if weight > 0.0:
                candidates.append((scenario_name, weight))

        if not candidates:
            return self.topology.choose_load_scenario(self.load_cfg, rng)[0]

        probs = np.asarray([weight for _name, weight in candidates], dtype=float)
        probs /= probs.sum()
        idx = int(rng.choice(len(candidates), p=probs))
        cfg, _name = self.topology.resolve_load_scenario(
            self.load_cfg,
            candidates[idx][0],
        )
        return self.topology._resolve_episode_trends(cfg, rng)

    def _obs_likelihood_under_cfg(self, obs, cfg):
        rho = obs["rho"]
        e_level = float(np.mean([rho[link] for link in self.e_links]))
        f_level = float(np.mean([rho[link] for link in self.f_links]))
        base_lo, base_hi = self._load_pair(cfg, "base_load", (0.25, 0.40))
        e_lo, e_hi = self._load_pair(cfg, "e_load", (0.60, 0.95))
        if "direct_load" in cfg:
            f_lo, f_hi = self._load_pair(cfg, "direct_load", (base_lo, base_hi))
        else:
            f_lo, f_hi = self._load_pair(cfg, "f_load", (base_lo, base_hi))
        return self._uniform_density(e_level, e_lo, e_hi) * self._uniform_density(
            f_level,
            f_lo,
            f_hi,
        )

    @staticmethod
    def _load_pair(cfg, key, default):
        lo, hi = cfg.get(key, default)
        return float(lo), float(hi)

    @staticmethod
    def _uniform_density(value, lo, hi):
        lo = float(lo)
        hi = float(hi)
        value = float(value)
        if hi < lo:
            return 0.0
        if not (lo <= value <= hi):
            return 0.0
        width = max(hi - lo, 1e-12)
        return 1.0 / width


def build_sampler(name, **kwargs):
    """Build a sampler by topology name."""
    if name == "routing_2path":
        return Sampler2Path(**kwargs)
    if name == "routing3":
        from measurements.samplers3 import Sampler3Path

        return Sampler3Path(**kwargs)
    raise ValueError(f"unknown topology: {name}")

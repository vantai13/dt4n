#!/usr/bin/env python3
"""Measurement metrics for the routing AoI stage."""

from dataclasses import asdict, dataclass, field

import numpy as np

from rl.routing_2path.baselines import ospf_calibrated, ospf_reactive
from rl.routing_2path.ditto_staleness_r import DittoStalenessWrapper
from rl.routing_2path.oracles import clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.topology_r import TOPO


SAFE_HOP = 'F'


@dataclass
class EpisodeStats:
    total_reward: float = 0.0
    steps: int = 0
    arrived: bool = False
    truncated: bool = False
    decisions: int = 0
    wrong: int = 0
    safe_opportunities: int = 0
    safe_choices: int = 0
    stale_steps: int = 0
    aoi_samples: list = field(default_factory=list)
    path: list = field(default_factory=list)

    def as_dict(self):
        data = asdict(self)
        data['wrong_rate'] = self.wrong / max(self.decisions, 1)
        data['safe_path_freq'] = self.safe_choices / max(self.safe_opportunities, 1)
        data['aoi_mean_s'] = float(np.mean(self.aoi_samples)) if self.aoi_samples else 0.0
        return data


def _valid_action(env, info, action):
    valid = np.flatnonzero(info['valid_mask'])
    if len(valid) == 0:
        return 0
    action = int(action)
    return action if action in set(valid.tolist()) else int(valid[0])


def run_episode(env, policy_fn, seed, target_fn=None):
    """Roll out one episode and optionally score actions against clairvoyance."""
    _obs, info = env.reset(seed=seed)
    stats = EpisodeStats(path=[info['current_node']])

    for _ in range(env.max_steps + 1):
        node = info['current_node']
        valid = np.flatnonzero(info['valid_mask'])
        n_valid = len(valid)
        action = _valid_action(env, info, policy_fn(env, info))

        if target_fn is not None and n_valid > 1:
            best = _valid_action(env, info, target_fn(env, info))
            stats.decisions += 1
            stats.wrong += int(action != best)

        neighbors = env.adj[node]
        if n_valid > 1 and SAFE_HOP in neighbors:
            stats.safe_opportunities += 1
            stats.safe_choices += int(neighbors[action] == SAFE_HOP)

        stats.aoi_samples.append(float(info.get('aoi_measured_s', 0.0)))
        stats.stale_steps += int(bool(info.get('util_is_stale', False)))

        _obs, reward, terminated, truncated, info = env.step(action)
        stats.total_reward += float(reward)
        stats.steps += 1
        stats.path.append(info['current_node'])

        if terminated or truncated:
            stats.arrived = bool(info.get('arrived', False))
            stats.truncated = bool(truncated)
            break

    return stats


def make_env(z_steps, seed=0, load_cfg=None, max_steps=15):
    """Create a wrapped RouteEnv at a fixed z."""
    base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=max_steps, seed=seed)
    return StalenessWrapper(base, z_steps_choices=(int(z_steps),))


def make_ditto_env(sync_period_s, seed=0, load_cfg=None, max_steps=15,
                   phase_s=None):
    """Create a RouteEnv wrapped by physical-time Ditto staleness."""
    base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=max_steps, seed=seed)
    return DittoStalenessWrapper(
        base,
        sync_period_s=float(sync_period_s),
        seed=seed,
        phase_s=phase_s,
    )


def summarize_episode_stats(rows):
    """Average a list of EpisodeStats dictionaries."""
    if not rows:
        return {}
    return {
        'return': float(np.mean([r['total_reward'] for r in rows])),
        'steps': float(np.mean([r['steps'] for r in rows])),
        'arrived': float(np.mean([r['arrived'] for r in rows])),
        'wrong_rate': float(np.mean([r['wrong_rate'] for r in rows])),
        'safe_path_freq': float(np.mean([r['safe_path_freq'] for r in rows])),
        'aoi_mean_s': float(np.mean([r['aoi_mean_s'] for r in rows])),
        'stale_steps': float(np.mean([r['stale_steps'] for r in rows])),
    }


def evaluate_policy(policy_fn, z_steps, seeds, load_cfg=None):
    """Evaluate one policy over fixed seeds at a fixed z."""
    rows = []
    for seed in seeds:
        env = make_env(z_steps, seed=seed, load_cfg=load_cfg)
        rows.append(
            run_episode(
                env,
                policy_fn,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows)


def evaluate_policy_sync(policy_fn, sync_period_s, seeds, load_cfg=None,
                         phase_s=None):
    """Evaluate one policy over fixed seeds at a fixed Ditto sync period."""
    rows = []
    for seed in seeds:
        env = make_ditto_env(
            sync_period_s,
            seed=seed,
            load_cfg=load_cfg,
            phase_s=phase_s,
        )
        rows.append(
            run_episode(
                env,
                policy_fn,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
    return summarize_episode_stats(rows)


def evaluate_z(z_steps, seeds, load_cfg=None, blind_policy=None,
               baseline_policy=None):
    """Evaluate clairvoyant, blind, and OSPF for one z."""
    from rl.routing_2path.oracles import blind_dijkstra

    blind_policy = blind_policy or blind_dijkstra
    baseline_policy = baseline_policy or ospf_calibrated
    clair = evaluate_policy(clairvoyant_dijkstra, z_steps, seeds, load_cfg)
    blind = evaluate_policy(blind_policy, z_steps, seeds, load_cfg)
    ospf = evaluate_policy(baseline_policy, z_steps, seeds, load_cfg)
    ospf0 = evaluate_policy(ospf_reactive, z_steps, seeds, load_cfg)

    return {
        'z_steps': int(z_steps),
        'aoi_mean_s': blind['aoi_mean_s'],
        'clair_return': clair['return'],
        'blind_return': blind['return'],
        'ospf_return': ospf['return'],
        'ospf_reactive_return': ospf0['return'],
        'cost_of_blindness': clair['return'] - blind['return'],
        'wrong_excess': blind['wrong_rate'] - clair['wrong_rate'],
        'voi_headroom': max(blind['return'], ospf['return']) - blind['return'],
        'clair_safe_path_freq': clair['safe_path_freq'],
        'blind_safe_path_freq': blind['safe_path_freq'],
        'clair_wrong_rate': clair['wrong_rate'],
        'blind_wrong_rate': blind['wrong_rate'],
    }


def evaluate_sync_period(sync_period_s, seeds, load_cfg=None, blind_policy=None,
                         baseline_policy=None, phase_s=None):
    """Evaluate clairvoyant, blind, and OSPF for one Ditto sync period."""
    from rl.routing_2path.oracles import blind_dijkstra

    blind_policy = blind_policy or blind_dijkstra
    baseline_policy = baseline_policy or ospf_calibrated
    clair = evaluate_policy_sync(
        clairvoyant_dijkstra,
        sync_period_s,
        seeds,
        load_cfg=load_cfg,
        phase_s=phase_s,
    )
    blind = evaluate_policy_sync(
        blind_policy,
        sync_period_s,
        seeds,
        load_cfg=load_cfg,
        phase_s=phase_s,
    )
    ospf = evaluate_policy_sync(
        baseline_policy,
        sync_period_s,
        seeds,
        load_cfg=load_cfg,
        phase_s=phase_s,
    )
    ospf0 = evaluate_policy_sync(
        ospf_reactive,
        sync_period_s,
        seeds,
        load_cfg=load_cfg,
        phase_s=phase_s,
    )

    return {
        'sync_period_s': float(sync_period_s),
        'aoi_mean_s': blind['aoi_mean_s'],
        'clair_return': clair['return'],
        'blind_return': blind['return'],
        'ospf_return': ospf['return'],
        'ospf_reactive_return': ospf0['return'],
        'cost_of_blindness': clair['return'] - blind['return'],
        'wrong_excess': blind['wrong_rate'] - clair['wrong_rate'],
        'voi_headroom': max(blind['return'], ospf['return']) - blind['return'],
        'clair_safe_path_freq': clair['safe_path_freq'],
        'blind_safe_path_freq': blind['safe_path_freq'],
        'clair_wrong_rate': clair['wrong_rate'],
        'blind_wrong_rate': blind['wrong_rate'],
        'blind_stale_steps': blind['stale_steps'],
    }


def evaluate_z_range(z_values=(0, 1, 2, 3, 5, 8), seeds=range(100),
                     load_cfg=None, baseline_policy=None):
    """Evaluate the main oracle/baseline table across z."""
    return [
        evaluate_z(z, seeds, load_cfg=load_cfg, baseline_policy=baseline_policy)
        for z in z_values
    ]


def evaluate_sync_range(sync_periods=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
                        seeds=range(100), load_cfg=None,
                        baseline_policy=None, phase_s=None):
    """Evaluate the main oracle/baseline table across Ditto sync periods."""
    return [
        evaluate_sync_period(
            period,
            seeds,
            load_cfg=load_cfg,
            baseline_policy=baseline_policy,
            phase_s=phase_s,
        )
        for period in sync_periods
    ]

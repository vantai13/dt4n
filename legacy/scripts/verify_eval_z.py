#!/usr/bin/env python3
"""Verify fixed-z probe observations at the C/D decision nodes."""

from __future__ import annotations

import argparse
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import AOI_DIMS
from rl.routing_2path.topology_r import (
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
)


PROBE_PREFIXES = {
    'C': ('A', 'C'),
    'D': ('B', 'D'),
}


def parse_int_list(value: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in str(value).split(',') if x.strip())


def build_load_cfg(kind: str) -> dict:
    if kind == 'dynamic':
        return {
            'scenarios': SCENARIOS_DYNAMIC,
            'scenario_mix': tuple(SCENARIOS_DYNAMIC),
        }
    if kind == 'static':
        return {
            'scenarios': SCENARIOS_TRAIN,
            'scenario_mix': tuple(SCENARIOS_TRAIN),
        }
    if kind == 'asym':
        return LOAD_CFG_ASYM
    return LOAD_CFG_ABLATION


def make_env(load_cfg: dict, z: int, seed: int, max_steps: int):
    base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=max_steps, seed=seed)
    return StalenessWrapper(base, z_steps_choices=(int(z),))


def force_prefix(env, obs, info, prefix: tuple[str, ...]):
    for next_hop in prefix:
        node = info['current_node']
        action = env.adj[node].index(next_hop)
        obs, _reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    return obs, info


def fmt(values) -> str:
    return '[' + ', '.join(f'{float(value):.3f}' for value in values) + ']'


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['dynamic', 'static', 'mix', 'asym'],
                        default='dynamic')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--z-values', '--z_values', default='0,2,4,6',
                        dest='z_values')
    parser.add_argument('--probe-node', choices=['C', 'D', 'both'],
                        default='both')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    load_cfg = build_load_cfg(args.scenario)
    z_values = parse_int_list(args.z_values)
    probe_nodes = ('C', 'D') if args.probe_node == 'both' else (args.probe_node,)
    failed = False

    print('Check: fixed z must reach the decision node with matching AoI.')
    for probe in probe_nodes:
        print(f'\nprobe_{probe}')
        for z in z_values:
            env = make_env(load_cfg, z=z, seed=args.seed, max_steps=args.max_steps)
            obs, info = env.reset(seed=args.seed)
            obs, info = force_prefix(env, obs, info, PROBE_PREFIXES[probe])

            node = info['current_node']
            links = [(node, nb) for nb in env.adj[node]]
            true = [info['rho_offered_snapshot'][link] for link in links]
            seen = [info['rho_offered_snapshot_observed'][link] for link in links]
            obs_aoi = [obs[idx] for idx in AOI_DIMS]
            z_seen = int(info.get('z_steps', -1))
            aoi_s = float(info.get('aoi_measured_s', 0.0))
            stale = bool(info.get('util_is_stale', False))

            if z_seen != int(z):
                failed = True
            if int(z) > 0 and aoi_s <= 0.0:
                failed = True

            print(
                f'  z={z:2d} z_seen={z_seen:2d} aoi_s={aoi_s:4.1f} '
                f'stale={str(stale):5s} obs_aoi={fmt(obs_aoi):>14s} '
                f'true={fmt(true):>16s} seen={fmt(seen):>16s}'
            )

    if failed:
        print('\nFAIL: at least one fixed-z probe did not expose the requested z.')
        return 1

    print('\nPASS: eval fixed-z plumbing is alive for every requested z.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

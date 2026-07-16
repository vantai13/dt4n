#!/usr/bin/env python3
"""Routing baselines: opponents, distinct from Dijkstra instruments."""

import numpy as np

from rl.routing.oracles import _hop_to_action, dijkstra_next_hop


def ospf_reactive(env, info):
    """Strawman static shortest path by base delay; ignores load and twin.

    Retained only as a reference. Do not use it to define the breaking point:
    on TOPO V2 it walks into the E bottleneck by construction because E has the
    shorter base delay.
    """
    node = info['current_node']
    empty_view = {link: 0.0 for link in env.link}
    next_hop = dijkstra_next_hop(env, empty_view, source=node)
    return _hop_to_action(env, node, next_hop)


def ospf_calibrated(env, info):
    """Twin-free OSPF-like baseline using expected load.

    This models an admin who knows capacity/history and sets static weights
    accordingly, while still ignoring instantaneous twin state.
    """
    node = info['current_node']
    e_lo, e_hi = env.load_cfg.get('e_load', (0.60, 0.95))
    b_lo, b_hi = env.load_cfg.get('base_load', (0.25, 0.40))
    e_mean = 0.5 * (float(e_lo) + float(e_hi))
    b_mean = 0.5 * (float(b_lo) + float(b_hi))
    bottlenecks = {('C', 'E'), ('D', 'E')}
    view = {
        link: (e_mean if link in bottlenecks else b_mean)
        for link in env.link
    }
    next_hop = dijkstra_next_hop(env, view, source=node)
    return _hop_to_action(env, node, next_hop)


def ecmp_static(env, info):
    """Deterministic ECMP-like split among static shortest next hops."""
    node = info['current_node']
    valid = np.flatnonzero(info['valid_mask'])
    if len(valid) == 0:
        return 0
    if len(valid) == 1:
        return int(valid[0])
    return int(valid[int(info.get('step', 0)) % len(valid)])


def random_valid(env, info):
    """Uniform random valid action, seeded by episode state for repeatability."""
    valid = np.flatnonzero(info['valid_mask'])
    if len(valid) == 0:
        return 0
    seed = int(info.get('step', 0)) + 10_007 * len(info.get('path', ()))
    rng = np.random.default_rng(seed)
    return int(rng.choice(valid))

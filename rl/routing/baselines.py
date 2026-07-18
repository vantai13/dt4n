#!/usr/bin/env python3
"""Routing baselines: opponents, distinct from Dijkstra instruments."""

import numpy as np

from rl.routing.link_model import loss_rate
from rl.routing.oracles import (
    _hop_to_action,
    dijkstra_next_hop,
    dijkstra_next_hop_by_weight,
    edge_cost,
)
from rl.routing.topology_r import sample_offered_load


_EXPECTED_WEIGHT_SAMPLES = 2_000
_EXPECTED_WEIGHT_CACHE = {}


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
    """Twin-free OSPF-like baseline using expected link cost.

    This models a competent admin who knows capacity/history and sets static
    weights accordingly, while still ignoring instantaneous twin state.

    Lesson 9.4: use ``E[cost(rho)]``, not ``cost(E[rho])``. The calibrated link
    model has a finite-queue cliff near saturation, so using only mean load
    systematically underprices the E bottleneck and creates a straw baseline.
    """
    node = info['current_node']
    weights = expected_ospf_weights(env)
    next_hop = dijkstra_next_hop_by_weight(env, weights, source=node)
    return _hop_to_action(env, node, next_hop)


def _weight_cache_key(env, n_samples):
    """Return a stable cache key for one static expected-weight table."""
    links = tuple(
        (
            link,
            meta['base_delay'],
            meta['base_bw'],
            meta['queue_pkts'],
        )
        for link, meta in sorted(env.link.items())
    )
    return (
        repr(env.load_cfg),
        links,
        int(n_samples),
    )


def expected_ospf_weights(env, n_samples=_EXPECTED_WEIGHT_SAMPLES):
    """Return static expected edge costs for the calibrated OSPF baseline.

    Values are in reward-cost units and exclude the fixed hop penalty. A fixed
    RNG seed makes the baseline deterministic and reproducible.
    """
    key = _weight_cache_key(env, n_samples)
    if key in _EXPECTED_WEIGHT_CACHE:
        return dict(_EXPECTED_WEIGHT_CACHE[key])

    rng = np.random.default_rng(12_345)
    costs_by_link = {link: [] for link in env.link}

    for _ in range(int(n_samples)):
        offered, _scenario_name, _active_cfg = sample_offered_load(
            env.link.keys(),
            env.load_cfg,
            rng,
        )
        for link, meta in env.link.items():
            # [9.4] Fail loud: missing capacity/queue metadata is a modeling bug.
            # Using .get() would pass None to the link model, silently disabling
            # the finite queue ceiling and making OSPF use the wrong physics.
            base_delay = meta['base_delay']
            bw_mbps = meta['base_bw']
            queue_pkts = meta['queue_pkts']

            rho_offered = offered[link]
            loss = loss_rate(rho_offered)
            costs_by_link[link].append(
                edge_cost(
                    base_delay,
                    rho_offered,
                    loss=loss,
                    bw_mbps=bw_mbps,
                    queue_pkts=queue_pkts,
                )
            )

    weights = {
        link: float(np.mean(costs))
        for link, costs in costs_by_link.items()
    }

    _EXPECTED_WEIGHT_CACHE[key] = dict(weights)
    return dict(weights)


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

#!/usr/bin/env python3
"""Matched Dijkstra oracles: measuring instruments, not baselines.

clairvoyant_dijkstra uses the true rho snapshot.
blind_dijkstra uses the observed snapshot, which may be stale.

Both run the same algorithm over the same topology and differ only in the data
they are allowed to see. Their gap is the isolated cost of stale twin state.
"""

import heapq

from rl.routing.link_model import loss_rate, total_delay_ms
from rl.routing.reward_r import DELAY_NORM_MS, W_HOP, W_LOSS


def edge_cost(base_delay_ms, rho, loss=None, bw_mbps=None, queue_pkts=None):
    """Cost of traversing one link in reward units, not milliseconds."""
    delay_ms = total_delay_ms(
        base_delay_ms,
        rho,
        bw_mbps=bw_mbps,
        queue_pkts=queue_pkts,
    )
    if loss is None:
        loss = loss_rate(rho)
    return delay_ms / DELAY_NORM_MS + W_LOSS * float(loss)


def _hop_to_action(env, node, next_hop):
    """Convert a next-hop node name into an action index."""
    if next_hop is None:
        return 0
    try:
        return int(env.adj[node].index(next_hop))
    except ValueError:
        return 0


def dijkstra_next_hop(env, rho_view, loss_view=None, source=None, dest=None):
    """Return the next hop on the cheapest path under ``rho_view``."""
    src = source if source is not None else env.current
    dst = dest if dest is not None else env.destination
    if src == dst:
        return None

    dist = {node: float('inf') for node in env.nodes}
    prev = {node: None for node in env.nodes}
    dist[src] = 0.0
    pq = [(0.0, src)]
    seen = set()

    while pq:
        cur_dist, node = heapq.heappop(pq)
        if node in seen:
            continue
        seen.add(node)
        if node == dst:
            break

        for nb in env.adj[node]:
            link = (node, nb)
            rho = rho_view.get(link)
            if rho is None:
                continue
            loss = loss_view.get(link) if loss_view is not None else None
            link_cfg = env.link[link]
            base_delay = link_cfg['base_delay']
            new_dist = cur_dist + edge_cost(
                base_delay,
                rho,
                loss=loss,
                bw_mbps=link_cfg.get('base_bw'),
                queue_pkts=link_cfg.get('queue_pkts'),
            ) + W_HOP
            if new_dist < dist[nb]:
                dist[nb] = new_dist
                prev[nb] = node
                heapq.heappush(pq, (new_dist, nb))

    if dist[dst] == float('inf'):
        return None

    node = dst
    while prev[node] is not None and prev[node] != src:
        node = prev[node]
    return node if prev[node] == src else None


def dijkstra_next_hop_by_weight(env, weight_view, source=None, dest=None):
    """Return the next hop using precomputed per-edge weights.

    ``weight_view`` values are edge costs in reward units, excluding the fixed
    hop penalty. This is useful for static baselines whose weights are expected
    costs rather than instantaneous utilization observations.
    """
    src = source if source is not None else env.current
    dst = dest if dest is not None else env.destination
    if src == dst:
        return None

    dist = {node: float('inf') for node in env.nodes}
    prev = {node: None for node in env.nodes}
    dist[src] = 0.0
    pq = [(0.0, src)]
    seen = set()

    while pq:
        cur_dist, node = heapq.heappop(pq)
        if node in seen:
            continue
        seen.add(node)
        if node == dst:
            break

        for nb in env.adj[node]:
            link = (node, nb)
            weight = weight_view.get(link)
            if weight is None:
                continue
            new_dist = cur_dist + float(weight) + W_HOP
            if new_dist < dist[nb]:
                dist[nb] = new_dist
                prev[nb] = node
                heapq.heappush(pq, (new_dist, nb))

    if dist[dst] == float('inf'):
        return None

    node = dst
    while prev[node] is not None and prev[node] != src:
        node = prev[node]
    return node if prev[node] == src else None


def clairvoyant_dijkstra(env, info):
    """Optimal next hop under true utilization."""
    next_hop = dijkstra_next_hop(
        env,
        info['rho_snapshot'],
        loss_view=info.get('loss_snapshot'),
    )
    return _hop_to_action(env, info['current_node'], next_hop)


def blind_dijkstra(env, info):
    """Optimal next hop under the observed, possibly stale, utilization."""
    rho_view = info.get('rho_snapshot_observed', info['rho_snapshot'])
    loss_view = info.get('loss_snapshot_observed', info.get('loss_snapshot'))
    next_hop = dijkstra_next_hop(env, rho_view, loss_view=loss_view)
    return _hop_to_action(env, info['current_node'], next_hop)


def posthoc_dijkstra(env, info):
    """Optimal next hop under the next rho snapshot.

    This is not a deployable policy: it uses the future. It exists only to
    measure the drift noise floor so wrong-rate metrics do not credit drift to
    staleness.
    """
    rho_view = info.get('rho_snapshot_next')
    loss_view = info.get('loss_snapshot_next')
    if rho_view is None:
        rho_view = env.peek_next_rho()
    if loss_view is None:
        loss_view = env.peek_next_loss()
    next_hop = dijkstra_next_hop(env, rho_view, loss_view=loss_view)
    return _hop_to_action(env, info['current_node'], next_hop)

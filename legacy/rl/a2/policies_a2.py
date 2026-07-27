#!/usr/bin/env python3
"""A2 scripted policies: baselines plus demand-aware myopic oracle."""


def policy_noop(env, obs, info):
    return 0


def policy_equal(env, obs, info):
    """Always move back toward the middle allocation level."""
    mid = env.alloc.n_levels // 2
    cur = env.alloc._level
    if cur < mid:
        return 1
    if cur > mid:
        return 2
    return 0


def policy_greedy(env, obs, info):
    """Shift toward the branch with lower current satisfaction."""
    sat_a, sat_b = obs[5], obs[6]
    if sat_a < sat_b - 0.05:
        return 2
    if sat_b < sat_a - 0.05:
        return 1
    return 0


def _best_level_from_demand(env, d_a, d_b):
    """Return the greedy best allocation level for a demand pair."""
    best_level = 0
    best_score = -1.0
    for level, (c_a, c_b) in enumerate(env.alloc.levels):
        sat_a = min(c_a / d_a, 1.0) if d_a > 1e-6 else 1.0
        sat_b = min(c_b / d_b, 1.0) if d_b > 1e-6 else 1.0
        score = sat_a + sat_b
        if score > best_score:
            best_level = level
            best_score = score
    return best_level


def _step_toward(env, best_level):
    cur = env.alloc._level
    if cur < best_level:
        return 1
    if cur > best_level:
        return 2
    return 0


def policy_greedy_strong(env, obs, info):
    """Fair strong rule baseline using the same state and action limits as RL.

    It reads demand from the observation, scores every allocation level by
    total satisfaction, then moves one relative step toward the best level.
    Unlike myopic_oracle, it does not call env.sync_true_demand_for_action(),
    so it does not peek at a demand flip before that flip appears in state.
    """
    c_total = env.alloc.c_total
    d_a = float(obs[3]) * c_total
    d_b = float(obs[4]) * c_total
    return _step_toward(env, _best_level_from_demand(env, d_a, d_b))


def policy_blind_oracle(env, obs, info):
    """Perfect greedy policy over the agent's observation, which may be stale."""
    c_total = env.alloc.c_total
    d_a = float(obs[3]) * c_total
    d_b = float(obs[4]) * c_total
    return _step_toward(env, _best_level_from_demand(env, d_a, d_b))


def policy_clairvoyant(env, obs, info):
    """Perfect greedy policy over true demand, ignoring observation staleness."""
    d_a, d_b = env.true_demand()
    return _step_toward(env, _best_level_from_demand(env, d_a, d_b))


def policy_oracle_dynamic(env, obs, info):
    """Myopic oracle: knows current demand, but optimizes only this step.

    It is not an optimal oracle over the whole episode. In dynamic A2 it may go
    too far toward the current high-demand branch and pay a reaction delay after
    the demand flips.
    """
    if hasattr(env, 'sync_true_demand_for_action'):
        d_a, d_b = env.sync_true_demand_for_action()
    elif hasattr(env, '_cur_demand'):
        d_a, d_b = env._cur_demand
    else:
        d_a = env._scenario.demand_A
        d_b = env._scenario.demand_B

    return _step_toward(env, _best_level_from_demand(env, d_a, d_b))


policy_myopic_oracle = policy_oracle_dynamic

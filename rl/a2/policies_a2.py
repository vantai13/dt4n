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

    best_level = 0
    best_score = -1.0
    for level, (c_a, c_b) in enumerate(env.alloc.levels):
        sat_a = min(c_a / d_a, 1.0) if d_a > 1e-6 else 1.0
        sat_b = min(c_b / d_b, 1.0) if d_b > 1e-6 else 1.0
        score = sat_a + sat_b
        if score > best_score:
            best_level = level
            best_score = score

    cur = env.alloc._level
    if cur < best_level:
        return 1
    if cur > best_level:
        return 2
    return 0


policy_myopic_oracle = policy_oracle_dynamic

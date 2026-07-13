#!/usr/bin/env python3
"""Oracle actions for scenario feasibility checks.

The oracle knows the scenario. It is not a Phase 6 baseline; it only answers
whether a generated fault has an obvious recovery path within a small step
budget before we ask a blind RL agent to learn it.
"""

from rl.scenarios import CongestionShift, LinkDegrade, LinkDown, TrafficFlood


def oracle_action(scenario):
    """Return a high-level corrective action tuple, or None if unsupported."""
    if isinstance(scenario, LinkDown):
        return ('bw_up', scenario.link_key)
    if isinstance(scenario, LinkDegrade):
        return ('bw_up', scenario.link_key)
    if isinstance(scenario, CongestionShift):
        return ('bw_up', scenario.degrade_link)
    if isinstance(scenario, TrafficFlood):
        return ('bw_up', 's2-s3')
    return None


def oracle_plan(scenario, max_steps=10):
    """Return a minimal feasible plan in high-level action form."""
    action = oracle_action(scenario)
    if action is None or max_steps < 1:
        return []
    return [action]


def oracle_feasible(scenario, max_steps=10):
    """True if the oracle can name a recovery action within max_steps."""
    return len(oracle_plan(scenario, max_steps=max_steps)) <= max_steps and bool(
        oracle_plan(scenario, max_steps=max_steps))

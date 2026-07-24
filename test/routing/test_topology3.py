#!/usr/bin/env python3
"""Guardrails for the Phase 14 three-path topology."""

import sys
from collections import Counter

import numpy as np

sys.path.insert(0, ".")

from measurements.samplers3 import Sampler3Path  # noqa: E402
from rl.routing3 import topology3 as T3  # noqa: E402


def test_topology3_paths_are_structurally_symmetric():
    cfg = T3.link_cfg()
    signatures = []
    for path in T3.PATH_NAMES:
        signatures.append(tuple(
            (cfg[link]["base_delay"], cfg[link]["base_bw"])
            for link in T3.PATH_LINKS[path]
        ))

    assert signatures[0] == signatures[1] == signatures[2]
    assert len(T3.PATH_NAMES) == 3
    assert len(set(T3.PATH_NAMES)) == 3


def test_topology3_base_sampler_is_symmetric():
    rng = np.random.default_rng(0)
    samples = {path: [] for path in T3.PATH_NAMES}
    for _ in range(4000):
        levels = T3.sample_base_levels(rng)
        for path in T3.PATH_NAMES:
            samples[path].append(levels[path])

    means = [float(np.mean(samples[path])) for path in T3.PATH_NAMES]
    assert max(means) - min(means) < 0.02


def test_topology3_crash_path_is_uniform_marginally():
    rng = np.random.default_rng(1)
    counts = Counter()
    for _ in range(3000):
        for event in T3.sample_event_schedule(rng):
            if event.get("crash"):
                counts[event["crash"]] += 1

    total = sum(counts.values())
    assert total > 0
    for path in T3.PATH_NAMES:
        assert abs(counts[path] / total - 1.0 / 3.0) < 0.03


def test_topology3_crash_bias_depends_on_state_not_path_name():
    old_temp = T3.CRASH_BIAS_TEMP
    try:
        T3.CRASH_BIAS_TEMP = 4.0
        levels = {"P1": 0.25, "P2": 0.55, "P3": 0.85}
        probs = T3._crash_probs_from_load(levels)
        assert probs[2] > probs[1] > probs[0]

        renamed_levels = {"P1": 0.85, "P2": 0.25, "P3": 0.55}
        renamed_probs = T3._crash_probs_from_load(renamed_levels)
        assert renamed_probs[0] > renamed_probs[2] > renamed_probs[1]
    finally:
        T3.CRASH_BIAS_TEMP = old_temp


def test_topology3_load_bands_straddle_calibrated_cliff():
    primary = T3.LOAD_BY_ROLE["primary"]
    backup1 = T3.LOAD_BY_ROLE["backup1"]
    backup2 = T3.LOAD_BY_ROLE["backup2"]

    assert primary[1] < T3.CLIFF
    assert backup1[0] < T3.CLIFF < backup1[1]
    assert backup2[0] > T3.CLIFF
    assert T3.CRASH_LOAD[0] > T3.CLIFF
    assert T3.FREE_LOAD[1] < T3.CLIFF


def test_topology3_events_are_frozen_and_deterministic():
    rng = np.random.default_rng(2)
    levels = T3.sample_initial_levels(rng)
    events = T3.sample_event_schedule(rng, episode_len=20)

    once = T3.levels_at_time(levels, events, 20)
    twice = T3.levels_at_time(levels, events, 20)

    assert once == twice
    if events:
        event = events[0]
        if event["type"] == "crash_swap":
            assert "crash_level" in event
            assert "free_level" in event
        else:
            assert "reset_levels" in event


def test_topology3_fresh_optimal_has_no_dominant_path():
    rng = np.random.default_rng(3)
    sampler = Sampler3Path()
    counts = Counter()
    for _ in range(2000):
        obs, _z_true = sampler.sample_observation((0,), rng)
        true_world = sampler.roll_forward(obs, 0, rng)
        q = {
            action: sampler.reward_of(action, true_world)
            for action in sampler.actions
        }
        counts[max(q, key=q.get)] += 1

    total = sum(counts.values())
    assert total == 2000
    assert max(counts.values()) / total < 0.45


def test_sampler3_public_observation_and_z0_identity():
    rng = np.random.default_rng(2)
    sampler = Sampler3Path()
    obs, z_true = sampler.sample_observation((0, 1, 3), rng)
    true_world = sampler.roll_forward(obs, 0, rng)

    assert set(obs) == {"rho"}
    assert z_true in {0, 1, 3}
    assert true_world["rho"] == obs["rho"]


def test_sampler3_reward_signature_blocks_obs_and_z_leakage():
    arg_names = Sampler3Path.reward_of.__code__.co_varnames[
        :Sampler3Path.reward_of.__code__.co_argcount
    ]

    assert arg_names == ("self", "action", "true_world")


def _run_as_script():
    tests = [
        test_topology3_paths_are_structurally_symmetric,
        test_topology3_base_sampler_is_symmetric,
        test_topology3_crash_path_is_uniform_marginally,
        test_topology3_crash_bias_depends_on_state_not_path_name,
        test_topology3_load_bands_straddle_calibrated_cliff,
        test_topology3_events_are_frozen_and_deterministic,
        test_topology3_fresh_optimal_has_no_dominant_path,
        test_sampler3_public_observation_and_z0_identity,
        test_sampler3_reward_signature_blocks_obs_and_z_leakage,
    ]
    for test in tests:
        test()
        print(f"  PASS  {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    _run_as_script()

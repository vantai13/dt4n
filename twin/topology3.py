#!/usr/bin/env python3
"""Three symmetric routing paths with an undirected event process.

This topology is the Phase 14 stage for measuring whether AoI can have
decision value after the 2-path negative control rejected the old design.

The design constraints are intentionally narrow:

* three paths are structurally identical, so there is no path prior;
* events are path-symmetric and have no directed trend;
* reset events and random warm-up make public observations many-to-many with
  event phase;
* load changes are event-driven rather than Gaussian drift, because a pure
  martingale moves the world but does not change action ranking in expectation.
"""

from __future__ import annotations

import os

import numpy as np

from twin.link_model import CLIFF_RHO_OFFERED


N_PATHS = 3
PATH_NAMES = ("P1", "P2", "P3")

TOPO_3PATH = {
    "nodes": ["SRC", "A1", "B1", "A2", "B2", "A3", "B3", "DST"],
    "default_queue_pkts": 13,
    "edges": [
        ["SRC", "A1", 2.0, 8.0],
        ["A1", "B1", 3.0, 6.0],
        ["B1", "DST", 2.0, 8.0],
        ["SRC", "A2", 2.0, 8.0],
        ["A2", "B2", 3.0, 6.0],
        ["B2", "DST", 2.0, 8.0],
        ["SRC", "A3", 2.0, 8.0],
        ["A3", "B3", 3.0, 6.0],
        ["B3", "DST", 2.0, 8.0],
    ],
    "source": "SRC",
    "destination": "DST",
}

TOPO = TOPO_3PATH

BOTTLENECK_LINKS = {
    "P1": ("A1", "B1"),
    "P2": ("A2", "B2"),
    "P3": ("A3", "B3"),
}
ACCESS_LINKS = {
    "P1": ("SRC", "A1"),
    "P2": ("SRC", "A2"),
    "P3": ("SRC", "A3"),
}
EGRESS_LINKS = {
    "P1": ("B1", "DST"),
    "P2": ("B2", "DST"),
    "P3": ("B3", "DST"),
}
PATH_LINKS = {
    path: (ACCESS_LINKS[path], BOTTLENECK_LINKS[path], EGRESS_LINKS[path])
    for path in PATH_NAMES
}

CLIFF = CLIFF_RHO_OFFERED

ROLES = ("primary", "backup1", "backup2")
LOAD_PROFILES = {
    "legacy": {
        "roles": {
            "primary": (0.35, 0.50),
            "backup1": (0.60, 0.72),
            "backup2": (0.70, 0.82),
        },
        "crash": (1.05, 1.20),
        "free": (0.18, 0.28),
    },
    "cliffband": {
        "roles": {
            "primary": (0.80, 0.88),
            "backup1": (0.92, 0.96),
            "backup2": (0.99, 1.04),
        },
        "crash": (1.10, 1.25),
        "free": (0.55, 0.70),
    },
    "narrow": {
        "roles": {
            "primary": (0.84, 0.86),
            "backup1": (0.93, 0.94),
            "backup2": (1.01, 1.02),
        },
        "crash": (1.10, 1.25),
        "free": (0.55, 0.70),
    },
    "wide": {
        "roles": {
            "primary": (0.75, 0.90),
            "backup1": (0.90, 0.98),
            "backup2": (0.98, 1.08),
        },
        "crash": (1.10, 1.25),
        "free": (0.55, 0.70),
    },
}
LOAD_PROFILE = os.environ.get("ROUTING3_BAND_PROFILE", "cliffband")
if LOAD_PROFILE not in LOAD_PROFILES:
    raise ValueError(
        "unknown ROUTING3_BAND_PROFILE "
        f"{LOAD_PROFILE!r}; expected one of {tuple(LOAD_PROFILES)}"
    )
_LOAD_PROFILE_CFG = LOAD_PROFILES[LOAD_PROFILE]
LOAD_BY_ROLE = dict(_LOAD_PROFILE_CFG["roles"])
BASE_LOAD = LOAD_BY_ROLE

CRASH_LOAD = tuple(_LOAD_PROFILE_CFG["crash"])
FREE_LOAD = tuple(_LOAD_PROFILE_CFG["free"])
JITTER_SIGMA = 0.02

OFFERED_LOAD_MIN = 0.15
OFFERED_LOAD_MAX = 1.30
BACKGROUND_LOAD = 0.25

EPISODE_LEN = 40
EVENT_RATE = float(os.environ.get("ROUTING3_EVENT_RATE", "0.12"))
CRASH_BIAS_TEMP = float(os.environ.get("ROUTING3_CRASH_BIAS_TEMP", "0.0"))
EVENT_TYPE_P = {
    "crash_swap": 0.70,
    "reset_base": 0.30,
}


def all_link_keys():
    return [
        (src, dst)
        for src, dst, _delay_ms, _bw_mbps in TOPO_3PATH["edges"]
    ]


def link_cfg():
    default_queue = TOPO_3PATH.get("default_queue_pkts")
    return {
        (src, dst): {
            "base_delay": float(delay_ms),
            "base_bw": float(bw_mbps),
            "queue_pkts": default_queue,
        }
        for src, dst, delay_ms, bw_mbps in TOPO_3PATH["edges"]
    }


def _u(rng, pair):
    lo, hi = pair
    return float(rng.uniform(float(lo), float(hi)))


def _clip(value):
    return float(np.clip(float(value), OFFERED_LOAD_MIN, OFFERED_LOAD_MAX))


def sample_initial_levels(rng):
    """Sample primary/backup levels with path identity randomized.

    This keeps a realistic primary/backup structure while preserving condition
    (2): no path name has a static prior advantage across episodes.
    """
    role_perm = rng.permutation(len(ROLES))
    role_of = {
        PATH_NAMES[path_idx]: ROLES[int(role_perm[path_idx])]
        for path_idx in range(N_PATHS)
    }
    return {
        path: _u(rng, LOAD_BY_ROLE[role])
        for path, role in role_of.items()
    }


def sample_base_levels(rng):
    """Backward-compatible alias for the randomized initial state sampler."""
    return sample_initial_levels(rng)


def _event_probs():
    names = tuple(EVENT_TYPE_P)
    probs = np.asarray([float(EVENT_TYPE_P[name]) for name in names], dtype=float)
    total = float(probs.sum())
    if total <= 0.0:
        raise ValueError("EVENT_TYPE_P weights must sum to a positive value")
    return names, probs / total


def _softmax(scores):
    scores = np.asarray(scores, dtype=float)
    shifted = scores - float(np.max(scores))
    weights = np.exp(shifted)
    total = float(weights.sum())
    if total <= 0.0:
        raise ValueError("softmax weights must sum to a positive value")
    return weights / total


def _crash_probs_from_load(levels):
    """Crash risk depends on current load, not static path identity."""
    loads = np.asarray([float(levels[path]) for path in PATH_NAMES], dtype=float)
    return _softmax(CRASH_BIAS_TEMP * (loads - float(loads.mean())))


def _free_probs_from_load(levels, remaining_indices):
    """Prefer freeing a loaded non-crashing path after a crash event."""
    loads = np.asarray(
        [max(float(levels[PATH_NAMES[idx]]), OFFERED_LOAD_MIN) for idx in remaining_indices],
        dtype=float,
    )
    total = float(loads.sum())
    if total <= 0.0:
        raise ValueError("free-path weights must sum to a positive value")
    return loads / total


def _sample_one_event(t, levels, rng):
    """Sample one event with its outcome frozen into the event object."""
    types, probs = _event_probs()
    etype = types[int(rng.choice(len(types), p=probs))]
    event = {
        "t": int(t),
        "type": etype,
    }
    if etype == "crash_swap":
        crash_probs = _crash_probs_from_load(levels)
        crash_idx = int(rng.choice(N_PATHS, p=crash_probs))
        remaining = [idx for idx in range(N_PATHS) if idx != crash_idx]
        free_probs = _free_probs_from_load(levels, remaining)
        free_idx = int(rng.choice(remaining, p=free_probs))
        event["crash"] = PATH_NAMES[crash_idx]
        event["free"] = PATH_NAMES[free_idx]
        event["crash_level"] = _u(rng, CRASH_LOAD)
        event["free_level"] = _u(rng, FREE_LOAD)
    elif etype == "reset_base":
        event["reset_levels"] = sample_initial_levels(rng)
    else:
        raise ValueError(f"unknown event type: {etype}")
    return event


def sample_event_schedule(rng, episode_len=EPISODE_LEN, base_levels=None):
    """Sample a frozen path-symmetric event schedule for diagnostics."""
    if base_levels is None:
        base_levels = sample_initial_levels(rng)
    return sample_events_between(0, int(episode_len), base_levels, rng)


def apply_event(levels, event):
    """Apply one frozen event deterministically."""
    out = dict(levels)
    etype = event["type"]
    if etype == "crash_swap":
        out[event["crash"]] = float(event["crash_level"])
        out[event["free"]] = float(event["free_level"])
    elif etype == "reset_base":
        out.update(event["reset_levels"])
    else:
        raise ValueError(f"unknown event type: {etype}")
    return {
        path: _clip(value)
        for path, value in out.items()
    }


def levels_at_time(base_levels, events, t):
    """Return deterministic latent path levels at time t."""
    levels = dict(base_levels)
    for event in events:
        if int(event["t"]) <= int(t):
            levels = apply_event(levels, event)
    return {
        path: _clip(value)
        for path, value in levels.items()
    }


def observe_levels(levels, rng):
    """Add instantaneous load jitter.

    Jitter is not accumulated state dynamics. It is sampled independently when
    a latent state is observed or realized, so variance does not leak phase.
    """
    return {
        path: _clip(float(value) + float(rng.normal(0.0, JITTER_SIGMA)))
        for path, value in dict(levels).items()
    }


def sample_world(rng, episode_len=EPISODE_LEN):
    """Sample a complete hidden event world for diagnostics."""
    t_obs = int(rng.integers(0, int(episode_len) + 1))
    base_levels = sample_initial_levels(rng)
    return {
        "base_levels": base_levels,
        "events": sample_event_schedule(rng, episode_len, base_levels),
        "t_obs": int(t_obs),
        "episode_len": int(episode_len),
    }


def sample_observation_levels(rng, episode_len=EPISODE_LEN):
    """Sample a public observation at the local t=0 counterfactual origin."""
    del episode_len
    return observe_levels(sample_initial_levels(rng), rng)


def sample_events_between(t0, t1, levels, rng):
    """Sample frozen events in the interval (t0, t1]."""
    events = []
    cur = {
        path: _clip(value)
        for path, value in dict(levels).items()
    }
    for t in range(int(t0) + 1, int(t1) + 1):
        if float(rng.random()) < EVENT_RATE:
            event = _sample_one_event(t, cur, rng)
            events.append(event)
            cur = apply_event(cur, event)
    return events


def advance_levels(levels, z_steps, rng):
    """Sample one possible current latent state z steps after an observation."""
    steps = int(z_steps)
    out = {
        path: _clip(value)
        for path, value in dict(levels).items()
    }
    if steps <= 0:
        return out

    for event in sample_events_between(0, steps, out, rng):
        out = apply_event(out, event)
    return out


def levels_to_rho(levels):
    """Expand path bottleneck levels to a per-link offered-load snapshot."""
    rho = {}
    for path in PATH_NAMES:
        rho[ACCESS_LINKS[path]] = BACKGROUND_LOAD
        rho[BOTTLENECK_LINKS[path]] = _clip(levels[path])
        rho[EGRESS_LINKS[path]] = BACKGROUND_LOAD
    return rho


def rho_to_levels(rho):
    """Extract path bottleneck levels from a per-link offered-load snapshot."""
    return {
        path: float(rho[BOTTLENECK_LINKS[path]])
        for path in PATH_NAMES
    }

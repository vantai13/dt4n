#!/usr/bin/env python3
"""Locked 8-node routing topology for Phase 8-12.

V2 is the 8-node topology inherited from the routing-sdn lineage, scaled down
to the small-machine Mininet budget and updated after Lesson 9.0 calibration.
The meaningful decision at C/D is not "avoid F": F is the convergence point on
every complete route. The choice is whether to detour through C/D->E->F or take
the direct C/D->F hop. The measured finite-queue cliff on these decision links
makes the best next hop depend on instantaneous offered load.

Structure:
    SRC -> {A,B} -> {C,D} -> {E narrow-fast -> F | F direct-wide} -> DST

Scenario load therefore pinches C/D->E and C/D->F independently. Pinching F
itself would affect every path and would not create a learnable branch choice.
"""

TOPO_V2 = {
    'nodes': ['SRC', 'A', 'B', 'C', 'D', 'E', 'F', 'DST'],
    # [from, to, base_delay_ms, base_bw_mbps]
    'default_queue_pkts': 13,
    'edges': [
        ['SRC', 'A', 2.0, 8.0],
        ['SRC', 'B', 2.5, 8.0],
        ['A', 'C', 3.0, 6.0],
        ['A', 'D', 4.0, 6.0],
        ['B', 'C', 4.0, 6.0],
        ['B', 'D', 3.0, 6.0],
        ['C', 'E', 2.0, 4.0],
        ['D', 'E', 2.0, 4.0],
        ['E', 'F', 1.0, 8.0],
        ['C', 'F', 6.0, 8.0],
        ['D', 'F', 6.0, 8.0],
        ['F', 'DST', 1.5, 8.0],
    ],
    'source': 'SRC',
    'destination': 'DST',
}

# Backward-compatible name used by the Lesson 8.2/8.3 code.
TOPO = TOPO_V2

VIA_E_LINKS = (('C', 'E'), ('D', 'E'))
DIRECT_F_LINKS = (('C', 'F'), ('D', 'F'))

# Load bands around the rev5 cliff ~= 0.9275. FREE is below the cliff; BUSY is
# above it.
_SCEN_BASE = (0.30, 0.50)
BASE_LOAD = _SCEN_BASE
FREE_LOAD = (0.40, 0.75)
BUSY_LOAD = (0.95, 1.15)
BORDERLINE_LOAD = (0.925, 0.935)

SCENARIOS = {
    # e_load controls C/D->E. direct_load controls C/D->F.
    'S1_via_E_free': {
        'base_load': BASE_LOAD,
        'e_load': FREE_LOAD,
        'direct_load': BUSY_LOAD,
        'drift_sigma': 0.0,
    },
    'S2_direct_F_free': {
        'base_load': BASE_LOAD,
        'e_load': BUSY_LOAD,
        'direct_load': FREE_LOAD,
        'drift_sigma': 0.0,
    },
    'S3_both_free': {
        'base_load': BASE_LOAD,
        'e_load': FREE_LOAD,
        'direct_load': FREE_LOAD,
        'drift_sigma': 0.0,
    },
    'S4_both_busy': {
        'base_load': BASE_LOAD,
        'e_load': BUSY_LOAD,
        'direct_load': BUSY_LOAD,
        'drift_sigma': 0.0,
    },
}

SCENARIOS_TRAIN = {
    'S1_viaE_better': {
        'base_load': _SCEN_BASE,
        'e_load': FREE_LOAD,
        'f_load': BUSY_LOAD,
        'drift_sigma': 0.0,
    },
    'S2_direct_better': {
        'base_load': _SCEN_BASE,
        'e_load': BUSY_LOAD,
        'f_load': FREE_LOAD,
        'drift_sigma': 0.0,
    },
    'S3_both_free': {
        'base_load': _SCEN_BASE,
        'e_load': FREE_LOAD,
        'f_load': FREE_LOAD,
        'drift_sigma': 0.0,
    },
    'S4_both_busy': {
        'base_load': _SCEN_BASE,
        'e_load': BUSY_LOAD,
        'f_load': BUSY_LOAD,
        'drift_sigma': 0.0,
    },
}

SCENARIOS_DYNAMIC = {
    'S5_E_rising': {
        'base_load': _SCEN_BASE,
        'e_load': FREE_LOAD,
        'f_load': FREE_LOAD,
        'drift_sigma': 0.20,
    },
    'S6_F_rising': {
        'base_load': _SCEN_BASE,
        'e_load': FREE_LOAD,
        'f_load': FREE_LOAD,
        'drift_sigma': 0.20,
    },
}

TRAIN_SCENARIO_MIX = tuple(SCENARIOS_TRAIN)

# Named deterministic evaluation slices. S1-S4 are the corrected branch-choice
# probes. The legacy names are kept as aliases for older analysis scripts.
LOAD_PRESETS = {
    **SCENARIOS,
    **SCENARIOS_TRAIN,
    'normal': SCENARIOS['S3_both_free'],
    'borderline': {
        'base_load': BASE_LOAD,
        'e_load': BORDERLINE_LOAD,
        'direct_load': FREE_LOAD,
        'drift_sigma': 0.0,
    },
    'bottleneck_E': SCENARIOS['S2_direct_F_free'],
}

LOAD_CFG_V1 = {
    'base_load': (0.25, 0.40),
    'e_load': (0.80, 0.97),
    'drift_sigma': 0.15,
}

# [9.3] Training load, intentionally separate from LOAD_CFG_V1.
#
# LOAD_CFG_TRAIN samples corrected branch-choice scenarios: C/D->E and C/D->F
# are pinched independently so there is no single always-safe direct path.
LOAD_CFG_TRAIN = {
    'base_load': BASE_LOAD,
    'scenarios': SCENARIOS_TRAIN,
    'scenario_mix': TRAIN_SCENARIO_MIX,
    'drift_sigma': 0.0,
}

# [11.2] Phase-11 ablation training load: S1-S4 static + S5-S6 dynamic.
#
# Keep drift_sigma owned by each child scenario. S1-S4 stay static
# (drift_sigma=0.0), while S5-S6 remain dynamic (drift_sigma=0.20). Do not put
# a parent drift_sigma here, otherwise it would be mixed into every scenario and
# blur the static/dynamic split this ablation is meant to expose.
LOAD_CFG_ABLATION = {
    'base_load': BASE_LOAD,
    'scenarios': {**SCENARIOS_TRAIN, **SCENARIOS_DYNAMIC},
    'scenario_mix': tuple(SCENARIOS_TRAIN) + tuple(SCENARIOS_DYNAMIC),
}

# [10.1] Phase-10 sweep load: reuse the calibrated S1-S4 branch-choice
# scenarios, but let the parent load config own drift. Child scenarios must not
# carry drift_sigma here, otherwise resolve_load_scenario() would shadow the
# parent value and silently disable drift.
SCENARIOS_SWEEP = {
    name: {key: value for key, value in scenario.items()
           if key != 'drift_sigma'}
    for name, scenario in SCENARIOS_TRAIN.items()
}

LOAD_CFG_SWEEP = {
    'base_load': BASE_LOAD,
    'scenarios': SCENARIOS_SWEEP,
    'scenario_mix': tuple(SCENARIOS_SWEEP),
    'drift_sigma': 0.15,
}


_LOAD_META_KEYS = {'scenarios', 'scenario_mix'}


def _clip(value, lo, hi):
    return max(float(lo), min(float(value), float(hi)))


def _load_pair(cfg, key, default):
    value = cfg.get(key, default)
    lo, hi = value
    return float(lo), float(hi)


def _direct_load_pair(cfg, default):
    if 'direct_load' in cfg:
        return _load_pair(cfg, 'direct_load', default)
    return _load_pair(cfg, 'f_load', default)


def resolve_load_scenario(load_cfg, scenario=None):
    """Merge a scenario entry with its parent load config.

    ``scenario`` may be a scenario name or an inline dict. Parent metadata such
    as ``scenarios`` and ``scenario_mix`` is intentionally removed from the
    active episode config.
    """
    base = {
        key: value
        for key, value in dict(load_cfg or {}).items()
        if key not in _LOAD_META_KEYS
    }
    if scenario is None:
        return base, base.get('scenario_name')

    if isinstance(scenario, str):
        scenarios = (load_cfg or {}).get('scenarios', {})
        if scenario not in scenarios:
            raise KeyError(f'unknown load scenario: {scenario}')
        child = dict(scenarios[scenario])
        name = scenario
    elif isinstance(scenario, dict):
        child = dict(scenario)
        name = child.pop('scenario_name', child.pop('name', None))
    else:
        raise TypeError('scenario must be a name, dict, or None')

    child.pop('scenarios', None)
    child.pop('scenario_mix', None)
    base.update(child)
    return base, name


def choose_load_scenario(load_cfg, rng):
    """Choose and resolve one episode scenario from ``load_cfg``."""
    scenarios = (load_cfg or {}).get('scenarios')
    mix = (load_cfg or {}).get('scenario_mix')
    if not mix and isinstance(scenarios, dict):
        mix = tuple(scenarios)
    if not mix and isinstance(scenarios, (list, tuple)):
        idx = int(rng.integers(0, len(scenarios)))
        return resolve_load_scenario(load_cfg, scenarios[idx])
    if not mix:
        return resolve_load_scenario(load_cfg)
    idx = int(rng.integers(0, len(mix)))
    return resolve_load_scenario(load_cfg, mix[idx])


def _iter_effective_load_cfgs(load_cfg):
    scenarios = (load_cfg or {}).get('scenarios')
    mix = (load_cfg or {}).get('scenario_mix')
    if not mix and isinstance(scenarios, dict):
        mix = tuple(scenarios)
    if not mix and isinstance(scenarios, (list, tuple)):
        for scenario in scenarios:
            cfg, _name = resolve_load_scenario(load_cfg, scenario)
            yield cfg
        return
    if not mix:
        cfg, _name = resolve_load_scenario(load_cfg)
        yield cfg
        return
    for scenario in mix:
        cfg, _name = resolve_load_scenario(load_cfg, scenario)
        yield cfg


def default_offered_load_max(load_cfg):
    """Return RouteEnv's default clipping ceiling for offered load."""
    hi_values = [1.30]
    for cfg in _iter_effective_load_cfgs(load_cfg or {}):
        _base_lo, base_hi = _load_pair(cfg, 'base_load', (0.25, 0.40))
        _e_lo, e_hi = _load_pair(cfg, 'e_load', (0.60, 0.95))
        _direct_lo, direct_hi = _direct_load_pair(
            cfg,
            (_base_lo, base_hi),
        )
        hi_values.extend([base_hi, e_hi, direct_hi])
    return float(max(hi_values))


def sample_offered_load(link_keys, load_cfg, rng):
    """Sample one RouteEnv-shaped offered-load snapshot.

    All non-decision links receive independent base-load samples. C/D->E share
    one ``e_load`` level, and C/D->F share one ``direct_load``/``f_load`` level
    so the two competing route families are pinched independently.
    """
    cfg, scenario_name = choose_load_scenario(load_cfg, rng)
    if 'offered_load_max' in cfg:
        hi_clip = float(cfg['offered_load_max'])
    elif (load_cfg or {}).get('offered_load_max') is not None:
        hi_clip = float(load_cfg['offered_load_max'])
    else:
        hi_clip = default_offered_load_max(load_cfg)
    base_lo, base_hi = _load_pair(cfg, 'base_load', (0.25, 0.40))
    e_lo, e_hi = _load_pair(cfg, 'e_load', (0.60, 0.95))
    direct_lo, direct_hi = _direct_load_pair(cfg, (base_lo, base_hi))

    links = list(link_keys)
    rho = {
        link: _clip(rng.uniform(base_lo, base_hi), 0.02, hi_clip)
        for link in links
    }

    e_level = _clip(rng.uniform(e_lo, e_hi), 0.02, hi_clip)
    for link in VIA_E_LINKS:
        if link in rho:
            rho[link] = e_level

    direct_level = _clip(rng.uniform(direct_lo, direct_hi), 0.02, hi_clip)
    for link in DIRECT_F_LINKS:
        if link in rho:
            rho[link] = direct_level

    return rho, scenario_name, cfg

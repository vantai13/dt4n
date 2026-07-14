#!/usr/bin/env python3
"""Pure tests for the 51-dimension draft state builder."""

import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.ditto_common import (  # noqa: E402
    make_thing_id_host,
    make_thing_id_link,
)
from rl.soft_reset_equivalence import ks_2samp  # noqa: E402
from rl.state_builder_draft import (  # noqa: E402
    DIM_NAMES,
    STATE_DIM,
    StateBuilderDraft,
    build_state_from_snapshot,
    dim_names,
    mm1_delay_norm,
)


def _spec():
    return json.load(open(ROOT / 'ditto/topology_spec.json', encoding='utf-8'))


def test_dim_names_are_51_and_stable():
    assert len(DIM_NAMES) == 51
    assert STATE_DIM == 51
    assert DIM_NAMES[0] == 'link_up:h1-s1'
    assert DIM_NAMES[-3:] == [
        'aoi_norm',
        'step_progress',
        'healthy_streak_norm',
    ]
    assert 'delay_mm1:s2-s3' in DIM_NAMES
    assert not any(name.startswith('path_latency_norm:') for name in DIM_NAMES)
    assert not any(name.startswith('path_loss_norm:') for name in DIM_NAMES)
    assert not any(name.startswith('switch_up:') for name in DIM_NAMES)
    assert 'max_aoi_norm' not in DIM_NAMES
    assert 'fetch_ms_norm' not in DIM_NAMES


def test_build_state_returns_51_numbers():
    spec = _spec()
    things = {}
    for host in spec['hosts']:
        things[make_thing_id_host(host['name'])] = {
            'features': {
                'status': {'properties': {'state': 'up'}},
                'traffic': {'properties': {'rxRate': 0, 'txRate': 0}},
            }
        }
    for a, b in spec['links']:
        things[make_thing_id_link(a, b)] = {
            'features': {
                'status': {'properties': {'state': 'up'}},
                'capacity': {'properties': {'bwMbps': 20}},
                'traffic': {'properties': {'rxRate': 1000000,
                                           'txRate': 0}},
            }
        }
    vector = build_state_from_snapshot(
        things, info={'data_fresh': 1.0,
                      'aoi': {
                          make_thing_id_host('h1'): 0.8,
                          make_thing_id_link('s2', 's3'): 0.7,
                      }},
        spec=spec,
    )
    assert len(vector) == 51
    assert all(isinstance(value, float) for value in vector)


def test_mm1_delay_norm_is_finite_and_monotonic():
    d0 = mm1_delay_norm(0.0)
    d50 = mm1_delay_norm(0.5)
    d99 = mm1_delay_norm(0.99)
    d100 = mm1_delay_norm(1.0)
    assert 0.0 <= d0 < d50 < d99 <= 1.0
    assert d100 == d99


def test_state_builder_reset_clears_util_history():
    spec = _spec()
    builder = StateBuilderDraft(spec=spec)
    things = {
        make_thing_id_link('s1', 's2'): {
            'features': {
                'status': {'properties': {'state': 'up'}},
                'capacity': {'properties': {'bwMbps': 20}},
                'traffic': {'properties': {'rxRate': 1000000,
                                           'txRate': 0}},
            }
        }
    }
    _first = builder.build(things, info={})
    second = builder.build(things, info={})
    builder.reset()
    after_reset = builder.build(things, info={})
    assert second == after_reset


def test_util_uses_current_bw_not_baseline():
    spec = _spec()
    builder = StateBuilderDraft(spec=spec)
    idx = builder.dim_names.index('util:s2-s3')

    def _things(bw_mbps, rate_bps):
        return {
            make_thing_id_link('s2', 's3'): {
                'features': {
                    'status': {'properties': {'state': 'up'}},
                    'capacity': {'properties': {'bwMbps': bw_mbps}},
                    'traffic': {'properties': {'rxRate': rate_bps / 8.0,
                                               'txRate': 0}},
                }
            }
        }

    u_before = builder.build(_things(5.0, 2e6))[idx]
    builder.reset()
    u_after = builder.build(_things(7.5, 2e6))[idx]
    assert abs(u_before - 0.40) < 0.01
    assert abs(u_after - 0.267) < 0.01
    assert u_after < u_before


def test_aoi_norm_ignores_irrelevant_things():
    spec = _spec()
    builder = StateBuilderDraft(spec=spec)
    idx = builder.dim_names.index('aoi_norm')
    vector = builder.build({}, info={'aoi': {
        make_thing_id_link('s2', 's3'): 0.7,
        make_thing_id_host('srv1'): 0.8,
        'org.dt4n:switch-s1': 30.0,
        'org.dt4n:controller': 30.0,
    }})
    assert 0.0 <= vector[idx] <= 1.0
    assert vector[idx] < 0.3


def test_episode_dims_default_zero_when_no_env():
    spec = _spec()
    vector = build_state_from_snapshot({}, info={}, episode=None, spec=spec)
    names = dim_names(spec)
    assert vector[names.index('step_progress')] == 0.0
    assert vector[names.index('healthy_streak_norm')] == 0.0


def test_episode_dims_normalize():
    spec = _spec()
    builder = StateBuilderDraft(spec=spec, t_max=30, k_healthy=3)
    vector = builder.build({}, info={}, episode={'t': 15,
                                                 'healthy_streak': 2})
    assert abs(vector[builder.dim_names.index('step_progress')] - 0.5) < 1e-9
    assert abs(vector[builder.dim_names.index('healthy_streak_norm')] -
               (2.0 / 3.0)) < 1e-9


def test_all_dims_in_expected_range_and_no_nan():
    spec = _spec()
    vector = build_state_from_snapshot({}, info={'aoi': {}}, spec=spec)
    assert len(vector) == 51
    assert all(not math.isnan(value) for value in vector)
    for value, name in zip(vector, dim_names(spec)):
        high = 5.0 if name.startswith('bw_norm:') else 1.0
        assert 0.0 <= value <= high, '%s = %s' % (name, value)


def test_ks_helper_detects_separated_samples():
    d_same, p_same = ks_2samp([1, 1, 1], [1, 1, 1])
    d_diff, p_diff = ks_2samp([0, 0, 0], [1, 1, 1])
    assert d_same == 0.0
    assert p_same >= 0.99
    assert d_diff == 1.0
    assert p_diff < p_same


if __name__ == '__main__':
    tests = [
        test_dim_names_are_51_and_stable,
        test_build_state_returns_51_numbers,
        test_mm1_delay_norm_is_finite_and_monotonic,
        test_state_builder_reset_clears_util_history,
        test_util_uses_current_bw_not_baseline,
        test_aoi_norm_ignores_irrelevant_things,
        test_episode_dims_default_zero_when_no_env,
        test_episode_dims_normalize,
        test_all_dims_in_expected_range_and_no_nan,
        test_ks_helper_detects_separated_samples,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('state_builder_draft tests passed')

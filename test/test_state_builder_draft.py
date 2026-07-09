#!/usr/bin/env python3
"""Pure tests for the 47-dimension draft state builder."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.ditto_common import make_thing_id_host, make_thing_id_link  # noqa: E402
from rl.soft_reset_equivalence import ks_2samp  # noqa: E402
from rl.state_builder_draft import (  # noqa: E402
    DIM_NAMES,
    StateBuilderDraft,
    build_state_from_snapshot,
)


def _spec():
    return json.load(open(ROOT / 'ditto/topology_spec.json', encoding='utf-8'))


def test_dim_names_are_47_and_stable():
    assert len(DIM_NAMES) == 47
    assert DIM_NAMES[0].startswith('link_up:')
    assert DIM_NAMES[-1] == 'fetch_ms_norm'


def test_build_state_returns_47_numbers():
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
                      'aoi_summary': {'max': 1.0},
                      'fetch_ms': 100.0},
        spec=spec,
    )
    assert len(vector) == 47
    assert all(isinstance(value, float) for value in vector)


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


def test_ks_helper_detects_separated_samples():
    d_same, p_same = ks_2samp([1, 1, 1], [1, 1, 1])
    d_diff, p_diff = ks_2samp([0, 0, 0], [1, 1, 1])
    assert d_same == 0.0
    assert p_same >= 0.99
    assert d_diff == 1.0
    assert p_diff < p_same


if __name__ == '__main__':
    tests = [
        test_dim_names_are_47_and_stable,
        test_build_state_returns_47_numbers,
        test_state_builder_reset_clears_util_history,
        test_ks_helper_detects_separated_samples,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('state_builder_draft tests passed')

#!/usr/bin/env python3
"""Draft DT4N state vector for Phase 4.5.6 validation.

This is intentionally a draft: Phase 5.3 will promote the real state builder and
normalization policy. Here we need a stable 47-dimensional numeric vector so
soft-reset equivalence can be tested with KS + Bonferroni.
"""

import os
import sys
from collections import deque


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_common import (
    make_thing_id_host,
    make_thing_id_link,
    make_thing_id_path,
    make_thing_id_switch,
)
from mininet.topology_meta import baseline_bw, canonical, load_spec


DEFAULT_SPEC_PATH = 'ditto/topology_spec.json'
DEFAULT_BW_BACKBONE = 20.0


def _link_keys(spec):
    return sorted({
        canonical(link[0], link[1])
        for link in spec.get('links', [])
    })


def _host_names(spec):
    return [host['name'] for host in spec.get('hosts', [])]


def _switch_names(spec):
    return [switch['name'] for switch in spec.get('switches', [])]


def dim_names(spec=None):
    spec = spec or load_spec(DEFAULT_SPEC_PATH)
    links = _link_keys(spec)
    hosts = _host_names(spec)
    switches = _switch_names(spec)
    names = []
    names += ['link_up:%s' % key for key in links]
    names += ['bw_norm:%s' % key for key in links]
    names += ['util:%s' % key for key in links]
    names += ['util_avg3:%s' % key for key in links]
    names += ['host_up:%s' % name for name in hosts]
    names += ['switch_up:%s' % name for name in switches]
    names += ['server_rx_norm:%s' % name for name in ('srv1', 'srv2')]
    names += [
        'path_latency_norm:h1-srv1',
        'path_loss_norm:h1-srv1',
        'data_fresh',
        'max_aoi_norm',
        'fetch_ms_norm',
    ]
    return names


DIM_NAMES = dim_names()


def _properties(thing, feature):
    return thing.get('features', {}).get(feature, {}).get('properties', {})


def _state_up(thing):
    return 1.0 if _properties(thing, 'status').get('state') == 'up' else 0.0


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class StateBuilderDraft:
    """Small state-vector builder with resettable util history."""

    def __init__(self, spec=None, util_window=3, bw_backbone=DEFAULT_BW_BACKBONE):
        self.spec = spec or load_spec(DEFAULT_SPEC_PATH)
        self.links = _link_keys(self.spec)
        self.hosts = _host_names(self.spec)
        self.switches = _switch_names(self.spec)
        self.bw0 = baseline_bw(self.spec)
        self.util_window = util_window
        self.bw_backbone = float(bw_backbone)
        self._util_hist = {
            key: deque(maxlen=util_window)
            for key in self.links
        }
        self.dim_names = dim_names(self.spec)
        if len(self.dim_names) != 47:
            raise ValueError('state draft expected 47 dims, got %d' %
                             len(self.dim_names))

    def reset(self):
        for hist in self._util_hist.values():
            hist.clear()

    def build(self, things, info=None):
        info = info or {}
        values = []
        utils = {}

        for key in self.links:
            tid = make_thing_id_link(*key.split('-', 1))
            values.append(_state_up(things.get(tid, {})))

        for key in self.links:
            tid = make_thing_id_link(*key.split('-', 1))
            bw = _num(_properties(things.get(tid, {}), 'capacity').get('bwMbps'))
            values.append(bw / max(self.bw0.get(key, bw or 1.0), 1e-9))

        for key in self.links:
            tid = make_thing_id_link(*key.split('-', 1))
            traffic = _properties(things.get(tid, {}), 'traffic')
            rate_bps = max(
                _num(traffic.get('rxRate')),
                _num(traffic.get('txRate')),
            ) * 8.0
            bw_mbps = self.bw0.get(key, DEFAULT_BW_BACKBONE)
            util = rate_bps / max(bw_mbps * 1e6, 1e-9)
            utils[key] = util
            values.append(util)

        for key in self.links:
            hist = self._util_hist[key]
            hist.append(utils[key])
            values.append(sum(hist) / len(hist) if hist else 0.0)

        for name in self.hosts:
            values.append(_state_up(things.get(make_thing_id_host(name), {})))

        for name in self.switches:
            values.append(_state_up(things.get(make_thing_id_switch(name), {})))

        for name in ('srv1', 'srv2'):
            traffic = _properties(things.get(make_thing_id_host(name), {}),
                                  'traffic')
            rx_mbps = _num(traffic.get('rxRate')) * 8.0 / 1e6
            values.append(rx_mbps / max(self.bw_backbone, 1e-9))

        path = things.get(make_thing_id_path('h1', 'srv1'), {})
        quality = _properties(path, 'quality')
        values.append(_num(quality.get('latency_ms')) / 100.0)
        values.append(_num(quality.get('packetLoss_pct')) / 100.0)

        values.append(_num(info.get('data_fresh'), 1.0))
        aoi_summary = info.get('aoi_summary', {}) or {}
        values.append(_num(aoi_summary.get('max')) / 10.0)
        values.append(_num(info.get('fetch_ms')) / 1000.0)

        if len(values) != 47:
            raise ValueError('state draft expected 47 values, got %d' %
                             len(values))
        return values


def build_state_from_snapshot(things, info=None, spec=None, builder=None):
    builder = builder or StateBuilderDraft(spec=spec)
    return builder.build(things, info=info)


def build_state_draft(runner, builder=None):
    things, info = runner.observe_raw()
    builder = builder or StateBuilderDraft(spec=runner.spec)
    return builder.build(things, info=info)


if __name__ == '__main__':
    print('dims=%d' % len(DIM_NAMES))
    for idx, name in enumerate(DIM_NAMES):
        print('%02d %s' % (idx, name))

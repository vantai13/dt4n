#!/usr/bin/env python3
"""Draft DT4N state vector for Phase 4.5.6 validation.

The state contract is intentionally frozen here: changing dimensions after
equivalence or training invalidates the measured state distribution and any
checkpoints trained against it.
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
)
from mininet.topology_meta import baseline_bw, canonical, load_spec


DEFAULT_SPEC_PATH = 'ditto/topology_spec.json'
DEFAULT_BW_BACKBONE = 20.0
PATH_LATENCY_DIVISOR = 100.0
PATH_LOSS_DIVISOR = 100.0
AOI_NORM_DIVISOR = 5.0
AOI_PERCENTILE = 0.95
BW_NORM_CLIP = 5.0
DEFAULT_T_MAX = 30
DEFAULT_K_HEALTHY = 3


def _link_endpoints(link):
    if isinstance(link, dict):
        return link['endpoints'][0], link['endpoints'][1]
    return link[0], link[1]


def _link_keys(spec):
    return sorted({
        canonical(*_link_endpoints(link))
        for link in spec.get('links', [])
    })


def _host_names(spec):
    return [host['name'] for host in spec.get('hosts', [])]


def _server_names(spec):
    return [host['name'] for host in spec.get('hosts', [])
            if host.get('role') == 'server']


def dynamic_thing_ids(spec):
    """Return Thing ids whose freshness is relevant to this observation."""
    ids = set()
    for name in _host_names(spec):
        ids.add(make_thing_id_host(name))
    for link in spec.get('links', []):
        ids.add(make_thing_id_link(*_link_endpoints(link)))
    ids.add(make_thing_id_path('h1', 'srv1'))
    return ids


def dim_names(spec=None):
    spec = spec or load_spec(DEFAULT_SPEC_PATH)
    links = _link_keys(spec)
    hosts = _host_names(spec)
    servers = _server_names(spec)
    names = []
    names += ['link_up:%s' % key for key in links]
    names += ['bw_norm:%s' % key for key in links]
    names += ['util:%s' % key for key in links]
    names += ['util_avg3:%s' % key for key in links]
    names += ['host_up:%s' % name for name in hosts]
    names += ['server_rx_norm:%s' % name for name in servers]
    names += [
        'path_latency_norm:h1-srv1',
        'path_loss_norm:h1-srv1',
        'data_fresh',
        'aoi_norm',
        'step_progress',
        'healthy_streak_norm',
    ]
    return names


DIM_NAMES = dim_names()
STATE_DIM = len(DIM_NAMES)


def _properties(thing, feature):
    return thing.get('features', {}).get(feature, {}).get('properties', {})


def _state_up(thing):
    return 1.0 if _properties(thing, 'status').get('state') == 'up' else 0.0


def _num(value, default=0.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return value if value == value else default


def _clip(value, lo=0.0, hi=1.0):
    return lo if value < lo else hi if value > hi else value


def _percentile(values, q):
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = q * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] + frac * (xs[hi] - xs[lo])


class StateBuilderDraft:
    """45-dimensional state-vector builder with resettable util history."""

    def __init__(self, spec=None, util_window=3, bw_backbone=DEFAULT_BW_BACKBONE,
                 t_max=DEFAULT_T_MAX, k_healthy=DEFAULT_K_HEALTHY):
        self.spec = spec or load_spec(DEFAULT_SPEC_PATH)
        self.links = _link_keys(self.spec)
        self.hosts = _host_names(self.spec)
        self.servers = _server_names(self.spec)
        self.bw0 = baseline_bw(self.spec)
        self.util_window = util_window
        self.bw_backbone = float(bw_backbone)
        self.t_max = int(t_max)
        self.k_healthy = int(k_healthy)
        self.dynamic_ids = dynamic_thing_ids(self.spec)
        self._util_hist = {
            key: deque(maxlen=util_window)
            for key in self.links
        }
        self.dim_names = dim_names(self.spec)
        if len(self.dim_names) != STATE_DIM:
            raise ValueError('state draft expected %d dims, got %d' %
                             (STATE_DIM, len(self.dim_names)))

    def reset(self):
        for hist in self._util_hist.values():
            hist.clear()

    def _aoi_norm(self, info):
        aoi = info.get('aoi') or {}
        values = [
            _num(value)
            for tid, value in aoi.items()
            if tid in self.dynamic_ids and value is not None
        ]
        values = [value for value in values if value >= -0.05]
        if not values:
            return 0.0
        return _clip(_percentile(values, AOI_PERCENTILE) / AOI_NORM_DIVISOR)

    def build(self, things, info=None, episode=None):
        info = info or {}
        episode = episode or {}
        values = []
        utils = {}

        for key in self.links:
            tid = make_thing_id_link(*key.split('-', 1))
            values.append(_state_up(things.get(tid, {})))

        for key in self.links:
            tid = make_thing_id_link(*key.split('-', 1))
            bw = _num(_properties(things.get(tid, {}), 'capacity').get('bwMbps'))
            values.append(_clip(
                bw / max(self.bw0.get(key, bw or 1.0), 1e-9),
                0.0,
                BW_NORM_CLIP,
            ))

        for key in self.links:
            tid = make_thing_id_link(*key.split('-', 1))
            traffic = _properties(things.get(tid, {}), 'traffic')
            rate_bps = max(
                _num(traffic.get('rxRate')),
                _num(traffic.get('txRate')),
            ) * 8.0
            bw_mbps = _num(
                _properties(things.get(tid, {}), 'capacity').get('bwMbps'),
                self.bw0.get(key, DEFAULT_BW_BACKBONE),
            )
            util = _clip(rate_bps / max(bw_mbps * 1e6, 1e-9))
            utils[key] = util
            values.append(util)

        for key in self.links:
            hist = self._util_hist[key]
            hist.append(utils[key])
            values.append(sum(hist) / len(hist) if hist else 0.0)

        for name in self.hosts:
            values.append(_state_up(things.get(make_thing_id_host(name), {})))

        for name in self.servers:
            traffic = _properties(things.get(make_thing_id_host(name), {}),
                                  'traffic')
            rx_mbps = _num(traffic.get('rxRate')) * 8.0 / 1e6
            values.append(_clip(rx_mbps / max(self.bw_backbone, 1e-9)))

        path = things.get(make_thing_id_path('h1', 'srv1'), {})
        quality = _properties(path, 'quality')
        values.append(_clip(_num(quality.get('latency_ms')) /
                            PATH_LATENCY_DIVISOR))
        values.append(_clip(_num(quality.get('packetLoss_pct')) /
                            PATH_LOSS_DIVISOR))

        values.append(_clip(_num(info.get('data_fresh'), 1.0)))
        values.append(self._aoi_norm(info))
        values.append(_clip(_num(episode.get('t')) / max(self.t_max, 1)))
        values.append(_clip(_num(episode.get('healthy_streak')) /
                            max(self.k_healthy, 1)))

        if len(values) != STATE_DIM:
            raise ValueError('state draft expected %d values, got %d' %
                             (STATE_DIM, len(values)))
        return values


def build_state_from_snapshot(things, info=None, spec=None, builder=None,
                              episode=None):
    builder = builder or StateBuilderDraft(spec=spec)
    return builder.build(things, info=info, episode=episode)


def build_state_draft(runner, builder=None, episode=None):
    things, info = runner.observe_raw()
    builder = builder or StateBuilderDraft(spec=runner.spec)
    return builder.build(things, info=info, episode=episode)


if __name__ == '__main__':
    print('STATE_DIM = %d' % STATE_DIM)
    for idx, name in enumerate(DIM_NAMES):
        print('%02d %s' % (idx, name))

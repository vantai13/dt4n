#!/usr/bin/env python3
"""Read routing-link utilization from kernel and Ditto for AoI calibration.

This module is intentionally small: it reuses the repo's existing Ditto AoI
helpers and the single routing-utilization formula, then joins the two layers
into samples that Lesson 9.0c can write to CSV.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

from bridge.ditto_common import make_thing_id_link
from bridge.ditto_reader import _get_one, compute_aoi, extract_t_source
from twin.util_spec import UTIL_DIRECTION, utilization_from_rate


PROC_NET_DEV = "/proc/net/dev"


def read_tx_bytes_kernel(ifname: str) -> Optional[int]:
    """Return the selected interface byte counter from the root namespace.

    Mininet switch interfaces such as ``sC-eth3`` live in the root namespace
    for the default topology setup. ``UTIL_DIRECTION`` keeps this probe aligned
    with the training/deployment utilization contract.
    """
    try:
        with open(PROC_NET_DEV, encoding="utf-8") as f:
            for line in f:
                if ":" not in line:
                    continue
                name, rest = line.split(":", 1)
                if name.strip() != ifname:
                    continue
                cols = rest.split()
                idx = 8 if UTIL_DIRECTION == "tx" else 0
                return int(cols[idx])
    except (OSError, IndexError, ValueError):
        return None
    return None


class KernelUtilMeter:
    """Convert a monotonically increasing kernel byte counter into utilization."""

    def __init__(self, ifname: str, bw_mbps: float):
        self.ifname = ifname
        self.bw_mbps = float(bw_mbps)
        self._prev: Optional[Tuple[int, float]] = None

    def sample(self):
        """Return ``(utilization_or_none, timestamp)``.

        The first call returns ``None`` because a rate needs two counter reads.
        Counter resets are treated the same way and reseed the meter.
        """
        byte_count = read_tx_bytes_kernel(self.ifname)
        ts = time.time()
        if byte_count is None:
            return None, ts

        if self._prev is None:
            self._prev = (byte_count, ts)
            return None, ts

        prev_bytes, prev_ts = self._prev
        self._prev = (byte_count, ts)
        dt = ts - prev_ts
        if dt <= 0.0 or byte_count < prev_bytes:
            return None, ts

        rate_bytes_s = (byte_count - prev_bytes) / dt
        return utilization_from_rate(rate_bytes_s, self.bw_mbps), ts


def _feature_properties(body, feature_name):
    feature = body.get("features", {}).get(feature_name, {})
    if not isinstance(feature, dict):
        return {}
    props = feature.get("properties")
    return props if isinstance(props, dict) else feature


def read_ditto_link(session, node_a: str, node_b: str):
    """Read one link Thing from Ditto.

    Returns ``(util, t_source, t_read, aoi_s, ok)``. AoI is computed through
    ``bridge.ditto_reader.compute_aoi`` so this measurement has the same
    definition as the rest of the repo.
    """
    thing_id = make_thing_id_link(node_a, node_b)
    body, ok = _get_one(session, thing_id)
    t_read = time.time()
    if not ok or body is None:
        return None, None, t_read, None, False

    t_source = extract_t_source(body)
    aoi = compute_aoi(
        {thing_id: body},
        t_read=t_read,
        read_times={thing_id: t_read},
    ).get(thing_id)

    traffic = _feature_properties(body, "traffic")
    capacity = _feature_properties(body, "capacity")
    try:
        rate = traffic.get("%sRate" % UTIL_DIRECTION)
        bw = capacity.get("bwMbps")
    except AttributeError:
        return None, t_source, t_read, aoi, False

    if rate is None or bw is None:
        return None, t_source, t_read, aoi, False

    return utilization_from_rate(rate, bw), t_source, t_read, aoi, True

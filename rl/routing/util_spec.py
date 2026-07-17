#!/usr/bin/env python3
"""Single definition of routing-link utilization.

Training sees simulated rho values. Deployment sees Ditto link Things with
``traffic.txRate``/``traffic.rxRate`` in bytes per second and
``capacity.bwMbps`` in megabits per second. If these two paths define
"utilization" differently, the policy is trained and served on different
observations.
"""

UTIL_DIRECTION = 'tx'
UTIL_MAX = 1.0
UTIL_MIN = 0.0


def clamp_util(value, lo=UTIL_MIN, hi=UTIL_MAX):
    return max(float(lo), min(float(value), float(hi)))


def utilization_from_rate(rate_bytes_per_s, bw_mbps):
    """Return measured utilization from a byte/s rate and Mbps capacity."""
    try:
        bw = float(bw_mbps)
        rate = float(rate_bytes_per_s)
    except (TypeError, ValueError):
        return 0.0
    if bw <= 0.0 or rate <= 0.0:
        return 0.0
    util = (rate * 8.0) / (bw * 1e6)
    return clamp_util(util)


def _feature_properties(features, name):
    feature = features.get(name, {}) if isinstance(features, dict) else {}
    if not isinstance(feature, dict):
        return {}
    props = feature.get('properties')
    return props if isinstance(props, dict) else feature


def utilization_from_ditto_link(link_thing, direction=UTIL_DIRECTION):
    """Return utilization from one Ditto link Thing or collector-shaped link."""
    if not isinstance(link_thing, dict):
        return 0.0
    features = link_thing.get('features', {})
    traffic = _feature_properties(features, 'traffic')
    capacity = _feature_properties(features, 'capacity')
    rate = traffic.get('%sRate' % direction, 0.0)
    bw = capacity.get('bwMbps', 0.0)
    return utilization_from_rate(rate, bw)

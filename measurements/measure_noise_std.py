#!/usr/bin/env python3
"""Measure baseline numeric noise from Ditto Things.

Run while the network is healthy and background traffic is steady. The output is
used to calibrate scenario strength with the 3-sigma rule.
"""

import argparse
import json
import math
import os
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_reader import expected_thing_ids, fetch_snapshot, make_session  # noqa: E402
from mininet.topology_meta import load_spec  # noqa: E402


EXCLUDE_FEATURE_PROPS = {
    ('meta', 'tSource'),
    ('traffic', 'rxBytes'),
    ('traffic', 'txBytes'),
}


def flatten_numeric(thing_id, thing):
    out = {}
    features = thing.get('features', {})
    for feature, fdata in features.items():
        props = fdata.get('properties', {})
        for prop, value in props.items():
            if (feature, prop) in EXCLUDE_FEATURE_PROPS:
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                out['%s.%s.%s' % (thing_id, feature, prop)] = float(value)
    return out


def summarize(samples):
    by_key = {}
    for sample in samples:
        for key, value in sample.items():
            by_key.setdefault(key, []).append(value)

    out = {}
    for key, values in sorted(by_key.items()):
        if len(values) < 2:
            std = 0.0
        else:
            std = statistics.stdev(values)
        out[key] = {
            'n': len(values),
            'mean': statistics.mean(values),
            'std': std,
            'three_sigma': 3.0 * std,
            'min': min(values),
            'max': max(values),
        }
    return out


def main():
    p = argparse.ArgumentParser(description='Measure DT4N baseline noise std')
    p.add_argument('--spec', default='ditto/topology_spec.json')
    p.add_argument('--samples', type=int, default=300)
    p.add_argument('--interval', type=float, default=1.0)
    p.add_argument('--out', default='docs/phase-4.5/baseline/noise_std.json')
    args = p.parse_args()

    spec = load_spec(args.spec)
    thing_ids = expected_thing_ids(spec)
    session = make_session()
    samples = []

    for idx in range(1, args.samples + 1):
        things, info = fetch_snapshot(session, thing_ids)
        sample = {}
        for thing_id, thing in things.items():
            sample.update(flatten_numeric(thing_id, thing))
        samples.append(sample)
        print('%03d/%03d keys=%d fetch=%.1fms fresh=%.1f' %
              (idx, args.samples, len(sample), info.get('fetch_ms', 0.0),
               info.get('data_fresh', 0.0)))
        if idx < args.samples:
            time.sleep(args.interval)

    result = {
        'measured': True,
        'samples': args.samples,
        'interval_s': args.interval,
        'generated_at_epoch': time.time(),
        'notes': (
            'Healthy-network baseline. Compare scenario deltas against '
            'three_sigma for at least one observation dimension.'
        ),
        'features': summarize(samples),
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

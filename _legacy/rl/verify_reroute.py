#!/usr/bin/env python3
"""Verify whether traffic reroutes when a main-path link is degraded.

Decision gate for making faults persistent:
  - If traffic moves from s1-s2 to s1-s3 when s1-s2 is degraded, the network
    has a natural reroute path, so durable faults should block multiple paths.
  - If it does not move, a single heavier link degradation may already be enough.

Run on the Mininet/controller machine:
    sudo -E env DT4N_FAST_PUSH=1 python rl/verify_reroute.py
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bridge.ditto_common import make_thing_id_link
from mininet.env_runner import EnvRunner
from mininet.topology_meta import canonical, load_spec
from rl.scenarios import LinkDegrade
from rl.state_builder_draft import (
    DEFAULT_BW_BACKBONE,
    _clip,
    _num,
    _properties,
)


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify self-reroute under degradation of s1-s2.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--settle', type=float, default=4.0)
    ap.add_argument('--target', default='s1-s2',
                    help='link to degrade, canonical form like s1-s2')
    ap.add_argument('--factor', type=float, default=0.7,
                    help='fraction of bandwidth removed; 0.7 leaves 30%% bw')
    ap.add_argument('--baseline-bw', type=float, default=20.0)
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def link_keys(spec):
    keys = []
    for link in spec.get('links', []):
        if isinstance(link, dict):
            a, b = link['endpoints'][0], link['endpoints'][1]
        else:
            a, b = link[0], link[1]
        keys.append(canonical(a, b))
    return sorted(set(keys))


def read_util(runner, keys):
    """Read per-link util through Ditto using the current state-builder formula."""
    things, _info = runner.observe_raw()
    utils = {}
    for key in keys:
        a, b = key.split('-', 1)
        thing = things.get(make_thing_id_link(a, b), {})
        traffic = _properties(thing, 'traffic')
        capacity = _properties(thing, 'capacity')
        rate_bps = max(
            _num(traffic.get('rxRate')),
            _num(traffic.get('txRate')),
        ) * 8.0
        bw_mbps = _num(capacity.get('bwMbps'), DEFAULT_BW_BACKBONE)
        if bw_mbps <= 0:
            utils[key] = 0.0
            continue
        utils[key] = round(_clip(rate_bps / max(bw_mbps * 1e6, 1e-9)), 3)
    return utils


def show(runner, keys, label, settle):
    time.sleep(settle)
    utils = read_util(runner, keys)
    print('\n[reroute] === %s ===' % label)
    for key in sorted(utils):
        mark = '  <<<' if utils[key] > 0.4 else ''
        print('   %-14s util=%.3f%s' % (key, utils[key], mark))
    return utils


def main():
    args = parse_args()
    spec = load_spec(args.spec)
    keys = link_keys(spec)

    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=0,
    )
    print('[reroute] start()...', flush=True)
    runner.start()
    runner._start_episode_traffic()
    runner._wait_steady_state()

    base = {}
    after = {}
    try:
        base = show(runner, keys, 'BASELINE', args.settle)

        sc = LinkDegrade(args.target, args.factor, '2ms', args.baseline_bw)
        with runner.net_lock:
            sc.apply(runner.net)
        print('\n[reroute] injected LinkDegrade %s factor=%.2f'
              % (args.target, args.factor))
        after = show(runner, keys, 'AFTER_DEGRADE_%s' % args.target,
                     args.settle)

        with runner.net_lock:
            sc.revert(runner.net)
    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[reroute] === ANALYSIS ===')
    main_before = base.get('s1-s2', 0.0)
    main_after = after.get('s1-s2', 0.0)
    alt_before = base.get('s1-s3', 0.0)
    alt_after = after.get('s1-s3', 0.0)
    print('[reroute] s1-s2 target: %.3f -> %.3f'
          % (main_before, main_after))
    print('[reroute] s1-s3 alternate: %.3f -> %.3f'
          % (alt_before, alt_after))

    if alt_after > alt_before + 0.2:
        print('[reroute] RESULT: CO REROUTE')
        print('[reroute] Strategy: make durable faults by blocking multiple paths.')
    else:
        print('[reroute] RESULT: KHONG RO / KHONG REROUTE')
        print('[reroute] Strategy: heavier single-link faults may be enough;')
        print('[reroute] steering may require controller/routing changes.')


if __name__ == '__main__':
    main()

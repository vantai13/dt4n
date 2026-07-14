#!/usr/bin/env python3
"""Verify whether DT4N link utilization is a reliable congestion signal.

This is a gate before util-centric state/reward changes. It checks:
  1. baseline util on all links,
  2. whether LinkDegrade on s2-s3 increases util[s2-s3],
  3. which links light up during a UDP flood to srv2.

Run on the Mininet/controller machine:
    sudo -E python rl/verify_util.py
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
from rl.scenarios import LinkDegrade, TrafficFlood
from rl.state_builder_draft import (
    DEFAULT_BW_BACKBONE,
    _clip,
    _num,
    _properties,
)


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify util:X from DT4N link traffic/capacity features.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--settle', type=float, default=4.0,
                    help='seconds to wait before each Ditto read')
    ap.add_argument('--flood-rate', type=int, default=50,
                    help='UDP flood rate in Mbps')
    ap.add_argument('--degrade-factor', type=float, default=0.6,
                    help='fraction of bandwidth removed from s2-s3')
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


def read_all_util(runner, keys):
    """Read util for every link using the same formula as StateBuilderDraft."""
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
    utils = read_all_util(runner, keys)
    print('\n[util] === %s ===' % label)
    if not utils:
        print('   <empty util map>')
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
    print('[util] start()...', flush=True)
    runner.start()
    runner._start_episode_traffic()
    runner._wait_steady_state()

    base = {}
    degrade = {}
    flood = {}
    try:
        base = show(runner, keys, 'BASELINE', args.settle)

        target = 's2-s3'
        sc = LinkDegrade(target, args.degrade_factor, '2ms', 5.0)
        with runner.net_lock:
            sc.apply(runner.net)
        print('\n[util] injected LinkDegrade %s (factor %.2f)'
              % (target, args.degrade_factor))
        degrade = show(runner, keys, 'DEGRADE %s' % target, args.settle)
        with runner.net_lock:
            sc.revert(runner.net)

        time.sleep(2.0)
        sc2 = TrafficFlood('h1', 'srv2', args.flood_rate)
        with runner.net_lock:
            sc2.apply(runner.net)
        print('\n[util] injected TrafficFlood h1->srv2 @%dMbps'
              % args.flood_rate)
        flood = show(runner, keys, 'FLOOD srv2', args.settle)
        with runner.net_lock:
            sc2.revert(runner.net)

    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[util] === ANALYSIS ===')
    target = 's2-s3'
    print('[util] LinkDegrade: util[%s] base=%.3f -> degrade=%.3f'
          % (target, base.get(target, 0.0), degrade.get(target, 0.0)))
    if degrade.get(target, 0.0) > base.get(target, 0.0) + 0.1:
        print('[util] OK: util reacts to LinkDegrade on s2-s3.')
    else:
        print('[util] WARN: util did not clearly react to LinkDegrade.')

    lit = sorted(
        [(value, key) for key, value in flood.items() if value > 0.4],
        reverse=True,
    )
    print('[util] Flood srv2 -> links with util > 0.4:')
    if not lit:
        print('       <none>')
    for value, key in lit:
        print('       %-14s util=%.3f' % (key, value))

    if lit:
        print('[util] Read this as: the listed links are the bottleneck candidates.')
    else:
        print('[util] If this is empty, do not switch to util-centric state yet.')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Verify whether server RX throughput behaves like useful goodput under flood.

This is a pre-state-change gate. If a UDP flood to srv2 makes srv2 rxRate grow,
then raw interface throughput is counting flood bytes and cannot replace loss
as a clean health signal.

Run on the Mininet/controller machine:
    sudo -E python rl/verify_goodput.py
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from rl.scenarios import TrafficFlood


def parse_args():
    ap = argparse.ArgumentParser(
        description='Verify raw throughput vs useful goodput under srv2 flood.')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--settle', type=float, default=4.0,
                    help='seconds between rate samples')
    ap.add_argument('--flood-rate', type=int, default=50,
                    help='UDP flood rate in Mbps')
    ap.add_argument('--cleanup-mn', action='store_true',
                    help='also run mn -c on exit; this may kill ryu-manager')
    return ap.parse_args()


def read_srv_rx_mbps(runner):
    """Read srv1/srv2 rxRate from the real collector and convert B/s to Mbps.

    Collector.collect_all() returns:
        snapshot['things']['host-<name>']['features']['traffic']['rxRate']
    where rxRate is bytes/second.
    """
    collector = getattr(runner.net, 'dt4n_collector', None)
    if collector is None:
        raise RuntimeError('runner.net.dt4n_collector is not available')

    snap = collector.collect_all()
    things = snap.get('things', {})
    out = {}
    for name in ('srv1', 'srv2'):
        data = things.get('host-%s' % name, {})
        tr = data.get('features', {}).get('traffic', {})
        rx_bps = float(tr.get('rxRate') or 0.0)
        out[name] = rx_bps * 8.0 / 1e6
    return out


def main():
    args = parse_args()
    runner = EnvRunner(
        spec_path=args.spec,
        sync_period=args.sync_period,
        hard_every=0,
    )
    print('[goodput] start()...', flush=True)
    runner.start()
    runner._start_episode_traffic()
    runner._wait_steady_state()

    def measure(label, settle=None):
        # Two reads are intentional: rxRate is a delta counter, so the first read
        # seeds the previous sample and the second one reports the interval rate.
        if settle is None:
            settle = args.settle
        read_srv_rx_mbps(runner)
        time.sleep(settle)
        rx = read_srv_rx_mbps(runner)
        print('[goodput] %-24s rx:srv1=%7.2f Mbps  rx:srv2=%7.2f Mbps'
              % (label, rx.get('srv1', 0.0), rx.get('srv2', 0.0)))
        return rx

    base = None
    flood = None
    after = None
    try:
        base = measure('BASELINE')

        sc = TrafficFlood('h1', 'srv2', args.flood_rate)
        with runner.net_lock:
            sc.apply(runner.net)
        print('[goodput] injected TrafficFlood h1->srv2 @%dMbps UDP'
              % args.flood_rate)
        flood = measure('DURING_FLOOD_srv2')

        with runner.net_lock:
            sc.revert(runner.net)
        after = measure('AFTER_REVERT', settle=max(2.0, args.settle / 2.0))

    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[goodput] === ANALYSIS ===')
    d_srv2 = flood.get('srv2', 0.0) - base.get('srv2', 0.0)
    print('[goodput] rx:srv2 base=%.2f -> flood=%.2f  delta=%+.2f Mbps'
          % (base.get('srv2', 0.0), flood.get('srv2', 0.0), d_srv2))
    print('[goodput] rx:srv2 after revert=%.2f Mbps' % after.get('srv2', 0.0))

    if d_srv2 > 5.0:
        print('[goodput] KQ2: rx:srv2 INCREASED under flood -> raw throughput counts flood bytes.')
        print('[goodput] Next: measure goodput or change the flood signal before removing loss.')
    elif d_srv2 < -2.0:
        print('[goodput] KQ1: rx:srv2 DECREASED under flood -> branch throughput is usable.')
        print('[goodput] Next: removing loss from state is safer.')
    else:
        print('[goodput] KQ3: rx:srv2 barely changed -> verify scenario/routing impact.')


if __name__ == '__main__':
    main()

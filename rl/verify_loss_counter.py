#!/usr/bin/env python3
"""Chang 1 GATE — Kiem dinh loss-tu-counter co dung khong TRUOC khi vao state.

Nguyen tac: inject su co DA BIET vao link DA BIET, xem loss co tang DUNG cho.
Bat 4 bay:
  Bay 1 (sai phia): doc ca 2 dau link, so sanh
  Bay 2 (HTB drop khong vao /proc): neu loss van 0 khi nghen -> lo ra
  Bay 3 (mau so 0 / link chet): xem loss khi LinkDown
  Bay 4 (namespace): loss rac khi mang khoe -> lo ra o Test 3

    sudo -E python rl/verify_loss_counter.py
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from mininet.topology_meta import load_spec
from bridge.collector import (read_intf_counters_full, canonical_link_key,
                              compute_rate)
from rl.scenarios import LinkDegrade, TrafficFlood
from bridge.ditto_common import make_thing_id_link


def parse_args():
    parser = argparse.ArgumentParser(
        description='Verify per-link loss from passive interface counters.')
    parser.add_argument(
        '--cleanup-mn',
        action='store_true',
        help='Also run Mininet cleanup on exit. This may kill ryu-manager.')
    return parser.parse_args()


def read_link_loss_both_sides(net, link, prev, now_ts):
    """Doc loss ca 2 dau link -> phat hien Bay 1 (drop o phia nao).

    Tra dict {'A': lossA, 'B': lossB, 'combined': loss_tong}.
    """
    def side_loss(intf, key):
        c = read_intf_counters_full(intf)
        if c is None:
            return None, None
        p = prev.get(key)
        if p is None:
            return 0.0, c
        d_tx = max(0, c['tx_packets'] - p['tx_packets'])
        d_drop = (max(0, c['tx_drop'] - p['tx_drop']) +
                  max(0, c['rx_drop'] - p['rx_drop']))
        total = d_tx + d_drop
        loss = (100.0 * d_drop / total) if total > 0 else 0.0
        return max(0.0, min(100.0, loss)), c

    a = link.intf1.node.name
    b = link.intf2.node.name
    key = canonical_link_key(a, b)
    lossA, cA = side_loss(link.intf1, key + ':A')
    lossB, cB = side_loss(link.intf2, key + ':B')
    if cA is not None:
        prev[key + ':A'] = cA
    if cB is not None:
        prev[key + ':B'] = cB
    combined = max(lossA or 0.0, lossB or 0.0)
    return {'A': lossA, 'B': lossB, 'combined': combined}


def snapshot_all_losses(net, prev, label):
    """Doc loss moi link (ca 2 dau). Tra dict {link_key: loss_info}."""
    now_ts = time.time()
    out = {}
    seen = set()
    for link in net.links:
        a, b = link.intf1.node.name, link.intf2.node.name
        key = canonical_link_key(a, b)
        if key in seen:
            continue
        seen.add(key)
        out[key] = read_link_loss_both_sides(net, link, prev, now_ts)
    return out


def find_link(net, canonical_key):
    for link in net.links:
        a, b = link.intf1.node.name, link.intf2.node.name
        loss_key = canonical_link_key(a, b)
        scenario_key = loss_key.replace('link-', '', 1)
        if canonical_key in (loss_key, scenario_key):
            return link
    return None


def main():
    args = parse_args()
    spec = load_spec('ditto/topology_spec.json')
    runner = EnvRunner(sync_period=0.5, hard_every=0)
    print('[verify] start()...', flush=True)
    runner.start()
    runner._start_episode_traffic()
    runner._wait_steady_state()

    net = runner.net
    prev = {}

    # warm-up: 2 lan doc de co prev (loss can Delta 2 snapshot)
    snapshot_all_losses(net, prev, 'warmup1')
    time.sleep(1.0)

    def measure(label, settle=3.0):
        time.sleep(settle)
        # doc 2 lan cach nhau de co Delta sach
        snapshot_all_losses(net, prev, label + '_pre')
        time.sleep(1.5)
        losses = snapshot_all_losses(net, prev, label)
        print('\n[verify] === %s ===' % label)
        for key in sorted(losses):
            info = losses[key]
            mark = '  <<<' if info['combined'] > 1.0 else ''
            print('   %-12s lossA=%5.1f%% lossB=%5.1f%% combined=%5.1f%%%s'
                  % (key, info['A'] or 0, info['B'] or 0,
                     info['combined'], mark))
        return losses

    try:
        # ---- TEST 3 truoc: baseline SACH (mang khoe, moi link phai ~0) ----
        base = measure('TEST3_baseline_clean')
        dirty = [k for k, v in base.items() if v['combined'] > 1.0]
        if dirty:
            print('[verify] ⚠️  BAY 4: link co loss>1%% khi mang KHOE: %s' % dirty)
        else:
            print('[verify] ✅ baseline sach: moi link loss ~0')

        # ---- TEST 1: LinkDegrade len s2-s3 ----
        target = 's2-s3'
        target_loss_key = canonical_link_key('s2', 's3')
        link = find_link(net, target)
        if link is not None:
            bw0 = 5.0
            sc = LinkDegrade(target, 0.6, '2ms', bw0)
            with runner.net_lock:
                sc.apply(net)
            print('\n[verify] injected LinkDegrade tren %s (bop 60%%)' % target)
            t1 = measure('TEST1_degrade_%s' % target)
            loss_target = t1.get(target_loss_key, {}).get('combined', 0)
            if loss_target > 1.0:
                print('[verify] ✅ loss[%s] TANG = %.1f%% -> counter BAT duoc nghen'
                      % (target, loss_target))
            else:
                print('[verify] ⚠️  BAY 2: loss[%s]=%.1f%% VAN ~0 du nghen. '
                      'HTB drop co the KHONG vao /proc/net/dev. '
                      'Can doc tc -s qdisc thay vi /proc.' % (target, loss_target))
            with runner.net_lock:
                sc.revert(net)

        # ---- TEST 2: TrafficFlood srv2 (mu nhanh?) ----
        time.sleep(3.0)
        snapshot_all_losses(net, prev, 'reset_pre')
        sc2 = TrafficFlood('h1', 'srv2', 50)
        with runner.net_lock:
            sc2.apply(net)
        print('\n[verify] injected TrafficFlood h1->srv2 @50M')
        t2 = measure('TEST2_flood_srv2')
        # nhanh srv2 = link s3-srv2; nhanh srv1 = link s2-srv1
        loss_srv2_branch = max(
            t2.get(canonical_link_key('s3', 'srv2'), {}).get('combined', 0),
            t2.get(canonical_link_key('s1', 's3'), {}).get('combined', 0))
        loss_srv1_branch = max(
            t2.get(canonical_link_key('s2', 'srv1'), {}).get('combined', 0),
            t2.get(canonical_link_key('s1', 's2'), {}).get('combined', 0))
        print('[verify] loss nhanh srv2 (max) = %.1f%%' % loss_srv2_branch)
        print('[verify] loss nhanh srv1 (max) = %.1f%%' % loss_srv1_branch)
        if loss_srv2_branch > loss_srv1_branch:
            print('[verify] ✅ HET MU NHANH: su co srv2 -> loss nhanh srv2 > srv1')
        else:
            print('[verify] ⚠️  chua phan biet duoc 2 nhanh — xem lai mapping link')
        with runner.net_lock:
            sc2.revert(net)

    finally:
        runner.close(cleanup_mn=args.cleanup_mn)

    print('\n[verify] === KET LUAN ===')
    print('[verify] Doc ky 3 test tren. Chang 1 dong KHI:')
    print('  - baseline sach (moi link ~0)')
    print('  - LinkDegrade -> loss link do tang (khong dinh Bay 2)')
    print('  - Flood srv2 -> loss nhanh srv2 > nhanh srv1 (het mu)')


if __name__ == '__main__':
    main()

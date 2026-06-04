#!/usr/bin/env python3
"""
run_sync.py — Khởi động Phase 2 Lesson 2.3: topology + bootstrap + sync agent.
Chạy 1 lệnh là twin bắt đầu sống. Mininet cần root.

CHẠY:
    # terminal 1: controller STP
    ryu-manager ryu.app.simple_switch_stp_13 --ofp-tcp-listen-port 6653
    # terminal 2:
    sudo mn -c
    sudo python3 -m mininet.run_sync --period 1.0
"""
import argparse, json, threading, time
from mininet.log import setLogLevel, info
from mininet.topology import build_net, start_net   # từ Phase 1 (đã refactor)
from bridge.bootstrap import bootstrap_all, entities_from_net
from bridge.sync_agent import run as sync_run
from mininet.cli import CLI
from measurements.measure_latency import main as measure_latency

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--clients', type=int, default=3)
    p.add_argument('--period', type=float, default=1.0)
    p.add_argument('--stp-wait', type=int, default=30)
    p.add_argument('--ping-every', type=int, default=5,
                   help='đo latency mỗi N chu kỳ; 0 = tắt ping probe')
    p.add_argument('--reconcile-every', type=int, default=30,
                   help='cứ N chu kỳ gửi full state; 0 = tắt reconciliation')
    p.add_argument('--measure-latency', action='store_true',
                   help='chạy đo sync latency link down rồi thoát, không mở CLI')
    p.add_argument('--trials', type=int, default=10,
                   help='số lần đo khi dùng --measure-latency')
    p.add_argument('--measure-link', default='h1-s1',
                   help='link để đo, dạng nodeA-nodeB, mặc định h1-s1')
    p.add_argument('--verify', action='store_true',
                   help='chạy nghiệm thu Phase 2 rồi thoát, không mở CLI')
    p.add_argument('--long', action='store_true',
                   help='khi --verify: chạy consistency dài hạn')
    p.add_argument('--duration', type=float, default=30,
                   help='số phút chạy consistency khi --verify --long')
    p.add_argument('--verify-interval', type=float, default=5,
                   help='số phút giữa mỗi lần check accuracy khi --verify --long')
    p.add_argument('--n-events', type=int, default=20,
                   help='số event link down để đo event fidelity khi --verify')
    p.add_argument('--verify-link', default='h1-s1',
                   help='link để verify event fidelity, dạng nodeA-nodeB')
    p.add_argument('--output', default='docs/phase-2/verify_report.json',
                   help='file JSON output khi --verify')
    p.add_argument('--policy', default='ditto/policy.json')
    a = p.parse_args()
    if a.measure_latency and a.verify:
        p.error('--measure-latency và --verify chỉ chạy một mode mỗi lần')
    setLogLevel('info')

    net = None
    t = None
    stop_event = threading.Event()
    net_lock = threading.RLock()
    try:
        # 1) dựng mạng (Phase 1)
        net = build_net(clients=a.clients)
        start_net(net, stp_wait=a.stp_wait, do_pingall=True)

        # 2) bootstrap Thing khung (Lesson 2.2) - idempotent, skip nếu đã có
        info('*** Bootstrap Things lên Ditto\n')
        policy = json.load(open(a.policy))
        bootstrap_all(entities_from_net(net), policy, mode='create')

        # 3) sync agent chạy NỀN trong thread riêng -> CLI vẫn dùng được để
        #    gõ kịch bản demo (iperf, link down) trong khi twin đang đồng bộ
        info('*** Khởi động Sync Agent (thread nền)\n')
        t = threading.Thread(target=sync_run, args=(net,),
                             kwargs={'period': a.period,
                                     'ping_every': a.ping_every,
                                     'reconcile_every': a.reconcile_every,
                                     'net_lock': net_lock,
                                     'stop_event': stop_event},
                             daemon=True)
        t.start()

        if a.measure_latency:
            # Cho sync agent vài chu kỳ đầu để đẩy trạng thái baseline lên Ditto.
            time.sleep(max(2.0, a.period * 3))
            h, s = a.measure_link.split('-', 1)
            measure_latency(net, n_trials=a.trials, h=h, s=s,
                            net_lock=net_lock)
            return

        if a.verify:
            from bridge.verify import run_full_verification
            time.sleep(max(2.0, a.period * 3))
            run_full_verification(net, a, net_lock=net_lock)
            return

        # 4) mở CLI để bạn chạy demo. Twin sống trong lúc bạn gõ lệnh.
        info('*** CLI sẵn sàng. Thử:  h1 iperf -s &   rồi  h2 iperf -c h1 -t 30\n')
        info('*** Mở Ditto UI xem rxRate nhảy. Gõ exit để dừng.\n')
        CLI(net)
    finally:
        stop_event.set()
        if t is not None:
            t.join(timeout=5)
        if net is not None:
            info('*** Tắt mạng\n')
            with net_lock:
                net.stop()

if __name__ == '__main__':
    main()

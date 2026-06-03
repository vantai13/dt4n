#!/usr/bin/env python3
"""
topology.py — Physical Twin cho DT4N (Phase 1, Lesson 1.2) — LỚP 1

Dựng topology TAM GIÁC có vòng (redundancy):

            s1
           /  \\
   (bw cao)    (bw cao)
         /      \\
        s2 ----- s3   <- link bottleneck (bw thấp) để tạo nghẽn cho ML/auto-scale

  - s1 gắn các CLIENT;  s2 gắn srv1;  s3 gắn srv2  -> load-balance/failover
  - Vòng s1-s2-s3 = đường dự phòng -> demo what-if link down / failover

THAY ĐỔI KIẾN TRÚC (so với bản cũ):
  Tách "DỰNG mạng" (build_net) khỏi "VẬN HÀNH vòng đời" (start/stop).
  - build_net()  -> trả `net` CHƯA start.
  - start_net()  -> start mạng, đợi STP, pingAll nếu cần.
  - run_cli()    -> chế độ cũ: dựng + mở CLI gõ tay (giữ lại để debug thủ công).
  Lý do: file này thuộc Lớp 1, chỉ lo "mạng trông thế nào". Việc ghép với
  collector (Lớp 2) là trách nhiệm của runner, KHÔNG nhét vào đây -> giữ tách lớp.

Cách chạy ĐỘC LẬP (debug thủ công, KHÔNG có collector):
    # terminal 1: controller STP cho vòng (tránh bão broadcast)
    ryu-manager ryu.app.simple_switch_stp_13 --ofp-tcp-listen-port 6653
    # terminal 2:
    sudo mn -c
    sudo python3 -m mininet.topology            # mở CLI gõ tay
"""

import argparse
import time

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink          # link đặt được bw/delay/loss (Linux tc)
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class TriangleTopo(Topo):
    """Bản VẼ (blueprint) của mạng. Lớp Topo chỉ MÔ TẢ cấu trúc."""

    def build(self, clients=3,
              bw_backbone=20,        # bw 2 link "xương sống" s1-s2, s1-s3 (Mbps)
              bw_bottleneck=5,       # bw link nghẽn s2-s3 (Mbps) -- CỐ TÌNH thấp
              delay='2ms',
              loss=0):
        # 1) 3 SWITCH
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', protocols='OpenFlow13')

        # 2) Nối TAM GIÁC (cái VÒNG)
        self.addLink(s1, s2, bw=bw_backbone, delay=delay)    # xương sống
        self.addLink(s1, s3, bw=bw_backbone, delay=delay)    # xương sống
        self.addLink(s2, s3, bw=bw_bottleneck, delay=delay)  # BOTTLENECK

        # 3) 2 SERVER vào s2, s3
        srv1 = self.addHost('srv1')
        srv2 = self.addHost('srv2')
        self.addLink(srv1, s2, bw=bw_backbone, delay=delay)
        self.addLink(srv2, s3, bw=bw_backbone, delay=delay)

        # 4) N CLIENT vào s1 (THAM SỐ HÓA)
        for i in range(1, clients + 1):
            h = self.addHost('h%d' % i)
            self.addLink(h, s1, bw=bw_backbone, delay=delay, loss=loss)


def build_net(clients=3, bw_backbone=20, bw_bottleneck=5,
              delay='2ms', loss=0,
              controller_ip='127.0.0.1', controller_port=6653):
    """DỰNG đối tượng Mininet từ blueprint, nhưng CHƯA start().

    Runner cầm `net` này để điều phối vòng đời: start, bật traffic, chạy
    collector, rồi net.stop() trong finally. Tách như vậy để topology.py chỉ
    mô tả/tạo mạng, không quyết định toàn bộ kịch bản demo.
    """
    topo = TriangleTopo(clients=clients, bw_backbone=bw_backbone,
                        bw_bottleneck=bw_bottleneck, delay=delay, loss=loss)
    net = Mininet(topo=topo, link=TCLink, switch=OVSSwitch,
                  controller=None, autoSetMacs=True, waitConnected=True)
    net.addController('c0', controller=RemoteController,
                      ip=controller_ip, port=controller_port)
    return net


def start_net(net, stp_wait=30, do_pingall=True):
    """Start mạng đã build, đợi Ryu/STP hội tụ, rồi kiểm tra ping nếu cần."""

    info('*** Bật mạng (tạo namespace, dựng switch, nối link)\n')
    net.start()

    if stp_wait > 0:
        info('*** Đợi Ryu STP hội tụ (%ds)\n' % stp_wait)
        time.sleep(stp_wait)

    info('*** Node: %s\n' % ', '.join(sorted(n.name for n in net.values())))

    if do_pingall:
        info('*** pingAll kiểm tra thông mạng\n')
        loss_pct = net.pingAll()
        info('*** pingAll packet loss = %.0f%%\n' % loss_pct)
    return net


def run_cli(stp_wait=30, do_pingall=True, **kwargs):
    """Chế độ debug thủ công: dựng + mở CLI + tự tắt khi thoát CLI."""
    net = build_net(**kwargs)
    try:
        start_net(net, stp_wait=stp_wait, do_pingall=do_pingall)
        info('*** Mở CLI. Gõ "exit" hoặc Ctrl-D để thoát.\n')
        CLI(net)
    finally:
        info('*** Tắt mạng và dọn dẹp\n')
        net.stop()


def parse_args():
    p = argparse.ArgumentParser(description='DT4N triangle topology (Phase 1)')
    p.add_argument('--clients', type=int, default=3, help='Số client gắn vào s1')
    p.add_argument('--bw-backbone', type=float, default=20, help='bw link xương sống (Mbps)')
    p.add_argument('--bw-bottleneck', type=float, default=5, help='bw link nghẽn s2-s3 (Mbps)')
    p.add_argument('--delay', type=str, default='2ms', help="độ trễ mỗi link, vd '5ms'")
    p.add_argument('--loss', type=float, default=0, help='tỉ lệ mất gói client link (%%)')
    p.add_argument('--stp-wait', type=int, default=30, help='giây đợi STP hội tụ')
    p.add_argument('--skip-pingall', action='store_true', help='bỏ qua pingAll sau khi start')
    return p.parse_args()


if __name__ == '__main__':
    setLogLevel('info')
    a = parse_args()
    run_cli(clients=a.clients, bw_backbone=a.bw_backbone,
            bw_bottleneck=a.bw_bottleneck, delay=a.delay,
            loss=a.loss, stp_wait=a.stp_wait,
            do_pingall=not a.skip_pingall)

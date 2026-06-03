#!/usr/bin/env python3
"""
topology.py — Physical Twin cho đồ án DT4N (Phase 1, Lesson 1.2)

Dựng một topology TAM GIÁC có vòng (redundancy) bằng Mininet Python API:

            s1
           /  \\
   (bw cao)    (bw cao)
         /      \\
        s2 ----- s3
            ^
        link bottleneck (bw thấp) -- để tạo nghẽn cho ML/auto-scale

  - s1 gắn các CLIENT (host bình thường)
  - s2 gắn srv1 (server),  s3 gắn srv2 (server)  -> cho load-balance/failover
  - Vòng s1-s2-s3 = đường dự phòng -> demo what-if link down / failover

THIẾT KẾ THAM SỐ HÓA: số client, băng thông, độ trễ đều là tham số,
không hardcode -> Phase 8 chứng minh scalability chỉ bằng đổi tham số.

Cách chạy:
    sudo python3 topology.py                 # mặc định
    sudo python3 topology.py --clients 5     # 5 client
    sudo python3 topology.py --bw-bottleneck 2   # link nghẽn 2 Mbps
    # terminal 1
    ryu-manager ryu.app.simple_switch_stp_13 --ofp-tcp-listen-port 6653

    # terminal 2
    sudo mn -c
    sudo python3 topology.py
"""

import argparse
import time

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink          # link đặt được bw/delay/loss (dùng Linux tc)
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class TriangleTopo(Topo):
    """Bản VẼ (blueprint) của mạng. Lớp Topo chỉ MÔ TẢ cấu trúc,
    chưa tạo namespace thật. Mininet sẽ 'xây' thật từ bản vẽ này."""

    # build() là hàm Mininet gọi tự động để dựng cấu trúc.
    # Các tham số (clients, bw_*, ...) được truyền vào từ lúc khởi tạo Topo.
    def build(self, clients=3,
              bw_backbone=20,        # băng thông 2 link "xương sống" s1-s2, s1-s3 (Mbps)
              bw_bottleneck=5,       # băng thông link nghẽn s2-s3 (Mbps) -- CỐ TÌNH thấp
              delay='2ms',           # độ trễ mỗi link
              loss=0):               # tỉ lệ mất gói mặc định (%) -- 0 = link sạch
        # ---- 1) Tạo 3 SWITCH ----
        # addSwitch trả về 'tên' (string) để tham chiếu sau này khi addLink.
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', protocols='OpenFlow13')

        # ---- 2) Nối 3 switch thành TAM GIÁC (đây là cái VÒNG) ----
        # Mỗi addLink dùng TCLink (vì ta set cls=TCLink ở Mininet bên dưới),
        # nên truyền được bw/delay vào.
        self.addLink(s1, s2, bw=bw_backbone, delay=delay)   # cạnh 1 (xương sống)
        self.addLink(s1, s3, bw=bw_backbone, delay=delay)   # cạnh 2 (xương sống)
        self.addLink(s2, s3, bw=bw_bottleneck, delay=delay) # cạnh 3 (BOTTLENECK)

        # ---- 3) Gắn 2 SERVER vào s2 và s3 ----
        # Đặt tên 'srv1','srv2' để code khác (Lesson 1.5) nhận ra vai trò server.
        srv1 = self.addHost('srv1')
        srv2 = self.addHost('srv2')
        self.addLink(srv1, s2, bw=bw_backbone, delay=delay)
        self.addLink(srv2, s3, bw=bw_backbone, delay=delay)

        # ---- 4) Gắn N CLIENT vào s1 (THAM SỐ HÓA bằng vòng lặp) ----
        # Đây là phần thể hiện 'tham số hóa quy mô': đổi `clients` -> đổi quy mô,
        # KHÔNG phải sửa code lõi.
        for i in range(1, clients + 1):
            h = self.addHost('h%d' % i)              # h1, h2, h3, ...
            self.addLink(h, s1, bw=bw_backbone, delay=delay, loss=loss)


def run(clients, bw_backbone, bw_bottleneck, delay, loss, interactive):
    """Dựng mạng thật từ blueprint, bật lên, kiểm tra, rồi mở CLI hoặc giữ sống."""

    # Tạo blueprint với tham số người dùng truyền vào.
    topo = TriangleTopo(clients=clients,
                        bw_backbone=bw_backbone,
                        bw_bottleneck=bw_bottleneck,
                        delay=delay,
                        loss=loss)

    # Tạo đối tượng Mininet (XÂY nhà thật từ bản vẽ).
    #   - topo=topo            : dùng bản vẽ ở trên
    #   - link=TCLink          : MỌI link là TCLink (nếu không, bw/delay bị bỏ qua!)
    #   - switch=OVSSwitch     : dùng Open vSwitch
    #   - controller=None       : tự add RemoteController bên dưới để nối tới Ryu
    #   - autoSetMacs=True     : MAC gọn gàng, dễ đọc khi debug
    #   - waitConnected=True   : đợi switch kết nối controller xong mới tiếp tục
    net = Mininet(topo=topo,
                  link=TCLink,
                  switch=OVSSwitch,
                  controller=None,
                  autoSetMacs=True,
                  waitConnected=True)
    net.addController('c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      port=6653)

    info('*** Bật mạng (tạo namespace, dựng switch, nối link)\n')
    net.start()

    info('*** Đợi Ryu STP hội tụ\n')
    time.sleep(30)

    # In ra để xác nhận các thực thể đã được tạo.
    info('*** Các node trong mạng: %s\n'
         % ', '.join(sorted(n.name for n in net.values())))

    # KIỂM TRA THÔNG MẠNG: mỗi host ping mọi host khác.
    # 0%% dropped = mạng thông hoàn toàn. >0%% = có vấn đề (xem phần debug).
    info('*** Chạy pingAll để kiểm tra thông mạng\n')
    net.pingAll()

    if interactive:
        # Mở CLI tương tác: gõ `pingall`, `nodes`, `h1 ifconfig`, `links`, ...
        # Đây là cách 'giữ mạng sống' để nghịch thủ công ở Lesson 1.2.
        info('*** Mở CLI. Gõ "exit" hoặc Ctrl-D để thoát.\n')
        CLI(net)
    else:
        # Chế độ không tương tác: chỉ dựng + pingAll rồi tắt (dùng cho test tự động).
        info('*** Chế độ non-interactive: bỏ qua CLI.\n')

    # LUÔN dọn dẹp khi xong, nếu không sẽ để lại 'mạng rác' (namespace/switch thừa).
    info('*** Tắt mạng và dọn dẹp\n')
    net.stop()


def parse_args():
    """Đọc tham số dòng lệnh -> đây là cách 'tham số hóa' ở tầng giao diện."""
    p = argparse.ArgumentParser(description='DT4N triangle topology (Phase 1)')
    p.add_argument('--clients', type=int, default=3,
                   help='Số host client gắn vào s1 (mặc định 3)')
    p.add_argument('--bw-backbone', type=float, default=20,
                   help='Băng thông link xương sống, Mbps (mặc định 20)')
    p.add_argument('--bw-bottleneck', type=float, default=5,
                   help='Băng thông link nghẽn s2-s3, Mbps (mặc định 5)')
    p.add_argument('--delay', type=str, default='2ms',
                   help="Độ trễ mỗi link, ví dụ '5ms' (mặc định 2ms)")
    p.add_argument('--loss', type=float, default=0,
                   help='Tỉ lệ mất gói client link, %% (mặc định 0)')
    p.add_argument('--no-cli', action='store_true',
                   help='Không mở CLI (chỉ dựng + pingAll rồi tắt)')
    return p.parse_args()


if __name__ == '__main__':
    # setLogLevel('info') để thấy các thông báo *** ... (rất hữu ích lúc học/debug).
    # Đổi sang 'debug' nếu muốn xem chi tiết hơn; 'output' nếu muốn yên tĩnh.
    setLogLevel('info')

    args = parse_args()
    run(clients=args.clients,
        bw_backbone=args.bw_backbone,
        bw_bottleneck=args.bw_bottleneck,
        delay=args.delay,
        loss=args.loss,
        interactive=not args.no_cli)

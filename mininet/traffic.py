#!/usr/bin/env python3
"""
traffic.py — Sinh traffic theo KỊCH BẢN cho mạng DT4N (Phase 1, Lesson 1.3)

Mục tiêu: làm mạng "sống" (có tải, có biến động) để có gì đó ĐÁNG đo.
Mỗi hàm = 1 kịch bản tái dùng xuyên suốt đồ án:

  start_iperf_server()  -> bật server NỀN (phải gọi TRƯỚC mọi client)
  traffic_normal()      -> TCP, tải nền bình thường   (baseline cho ML - Phase 5)
  traffic_flood()       -> UDP tốc độ cao, vượt bw link (flood - Phase 7, bất thường ML)
  measure_latency()     -> ping, đo RTT + phát hiện mất kết nối

CÁCH DÙNG: import các hàm này vào topology.py, hoặc copy-paste vào CLI Mininet
(qua `py`). LƯU Ý: mọi lệnh chạy bằng host.cmd() => chạy TRONG namespace của host
(không phải máy thật) — đây là điểm bản lề từ Lesson 1.2.

Tham khảo cú pháp iperf v2 (Mininet thường đi kèm iperf v2, KHÔNG phải iperf3):
  server: iperf -s            (TCP)   |  iperf -s -u            (UDP)
  client: iperf -c IP -t 10   (TCP)   |  iperf -c IP -u -b 50M -t 10  (UDP)
"""

import time


# Cổng mặc định iperf v2
IPERF_PORT = 5001


def start_iperf_server(host, udp=False):
    """Bật iperf server CHẠY NỀN trên `host`.

    QUAN TRỌNG:
      - Dùng '&' để chạy NỀN, nếu không host.cmd() sẽ TREO (server chạy mãi).
      - UDP và TCP là 2 server riêng; nếu cần đo cả hai, bật server UDP riêng
        (ở đây để đơn giản: 1 cờ udp chọn 1 loại).
    """
    proto = '-u' if udp else ''
    # '> /tmp/...' để khỏi rác stdout; '&' để chạy nền.
    host.cmd('iperf -s %s -p %d > /tmp/iperf_srv_%s.log 2>&1 &'
             % (proto, IPERF_PORT, host.name))
    # Cho server một nhịp để mở cổng lắng nghe (tránh 'connection refused').
    time.sleep(1)
    print('[traffic] iperf server (%s) bật nền trên %s'
          % ('UDP' if udp else 'TCP', host.name))


def traffic_normal(client, server_ip, duration=10):
    """KỊCH BẢN 1: Tải nền BÌNH THƯỜNG (TCP).
    Đo throughput trong điều kiện hiện tại. Dùng làm BASELINE cho ML.
    Trả về output thô để bạn đọc cột Bandwidth.
    """
    print('[traffic] NORMAL (TCP) %s -> %s trong %ds'
          % (client.name, server_ip, duration))
    out = client.cmd('iperf -c %s -p %d -t %d'
                     % (server_ip, IPERF_PORT, duration))
    print(out)
    return out


def traffic_flood(client, server_ip, rate='50M', duration=10):
    """KỊCH BẢN 2: FLOOD (UDP tốc độ cao).
    Bắn `rate` (vd 50M) — nếu vượt bw link, gói thừa rơi rụng -> packet loss CAO.
    LOSS CAO Ở ĐÂY LÀ ĐÚNG DỰ KIẾN (đang mô phỏng tấn công/quá tải), KHÔNG phải bug.

    LƯU Ý ĐỌC OUTPUT: jitter + packet loss nằm ở report PHÍA SERVER, không phải
    client. Hàm này in output client; để lấy loss/jitter, đọc /tmp/iperf_srv_*.log
    trên host server (hoặc bật server với cờ udp và đọc log của nó).
    """
    print('[traffic] FLOOD (UDP @%s) %s -> %s trong %ds'
          % (rate, client.name, server_ip, duration))
    out = client.cmd('iperf -c %s -p %d -u -b %s -t %d'
                     % (server_ip, IPERF_PORT, rate, duration))
    print(out)
    return out


def read_server_udp_report(server):
    """Đọc report UDP từ log của server (nơi CÓ jitter + packet loss).
    Gọi sau khi flood xong. Đây là cách đọc ĐÚNG phía server.
    """
    out = server.cmd('cat /tmp/iperf_srv_%s.log' % server.name)
    print('[traffic] ==== UDP server report (%s) — jitter + loss ở đây ===='
          % server.name)
    print(out)
    return out


def measure_latency(src, dst_ip, count=10):
    """Đo RTT (round-trip time) bằng ping. Cũng phát hiện MẤT KẾT NỐI
    (100% loss = link/host down). Chạy SONG SONG với flood để thấy
    nghẽn làm latency tăng thế nào.
    """
    print('[traffic] PING %s -> %s (%d gói)' % (src.name, dst_ip, count))
    out = src.cmd('ping -c %d %s' % (count, dst_ip))
    print(out)
    return out


def stop_all_iperf(*hosts):
    """Dọn dẹp: tắt mọi iperf server nền (tránh chiếm cổng ở lần chạy sau).
    Pitfall (file Phase 1): quên dừng server -> port bị chiếm.
    """
    for h in hosts:
        h.cmd('kill %iperf 2>/dev/null')   # kill job nền tên 'iperf'
        h.cmd('pkill -f "iperf -s" 2>/dev/null')
    print('[traffic] đã dừng các iperf server')


# ---------------------------------------------------------------------------
# Ví dụ kịch bản chạy hoàn chỉnh (chạy TRONG script đã có đối tượng `net`).
# KHÔNG chạy file này độc lập — nó cần `net` từ Mininet.
# ---------------------------------------------------------------------------
def demo_scenarios(net):
    """Chạy thử cả 2 kịch bản. Gọi từ topology.py sau net.start()."""
    h1 = net.get('h1')          # client
    srv1 = net.get('srv1')      # server
    srv1_ip = srv1.IP()

    # --- Kịch bản 1: tải bình thường (TCP) ---
    start_iperf_server(srv1, udp=False)
    traffic_normal(h1, srv1_ip, duration=10)
    stop_all_iperf(srv1)

    # --- Kịch bản 2: flood (UDP) + đo latency song song ---
    start_iperf_server(srv1, udp=True)
    # Chạy ping nền để quan sát latency TĂNG khi flood (chạy song song).
    h1.cmd('ping -c 12 %s > /tmp/ping_during_flood.log 2>&1 &' % srv1_ip)
    traffic_flood(h1, srv1_ip, rate='50M', duration=10)
    read_server_udp_report(srv1)            # <-- jitter + loss ở đây
    print(h1.cmd('cat /tmp/ping_during_flood.log'))  # latency trong lúc flood
    stop_all_iperf(srv1)
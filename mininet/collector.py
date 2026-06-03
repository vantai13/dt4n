#!/usr/bin/env python3
"""
collector.py — Bộ thu thập metrics cho DT4N (Phase 1, Lesson 1.5)

VAI TRÒ: "nửa dưới" của Sync Agent. Thu thập metric từ Mininet -> xuất JSON
có cấu trúc (khít với Ditto Thing) + ghi log. KHÔNG đẩy lên Ditto (đó là Phase 2).

NGUYÊN TẮC THIẾT KẾ:
  - Separation of Concerns: chỉ THU THẬP, không biết Ditto tồn tại.
  - Đọc metric host PHẢI qua host.cmd() (trong namespace) — nếu không -> số sai.
  - rate = (counter_now - counter_prev) / Δt_THẬT (đo bằng timestamp, không giả định).
  - Output JSON cố tình giống cấu trúc Thing của Ditto -> Phase 2 chỉ việc PUT.

CÁCH DÙNG (trong script đã có đối tượng `net`, sau net.start()):
    from collector import Collector
    col = Collector(net, interval=1.0)
    col.run(duration=30)            # chạy 30s, in + ghi snapshot mỗi 1s
"""

import json
import time
import datetime


# ---------------------------------------------------------------------------
# PARSE HELPERS — thuần logic, test được KHÔNG cần Mininet
# ---------------------------------------------------------------------------
def parse_proc_net_dev(text, iface):
    """Trả (rxBytes, txBytes) của `iface` từ nội dung /proc/net/dev.
    rxBytes = cột bytes nhóm Receive (index 0 sau ':')
    txBytes = cột bytes nhóm Transmit (index 8 sau ':')
    Trả None nếu không tìm thấy interface.
    """
    for line in text.splitlines():
        if ':' not in line:
            continue                         # bỏ 2 dòng header
        name, stats = line.split(':', 1)
        if name.strip() != iface:
            continue
        cols = stats.split()
        return int(cols[0]), int(cols[8])
    return None


def parse_ping(text):
    """Parse output `ping -c N`. Trả dict {latency_ms, packet_loss_pct}.
    - latency: lấy từ dòng 'rtt min/avg/max' (phần avg).
    - packet loss: lấy từ dòng 'X% packet loss'.
    Trả giá trị None cho field không đọc được (vd 100% loss thì không có rtt).
    """
    result = {'latency_ms': None, 'packet_loss_pct': None}
    for line in text.splitlines():
        # dòng kiểu: "10 packets transmitted, 9 received, 10% packet loss, time 9012ms"
        if 'packet loss' in line:
            for token in line.split(','):
                if 'packet loss' in token:
                    pct = token.strip().split('%')[0].strip()
                    try:
                        result['packet_loss_pct'] = float(pct)
                    except ValueError:
                        pass
        # dòng kiểu: "rtt min/avg/max/mdev = 0.041/0.055/0.078/0.013 ms"
        if 'min/avg/max' in line and '=' in line:
            nums = line.split('=')[1].strip().split()[0]   # "0.041/0.055/0.078/0.013"
            parts = nums.split('/')
            if len(parts) >= 2:
                try:
                    result['latency_ms'] = float(parts[1])   # avg
                except ValueError:
                    pass
    return result


def compute_rate(now_val, prev_val, dt):
    """Tính rate an toàn:
    - prev_val None (chu kỳ đầu) -> rate = 0 (chưa đủ dữ liệu).
    - dt <= 0 -> rate = 0 (tránh chia 0).
    - now < prev (counter reset/overflow) -> rate = 0 (bỏ qua, không trả số âm).
    """
    if prev_val is None or dt <= 0:
        return 0.0
    delta = now_val - prev_val
    if delta < 0:                 # counter reset/tràn
        return 0.0
    return delta / dt


def utc_now_iso():
    """Timestamp ISO 8601 UTC (vd '2026-05-30T10:00:00Z') — đúng định dạng Ditto."""
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ---------------------------------------------------------------------------
# COLLECTOR — phần CẦN Mininet (đối tượng net). Không test được trong sandbox.
# ---------------------------------------------------------------------------
class Collector:
    def __init__(self, net, interval=1.0, server_names=('srv1', 'srv2'),
                 log_path='/tmp/dt4n_snapshots.jsonl', cmd_timeout=3):
        self.net = net
        self.interval = interval                 # chu kỳ polling (giây) — Lesson 1.4
        self.server_names = set(server_names)     # host nào đóng vai 'server'
        self.log_path = log_path                  # ghi mỗi snapshot 1 dòng JSON (JSONL)
        self.cmd_timeout = cmd_timeout            # timeout lệnh (tránh treo cả vòng lặp)
        self._prev = {}                           # lưu (rxBytes,txBytes,timestamp) chu kỳ trước theo host
        self._ping_counter = 0                    # đếm chu kỳ để đo latency THƯA hơn

    # ---- thu thập 1 HOST (qua namespace) ----
    def collect_host(self, host, now_ts):
        name = host.name
        iface = '%s-eth0' % name                  # interface chính của host trong Mininet
        # ĐỌC TRONG NAMESPACE — bắt buộc host.cmd()
        raw = host.cmd('cat /proc/net/dev')
        parsed = parse_proc_net_dev(raw, iface)

        if parsed is None:
            # interface chưa sẵn sàng / tên khác -> báo state nhưng không crash
            return {
                'attributes': {'type': 'host',
                               'role': 'server' if name in self.server_names else 'client'},
                'features': {
                    'traffic': {'rxBytes': None, 'txBytes': None, 'rxRate': 0.0, 'txRate': 0.0},
                    'status': {'state': 'unknown'},
                },
            }

        rx, tx = parsed
        prev = self._prev.get(name)               # (rx_prev, tx_prev, ts_prev) hoặc None
        if prev is None:
            dt = 0
            rx_rate = tx_rate = 0.0
        else:
            dt = now_ts - prev[2]                 # Δt THẬT (timestamp now - prev)
            rx_rate = compute_rate(rx, prev[0], dt)
            tx_rate = compute_rate(tx, prev[1], dt)
        self._prev[name] = (rx, tx, now_ts)       # lưu cho chu kỳ sau

        return {
            'attributes': {'type': 'host',
                           'role': 'server' if name in self.server_names else 'client'},
            'features': {
                'traffic': {'rxBytes': rx, 'txBytes': tx,
                            'rxRate': round(rx_rate, 2), 'txRate': round(tx_rate, 2)},
                'status': {'state': 'up'},
            },
        }

    # ---- thu thập 1 SWITCH (ở ROOT namespace, dùng ovs-ofctl) ----
    def collect_switch(self, switch):
        name = switch.name
        # ovs-ofctl chạy ở root (switch KHÔNG cô lập như host) -> dùng switch.cmd hoặc net
        out = switch.cmd('ovs-ofctl dump-ports %s' % name)
        # (Parse port stats chi tiết tùy format; ở đây giữ raw + state để Phase 2 mở rộng.)
        state = 'up' if 'port' in out.lower() or out.strip() else 'unknown'
        return {
            'attributes': {'type': 'switch'},
            'features': {
                'status': {'state': state},
                'portStatsRaw': {'dump': out.strip()[:500]},   # cắt bớt cho gọn log
            },
        }

    # ---- đo LATENCY (thưa hơn — Lesson 1.4: không phải metric nào cũng cùng tần suất) ----
    def collect_latency(self, src, dst_ip):
        out = src.cmd('ping -c 3 -W 1 %s' % dst_ip)
        return parse_ping(out)

    # ---- gom TẤT CẢ thành 1 snapshot ----
    def collect_all(self):
        now_ts = time.time()
        snapshot = {'timestamp': utc_now_iso(), 'things': {}}

        # hosts
        for host in self.net.hosts:
            snapshot['things']['host-%s' % host.name] = self.collect_host(host, now_ts)

        # switches
        for sw in self.net.switches:
            snapshot['things']['switch-%s' % sw.name] = self.collect_switch(sw)

        # latency: đo THƯA — mỗi 5 chu kỳ một lần (vì ping tốn + tự gây nhiễu)
        self._ping_counter += 1
        if self._ping_counter % 5 == 0 and len(self.net.hosts) >= 2:
            h1 = self.net.hosts[0]
            srv = self.net.get('srv1') if 'srv1' in [h.name for h in self.net.hosts] else self.net.hosts[-1]
            lat = self.collect_latency(h1, srv.IP())
            key = 'link-%s-%s' % (h1.name, srv.name)
            snapshot['things'][key] = {
                'attributes': {'type': 'path', 'src': h1.name, 'dst': srv.name},
                'features': {'quality': {'latency_ms': lat['latency_ms'],
                                         'packetLoss_pct': lat['packet_loss_pct']}},
            }
        return snapshot

    # ---- VÒNG LẶP chu kỳ ----
    def run(self, duration=30):
        """Chạy `duration` giây, mỗi `interval` giây xuất 1 snapshot.
        In ra console + ghi 1 dòng JSON vào log (JSONL -> dataset thô cho ML Phase 5)."""
        end = time.time() + duration
        print('[collector] bắt đầu, interval=%.1fs, ghi log -> %s'
              % (self.interval, self.log_path))
        with open(self.log_path, 'a') as logf:
            while time.time() < end:
                t0 = time.time()
                snap = self.collect_all()
                line = json.dumps(snap)
                print(line)                       # console
                logf.write(line + '\n')           # 1 snapshot = 1 dòng (JSONL)
                logf.flush()
                # ngủ phần còn lại của chu kỳ (trừ thời gian đã tốn cho collect)
                elapsed = time.time() - t0
                time.sleep(max(0, self.interval - elapsed))
        print('[collector] kết thúc.')
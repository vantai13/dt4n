#!/usr/bin/env python3
"""
collector.py — Bộ thu thập metrics cho DT4N (Phase 1, Lesson 1.5)

VAI TRÒ KIẾN TRÚC: "nửa dưới" của Sync Agent — thuộc LỚP 2 (Bridge), KHÔNG phải
Lớp 1. Nó CHẠM vào Mininet (qua host.cmd) để đọc, nhưng mục đích tồn tại của nó
là CHUẨN BỊ DỮ LIỆU cho việc đồng bộ. Vì thế file này nằm ở bridge/, không phải
mininet/. (Test: đổi Mininet -> GNS3 thì topology.py phải viết lại, còn logic
parse/tính rate/format JSON ở đây GIỮ NGUYÊN -> bằng chứng nó thuộc Lớp 2.)

NGUYÊN TẮC THIẾT KẾ:
  - Separation of Concerns: chỉ THU THẬP, không biết Ditto tồn tại (Phase 2 mới đẩy).
  - Đọc metric host PHẢI qua host.cmd() (trong namespace) — nếu không -> số sai.
  - rate = (counter_now - counter_prev) / Δt_THẬT (đo bằng timestamp, không giả định).
  - Output JSON cố tình giống cấu trúc Thing của Ditto -> Phase 2 chỉ việc PUT.

CÁCH DÙNG (KHÔNG chạy độc lập — cần đối tượng `net` từ tiến trình Mininet):
    # bên trong run_phase1.py, sau net.start():
    from bridge.collector import Collector
    col = Collector(net, interval=1.0)
    col.run(duration=30)            # chạy 30s, in + ghi snapshot mỗi 1s

VÌ SAO KHÔNG CHẠY ĐƯỢC `python3 collector.py`?
    Vì `net` chỉ sống trong tiến trình Python đang giữ Mininet. Đây là thiết kế
    in-process, KHÔNG phải bug. Muốn chạy -> dùng runner run_phase1.py.
"""

import json
import os
import time
import datetime


# ---------------------------------------------------------------------------
# PARSE HELPERS — thuần logic, TEST ĐƯỢC KHÔNG CẦN MININET
# (Đây là phần chứng minh "logic thuộc Lớp 2": không đụng gì tới namespace.)
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


def ensure_parent_dir(path):
    """Tạo thư mục cha cho file log nếu chưa có."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def fmt_num(value):
    if value is None:
        return '-'
    if isinstance(value, float):
        return '%.2f' % value
    return str(value)


def fmt_mbps(bytes_per_sec):
    if bytes_per_sec is None:
        return '-'
    return '%.2f' % ((bytes_per_sec * 8.0) / 1000000.0)


def format_snapshot_pretty(snapshot, index):
    """Format snapshot thành log dễ đọc cho người, khác JSONL dành cho máy."""
    things = snapshot.get('things', {})
    lines = []
    lines.append('=' * 92)
    lines.append('DT4N PHASE 1 SNAPSHOT #%03d' % index)
    lines.append('timestamp: %s' % snapshot.get('timestamp', '-'))
    lines.append('-' * 92)

    lines.append('HOST TRAFFIC')
    lines.append('  %-10s %-8s %-8s %14s %14s %12s %12s'
                 % ('name', 'role', 'state', 'rxBytes', 'txBytes', 'rxMbps', 'txMbps'))
    for key in sorted(things):
        if not key.startswith('host-'):
            continue
        item = things[key]
        attrs = item.get('attributes', {})
        features = item.get('features', {})
        traffic = features.get('traffic', {})
        status = features.get('status', {})
        lines.append('  %-10s %-8s %-8s %14s %14s %12s %12s'
                     % (key.replace('host-', ''),
                        attrs.get('role', '-'),
                        status.get('state', '-'),
                        fmt_num(traffic.get('rxBytes')),
                        fmt_num(traffic.get('txBytes')),
                        fmt_mbps(traffic.get('rxRate')),
                        fmt_mbps(traffic.get('txRate'))))

    lines.append('')
    lines.append('SWITCH STATUS')
    lines.append('  %-10s %-8s' % ('name', 'state'))
    for key in sorted(things):
        if not key.startswith('switch-'):
            continue
        item = things[key]
        status = item.get('features', {}).get('status', {})
        lines.append('  %-10s %-8s' % (key.replace('switch-', ''), status.get('state', '-')))

    path_rows = []
    for key in sorted(things):
        if not key.startswith('link-'):
            continue
        item = things[key]
        attrs = item.get('attributes', {})
        quality = item.get('features', {}).get('quality', {})
        path_rows.append((attrs, quality))
    if path_rows:
        lines.append('')
        lines.append('PATH QUALITY')
        lines.append('  %-8s -> %-8s %14s %14s' % ('src', 'dst', 'latency_ms', 'loss_pct'))
        for attrs, quality in path_rows:
            lines.append('  %-8s -> %-8s %14s %14s'
                         % (attrs.get('src', '-'), attrs.get('dst', '-'),
                            fmt_num(quality.get('latency_ms')),
                            fmt_num(quality.get('packetLoss_pct'))))

    lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# COLLECTOR — phần CẦN Mininet (đối tượng net). Không test được trong sandbox.
# ---------------------------------------------------------------------------
class Collector:
    def __init__(self, net, interval=1.0, server_names=('srv1', 'srv2'),
                 log_path='logs/dt4n_snapshots.jsonl',
                 pretty_log_path='logs/phase1.log',
                 cmd_timeout=3, ping_every=5, overwrite=True):
        self.net = net
        self.interval = interval                 # chu kỳ polling (giây) — Lesson 1.4
        self.server_names = set(server_names)     # host nào đóng vai 'server'
        self.log_path = log_path                  # ghi mỗi snapshot 1 dòng JSON (JSONL)
        self.pretty_log_path = pretty_log_path    # log dễ đọc cho người xem demo
        self.cmd_timeout = cmd_timeout            # timeout lệnh (tránh treo cả vòng lặp)
        self.ping_every = ping_every              # đo latency mỗi N chu kỳ (ping tốn + tự nhiễu)
        self.overwrite = overwrite                # True -> lần chạy sau đè log lần trước
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

        # latency: đo THƯA — mỗi ping_every chu kỳ (vì ping tốn + tự gây nhiễu)
        self._ping_counter += 1
        if self._ping_counter % self.ping_every == 0 and len(self.net.hosts) >= 2:
            h1 = self.net.hosts[0]
            host_names = [h.name for h in self.net.hosts]
            srv = self.net.get('srv1') if 'srv1' in host_names else self.net.hosts[-1]
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
        mode = 'w' if self.overwrite else 'a'
        ensure_parent_dir(self.log_path)
        if self.pretty_log_path:
            ensure_parent_dir(self.pretty_log_path)
        print('[collector] bắt đầu, interval=%.1fs' % self.interval)
        print('[collector] JSONL log  -> %s (%s)' % (self.log_path, 'overwrite' if mode == 'w' else 'append'))
        if self.pretty_log_path:
            print('[collector] Pretty log -> %s (%s)' % (self.pretty_log_path,
                                                         'overwrite' if mode == 'w' else 'append'))
        n = 0
        prettyf = open(self.pretty_log_path, mode) if self.pretty_log_path else None
        with open(self.log_path, mode) as logf:
            while time.time() < end:
                t0 = time.time()
                snap = self.collect_all()
                line = json.dumps(snap)
                print('[collector] snapshot #%03d %s' % (n + 1, snap.get('timestamp', '-')))
                logf.write(line + '\n')           # 1 snapshot = 1 dòng (JSONL)
                logf.flush()
                if prettyf:
                    prettyf.write(format_snapshot_pretty(snap, n + 1) + '\n')
                    prettyf.flush()
                n += 1
                # ngủ phần còn lại của chu kỳ (trừ thời gian đã tốn cho collect)
                elapsed = time.time() - t0
                time.sleep(max(0, self.interval - elapsed))
        if prettyf:
            prettyf.close()
        print('[collector] kết thúc. Đã ghi %d snapshot -> %s' % (n, self.log_path))
        if self.pretty_log_path:
            print('[collector] log dễ đọc -> %s' % self.pretty_log_path)
        return n

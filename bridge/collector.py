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
from contextlib import nullcontext


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
        if len(cols) <= 8:
            continue
        try:
            return int(cols[0]), int(cols[8])
        except ValueError:
            # Defensive: Mininet shell output can be interleaved with commands such
            # as ifconfig during link up/down. Treat that as "not a procfs row"
            # instead of crashing the whole sync cycle.
            continue
    return None


def read_host_net_dev(host):
    """Read /proc/net/dev for a Mininet host without using its interactive shell.

    host.cmd() is fragile when the Mininet CLI is also issuing commands. Reading
    /proc/<pid>/net/dev uses the host network namespace directly and avoids shell
    output interleaving; fallback keeps tests/older Mininet objects working.
    """
    pid = getattr(host, 'pid', None)
    if pid:
        path = '/proc/%s/net/dev' % pid
        try:
            with open(path) as f:
                return f.read()
        except OSError:
            pass
    return host.cmd('cat /proc/net/dev')


def read_intf_counters(intf):
    """Return (rxBytes, txBytes) for one Mininet interface, or None.

    Host interfaces live in the host namespace, while OVS switch interfaces live
    in the root namespace. Use the interface object's real name; do not guess
    names such as '<node>-eth0'.
    """
    node = intf.node
    iface = intf.name
    is_switch = hasattr(node, 'dpid') or node.__class__.__name__.endswith('Switch')
    pid = getattr(node, 'pid', None)

    try:
        if is_switch or not pid:
            with open('/proc/net/dev') as f:
                text = f.read()
        else:
            with open('/proc/%s/net/dev' % pid) as f:
                text = f.read()
    except OSError:
        try:
            text = node.cmd('cat /proc/net/dev')
        except Exception:
            return None

    return parse_proc_net_dev(text, iface)


def canonical_link_key(a, b):
    lo, hi = sorted([a, b])
    return 'link-%s-%s' % (lo, hi)


def link_side_a_intf(link):
    """Return the interface on canonical side A of an undirected link.

    Convention: for link-A-B where A is alphabetically smaller,
    rxRate/txRate are the RX/TX counters of A's interface.
    """
    a = link.intf1.node.name
    b = link.intf2.node.name
    return link.intf1 if a <= b else link.intf2


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


def parse_ovs_dump_ports_state(text):
    """Return switch state from `ovs-ofctl dump-ports` output.

    ovs-ofctl writes useful error text when a stopped switch cannot be reached.
    Non-empty output alone is therefore not evidence that the switch is up.
    """
    out = (text or '').strip()
    if not out:
        return 'unknown'

    lower = out.lower()
    connection_errors = (
        'failed to connect',
        'broken pipe',
        'connection refused',
        'no such bridge',
        'is not a bridge',
        'does not exist',
        'version negotiation failed',
    )
    if any(marker in lower for marker in connection_errors):
        return 'down'
    if 'port' in lower:
        return 'up'
    return 'unknown'


def link_configured_bw(link):
    """Return configured link bandwidth in Mbps, or None if unknown.

    Prefer dt4n_bw, stamped by topology/command agent. Fall back to Mininet's
    interface params so pure topology-created links still expose their capacity.
    """
    bw = getattr(link, 'dt4n_bw', None)
    if bw is not None:
        try:
            return float(bw)
        except (TypeError, ValueError):
            return None

    for intf in (getattr(link, 'intf1', None), getattr(link, 'intf2', None)):
        params = getattr(intf, 'params', None)
        if isinstance(params, dict) and params.get('bw') is not None:
            try:
                return float(params['bw'])
            except (TypeError, ValueError):
                pass
    return None


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
                 cmd_timeout=3, ping_every=5, overwrite=True,
                 net_lock=None):
        self.net = net
        self.interval = interval                 # chu kỳ polling (giây) — Lesson 1.4
        self.server_names = set(server_names)     # host nào đóng vai 'server'
        self.log_path = log_path                  # ghi mỗi snapshot 1 dòng JSON (JSONL)
        self.pretty_log_path = pretty_log_path    # log dễ đọc cho người xem demo
        self.cmd_timeout = cmd_timeout            # timeout lệnh (tránh treo cả vòng lặp)
        self.ping_every = ping_every              # đo latency mỗi N chu kỳ (ping tốn + tự nhiễu)
        self.overwrite = overwrite                # True -> lần chạy sau đè log lần trước
        self._prev = {}                           # lưu (rxBytes,txBytes,timestamp) chu kỳ trước theo host
        self._prev_link = {}                      # link_key -> (rxBytes,txBytes,timestamp)
        self._ping_counter = 0                    # đếm chu kỳ để đo latency THƯA hơn
        self.net_lock = net_lock                  # Mininet node.cmd không thread-safe

    # ---- thu thập 1 HOST (qua namespace) ----
    def collect_host(self, host, now_ts):
        name = host.name
        iface = '%s-eth0' % name                  # interface chính của host trong Mininet
        # ĐỌC TRONG NAMESPACE nhưng tránh host.cmd() khi có thể để không đụng CLI.
        raw = read_host_net_dev(host)
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

        # Trạng thái vật lý thật của host: interface chính có cờ UP hay không.
        default_intf = getattr(host, 'defaultIntf', None)
        intf = default_intf() if callable(default_intf) else None
        is_up = intf.isUp() if (intf is not None and hasattr(intf, 'isUp')) else True

        return {
            'attributes': {'type': 'host',
                           'role': 'server' if name in self.server_names else 'client'},
            'features': {
                'traffic': {'rxBytes': rx, 'txBytes': tx,
                            'rxRate': round(rx_rate, 2), 'txRate': round(tx_rate, 2)},
                'status': {'state': 'up' if is_up else 'down'},
            },
        }

    # ---- thu thập 1 SWITCH (ở ROOT namespace, tránh shell tương tác) ----
    def collect_switch(self, switch):
        name = switch.name

        if getattr(switch, 'dt4n_admin_down', False):
            return {
                'attributes': {'type': 'switch'},
                'features': {
                    'status': {'state': 'down'},
                    'portStatsRaw': {'dump': 'admin down (switch stopped)'},
                },
            }

        try:
            # switch.cmd('ovs-ofctl ...') có thể treo/đụng OpenFlow version khi
            # Mininet CLI và Command Agent cùng sống trong một tiến trình. Dùng
            # API Mininet qua OVSDB để hỏi trạng thái controller connection là
            # đủ cho dashboard, và không giữ net_lock lâu một cách nguy hiểm.
            connected = switch.connected()
            state = 'up' if connected else 'down'
            raw = 'controller_connected=%s' % connected
        except Exception as e:
            state = 'unknown'
            raw = 'connected() error: %s' % e
        return {
            'attributes': {'type': 'switch'},
            'features': {
                'status': {'state': state},
                'portStatsRaw': {'dump': raw[:500]},   # cắt bớt cho gọn log
            },
        }

    # ---- đo LATENCY (thưa hơn — Lesson 1.4: không phải metric nào cũng cùng tần suất) ----
    def collect_latency(self, src, dst_ip):
        # -i 0.2: 3 gói mất khoảng 0.6s thay vì mặc định khoảng 2s.
        out = src.cmd('ping -c 3 -i 0.2 -W 1 %s' % dst_ip)
        return parse_ping(out)

    def collect_link(self, link, now_ts=None):
        """Thu trạng thái 1 physical link trong Mininet.

        net.configLinkStatus(a, b, 'down') sẽ kéo interface ở 2 đầu xuống, nên
        chỉ cần kiểm tra isUp() của cả 2 interface để phản ánh trạng thái link.
        now_ts=None giữ hành vi cũ; now_ts=float thì thêm traffic rxRate/txRate.
        """
        a = link.intf1.node.name
        b = link.intf2.node.name
        up1 = link.intf1.isUp() if hasattr(link.intf1, 'isUp') else True
        up2 = link.intf2.isUp() if hasattr(link.intf2, 'isUp') else True
        state = 'up' if up1 and up2 else 'down'

        features = {'status': {'state': state}}
        bw = link_configured_bw(link)
        if bw is not None:
            features['capacity'] = {'bwMbps': bw}
        if now_ts is not None:
            key = canonical_link_key(a, b)
            counters = read_intf_counters(link_side_a_intf(link))
            if counters is not None:
                rx, tx = counters
                prev = self._prev_link.get(key)
                if prev is None:
                    rx_rate = tx_rate = 0.0
                else:
                    dt = now_ts - prev[2]
                    rx_rate = compute_rate(rx, prev[0], dt)
                    tx_rate = compute_rate(tx, prev[1], dt)
                self._prev_link[key] = (rx, tx, now_ts)
                features['traffic'] = {
                    'rxRate': round(rx_rate, 2),
                    'txRate': round(tx_rate, 2),
                }
        return {
            'attributes': {'type': 'link', 'endpointA': a, 'endpointB': b},
            'features': features,
        }

    # ---- gom TẤT CẢ thành 1 snapshot ----
    def collect_all(self):
        """Thu snapshot theo 2 giai đoạn để không giữ net_lock lúc ping.

        Một lock duy nhất vẫn bảo vệ tài nguyên chung `net`, nhưng vùng giữ lock
        chỉ bao quanh các thao tác đọc nhanh. Ping là I/O chậm nên chạy sau khi
        đã nhả lock, giúp Command Agent chen vào tắt/bật link ngay.
        """
        lock = self.net_lock if self.net_lock is not None else nullcontext()
        with lock:
            now_ts = time.time()
            snapshot = {'timestamp': utc_now_iso(),
                        't_source': now_ts,
                        'things': {}}

            # hosts
            for host in self.net.hosts:
                data = self.collect_host(host, now_ts)
                data['t_source'] = now_ts
                snapshot['things']['host-%s' % host.name] = data

            # switches
            for sw in self.net.switches:
                data = self.collect_switch(sw)
                data['t_source'] = now_ts
                snapshot['things']['switch-%s' % sw.name] = data

            # physical links: cần để đo sync latency khi link up/down
            seen_links = set()
            for link in self.net.links:
                a = link.intf1.node.name
                b = link.intf2.node.name
                key = canonical_link_key(a, b)
                if key in seen_links:
                    continue
                seen_links.add(key)
                data = self.collect_link(link, now_ts)
                data['t_source'] = now_ts
                snapshot['things'][key] = data

            # Chỉ quyết định và lấy sẵn tham số ping trong lock; chưa ping ở đây.
            self._ping_counter += 1
            ping_ctx = None
            if self.ping_every > 0 and self._ping_counter % self.ping_every == 0 and len(self.net.hosts) >= 2:
                host_names = [h.name for h in self.net.hosts]
                h1 = self.net.get('h1') if 'h1' in host_names else self.net.hosts[0]
                srv = self.net.get('srv1') if 'srv1' in host_names else self.net.hosts[-1]
                ping_ctx = {
                    'src': h1,
                    'dst_ip': srv.IP(),
                    'src_name': h1.name,
                    'dst_name': srv.name,
                }

        # Hết lock: ping chậm không còn chặn Command Agent.
        if ping_ctx is not None:
            t_ping_start = time.time()
            lat = self.collect_latency(ping_ctx['src'], ping_ctx['dst_ip'])
            t_ping_end = time.time()
            t_source_path = (t_ping_start + t_ping_end) / 2.0
            key = 'path-%s-%s' % (ping_ctx['src_name'], ping_ctx['dst_name'])
            snapshot['things'][key] = {
                'attributes': {'type': 'path',
                               'src': ping_ctx['src_name'],
                               'dst': ping_ctx['dst_name']},
                'features': {'quality': {'latency_ms': lat['latency_ms'],
                                         'packetLoss_pct': lat['packet_loss_pct']}},
                't_source': t_source_path,
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

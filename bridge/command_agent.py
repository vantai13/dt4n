#!/usr/bin/env python3
"""
command_agent.py — Command Agent (chiều XUỐNG, Phase 4). LỚP 2 (Bridge).

VAI TRÒ: đối xứng với sync_agent.py. Nếu Sync Agent là "miệng" (đẩy state LÊN
Ditto), thì Command Agent là "TAI" (nghe lệnh TỪ Ditto để thực thi XUỐNG mạng).

BẢN LESSON 4.2 — CHỈ PHẦN "TAI":
  - Mở SSE nghe messages gửi tới controller Thing.
  - Parse subject (tên lệnh) + payload (target/params) + correlation-id.
  - TẠM THỜI chỉ LOG. Chưa thực thi (đó là Lesson 4.3), chưa phản hồi (4.4).
  Mục đích: chứng minh phần "nghe" hoạt động ĐỘC LẬP trước khi ghép phần "tay".
  (isolate before integrate — cô lập từng phần trước khi tích hợp.)

VÌ SAO SSE (push) chứ không polling (pull):
  Lệnh tới BẤT CHỢT và cần phản ứng NGAY. Polling thì trễ + lãng phí (99% câu
  hỏi rỗng). SSE giữ 1 kết nối mở, Ditto ĐẨY lệnh xuống ngay khi có -> không trễ,
  không lãng phí. (Ngược với Sync Agent Phase 2 dùng polling vì metrics cần đọc
  định kỳ đằng nào cũng lấy — hai chiều, hai mô hình khác nhau, có chủ đích.)

VÌ SAO CHUNG TIẾN TRÌNH với Mininet:
  Lesson 4.3 sẽ gọi net.configLinkStatus(...) -> cần đối tượng `net`, mà `net`
  chỉ sống trong tiến trình giữ Mininet. Nên agent này chạy như 1 THREAD NỀN
  trong run_sync.py, cạnh thread Sync Agent, dùng CHUNG net_lock để tránh race.
"""

import json
import datetime
import logging
import time

import requests

from bridge.ditto_common import (
    DITTO_BASE_URL, DITTO_AUTH, NAMESPACE, HTTP_TIMEOUT,
)

log = logging.getLogger('command_agent')

# controller Thing: điểm nhận MỌI lệnh (quyết định 4.1 — single control point).
CONTROLLER_THING_ID = '%s:controller' % NAMESPACE

# Endpoint SSE nghe message gửi tới inbox controller. KHÔNG lọc subject ở URL
# -> nhận cả 5 lệnh, tự phân loại trong code (đúng controller-Thing pattern).
INBOX_SSE_URL = '%s/things/%s/inbox/messages' % (DITTO_BASE_URL, CONTROLLER_THING_ID)

# Reconnect: kết nối sống-lâu SẼ rớt (Ditto restart, mạng chớp). Ở Python phải
# TỰ viết vòng reconnect (khác EventSource của trình duyệt tự làm giúp).
RECONNECT_DELAY = 2.0     # giây — chờ trước khi mở lại stream sau khi đứt
SSE_READ_TIMEOUT = None   # None = không timeout đọc; stream giữ mở chờ event

AUDIT_PATH = 'logs/command_agent_audit.log'   # JSON-mỗi-dòng (JSONL)

# Ngưỡng bandwidth hợp lệ (Mbps). Chặn giá trị điên rồ gây hành vi lạ ở tc.
BW_MIN = 0
BW_MAX = 100


def _ok(detail='ok'):
    return (True, 200, detail)


def _reject(code, reason):
    return (False, code, reason)


def audit(correlation_id, subject, target, params, result, reason=None):
    """Ghi 1 dòng JSON vào audit log. Không để lỗi ghi log làm sập xử lý lệnh."""
    row = {
        'ts': datetime.datetime.utcnow().isoformat() + 'Z',
        'correlationId': correlation_id,
        'subject': subject,
        'target': target,
        'params': params,
        'result': result,
        'reason': reason,
    }
    try:
        with open(AUDIT_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    except Exception as e:
        log.warning('Ghi audit lỗi (bỏ qua): %s', e)


def _resolve_link(net, thing_id):
    """org.dt4n:link-<a>-<b> -> đối tượng link trong net, hoặc None."""
    if not isinstance(thing_id, str) or ':link-' not in thing_id:
        return None
    body = thing_id.split(':link-', 1)[-1]
    parts = body.split('-')
    if len(parts) < 2:
        return None
    want = {parts[0], '-'.join(parts[1:])}
    for ln in net.links:
        a = ln.intf1.node.name
        b = ln.intf2.node.name
        if {a, b} == want:
            return ln
    return None


def _resolve_host(net, thing_id):
    """org.dt4n:host-<name> -> đối tượng host trong net, hoặc None."""
    if not isinstance(thing_id, str) or ':host-' not in thing_id:
        return None
    name = thing_id.split(':host-', 1)[-1]
    for h in net.hosts:
        if h.name == name:
            return h
    return None


def h_disable_link(net, target, params):
    ln = _resolve_link(net, target)
    if ln is None:
        return _reject(404, 'target not found: %s' % target)
    a, b = ln.intf1.node.name, ln.intf2.node.name
    net.configLinkStatus(a, b, 'down')
    return _ok('link %s-%s -> down' % (a, b))


def h_enable_link(net, target, params):
    ln = _resolve_link(net, target)
    if ln is None:
        return _reject(404, 'target not found: %s' % target)
    a, b = ln.intf1.node.name, ln.intf2.node.name
    net.configLinkStatus(a, b, 'up')
    return _ok('link %s-%s -> up' % (a, b))


def h_set_bandwidth(net, target, params):
    ln = _resolve_link(net, target)
    if ln is None:
        return _reject(404, 'target not found: %s' % target)
    if not isinstance(params, dict) or 'bw' not in params:
        return _reject(400, 'missing param: bw')
    bw = params['bw']
    if not isinstance(bw, (int, float)):
        return _reject(400, 'bw must be a number, got %r' % (bw,))
    if not (BW_MIN < bw <= BW_MAX):
        return _reject(400, 'bw out of range (%d, %d], got %s' %
                       (BW_MIN, BW_MAX, bw))
    ln.intf1.config(bw=bw)
    ln.intf2.config(bw=bw)
    return _ok('link bw -> %s Mbps' % bw)


def h_disable_host(net, target, params):
    h = _resolve_host(net, target)
    if h is None:
        return _reject(404, 'target not found: %s' % target)
    intf = h.defaultIntf()
    h.cmd('ifconfig %s down' % intf)
    return _ok('host %s -> down' % h.name)


def h_enable_host(net, target, params):
    h = _resolve_host(net, target)
    if h is None:
        return _reject(404, 'target not found: %s' % target)
    intf = h.defaultIntf()
    h.cmd('ifconfig %s up' % intf)
    return _ok('host %s -> up' % h.name)


HANDLERS = {
    'disableLink': h_disable_link,
    'enableLink': h_enable_link,
    'setBandwidth': h_set_bandwidth,
    'disableHost': h_disable_host,
    'enableHost': h_enable_host,
}


def parse_message_event(raw, event_name=None, sse_fields=None):
    """Nhận CHUỖI event.data thô từ SSE -> trả dict {subject, value, correlation_id}
    hoặc None nếu không phải message thật (heartbeat/comment/JSON hỏng).

    LƯU Ý QUAN TRỌNG (observe, don't assume ở cấp DEBUG):
      Cấu trúc envelope message của Ditto TÙY VERSION và hơi rườm rà. Ở bản 4.2
      này ta CỐ TÌNH log cả raw để NHÌN TẬN MẮT cấu trúc thật, rồi mới chỉnh path
      parse cho khớp. ĐỪNG parse mù theo trí nhớ. Các key dưới đây là điểm KHỞI
      ĐẦU hợp lý theo Ditto Protocol; bạn chỉnh lại sau khi thấy raw thật.
    """
    if not raw or not raw.strip():
        return None                      # heartbeat/dòng rỗng -> bỏ qua

    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        log.warning('SSE: bỏ qua event không parse được JSON: %.120s', raw)
        return None

    sse_fields = sse_fields or {}

    if not isinstance(msg, dict):
        return {'subject': event_name, 'value': msg,
                'correlation_id': (sse_fields.get('correlation-id')
                                   or sse_fields.get('correlationId')),
                'raw': msg}

    # Ditto có 2 dạng hay gặp:
    # 1) Protocol envelope: subject nằm trong topic/subject, payload ở value.
    # 2) SSE message endpoint bản hiện tại: subject nằm ở dòng "event:",
    #    data chính là payload JSON.
    topic = msg.get('topic', '')
    subject = topic.rsplit('/', 1)[-1] if topic else msg.get('subject')
    if subject is None:
        subject = event_name

    if 'value' in msg or 'topic' in msg or 'headers' in msg:
        value = msg.get('value')
    else:
        value = msg

    headers = msg.get('headers', {}) or {}
    correlation_id = (sse_fields.get('correlation-id')
                      or sse_fields.get('correlationId')
                      or headers.get('correlation-id')
                      or headers.get('correlationId')
                      or msg.get('correlation-id')
                      or msg.get('correlationId'))

    return {'subject': subject, 'value': value,
            'correlation_id': correlation_id, 'raw': msg}


def handle_command(parsed, net=None, net_lock=None):
    """Xử lý một lệnh: whitelist, resolve/validate, thực thi và audit.

    Trả (ok, http_code, detail) để Lesson 4.4 dùng làm response.
    """
    subject = parsed.get('subject')
    value = parsed.get('value') or {}
    cid = parsed.get('correlation_id')
    target = value.get('target') if isinstance(value, dict) else None
    params = {k: v for k, v in value.items() if k != 'target'} \
             if isinstance(value, dict) else {}

    handler = HANDLERS.get(subject)
    if handler is None:
        reason = 'unknown command: %s' % subject
        log.warning('TỪ CHỐI [%s]: %s', cid, reason)
        audit(cid, subject, target, params, 'rejected', reason)
        return _reject(400, reason)

    if net is None:
        reason = 'agent chưa gắn net (chạy sai tiến trình?)'
        audit(cid, subject, target, params, 'error', reason)
        return _reject(500, reason)

    try:
        # Khóa cả resolve + execute để trạng thái net không đổi giữa chừng.
        if net_lock is not None:
            with net_lock:
                ok, code, detail = handler(net, target, params)
        else:
            ok, code, detail = handler(net, target, params)
    except Exception as e:
        log.exception('THỰC THI LỖI [%s] %s: %s', cid, subject, e)
        audit(cid, subject, target, params, 'error', str(e))
        return _reject(500, 'execution error: %s' % e)

    result = 'ok' if ok else 'rejected'
    log.info('%s [%s] %s target=%s -> %s',
             'THỰC THI' if ok else 'TỪ CHỐI', cid, subject, target, detail)
    audit(cid, subject, target, params, result, None if ok else detail)
    return (ok, code, detail)


def send_response(session, thing_id, subject, correlation_id, http_code, detail, ok):
    """Gửi biên nhận tức thì cho lệnh đã xử lý, nếu stream cung cấp correlation-id.

    Không cập nhật twin state ở đây. State thật vẫn đi vòng Mininet -> Sync Agent
    -> Ditto, đúng nguyên tắc observe don't assume.
    """
    if not correlation_id:
        log.warning('Message không có correlation-id -> không gửi được response')
        return
    if not subject:
        log.warning('Message không có subject -> không gửi được response [%s]',
                    correlation_id)
        return

    # Response cho lệnh gửi tới inbox phải đi ra chiều outbox. Gửi lại inbox sẽ
    # tự tạo một lệnh mới cho Command Agent và có nguy cơ lặp.
    url = '%s/things/%s/outbox/messages/%s' % (
        DITTO_BASE_URL, thing_id, subject)
    body = {
        'status': 'accepted' if ok else 'rejected',
        'action': subject,
        'code': http_code,
        'result': detail,
    }
    headers = {
        'Content-Type': 'application/json',
        'correlation-id': correlation_id,
    }
    try:
        r = session.post(url, json=body, headers=headers, auth=DITTO_AUTH,
                         params={'timeout': 0}, timeout=HTTP_TIMEOUT)
        if r.status_code not in (200, 201, 202, 204):
            log.warning('Gửi response [%s] trả HTTP %d: %.160s',
                        correlation_id, r.status_code, r.text)
    except Exception as e:
        log.warning('Gửi response [%s] lỗi (bỏ qua): %s', correlation_id, e)


def _stream_once(session, stop_event, net, net_lock):
    """Mở MỘT phiên SSE, đọc từng dòng cho tới khi đứt/stop. Trả về khi cần
    reconnect. Không tự ngủ — vòng ngoài lo reconnect delay."""
    headers = {'Accept': 'text/event-stream'}
    with session.get(INBOX_SSE_URL, headers=headers, auth=DITTO_AUTH,
                     stream=True, timeout=SSE_READ_TIMEOUT) as resp:
        if resp.status_code != 200:
            # 403 -> Policy thiếu message:/ READ. 404 -> controller Thing chưa tạo.
            log.error('SSE mở thất bại: HTTP %d (%s). Kiểm Policy message:/ READ '
                      'và controller Thing tồn tại?', resp.status_code,
                      resp.text[:120])
            return
        log.info('SSE kết nối OK, đang nghe lệnh tại %s', INBOX_SSE_URL)

        # iter_lines: đọc TỪNG DÒNG khi nó tới (streaming). SSE gói event là
        # một nhóm field "event:", "data:", có thể kèm metadata tùy Ditto version.
        fields = {}
        data_buf = []
        for line in resp.iter_lines(decode_unicode=True):
            if stop_event is not None and stop_event.is_set():
                log.info('Nhận stop_event -> đóng SSE.')
                return

            if line is None:
                continue
            if line == '':
                # dòng trống = HẾT một event -> ghép buffer, xử lý, reset.
                if data_buf:
                    raw = '\n'.join(data_buf)
                    fields['data'] = raw
                    data_buf = []
                    parsed = parse_message_event(raw,
                                                 event_name=fields.get('event'),
                                                 sse_fields=fields)
                    if parsed is not None:
                        try:
                            ok, code, detail = handle_command(
                                parsed, net=net, net_lock=net_lock)
                            # Phản hồi tức thì: chỉ là biên nhận, không PATCH state.
                            send_response(session,
                                          CONTROLLER_THING_ID,
                                          parsed.get('subject'),
                                          parsed.get('correlation_id'),
                                          code, detail, ok)
                        except Exception as e:
                            # 1 lệnh lỗi KHÔNG được làm sập stream (defensive).
                            log.exception('Xử lý lệnh lỗi (bỏ qua event): %s', e)
                fields = {}
                data_buf = []
                continue

            if line.startswith(':'):
                continue                 # comment/heartbeat của SSE -> bỏ qua
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.lstrip()
                if key == 'data':
                    data_buf.append(value)
                elif key:
                    fields[key] = value
            else:
                fields[line.strip()] = ''


def run(net=None, net_lock=None, stop_event=None):
    """Vòng đời Command Agent với RECONNECT tự động.

    Bản 4.2: net và net_lock nhận vào nhưng CHƯA dùng (chưa chạm mạng). Nhận
    SẴN từ bây giờ để 4.3 dùng ngay, không phải đổi chữ ký hàm.
    """
    log.info('Command Agent start (bản 4.4: nghe + thực thi + response). controller=%s',
             CONTROLLER_THING_ID)
    session = requests.Session()
    session.auth = DITTO_AUTH

    while not (stop_event is not None and stop_event.is_set()):
        try:
            _stream_once(session, stop_event, net, net_lock)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.Timeout) as e:
            log.warning('SSE đứt (%s) -> reconnect sau %.1fs',
                        type(e).__name__, RECONNECT_DELAY)
        except Exception as e:
            log.exception('SSE lỗi bất ngờ -> reconnect sau %.1fs: %s',
                          RECONNECT_DELAY, e)

        # Ngủ trước khi mở lại (trừ khi được yêu cầu dừng).
        if stop_event is not None:
            if stop_event.wait(RECONNECT_DELAY):
                break
        else:
            time.sleep(RECONNECT_DELAY)

    log.info('Command Agent dừng.')

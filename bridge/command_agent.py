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
import logging
import time

import requests

from bridge.ditto_common import (DITTO_BASE_URL, DITTO_AUTH, NAMESPACE)

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


def parse_message_event(raw):
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

    # --- Điểm khởi đầu theo Ditto Protocol envelope ---
    # topic thường dạng: <ns>/<thingName>/things/live/messages/<subject>
    # -> subject là phần cuối cùng của topic.
    topic = msg.get('topic', '')
    subject = topic.rsplit('/', 1)[-1] if topic else msg.get('subject')

    # payload nằm ở 'value'; correlation-id ở headers.
    value = msg.get('value')
    headers = msg.get('headers', {}) or {}
    correlation_id = (headers.get('correlation-id')
                      or headers.get('correlationId'))

    return {'subject': subject, 'value': value,
            'correlation_id': correlation_id, 'raw': msg}


def handle_command(parsed):
    """Bản 4.2: CHỈ LOG. (4.3 sẽ thay bằng whitelist + validate + thực thi.)"""
    subject = parsed.get('subject')
    value = parsed.get('value')
    cid = parsed.get('correlation_id')
    log.info('LỆNH NHẬN: subject=%s | value=%s | correlation-id=%s',
             subject, value, cid)
    # (4.3: map subject -> handler, validate, net.configLinkStatus..., audit)
    # (4.4: trả response qua correlation-id, đóng vòng kín)


def _stream_once(session, stop_event):
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

        # iter_lines: đọc TỪNG DÒNG khi nó tới (streaming). SSE gói event dạng
        # "data: {...}\n\n". Ta gom các dòng 'data:' của MỘT event lại.
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
                    data_buf = []
                    parsed = parse_message_event(raw)
                    if parsed is not None:
                        try:
                            handle_command(parsed)
                        except Exception as e:
                            # 1 lệnh lỗi KHÔNG được làm sập stream (defensive).
                            log.exception('Xử lý lệnh lỗi (bỏ qua event): %s', e)
                continue

            if line.startswith(':'):
                continue                 # comment/heartbeat của SSE -> bỏ qua
            if line.startswith('data:'):
                data_buf.append(line[len('data:'):].lstrip())
            # (các field khác như 'event:', 'id:' — bản 4.2 chưa cần)


def run(net=None, net_lock=None, stop_event=None):
    """Vòng đời Command Agent với RECONNECT tự động.

    Bản 4.2: net và net_lock nhận vào nhưng CHƯA dùng (chưa chạm mạng). Nhận
    SẴN từ bây giờ để 4.3 dùng ngay, không phải đổi chữ ký hàm.
    """
    log.info('Command Agent start (bản 4.2: chỉ nghe + log). controller=%s',
             CONTROLLER_THING_ID)
    session = requests.Session()
    session.auth = DITTO_AUTH

    while not (stop_event is not None and stop_event.is_set()):
        try:
            _stream_once(session, stop_event)
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
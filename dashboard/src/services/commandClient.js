// ---------------------------------------------------------------------------
// commandClient.js — TẦNG DỊCH VỤ gửi LỆNH (chiều XUỐNG). LỚP 4.
// Song song với dittoClient.js (đọc state) và sseClient.js (nghe state).
// Đây là "kênh gửi" mới — POST message tới controller Thing.
//
// TRÁCH NHIỆM DUY NHẤT: gói lệnh thành HTTP POST đúng giao thức 4.1, sinh
//   correlation-id, trả response ①. KHÔNG biết gì về vẽ/merge (việc của App.vue).
// ---------------------------------------------------------------------------

const NAMESPACE = import.meta.env.VITE_DITTO_NAMESPACE || 'org.dt4n'
const DITTO_PREFIX = '/ditto/api/2'
const CONTROLLER = `${NAMESPACE}:controller`

// Sinh correlation-id duy nhất mỗi lệnh (để ghép response ①). crypto.randomUUID
// có sẵn trong trình duyệt hiện đại.
function newCorrelationId() {
  return (crypto?.randomUUID?.() || 'cmd-' + Date.now() + '-' + Math.random())
}

// Gửi MỘT lệnh. Trả về { ok, response } của phản hồi ① (biên nhận tức thì).
// LƯU Ý: ok ở đây = "lệnh HỢP LỆ & agent đã thực thi", KHÔNG phải "mạng đã đổi".
// Bằng chứng mạng đổi = SSE state (kênh nhận), App.vue quan sát riêng.
export async function sendCommand(subject, target, params = {}) {
  const cid = newCorrelationId()
  const url = `${DITTO_PREFIX}/things/${CONTROLLER}/inbox/messages/${subject}`
         + `?timeout=5`
  const body = { target, ...params }

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'correlation-id': cid,
    },
    body: JSON.stringify(body),
  })

  // response ① có thể là JSON {status:accepted/rejected,...} hoặc lỗi HTTP.
  let response = null
  try { response = await res.json() } catch (_) { /* có thể rỗng */ }
  return { ok: res.ok, correlationId: cid, response }
}
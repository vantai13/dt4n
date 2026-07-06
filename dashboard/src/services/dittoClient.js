// ---------------------------------------------------------------------------
// dittoClient.js — TẦNG DỊCH VỤ (service layer) nói chuyện với Ditto.
// Khâu FETCH trong pipeline Lesson 3.2. LỚP 4 (frontend), phần "lấy dữ liệu".
//
// TRÁCH NHIỆM DUY NHẤT: biết CÁCH lấy Thing từ Ditto (URL, Search API,
//   pagination, lỗi HTTP). KHÔNG biết gì về vẽ đồ thị, node, cạnh -> việc đó
//   là của translate.js. Tách bạch (Separation of Concerns).
//
// VÌ SAO TỒN TẠI (DRY): gom mọi lời gọi Ditto về MỘT nơi. Đổi API -> sửa 1 file.
//   Component chỉ gọi fetchAllThings(), không cần biết bên dưới có pagination.
// ---------------------------------------------------------------------------

// Namespace chứa Thing của dự án. Đọc từ .env (biến VITE_* mới lọt xuống browser).
// Fallback 'org.dt4n' cho khớp bridge/ditto_common.py.
const NAMESPACE = import.meta.env.VITE_DITTO_NAMESPACE || 'org.dt4n'

// Tiền tố '/ditto' khớp proxy trong vite.config.js. Browser gọi cùng origin,
// Vite chuyển tiếp sang Ditto :8080 (kèm auth). KHÔNG bao giờ ghi thẳng
// 'http://localhost:8080' ở đây -> nếu ghi thẳng sẽ dính CORS + lộ ý đồ.
const DITTO_PREFIX = '/ditto/api/2'


// ===========================================================================
// HÀM TẦNG THẤP: dittoUrl — nơi DUY NHẤT chạm fetch() và xử lý lỗi HTTP thô.
// ===========================================================================
async function dittoGet(path) {
  // Gửi request. 'await' = đợi (không đơ) tới khi Ditto phản hồi.
  const res = await fetch(DITTO_PREFIX + path, {
    headers: { Accept: 'application/json' },
  })

  // fetch KHÔNG tự ném lỗi khi server trả 4xx/5xx (đây là bẫy người mới hay dính!)
  // -> phải TỰ kiểm tra res.ok (true nếu status 200-299).
  if (!res.ok) {  
    const body = await res.text()
    throw new Error(`Ditto ${res.status} tại ${path}: ${body.slice(0, 200)}`)
  }

  // Parse body JSON thành object JS. Cũng là bất đồng bộ -> await.
  return res.json()
}


// ===========================================================================
// HÀM TẦNG GIỮA: searchThingsPage — lấy MỘT trang kết quả + con trỏ trang sau.
// ===========================================================================
async function searchThingsPage(cursor) {
  // Xây query string cho Ditto Search API:
  //   - filter: chỉ lấy Thing trong namespace của mình (eq = equals).
  //   - option: size(200) mỗi trang; cursor(...) để lấy trang tiếp theo.
  const params = new URLSearchParams()
  params.set('filter', `eq(_namespace,"${NAMESPACE}")`)

  const options = ['size(200)']
  if (cursor) options.push(`cursor(${cursor})`)
  params.set('option', options.join(','))

  const data = await dittoGet('/search/things?' + params.toString())

  // Ditto trả { items: [...Thing...], cursor: "..." (nếu còn trang sau) }.
  return {
    items: data.items || [],
    nextCursor: data.cursor || null,   // null = hết trang
  }
}


// ===========================================================================
// HÀM TẦNG CAO (API CÔNG KHAI): fetchAllThings — lấy HẾT mọi Thing, gộp lại.
// Đây là hàm DUY NHẤT component cần gọi. Nó GIẤU chuyện phân trang.
// ===========================================================================
export async function fetchAllThings() {
  const all = []
  let cursor = null
  let guard = 0   // van an toàn: chặn vòng lặp vô hạn nếu Ditto trả cursor lỗi.

  do {
    const { items, nextCursor } = await searchThingsPage(cursor)
    all.push(...items)
    cursor = nextCursor
    guard += 1
  } while (cursor && guard < 100)   // còn cursor -> còn trang -> lấy tiếp

  return all
}
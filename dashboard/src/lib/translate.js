// ---------------------------------------------------------------------------
// translate.js — LỚP DỊCH (Anti-Corruption Layer) phía frontend.
// Khâu TRANSLATE trong pipeline Lesson 3.2. LỚP 4 (frontend), phần "dịch".
//
// TRÁCH NHIỆM DUY NHẤT: biến Thing (ngôn ngữ Ditto) -> node/edge (ngôn ngữ
//   vis-network). KHÔNG gọi mạng, KHÔNG đụng DOM -> đây là các PURE FUNCTION
//   (cùng input luôn cho cùng output) => test được không cần browser.
//
// SỬA LỖI REPO CŨ: repo cũ đoán loại qua tên (id.startsWith('h')) -> 'srv1'
//   bị tưởng là switch. Ở đây ta ĐỌC attributes.type mà backend đã lưu tường
//   minh -> "đừng suy diễn cái phải được khai báo".
// ---------------------------------------------------------------------------


// ===========================================================================
// Việc 1: tách TÊN NGẮN từ thingId đầy đủ.
//   'org.dt4n:host-h1'    -> 'h1'
//   'org.dt4n:switch-s1'  -> 's1'
//   'org.dt4n:link-h1-s1' -> 'h1-s1'  (link không dùng làm node id, nhưng để đồng nhất)
// Lấy phần sau dấu ':' rồi bỏ tiền tố loại ('host-'/'switch-'/'link-').
// ===========================================================================
export function shortName(thingId) {
  const afterColon = thingId.split(':').pop()          // 'host-h1'
  return afterColon.replace(/^(host|switch|link)-/, '') // 'h1'
}


// ===========================================================================
// Đọc một property lồng sâu an toàn: features.<feature>.properties.<key>.
// Ditto lồng 'properties' (nhớ adapter.py). Dùng ?. để KHÔNG vỡ nếu thiếu tầng.
// ===========================================================================
function prop(thing, feature, key) {
  return thing?.features?.[feature]?.properties?.[key]
}


// ===========================================================================
// Việc 2 + 3: dịch danh sách Thing -> { nodes: [...], edges: [...] }.
// Đây là HÀM CHÍNH mà component gọi.
// ===========================================================================
export function thingsToGraph(things) {
  const nodes = []
  const edges = []

  for (const thing of things) {
    // NGUỒN SỰ THẬT về loại: attributes.type (KHÔNG đoán qua tên).
    const type = thing?.attributes?.type
    const name = shortName(thing.thingId)

    if (type === 'host' || type === 'switch') {
      // --- HOST / SWITCH -> NODE ---
      const state = prop(thing, 'status', 'state') || 'unknown'

      nodes.push({
        id: name,                 // tên ngắn -> khớp endpointA/B của link
        label: name,
        type,                     // giữ để chọn icon/màu ở tầng vẽ
        state,                    // 'up' | 'down' | ...
        // Gom mọi thông tin thô để InfoPanel hiển thị khi click (không mất mát).
        raw: thing,
      })
    } else if (type === 'link') {
      // --- LINK -> EDGE --- (đọc 2 đầu đã lưu sẵn ở Phase 2)
      const a = thing?.attributes?.endpointA
      const b = thing?.attributes?.endpointB
      if (!a || !b) continue      // thiếu 2 đầu -> bỏ qua an toàn, không vẽ cạnh mồ côi

      edges.push({
        id: name,                 // 'h1-s1'
        from: a,
        to: b,
        state: prop(thing, 'status', 'state') || 'unknown',
        raw: thing,
      })
    }
    // type lạ / thiếu -> lặng lẽ bỏ qua (defensive: không cho dữ liệu rác làm vỡ đồ thị)
  }

  return { nodes, edges }
}
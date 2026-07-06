<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import TopologyView from './components/TopologyView.vue'
import InfoPanel from './components/InfoPanel.vue'
import AlertPanel from './components/AlertPanel.vue'
import { fetchAllThings } from './services/dittoClient.js'
import { openThingStream } from './services/sseClient.js'
import { thingsToGraph, applyDelta } from './lib/translate.js'

// ---------------------------------------------------------------------------
// App.vue — ĐIỀU PHỐI (orchestrator). LỚP 4.
// Lesson 3.2: fetch -> dịch -> vẽ (tĩnh).
// Lesson 3.3: THÊM real-time — giữ STATE (thingsById), nghe SSE, merge delta,
//   re-sync khi reconnect. STATE là trung tâm: fetch dựng, delta merge vào,
//   đồ thị vẽ TỪ state (không bao giờ vẽ thẳng từ delta).
// ---------------------------------------------------------------------------

const graph = ref({ nodes: [], edges: [] })   // dữ liệu ĐÃ dịch, cho TopologyView
const status = ref('loading')
const errorMsg = ref('')
const live = ref(false)                        // đang nhận real-time?
const selectedNodeId = ref(null)
const selectedEdgeId = ref(null)

// STATE trung tâm: map thingId -> Thing đầy đủ. KHÔNG phải ref (không cần Vue
// theo dõi sâu map này); mỗi lần đổi ta dịch lại -> gán graph.value (ref) -> UI đổi.
let thingsById = {}

// Dựng lại state đầy đủ từ Ditto (dùng cho lần đầu VÀ mỗi lần re-sync).
async function resync() {
  const things = await fetchAllThings()        // FETCH snapshot đầy đủ
  thingsById = Object.fromEntries(things.map(t => [t.thingId, t]))
  rebuildGraph()
}

// Dịch state -> graph (đồ thị vẽ TỪ state, đây là điểm mấu chốt kiến trúc).
function rebuildGraph() {
  graph.value = thingsToGraph(Object.values(thingsById))
  status.value = graph.value.nodes.length ? 'ready' : 'error'
  if (!graph.value.nodes.length)
    errorMsg.value = 'Ditto không trả về Thing nào. Kiểm tra namespace / bootstrap / Sync Agent.'
}

async function loadTopology() {
  status.value = 'loading'
  try {
    await resync()                             // snapshot ban đầu
    startStream()                              // rồi mới nghe delta
  } catch (e) {
    status.value = 'error'
    errorMsg.value = e.message
  }
}

// --- Real-time: mở SSE, xử lý 3 callback ---
let closeStream = null
function startStream() {
  if (closeStream) return                      // đã mở rồi -> không mở trùng
  closeStream = openThingStream({
    // Mỗi delta (Thing-mảnh) -> merge vào state -> dịch lại -> đồ thị đổi.
    onDelta: (partial) => {
      thingsById = applyDelta(thingsById, partial)   // MERGE (đã test kỹ)
      rebuildGraph()
    },
    // Kết nối (lại) OK -> RE-SYNC: lấy lại snapshot phòng khi bỏ lỡ delta lúc rớt.
    onOpen: async () => {
      live.value = true
      try { await resync() } catch (_) { /* giữ state cũ nếu re-sync lỗi tạm */ }
    },
    onError: () => { live.value = false },      // EventSource sẽ tự thử lại
  })
}

onMounted(loadTopology)
onUnmounted(() => { if (closeStream) closeStream() })   // dọn kết nối khi rời trang

// Nhận sự kiện click từ TopologyView -> cho InfoPanel biết đang chọn gì.
const onNode = id => { selectedNodeId.value = id; selectedEdgeId.value = null }
const onEdge = id => { selectedEdgeId.value = id; selectedNodeId.value = null }
const onClear = () => { selectedNodeId.value = null; selectedEdgeId.value = null }

// Click một cảnh báo -> chọn đúng node/edge đó (nối AlertPanel với InfoPanel).
const onAlertFocus = (a) => {
  if (a.kind === 'node') onNode(a.id)
  else onEdge(a.id)
}
</script>

<template>
  <div class="app">
    <header class="app-header">
      <span class="brand">Digital Twin — Network Dashboard</span>
      <span class="live" :class="{ on: live }">
        <span class="dot"></span>{{ live ? 'LIVE' : 'OFFLINE' }}
      </span>
    </header>

    <div v-if="status === 'ready'" class="main">
      <TopologyView
        :graph="graph"
        @node-selected="onNode"
        @edge-selected="onEdge"
        @selection-cleared="onClear"
      />
      <div class="side">
        <AlertPanel :graph="graph" @focus="onAlertFocus" />
        <InfoPanel :graph="graph" :selectedNodeId="selectedNodeId" :selectedEdgeId="selectedEdgeId" />
      </div>
    </div>

    <div v-else-if="status === 'loading'" class="center">
      <div class="spinner"></div><p>Đang tải topology từ Ditto…</p>
    </div>

    <div v-else class="center error">
      <div class="err-icon">⚠️</div>
      <h2>Không tải được topology</h2>
      <p>{{ errorMsg }}</p>
      <button class="reload" @click="loadTopology">↻ Thử lại</button>
    </div>
  </div>
</template>

<style>
body, html { margin: 0; height: 100%; font-family: Arial, sans-serif; background: #0f172a; }
.app { display: flex; flex-direction: column; height: 100vh; }
.app-header { display: flex; align-items: center; justify-content: space-between;
  height: 60px; padding: 0 1.5rem; border-bottom: 1px solid #334155; }
.brand { color: #00F7F7; font-size: 1.25rem; font-weight: 700;
  text-shadow: 0 0 8px rgba(0,247,247,0.4); }
.reload { background: #00F7F7; color: #0f172a; border: none; border-radius: 6px;
  padding: 6px 14px; font-weight: 600; cursor: pointer; }
.live { display: flex; align-items: center; gap: 6px; font-size: 0.8rem;
  font-weight: 700; letter-spacing: 1px; color: #64748b; }
.live.on { color: #22c55e; }
.live .dot { width: 9px; height: 9px; border-radius: 50%; background: #64748b; }
.live.on .dot { background: #22c55e; box-shadow: 0 0 8px #22c55e; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
.main { display: flex; flex: 1; overflow: hidden; }
.side { width: 340px; flex-shrink: 0; display: flex; flex-direction: column;
  background: #1e293b; border-left: 1px solid #334155; overflow-y: auto; }
.side > * { border-left: none; }
.center { display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: calc(100vh - 60px); color: #94a3b8; gap: 1rem; padding: 2rem; text-align: center; }
.center.error h2 { color: #f87171; margin: 0; }
.err-icon { font-size: 3rem; }
.spinner { width: 48px; height: 48px; border: 4px solid #334155; border-top-color: #00F7F7;
  border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
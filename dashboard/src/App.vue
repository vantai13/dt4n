<script setup>
import { ref, onMounted } from 'vue'
import TopologyView from './components/TopologyView.vue'
import InfoPanel from './components/InfoPanel.vue'
import { fetchAllThings } from './services/dittoClient.js'
import { thingsToGraph } from './lib/translate.js'

// ---------------------------------------------------------------------------
// App.vue — ĐIỀU PHỐI (orchestrator). LỚP 4.
// So với repo cũ (~400 dòng God Component ôm socket + merge + đoán loại), bản
// này CHỈ điều phối: gọi fetch -> dịch -> đưa xuống component con. Logic nặng
// nằm ở dittoClient.js (fetch) và translate.js (dịch) -> mỗi file 1 trách nhiệm.
// ---------------------------------------------------------------------------

const graph = ref({ nodes: [], edges: [] })   // dữ liệu đã dịch, sẵn cho TopologyView
const status = ref('loading')                  // 'loading' | 'ready' | 'error'
const errorMsg = ref('')
const selectedNodeId = ref(null)
const selectedEdgeId = ref(null)

async function loadTopology() {
  status.value = 'loading'
  try {
    const things = await fetchAllThings()      // Chặng 1: FETCH
    graph.value = thingsToGraph(things)         // Chặng 2: TRANSLATE
    status.value = graph.value.nodes.length ? 'ready' : 'error'
    if (!graph.value.nodes.length)
      errorMsg.value = 'Ditto không trả về Thing nào. Kiểm tra namespace / bootstrap / Sync Agent.'
  } catch (e) {
    status.value = 'error'
    errorMsg.value = e.message                  // hiện lỗi thật để dễ debug
  }
}

onMounted(loadTopology)

// Nhận sự kiện click từ TopologyView -> cho InfoPanel biết đang chọn gì.
const onNode = id => { selectedNodeId.value = id; selectedEdgeId.value = null }
const onEdge = id => { selectedEdgeId.value = id; selectedNodeId.value = null }
const onClear = () => { selectedNodeId.value = null; selectedEdgeId.value = null }
</script>

<template>
  <div class="app">
    <header class="app-header">
      <span class="brand">Digital Twin — Network Dashboard</span>
      <button class="reload" @click="loadTopology">↻ Tải lại</button>
    </header>

    <div v-if="status === 'ready'" class="main">
      <TopologyView
        :graph="graph"
        @node-selected="onNode"
        @edge-selected="onEdge"
        @selection-cleared="onClear"
      />
      <InfoPanel :graph="graph" :selectedNodeId="selectedNodeId" :selectedEdgeId="selectedEdgeId" />
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
.main { display: flex; flex: 1; overflow: hidden; }
.center { display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: calc(100vh - 60px); color: #94a3b8; gap: 1rem; padding: 2rem; text-align: center; }
.center.error h2 { color: #f87171; margin: 0; }
.err-icon { font-size: 3rem; }
.spinner { width: 48px; height: 48px; border: 4px solid #334155; border-top-color: #00F7F7;
  border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
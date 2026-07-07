<template>
  <aside class="info-panel">
    <h3>INFO PANEL</h3>

    <div class="info-card">
      <h4>Network Overview</h4>
      <p><span>Total Nodes:</span> <strong>{{ graph.nodes.length }}</strong></p>
      <p><span>Total Links:</span> <strong>{{ graph.edges.length }}</strong></p>
    </div>

    <div class="info-card">
      <h4>Selected Details</h4>

      <template v-if="node">
        <div v-if="node.state === 'down'" class="warn">⚠️ Device is DOWN</div>
        <p><span>Name:</span> <strong>{{ node.id }}</strong></p>
        <p><span>Type:</span> <strong>{{ node.type }}</strong></p>
        <p><span>Status:</span> <strong>{{ node.state }}</strong></p>
        <p v-if="ip"><span>IP:</span> <strong>{{ ip }}</strong></p>
      </template>

      <template v-else-if="edge">
        <div v-if="edge.state === 'down'" class="warn">⚠️ Link is DOWN</div>
        <p><span>Link:</span> <strong>{{ edge.id }}</strong></p>
        <p><span>From:</span> <strong>{{ edge.from }}</strong></p>
        <p><span>To:</span> <strong>{{ edge.to }}</strong></p>
        <p><span>Status:</span> <strong>{{ edge.state }}</strong></p>
      </template>

      <template v-else>
        <p class="placeholder">(Click a node or link to view details)</p>
      </template>
    </div>

    <div class="info-card" v-if="edge">
      <h4>Điều khiển Link</h4>
      <button v-if="edge.state !== 'down'" class="cmd-btn danger"
              @click="emitCmd('disableLink', edge.rawId)">Tắt link</button>
      <button v-else class="cmd-btn ok"
              @click="emitCmd('enableLink', edge.rawId)">Bật lại link</button>
      <div class="bw-row">
        <input type="number" v-model.number="bw" min="1" max="100" placeholder="bw (Mbps)">
        <button class="cmd-btn" @click="emitCmd('setBandwidth', edge.rawId, { bw })">Đặt bw</button>
      </div>
      <p v-if="cmdStatus" class="cmd-status">{{ cmdStatus }}</p>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps(['graph', 'selectedNodeId', 'selectedEdgeId', 'cmdFeedback'])
const emit = defineEmits(['command'])

const node = computed(() =>
  props.selectedNodeId ? props.graph.nodes.find(n => n.id === props.selectedNodeId) : null)
const edge = computed(() =>
  props.selectedEdgeId ? props.graph.edges.find(e => e.id === props.selectedEdgeId) : null)

// IP lấy từ raw Thing (attributes.ip) — nhờ translate.js giữ 'raw' nên có sẵn.
const ip = computed(() => node.value?.raw?.attributes?.ip)
const bw = ref(10)
const localCmdStatus = ref('')
const cmdStatus = computed(() => props.cmdFeedback || localCmdStatus.value)

function emitCmd(subject, target, params = {}) {
  localCmdStatus.value = 'Đang gửi lệnh...'
  emit('command', { subject, target, params })
}
</script>

<style scoped>
.info-panel { width: 340px; flex-shrink: 0; background: #1e293b; padding: 1.5rem;
  color: #94a3b8; border-left: 1px solid #334155; overflow-y: auto; }
h3 { color: #00F7F7; text-transform: uppercase; letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0,247,247,0.7); }
.info-card { background: #0f172a; padding: 1rem; border-radius: 8px;
  margin-bottom: 1rem; border: 1px solid #334155; }
.info-card h4 { color: #00F7F7; margin: 0 0 0.75rem; border-bottom: 1px solid #334155;
  padding-bottom: 0.5rem; }
.info-card p { display: flex; justify-content: space-between; margin: 0.5rem 0; font-size: 0.9rem; }
.info-card p strong { color: #00F7F7; }
.placeholder { font-style: italic; color: #64748b; text-align: center; }
.warn { background: #5a1d1d; border: 1px solid #dc2626; color: #fca5a5;
  padding: 0.6rem; border-radius: 6px; text-align: center; margin-bottom: 0.75rem; font-weight: bold; }
.cmd-btn { width: 100%; border: none; border-radius: 6px; padding: 0.6rem 0.75rem;
  background: #334155; color: #e2e8f0; font-weight: 700; cursor: pointer; }
.cmd-btn:hover { filter: brightness(1.15); }
.cmd-btn.danger { background: #dc2626; color: #fff; }
.cmd-btn.ok { background: #16a34a; color: #fff; }
.bw-row { display: grid; grid-template-columns: 1fr 92px; gap: 0.5rem; margin-top: 0.75rem; }
.bw-row input { min-width: 0; background: #020617; border: 1px solid #334155;
  border-radius: 6px; color: #e2e8f0; padding: 0.55rem 0.65rem; }
.cmd-status { color: #e2e8f0; display: block !important; line-height: 1.35; }
</style>

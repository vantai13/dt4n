<script setup>
import { Network } from 'vis-network/standalone';
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  selectedKey: { type: String, default: '' },
});

const emit = defineEmits(['select']);
const container = ref(null);
let network = null;

const hasData = computed(() => props.nodes.length > 0 || props.edges.length > 0);

const options = {
  autoResize: true,
  interaction: {
    hover: true,
    multiselect: false,
    navigationButtons: true,
    keyboard: false,
  },
  physics: {
    enabled: true,
    solver: 'forceAtlas2Based',
    stabilization: { iterations: 80, fit: true },
    forceAtlas2Based: {
      gravitationalConstant: -70,
      centralGravity: 0.012,
      springLength: 155,
      springConstant: 0.08,
    },
  },
  nodes: {
    borderWidth: 2,
    borderWidthSelected: 4,
    shadow: false,
    margin: 10,
  },
  edges: {
    smooth: {
      type: 'dynamic',
      roundness: 0.18,
    },
    selectionWidth: 2,
  },
};

function processNodes(nodes) {
  return nodes.map((node) => {
    const selected = props.selectedKey === `node:${node.id}`;
    return {
      ...node,
      borderWidth: selected ? 4 : 2,
      font: {
        ...(node.font || {}),
        bold: selected,
      },
    };
  });
}

function processEdges(edges) {
  return edges.map((edge) => {
    const selected = props.selectedKey === `edge:${edge.id}`;
    return {
      ...edge,
      width: selected ? Math.max(4, edge.width || 2) : edge.width,
    };
  });
}

function graphData() {
  return {
    nodes: processNodes(props.nodes),
    edges: processEdges(props.edges),
  };
}

function setGraphData() {
  if (!network) {
    return;
  }
  network.setData(graphData());
  nextTick(() => network?.fit({ animation: { duration: 250, easingFunction: 'easeInOutQuad' } }));
}

function handleClick(params) {
  if (params.nodes.length) {
    emit('select', { type: 'node', id: params.nodes[0] });
    return;
  }
  if (params.edges.length) {
    emit('select', { type: 'edge', id: params.edges[0] });
    return;
  }
  emit('select', null);
}

onMounted(() => {
  network = new Network(container.value, graphData(), options);
  network.on('click', handleClick);
});

onBeforeUnmount(() => {
  if (network) {
    network.destroy();
    network = null;
  }
});

watch(() => [props.nodes, props.edges], setGraphData, { deep: true });
watch(() => props.selectedKey, setGraphData);
</script>

<template>
  <section class="topology-surface" aria-label="Network topology">
    <div ref="container" class="network-canvas"></div>
    <div v-if="props.loading && !hasData" class="empty-state">Loading Ditto Things</div>
    <div v-else-if="!hasData" class="empty-state">No Things found</div>
  </section>
</template>

<style scoped>
.topology-surface {
  position: relative;
  min-height: 520px;
  height: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #ffffff;
  overflow: hidden;
}

.network-canvas {
  width: 100%;
  height: 100%;
  min-height: 520px;
}

.empty-state {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--muted);
  font-size: 15px;
  pointer-events: none;
}

:deep(.vis-navigation .vis-button) {
  border-radius: 8px;
  box-shadow: none;
}

@media (max-width: 920px) {
  .topology-surface,
  .network-canvas {
    min-height: 420px;
  }
}
</style>

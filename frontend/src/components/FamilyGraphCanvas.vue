<template>
  <div class="grid gap-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-sm text-muted-foreground">{{ summary }}</p>
      <div class="flex items-center gap-2">
        <Button type="button" variant="outline" size="sm" @click="zoomOut">缩小</Button>
        <Badge variant="secondary">{{ Math.round(zoom * 100) }}%</Badge>
        <Button type="button" variant="outline" size="sm" @click="zoomIn">放大</Button>
        <Button type="button" variant="ghost" size="sm" @click="resetView">重置</Button>
      </div>
    </div>

    <div class="overflow-auto rounded-lg border bg-muted/20 p-4">
      <div class="relative origin-top-left transition-transform" :style="canvasStyle">
        <svg class="pointer-events-none absolute inset-0" :width="width" :height="height" aria-hidden="true">
          <g v-for="edge in visibleEdges" :key="`${edge.from}-${edge.to}-${edge.label}`">
            <path
              :d="edgePath(edge)"
              class="fill-none stroke-border"
              stroke-width="2"
              stroke-linecap="round"
            />
            <text
              :x="edgeLabelPosition(edge).x"
              :y="edgeLabelPosition(edge).y"
              class="fill-primary text-[12px] font-medium"
              text-anchor="middle"
            >
              {{ edge.label }}
            </text>
          </g>
        </svg>

        <div
          v-for="node in visibleNodes"
          :key="node.id"
          class="absolute"
          :style="{ left: `${node.x}px`, top: `${node.y}px`, width: `${nodeWidth}px` }"
        >
          <div class="rounded-lg border bg-card p-3 shadow-sm">
            <div class="flex items-start justify-between gap-2">
              <RouterLink
                class="min-w-0 font-medium leading-none hover:text-primary"
                :to="{ name: 'member-detail', params: { treeId, memberId: node.id } }"
              >
                <span class="block truncate">{{ node.name }}</span>
              </RouterLink>
              <Button
                v-if="collapsibleIds.has(node.id)"
                type="button"
                variant="ghost"
                size="sm"
                class="h-6 px-2"
                @click="toggleCollapse(node.id)"
              >
                {{ collapsedIds.has(node.id) ? "展开" : "折叠" }}
              </Button>
            </div>
            <p class="mt-2 text-xs text-muted-foreground">#{{ node.id }} · {{ node.meta }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface GraphNode {
  id: number;
  name: string;
  meta: string;
  x: number;
  y: number;
}

export interface GraphEdge {
  from: number;
  to: number;
  label: string;
}

const nodeWidth = 180;
const nodeHeight = 72;
const padding = 48;

const props = defineProps<{
  treeId: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}>();

const zoom = ref(1);
const collapsedIds = ref(new Set<number>());

const childrenByNode = computed(() => {
  const children = new Map<number, number[]>();
  for (const edge of props.edges) {
    children.set(edge.from, [...(children.get(edge.from) ?? []), edge.to]);
  }
  return children;
});

const collapsibleIds = computed(() => {
  return new Set([...childrenByNode.value.entries()].filter(([, children]) => children.length > 0).map(([id]) => id));
});

const hiddenIds = computed(() => {
  const hidden = new Set<number>();
  const visit = (nodeId: number) => {
    for (const childId of childrenByNode.value.get(nodeId) ?? []) {
      hidden.add(childId);
      visit(childId);
    }
  };
  for (const nodeId of collapsedIds.value) {
    visit(nodeId);
  }
  return hidden;
});

const visibleNodes = computed(() => props.nodes.filter((node) => !hiddenIds.value.has(node.id)));
const visibleNodeIds = computed(() => new Set(visibleNodes.value.map((node) => node.id)));
const visibleEdges = computed(() =>
  props.edges.filter((edge) => visibleNodeIds.value.has(edge.from) && visibleNodeIds.value.has(edge.to))
);

const width = computed(() => {
  const maxX = Math.max(...props.nodes.map((node) => node.x), 0);
  return maxX + nodeWidth + padding;
});

const height = computed(() => {
  const maxY = Math.max(...props.nodes.map((node) => node.y), 0);
  return maxY + nodeHeight + padding;
});

const canvasStyle = computed(() => ({
  width: `${width.value}px`,
  height: `${height.value}px`,
  transform: `scale(${zoom.value})`
}));

const summary = computed(() => `图谱节点 ${visibleNodes.value.length}/${props.nodes.length}，连线 ${visibleEdges.value.length}`);

function nodeCenter(nodeId: number) {
  const node = props.nodes.find((item) => item.id === nodeId);
  return {
    x: (node?.x ?? 0) + nodeWidth / 2,
    y: (node?.y ?? 0) + nodeHeight / 2
  };
}

function edgePath(edge: GraphEdge) {
  const from = nodeCenter(edge.from);
  const to = nodeCenter(edge.to);
  const midY = (from.y + to.y) / 2;
  if (Math.abs(from.y - to.y) < 12) {
    return `M ${from.x} ${from.y} L ${to.x} ${to.y}`;
  }
  return `M ${from.x} ${from.y} C ${from.x} ${midY}, ${to.x} ${midY}, ${to.x} ${to.y}`;
}

function edgeLabelPosition(edge: GraphEdge) {
  const from = nodeCenter(edge.from);
  const to = nodeCenter(edge.to);
  return {
    x: (from.x + to.x) / 2,
    y: (from.y + to.y) / 2 - 8
  };
}

function toggleCollapse(nodeId: number) {
  const next = new Set(collapsedIds.value);
  if (next.has(nodeId)) {
    next.delete(nodeId);
  } else {
    next.add(nodeId);
  }
  collapsedIds.value = next;
}

function zoomIn() {
  zoom.value = Math.min(1.8, Number((zoom.value + 0.1).toFixed(2)));
}

function zoomOut() {
  zoom.value = Math.max(0.5, Number((zoom.value - 0.1).toFixed(2)));
}

function resetView() {
  zoom.value = 1;
  collapsedIds.value = new Set();
}

watch(
  () => props.nodes,
  () => {
    collapsedIds.value = new Set();
    zoom.value = 1;
  }
);
</script>

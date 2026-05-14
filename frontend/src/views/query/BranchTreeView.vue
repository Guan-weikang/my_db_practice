<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">查询</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">分支树</h1>
        <p class="mt-2 text-sm text-muted-foreground">输入根成员，按层级查看后代分支。</p>
      </div>
      <Button as-child variant="outline">
        <RouterLink :to="{ name: 'family-tree-detail', params: { treeId } }">返回族谱</RouterLink>
      </Button>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>查询条件</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="grid gap-4 md:grid-cols-[220px_180px_auto]" @submit.prevent="handleLoadTree">
          <div class="grid gap-2">
            <Label for="root-member">根成员 ID</Label>
            <Input id="root-member" v-model.number="rootMemberId" min="1" required type="number" :placeholder="memberIdPlaceholder" />
            <p class="text-xs text-muted-foreground">{{ memberIdHint }}</p>
          </div>
          <div class="grid gap-2">
            <Label for="max-depth">最大深度</Label>
            <Input id="max-depth" v-model.number="maxDepth" max="10" min="1" type="number" />
          </div>
          <div class="flex items-end">
            <Button class="w-full" :disabled="loading" type="submit">
              <Spinner v-if="loading" data-icon="inline-start" />
              {{ loading ? "加载中" : "查看分支" }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <Alert v-if="feedback" :variant="feedbackType === 'error' ? 'destructive' : 'default'">
      <AlertTitle>{{ feedbackType === "error" ? "加载失败" : "加载完成" }}</AlertTitle>
      <AlertDescription>{{ feedback }}</AlertDescription>
    </Alert>

    <Card v-if="loading">
      <CardContent class="grid gap-3 p-6">
        <Skeleton class="h-12 w-full" />
        <Skeleton class="h-12 w-11/12" />
        <Skeleton class="h-12 w-10/12" />
      </CardContent>
    </Card>

    <Card v-else-if="tree">
      <CardHeader>
        <CardTitle>{{ tree.root_member.name }} 的后代分支</CardTitle>
        <CardDescription>根成员 #{{ tree.root_member.member_id }}，最大深度 {{ tree.max_depth }}。</CardDescription>
      </CardHeader>
      <CardContent>
        <Alert v-if="isGraphLimited" class="mb-4">
          <AlertTitle>图谱已聚焦展示</AlertTitle>
          <AlertDescription>当前结果较大，图谱先展示前 {{ graphDepthLimit }} 层、最多 {{ graphNodeLimit }} 个节点；完整分支结果仍在下方列表中。</AlertDescription>
        </Alert>
        <div v-if="tree.nodes.length === 0" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          当前根成员没有可展示的分支节点。
        </div>
        <div v-else class="grid gap-5">
          <FamilyGraphCanvas :tree-id="treeId" :nodes="graphNodes" :edges="graphEdges" />
          <RouterLink
            v-for="node in tree.nodes"
            :key="`${node.path_member_ids.join('-')}-${node.member_id}`"
            class="block rounded-md border bg-card p-4 transition hover:border-primary/50 hover:bg-accent/50"
            :style="{ marginLeft: `${Math.min(node.depth, 8) * 24}px` }"
            :to="{ name: 'member-detail', params: { treeId, memberId: node.member_id } }"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">{{ node.name }}</p>
                <p class="text-xs text-muted-foreground">#{{ node.member_id }} · 深度 {{ node.depth }} · {{ relationshipLabel(node.incoming_parent_role) }}</p>
              </div>
              <Badge variant="outline">{{ node.generation_no ?? "未填写" }} 代</Badge>
            </div>
          </RouterLink>
        </div>
      </CardContent>
    </Card>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchMemberIdRange, type MemberIdRangeResponse } from "@/api/member";
import { fetchBranchTree, type BranchTreeResponse } from "@/api/search";
import FamilyGraphCanvas, { type GraphEdge, type GraphNode } from "@/components/FamilyGraphCanvas.vue";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const rootMemberId = ref(Number(route.query.rootMemberId ?? route.query.memberId ?? 0) || 0);
const maxDepth = ref(Number(route.query.maxDepth ?? 4) || 4);
const tree = ref<BranchTreeResponse | null>(null);
const memberIdRange = ref<MemberIdRangeResponse | null>(null);
const loading = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const graphDepthLimit = 8;
const graphNodeLimit = 200;
const layerGapX = 240;
const layerGapY = 150;

const memberIdPlaceholder = computed(() => {
  if (memberIdRange.value?.min_member_id && memberIdRange.value.max_member_id) {
    return `${memberIdRange.value.min_member_id} - ${memberIdRange.value.max_member_id}`;
  }
  return "请输入成员 ID";
});

const memberIdHint = computed(() => {
  if (!memberIdRange.value || memberIdRange.value.total === 0) {
    return "当前族谱暂无成员编号范围。";
  }
  return `当前族谱共有 ${memberIdRange.value.total} 名成员，成员 ID 范围为 ${memberIdRange.value.min_member_id} - ${memberIdRange.value.max_member_id}。`;
});

const graphNodes = computed<GraphNode[]>(() => {
  if (!tree.value) {
    return [];
  }

  const layers = new Map<number, { id: number; name: string; meta: string }[]>();
  for (const node of tree.value.nodes) {
    if (node.depth > graphDepthLimit) {
      continue;
    }
    const currentCount = [...layers.values()].reduce((total, items) => total + items.length, 0);
    if (currentCount >= graphNodeLimit) {
      break;
    }
    layers.set(node.depth, [
      ...(layers.get(node.depth) ?? []),
      {
        id: node.member_id,
        name: node.name,
        meta: `${node.generation_no ?? "未填写"} 代 · 深度 ${node.depth}`
      }
    ]);
  }

  const maxLayerSize = Math.max(...[...layers.values()].map((items) => items.length), 1);
  const canvasCenter = ((maxLayerSize - 1) * layerGapX) / 2;
  const nodes: GraphNode[] = [];
  for (const [depth, items] of [...layers.entries()].sort(([left], [right]) => left - right)) {
    const layerWidth = (items.length - 1) * layerGapX;
    const startX = canvasCenter - layerWidth / 2;
    items.forEach((item, index) => {
      nodes.push({
        ...item,
        x: startX + index * layerGapX,
        y: 40 + depth * layerGapY
      });
    });
  }

  return nodes;
});

const graphNodeIds = computed(() => new Set(graphNodes.value.map((node) => node.id)));

const graphEdges = computed<GraphEdge[]>(() => {
  if (!tree.value) {
    return [];
  }
  return tree.value.nodes
    .filter((node) => node.parent_member_id !== null && graphNodeIds.value.has(Number(node.parent_member_id)) && graphNodeIds.value.has(node.member_id))
    .map((node) => ({
      from: Number(node.parent_member_id),
      to: node.member_id,
      label: relationshipLabel(node.incoming_parent_role)
    }));
});

const isGraphLimited = computed(() => {
  if (!tree.value) {
    return false;
  }
  return tree.value.nodes.some((node) => node.depth > graphDepthLimit) || tree.value.nodes.length > graphNodeLimit;
});

function relationshipLabel(role: string | null) {
  if (role === "father") {
    return "父系进入";
  }
  if (role === "mother") {
    return "母系进入";
  }
  return "根节点";
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function handleLoadTree() {
  if (!rootMemberId.value) {
    feedbackType.value = "error";
    feedback.value = "请输入有效的根成员 ID。";
    return;
  }

  loading.value = true;
  feedback.value = "";
  try {
    const response = await fetchBranchTree(treeId.value, rootMemberId.value, maxDepth.value);
    tree.value = response.data;
    feedbackType.value = "success";
    feedback.value = `已加载 ${response.data.nodes.length} 个分支节点。`;
  } catch (error) {
    tree.value = null;
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "分支树加载失败，请稍后重试。");
  } finally {
    loading.value = false;
  }
}

async function loadMemberIdRange() {
  try {
    const response = await fetchMemberIdRange(treeId.value);
    memberIdRange.value = response.data;
  } catch {
    memberIdRange.value = null;
  }
}

onMounted(async () => {
  await loadMemberIdRange();
  if (rootMemberId.value > 0) {
    await handleLoadTree();
  }
});
</script>

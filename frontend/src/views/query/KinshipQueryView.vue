<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">查询</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">亲缘路径</h1>
        <p class="mt-2 text-sm text-muted-foreground">输入两名成员，查看最短关系链。</p>
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
        <form class="grid gap-4 md:grid-cols-[180px_180px_160px_180px_auto]" @submit.prevent="handleLoadPath">
          <div class="grid gap-2">
            <Label for="member-a">成员 A ID</Label>
            <Input id="member-a" v-model.number="memberA" min="1" required type="number" :placeholder="memberIdPlaceholder" />
            <p class="text-xs text-muted-foreground">{{ memberIdHint }}</p>
          </div>
          <div class="grid gap-2">
            <Label for="member-b">成员 B ID</Label>
            <Input id="member-b" v-model.number="memberB" min="1" required type="number" :placeholder="memberIdPlaceholder" />
            <p class="text-xs text-muted-foreground">{{ memberIdHint }}</p>
          </div>
          <div class="grid gap-2">
            <Label for="max-depth">最大跳数</Label>
            <Input id="max-depth" v-model.number="maxDepth" max="20" min="1" type="number" />
          </div>
          <label class="flex items-end gap-2 rounded-md border px-3 py-2 text-sm">
            <Checkbox v-model:checked="includeEndedMarriages" />
            <span>包含已结束婚姻</span>
          </label>
          <div class="flex items-end">
            <Button class="w-full" :disabled="loading" type="submit">
              <Spinner v-if="loading" data-icon="inline-start" />
              {{ loading ? "查询中" : "查看路径" }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <Alert v-if="feedback" :variant="feedbackType === 'error' ? 'destructive' : 'default'">
      <AlertTitle>{{ feedbackType === "error" ? "查询失败" : "查询完成" }}</AlertTitle>
      <AlertDescription>{{ feedback }}</AlertDescription>
    </Alert>

    <Card v-if="loading">
      <CardContent class="grid gap-3 p-6">
        <Skeleton class="h-16 w-full" />
        <Skeleton class="h-16 w-11/12" />
        <Skeleton class="h-16 w-10/12" />
      </CardContent>
    </Card>

    <Card v-else-if="data">
      <CardHeader>
        <CardTitle>{{ data.exists ? "最短关系链" : "暂无关系链" }}</CardTitle>
        <CardDescription v-if="data.exists">跳数 {{ data.hop_count }}，共 {{ data.nodes.length }} 个节点。</CardDescription>
        <CardDescription v-else>可以尝试提高最大跳数，或包含已结束婚姻。</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="!data.exists" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          两名成员之间暂无可展示路径。
        </div>
        <div v-else class="grid gap-5">
          <FamilyGraphCanvas :tree-id="treeId" :nodes="graphNodes" :edges="graphEdges" />
          <div v-for="(node, index) in data.nodes" :key="node.member_id" class="grid gap-3">
            <RouterLink
              class="block rounded-md border bg-card p-4 transition hover:border-primary/50 hover:bg-accent/50"
              :to="{ name: 'member-detail', params: { treeId, memberId: node.member_id } }"
            >
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p class="font-medium">{{ node.name }}</p>
                  <p class="text-xs text-muted-foreground">#{{ node.member_id }} · {{ node.generation_no ?? "未填写" }} 代 · {{ node.generation_name ?? "无字辈" }}</p>
                </div>
                <Badge variant="outline">{{ genderLabel(node.gender) }}</Badge>
              </div>
            </RouterLink>
            <div v-if="data.edges[index]" class="ml-6 border-l border-dashed py-2 pl-4 text-sm font-medium text-primary">
              {{ edgeLabel(data.edges[index]) }}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchKinshipPath, type KinshipPathEdge, type KinshipPathResponse } from "@/api/kinship";
import { fetchMemberIdRange, type MemberIdRangeResponse } from "@/api/member";
import FamilyGraphCanvas, { type GraphEdge, type GraphNode } from "@/components/FamilyGraphCanvas.vue";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const memberA = ref(Number(route.query.memberA ?? route.query.memberId ?? 0) || 0);
const memberB = ref(Number(route.query.memberB ?? 0) || 0);
const maxDepth = ref(Number(route.query.maxDepth ?? 12) || 12);
const includeEndedMarriages = ref(route.query.includeEndedMarriages === "true");
const data = ref<KinshipPathResponse | null>(null);
const memberIdRange = ref<MemberIdRangeResponse | null>(null);
const loading = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

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
  if (!data.value?.exists) {
    return [];
  }
  return data.value.nodes.map((node, index) => ({
    id: node.member_id,
    name: node.name,
    meta: `${node.generation_no ?? "未填写"} 代 · ${node.generation_name ?? "无字辈"}`,
    x: index * 240,
    y: 40
  }));
});

const graphEdges = computed<GraphEdge[]>(() => {
  if (!data.value?.exists) {
    return [];
  }
  return data.value.edges.map((edge) => ({
    from: edge.from_member_id,
    to: edge.to_member_id,
    label: edgeLabel(edge)
  }));
});

function genderLabel(gender: string) {
  if (gender === "male") {
    return "男";
  }
  if (gender === "female") {
    return "女";
  }
  return "未知";
}

function edgeLabel(edge: KinshipPathEdge) {
  if (edge.relation_type === "parent") {
    return `${edge.parent_role === "father" ? "父系" : "母系"}向下`;
  }
  if (edge.relation_type === "child") {
    return `${edge.parent_role === "father" ? "父系" : "母系"}向上`;
  }
  return edge.marriage_status === "ended" ? "已结束婚姻" : "婚姻关系";
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function handleLoadPath() {
  if (!memberA.value || !memberB.value) {
    feedbackType.value = "error";
    feedback.value = "请输入两名有效成员的 ID。";
    return;
  }

  loading.value = true;
  feedback.value = "";
  try {
    const response = await fetchKinshipPath(
      treeId.value,
      memberA.value,
      memberB.value,
      maxDepth.value,
      includeEndedMarriages.value
    );
    data.value = response.data;
    feedbackType.value = "success";
    feedback.value = response.data.exists ? "已找到最短亲缘路径。" : "未找到亲缘路径。";
  } catch (error) {
    data.value = null;
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "亲缘路径查询失败，请稍后重试。");
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
  if (memberA.value > 0 && memberB.value > 0) {
    await handleLoadPath();
  }
});
</script>

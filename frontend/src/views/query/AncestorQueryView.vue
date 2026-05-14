<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">查询</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">祖先查询</h1>
        <p class="mt-2 text-sm text-muted-foreground">输入成员编号，按层级查看父系和母系祖先。</p>
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
        <form class="grid gap-4 md:grid-cols-[220px_180px_auto]" @submit.prevent="handleLoadAncestors">
          <div class="grid gap-2">
            <Label for="member-id">成员 ID</Label>
            <Input id="member-id" v-model.number="memberId" min="1" required type="number" :placeholder="memberIdPlaceholder" />
            <p class="text-xs text-muted-foreground">{{ memberIdHint }}</p>
          </div>
          <div class="grid gap-2">
            <Label for="max-depth">最大深度</Label>
            <Input id="max-depth" v-model.number="maxDepth" max="100" min="1" type="number" />
          </div>
          <div class="flex items-end">
            <Button class="w-full" :disabled="loading" type="submit">
              <Spinner v-if="loading" data-icon="inline-start" />
              {{ loading ? "查询中" : "查看祖先" }}
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
        <Skeleton class="h-12 w-full" />
        <Skeleton class="h-12 w-11/12" />
        <Skeleton class="h-12 w-10/12" />
      </CardContent>
    </Card>

    <Card v-else-if="data">
      <CardHeader>
        <CardTitle>{{ data.start_member.name }} 的祖先链</CardTitle>
        <CardDescription>起点成员 #{{ data.start_member.member_id }}，最大深度 {{ data.max_depth }}。</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="data.nodes.length === 0" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          当前成员没有可展示的祖先记录。
        </div>
        <div v-else class="grid gap-3">
          <RouterLink
            v-for="node in data.nodes"
            :key="`${node.path_member_ids.join('-')}-${node.member_id}`"
            class="block rounded-md border bg-card p-4 transition hover:border-primary/50 hover:bg-accent/50"
            :style="{ marginLeft: `${Math.min(node.depth, 8) * 24}px` }"
            :to="{ name: 'member-detail', params: { treeId, memberId: node.member_id } }"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">{{ node.name }}</p>
                <p class="text-xs text-muted-foreground">#{{ node.member_id }} · 深度 {{ node.depth }} · 来自子成员 #{{ node.child_member_id }}</p>
              </div>
              <Badge variant="outline">{{ roleLabel(node.parent_role) }}</Badge>
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

import { fetchAncestors, type AncestorResponse } from "@/api/kinship";
import { fetchMemberIdRange, type MemberIdRangeResponse } from "@/api/member";
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
const memberId = ref(Number(route.query.memberId ?? 0) || 0);
const maxDepth = ref(Number(route.query.maxDepth ?? 30) || 30);
const data = ref<AncestorResponse | null>(null);
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

function roleLabel(role: string) {
  return role === "father" ? "父系祖先" : "母系祖先";
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function handleLoadAncestors() {
  if (!memberId.value) {
    feedbackType.value = "error";
    feedback.value = "请输入有效的成员 ID。";
    return;
  }

  loading.value = true;
  feedback.value = "";
  try {
    const response = await fetchAncestors(treeId.value, memberId.value, maxDepth.value);
    data.value = response.data;
    feedbackType.value = "success";
    feedback.value = `已返回 ${response.data.nodes.length} 个祖先节点。`;
  } catch (error) {
    data.value = null;
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "祖先查询失败，请稍后重试。");
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
  if (memberId.value > 0) {
    await handleLoadAncestors();
  }
});
</script>

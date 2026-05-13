<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">总览</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">族谱统计</h1>
        <p class="mt-2 text-sm text-muted-foreground">选择一棵族谱，查看成员构成、代际寿命和重点成员清单。</p>
      </div>

      <div class="flex flex-col gap-2 sm:flex-row">
        <Select :model-value="selectedTreeValue" :disabled="loadingTrees || trees.length === 0" @update:model-value="handleTreeSelect">
          <SelectTrigger class="w-full sm:w-72">
            <SelectValue placeholder="选择族谱" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem v-for="tree in trees" :key="tree.tree_id" :value="String(tree.tree_id)">
                {{ tree.tree_name }} · {{ roleLabel(tree.access_role) }}
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button :disabled="loadingAny || !selectedTreeId" variant="outline" @click="reloadAnalytics">
          <RefreshCwIcon data-icon="inline-start" />
          {{ loadingAny ? "刷新中" : "刷新" }}
        </Button>
        <Button v-if="selectedTreeId" as-child>
          <RouterLink :to="{ name: 'family-tree-detail', params: { treeId: selectedTreeId } }">
            查看族谱
          </RouterLink>
        </Button>
      </div>
    </div>

    <Alert v-if="feedback" :variant="feedbackType === 'error' ? 'destructive' : 'default'">
      <AlertTitle>{{ feedbackType === "error" ? "加载失败" : "已更新" }}</AlertTitle>
      <AlertDescription>{{ feedback }}</AlertDescription>
    </Alert>

    <Card v-if="loadingTrees">
      <CardContent class="grid gap-3 p-6">
        <Skeleton class="h-5 w-48" />
        <Skeleton class="h-24 w-full" />
      </CardContent>
    </Card>

    <Card v-else-if="trees.length === 0">
      <CardHeader>
        <CardTitle>暂无族谱</CardTitle>
        <CardDescription>当前账号还没有可查看的族谱。</CardDescription>
      </CardHeader>
      <CardFooter>
        <Button as-child>
          <RouterLink :to="{ name: 'family-tree-list' }">前往族谱列表</RouterLink>
        </Button>
      </CardFooter>
    </Card>

    <template v-else>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader class="pb-2">
            <CardDescription>总人数</CardDescription>
            <CardTitle class="text-3xl">{{ formatNumber(dashboard?.summary.total_members) }}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader class="pb-2">
            <CardDescription>男性</CardDescription>
            <CardTitle class="text-3xl">{{ formatNumber(dashboard?.summary.male_count) }}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader class="pb-2">
            <CardDescription>女性</CardDescription>
            <CardTitle class="text-3xl">{{ formatNumber(dashboard?.summary.female_count) }}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader class="pb-2">
            <CardDescription>未知性别</CardDescription>
            <CardTitle class="text-3xl">{{ formatNumber(dashboard?.summary.unknown_count) }}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div class="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(340px,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle>成员构成</CardTitle>
            <CardDescription>按性别汇总当前族谱成员。</CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="dashboardState.loading" class="grid gap-3">
              <Skeleton class="h-48 w-full" />
            </div>
            <Alert v-else-if="dashboardState.error" variant="destructive">
              <AlertTitle>统计加载失败</AlertTitle>
              <AlertDescription>{{ dashboardState.error }}</AlertDescription>
            </Alert>
            <ChartContainer v-else :config="chartConfig" class="h-64">
              <div class="flex h-full flex-col justify-end gap-4">
                <div
                  v-for="item in chartItems"
                  :key="item.key"
                  class="grid gap-2"
                >
                  <div class="flex items-center justify-between gap-3 text-sm">
                    <span class="font-medium">{{ item.label }}</span>
                    <span class="text-muted-foreground">{{ item.value }} 人 · {{ item.ratio }}</span>
                  </div>
                  <div class="h-4 overflow-hidden rounded-full bg-muted">
                    <div class="h-full rounded-full" :class="item.className" :style="{ width: item.width }" />
                  </div>
                </div>
              </div>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>平均寿命最长的一代</CardTitle>
            <CardDescription>展示当前族谱中平均寿命最高的代际。</CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="lifespanState.loading" class="grid gap-3">
              <Skeleton class="h-8 w-40" />
              <Skeleton class="h-16 w-full" />
            </div>
            <Alert v-else-if="lifespanState.error" variant="destructive">
              <AlertTitle>代际统计失败</AlertTitle>
              <AlertDescription>{{ lifespanState.error }}</AlertDescription>
            </Alert>
            <div v-else-if="!maxAverageLifespan?.item" class="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
              当前族谱还没有足够的出生和代际信息。
            </div>
            <div v-else class="grid gap-4 sm:grid-cols-2">
              <div class="rounded-md border p-4">
                <p class="text-sm text-muted-foreground">代际编号</p>
                <p class="mt-2 text-3xl font-semibold">{{ maxAverageLifespan.item.generation_no }}</p>
              </div>
              <div class="rounded-md border p-4">
                <p class="text-sm text-muted-foreground">平均寿命</p>
                <p class="mt-2 text-3xl font-semibold">{{ maxAverageLifespan.item.avg_lifespan_years.toFixed(2) }} 年</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div class="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>超过 50 岁且没有配偶的男性成员</CardTitle>
            <CardDescription>用于快速查看当前族谱中的重点成员。</CardDescription>
          </CardHeader>
          <CardContent>
            <DataState :loading="olderMaleState.loading" :error="olderMaleState.error" empty-title="没有符合条件的成员" :empty="olderThan50UnmarriedMale.length === 0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>成员</TableHead>
                    <TableHead>出生日期</TableHead>
                    <TableHead>年龄</TableHead>
                    <TableHead>代际</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="item in olderThan50UnmarriedMale" :key="item.member_id">
                    <TableCell>
                      <div class="font-medium">{{ item.name }}</div>
                      <div class="text-xs text-muted-foreground">#{{ item.member_id }}</div>
                    </TableCell>
                    <TableCell>{{ item.birth_date }}</TableCell>
                    <TableCell>{{ item.age_years }}</TableCell>
                    <TableCell>{{ item.generation_no ?? "未填写" }} / {{ item.generation_name ?? "未填写" }}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </DataState>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>出生年份早于本代平均出生年份的成员</CardTitle>
            <CardDescription>按代际和出生年份核对成员分布。</CardDescription>
          </CardHeader>
          <CardContent>
            <DataState :loading="birthYearState.loading" :error="birthYearState.error" empty-title="没有符合条件的成员" :empty="beforeGenerationAverageBirthYear.length === 0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>成员</TableHead>
                    <TableHead>代际</TableHead>
                    <TableHead>出生年份</TableHead>
                    <TableHead>本代平均出生年份</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="item in beforeGenerationAverageBirthYear" :key="item.member_id">
                    <TableCell>
                      <div class="font-medium">{{ item.name }}</div>
                      <div class="text-xs text-muted-foreground">#{{ item.member_id }}</div>
                    </TableCell>
                    <TableCell>{{ item.generation_no }} / {{ item.generation_name ?? "未填写" }}</TableCell>
                    <TableCell>{{ item.birth_year }}</TableCell>
                    <TableCell>{{ item.avg_birth_year.toFixed(2) }}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </DataState>
          </CardContent>
        </Card>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import type { Component } from "vue";
import { computed, defineComponent, h, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RefreshCwIcon } from "lucide-vue-next";

import {
  fetchBeforeGenerationAverageBirthYear,
  fetchDashboard,
  fetchMaxAverageLifespan,
  fetchOlderThan50UnmarriedMale,
  type BeforeGenerationAverageBirthYearItem,
  type DashboardResponse,
  type GenerationMaxAverageLifespanResponse,
  type OlderThan50UnmarriedMaleItem
} from "@/api/analytics";
import { fetchFamilyTrees, type FamilyTreeListItem } from "@/api/familyTree";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type LoadState = {
  loading: boolean;
  error: string;
};

const DataState = defineComponent({
  props: {
    loading: { type: Boolean, required: true },
    error: { type: String, required: true },
    empty: { type: Boolean, required: true },
    emptyTitle: { type: String, required: true }
  },
  setup(props, { slots }) {
    return () => {
      if (props.loading) {
        return h("div", { class: "grid gap-3" }, [
          h(Skeleton as Component, { class: "h-10 w-full" }),
          h(Skeleton as Component, { class: "h-10 w-full" }),
          h(Skeleton as Component, { class: "h-10 w-full" })
        ]);
      }
      if (props.error) {
        return h(Alert as Component, { variant: "destructive" }, () => [
          h(AlertTitle as Component, null, () => "加载失败"),
          h(AlertDescription as Component, null, () => props.error)
        ]);
      }
      if (props.empty) {
        return h("div", { class: "rounded-md border border-dashed p-4 text-sm text-muted-foreground" }, props.emptyTitle);
      }
      return slots.default?.();
    };
  }
});

const route = useRoute();
const router = useRouter();

const trees = ref<FamilyTreeListItem[]>([]);
const loadingTrees = ref(false);
const selectedTreeId = ref(0);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

const dashboard = ref<DashboardResponse | null>(null);
const maxAverageLifespan = ref<GenerationMaxAverageLifespanResponse | null>(null);
const olderThan50UnmarriedMale = ref<OlderThan50UnmarriedMaleItem[]>([]);
const beforeGenerationAverageBirthYear = ref<BeforeGenerationAverageBirthYearItem[]>([]);

const dashboardState = ref<LoadState>({ loading: false, error: "" });
const lifespanState = ref<LoadState>({ loading: false, error: "" });
const olderMaleState = ref<LoadState>({ loading: false, error: "" });
const birthYearState = ref<LoadState>({ loading: false, error: "" });

const chartConfig = {
  male: { label: "男性", color: "var(--chart-1)" },
  female: { label: "女性", color: "var(--chart-2)" },
  unknown: { label: "未知", color: "var(--chart-4)" }
} satisfies ChartConfig;

const loadingAny = computed(
  () =>
    dashboardState.value.loading ||
    lifespanState.value.loading ||
    olderMaleState.value.loading ||
    birthYearState.value.loading
);

const selectedTreeValue = computed(() => (selectedTreeId.value ? String(selectedTreeId.value) : undefined));

const chartItems = computed(() => {
  const summary = dashboard.value?.summary;
  const total = summary?.total_members ?? 0;
  const items = [
    { key: "male", label: "男性", value: summary?.male_count ?? 0, className: "bg-[var(--chart-1)]" },
    { key: "female", label: "女性", value: summary?.female_count ?? 0, className: "bg-[var(--chart-2)]" },
    { key: "unknown", label: "未知", value: summary?.unknown_count ?? 0, className: "bg-[var(--chart-4)]" }
  ];

  return items.map((item) => ({
    ...item,
    ratio: total > 0 ? `${((item.value / total) * 100).toFixed(2)}%` : "暂无",
    width: total > 0 ? `${Math.max((item.value / total) * 100, item.value > 0 ? 4 : 0)}%` : "0%"
  }));
});

function roleLabel(role: string) {
  if (role === "creator") {
    return "创建者";
  }
  if (role === "collaborator") {
    return "协作者";
  }
  return "只读";
}

function formatNumber(value: number | undefined) {
  return typeof value === "number" ? value.toLocaleString("zh-CN") : "0";
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function syncTreeQuery(treeId: number) {
  await router.replace({
    query: {
      ...route.query,
      treeId: String(treeId)
    }
  });
}

async function handleTreeSelect(value: string | number | null | undefined) {
  const treeId = Number(value);
  if (!Number.isFinite(treeId) || treeId <= 0) {
    return;
  }
  selectedTreeId.value = treeId;
  await syncTreeQuery(treeId);
  await reloadAnalytics();
}

async function loadTrees() {
  loadingTrees.value = true;
  feedback.value = "";
  try {
    const response = await fetchFamilyTrees(1, 100);
    trees.value = response.data.items;
    const queryTreeId = Number(route.query.treeId);
    selectedTreeId.value =
      Number.isFinite(queryTreeId) && queryTreeId > 0 ? queryTreeId : trees.value[0]?.tree_id ?? 0;
    if (selectedTreeId.value) {
      await reloadAnalytics();
    }
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "族谱列表加载失败，请稍后重试。");
  } finally {
    loadingTrees.value = false;
  }
}

async function loadDashboard(treeId: number) {
  dashboardState.value = { loading: true, error: "" };
  try {
    const response = await fetchDashboard(treeId);
    dashboard.value = response.data;
  } catch (error) {
    dashboardState.value.error = errorMessage(error, "统计信息加载失败，请稍后重试。");
  } finally {
    dashboardState.value.loading = false;
  }
}

async function loadLifespan(treeId: number) {
  lifespanState.value = { loading: true, error: "" };
  try {
    const response = await fetchMaxAverageLifespan(treeId);
    maxAverageLifespan.value = response.data;
  } catch (error) {
    lifespanState.value.error = errorMessage(error, "代际寿命加载失败，请稍后重试。");
  } finally {
    lifespanState.value.loading = false;
  }
}

async function loadOlderMale(treeId: number) {
  olderMaleState.value = { loading: true, error: "" };
  try {
    const response = await fetchOlderThan50UnmarriedMale(treeId);
    olderThan50UnmarriedMale.value = response.data.items;
  } catch (error) {
    olderMaleState.value.error = errorMessage(error, "成员清单加载失败，请稍后重试。");
  } finally {
    olderMaleState.value.loading = false;
  }
}

async function loadBirthYear(treeId: number) {
  birthYearState.value = { loading: true, error: "" };
  try {
    const response = await fetchBeforeGenerationAverageBirthYear(treeId);
    beforeGenerationAverageBirthYear.value = response.data.items;
  } catch (error) {
    birthYearState.value.error = errorMessage(error, "出生年份清单加载失败，请稍后重试。");
  } finally {
    birthYearState.value.loading = false;
  }
}

async function reloadAnalytics() {
  if (!selectedTreeId.value) {
    return;
  }

  feedback.value = "";
  await Promise.all([
    loadDashboard(selectedTreeId.value),
    loadLifespan(selectedTreeId.value),
    loadOlderMale(selectedTreeId.value),
    loadBirthYear(selectedTreeId.value)
  ]);
}

onMounted(loadTrees);
</script>

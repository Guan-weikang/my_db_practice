<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 6</p>
        <h1>Dashboard</h1>
        <p class="muted">按族谱查看汇总统计与课程要求的三类分析结果。</p>
      </div>
      <router-link
        v-if="selectedTreeId"
        class="button-link button-link--ghost"
        :to="{ name: 'family-tree-detail', params: { treeId: selectedTreeId } }"
      >
        查看当前族谱
      </router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <div v-if="loadingTrees" class="muted">正在加载可访问族谱...</div>

    <div v-else-if="trees.length === 0" class="empty-state">
      <strong>当前还没有可展示的族谱</strong>
      <p class="muted">请先创建族谱，或确认当前账号是否具备读取权限。</p>
    </div>

    <template v-else>
      <form class="inline-form" @submit.prevent="reloadAnalytics">
        <label class="field field--wide">
          <span>当前族谱</span>
          <select v-model.number="selectedTreeId" @change="handleTreeChange">
            <option v-for="tree in trees" :key="tree.tree_id" :value="tree.tree_id">
              {{ tree.tree_name }} (#{{ tree.tree_id }}) / {{ roleLabel(tree.access_role) }}
            </option>
          </select>
        </label>
        <button class="button button--ghost" :disabled="loadingAny" type="submit">
          {{ loadingAny ? "刷新中..." : "刷新统计" }}
        </button>
      </form>

      <div class="card-grid">
        <article class="record-card">
          <div class="record-card__meta">
            <h2>汇总统计</h2>
            <span class="role-pill role-pill--muted">Dashboard</span>
          </div>
          <p v-if="dashboardState.loading" class="muted">正在加载汇总统计...</p>
          <p v-else-if="dashboardState.error" class="feedback feedback--error">{{ dashboardState.error }}</p>
          <template v-else-if="dashboard">
            <div class="stats-grid">
              <div class="stat-box">
                <span class="muted">总人数</span>
                <strong>{{ dashboard.summary.total_members }}</strong>
              </div>
              <div class="stat-box">
                <span class="muted">男性</span>
                <strong>{{ dashboard.summary.male_count }}</strong>
              </div>
              <div class="stat-box">
                <span class="muted">女性</span>
                <strong>{{ dashboard.summary.female_count }}</strong>
              </div>
              <div class="stat-box">
                <span class="muted">未知性别</span>
                <strong>{{ dashboard.summary.unknown_count }}</strong>
              </div>
            </div>
            <div class="stats-grid">
              <div class="detail-item">
                <span class="muted">男性比例</span>
                <strong>{{ formatRatio(dashboard.summary.male_ratio) }}</strong>
              </div>
              <div class="detail-item">
                <span class="muted">女性比例</span>
                <strong>{{ formatRatio(dashboard.summary.female_ratio) }}</strong>
              </div>
            </div>
          </template>
        </article>

        <article class="record-card">
          <div class="record-card__meta">
            <h2>平均寿命最长的一代</h2>
            <span class="role-pill role-pill--muted">统计一</span>
          </div>
          <p v-if="lifespanState.loading" class="muted">正在计算代际寿命...</p>
          <p v-else-if="lifespanState.error" class="feedback feedback--error">{{ lifespanState.error }}</p>
          <div v-else-if="!maxAverageLifespan?.item" class="empty-state">
            <strong>暂无可统计代际</strong>
            <p class="muted">当前族谱缺少可用于寿命分析的代际或出生数据。</p>
          </div>
          <div v-else class="detail-grid">
            <div class="detail-item">
              <span class="muted">代际编号</span>
              <strong>{{ maxAverageLifespan.item.generation_no }}</strong>
            </div>
            <div class="detail-item">
              <span class="muted">平均寿命</span>
              <strong>{{ maxAverageLifespan.item.avg_lifespan_years.toFixed(2) }} 年</strong>
            </div>
          </div>
        </article>
      </div>

      <div class="detail-grid dashboard-blocks">
        <article class="detail-item detail-item--wide">
          <div class="section-heading">
            <div>
              <h3>超过 50 岁且没有配偶的男性成员</h3>
              <p class="muted">按出生日期升序展示，已结束婚姻也视为有过配偶。</p>
            </div>
            <span class="role-pill role-pill--muted">统计二</span>
          </div>
          <p v-if="olderMaleState.loading" class="muted">正在筛选成员...</p>
          <p v-else-if="olderMaleState.error" class="feedback feedback--error">{{ olderMaleState.error }}</p>
          <div v-else-if="olderThan50UnmarriedMale.length === 0" class="empty-state">
            <strong>没有命中成员</strong>
            <p class="muted">当前族谱中没有符合“超过 50 岁且无配偶”的男性成员。</p>
          </div>
          <table v-else class="table">
            <thead>
              <tr>
                <th>成员</th>
                <th>出生日期</th>
                <th>年龄</th>
                <th>代际</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in olderThan50UnmarriedMale" :key="item.member_id">
                <td>
                  <strong>{{ item.name }}</strong>
                  <div class="muted">#{{ item.member_id }}</div>
                </td>
                <td>{{ item.birth_date }}</td>
                <td>{{ item.age_years }}</td>
                <td>{{ item.generation_no ?? "未填写" }} / {{ item.generation_name ?? "未填写" }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="detail-item detail-item--wide">
          <div class="section-heading">
            <div>
              <h3>出生年份早于本代平均出生年份的成员</h3>
              <p class="muted">按代际、出生年份、成员编号排序，方便直接核对课程 SQL 结果。</p>
            </div>
            <span class="role-pill role-pill--muted">统计三</span>
          </div>
          <p v-if="birthYearState.loading" class="muted">正在计算出生年份对比...</p>
          <p v-else-if="birthYearState.error" class="feedback feedback--error">{{ birthYearState.error }}</p>
          <div v-else-if="beforeGenerationAverageBirthYear.length === 0" class="empty-state">
            <strong>没有命中成员</strong>
            <p class="muted">当前族谱中没有成员早于本代平均出生年份。</p>
          </div>
          <table v-else class="table">
            <thead>
              <tr>
                <th>成员</th>
                <th>代际</th>
                <th>出生年份</th>
                <th>本代平均出生年份</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in beforeGenerationAverageBirthYear" :key="item.member_id">
                <td>
                  <strong>{{ item.name }}</strong>
                  <div class="muted">#{{ item.member_id }}</div>
                </td>
                <td>{{ item.generation_no }} / {{ item.generation_name ?? "未填写" }}</td>
                <td>{{ item.birth_year }}</td>
                <td>{{ item.avg_birth_year.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  fetchBeforeGenerationAverageBirthYear,
  fetchDashboard,
  fetchMaxAverageLifespan,
  fetchOlderThan50UnmarriedMale,
  type BeforeGenerationAverageBirthYearItem,
  type DashboardResponse,
  type GenerationMaxAverageLifespanResponse,
  type OlderThan50UnmarriedMaleItem
} from "../../api/analytics";
import { fetchFamilyTrees, type FamilyTreeListItem } from "../../api/familyTree";

type LoadState = {
  loading: boolean;
  error: string;
};

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

const loadingAny = computed(
  () =>
    dashboardState.value.loading ||
    lifespanState.value.loading ||
    olderMaleState.value.loading ||
    birthYearState.value.loading
);

function roleLabel(role: string) {
  if (role === "creator") {
    return "创建者";
  }
  if (role === "collaborator") {
    return "协作者";
  }
  return "只读";
}

function formatRatio(value: number | null) {
  if (value === null) {
    return "暂无";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function syncTreeQuery(treeId: number) {
  await router.replace({
    name: "dashboard",
    query: {
      ...route.query,
      treeId: String(treeId)
    }
  });
}

async function loadFamilyTreeOptions() {
  loadingTrees.value = true;
  feedback.value = "";
  try {
    const response = await fetchFamilyTrees();
    trees.value = response.data.items;

    if (trees.value.length === 0) {
      selectedTreeId.value = 0;
      return;
    }

    const queryTreeId = Number(route.query.treeId ?? 0) || 0;
    const matchedTree = trees.value.find((tree) => tree.tree_id === queryTreeId);
    selectedTreeId.value = matchedTree?.tree_id ?? trees.value[0].tree_id;
    await syncTreeQuery(selectedTreeId.value);
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "族谱列表加载失败。");
  } finally {
    loadingTrees.value = false;
  }
}

async function reloadAnalytics() {
  if (!selectedTreeId.value) {
    return;
  }

  feedback.value = "";
  dashboardState.value = { loading: true, error: "" };
  lifespanState.value = { loading: true, error: "" };
  olderMaleState.value = { loading: true, error: "" };
  birthYearState.value = { loading: true, error: "" };

  await Promise.allSettled([
    (async () => {
      try {
        const response = await fetchDashboard(selectedTreeId.value);
        dashboard.value = response.data;
      } catch (error) {
        dashboard.value = null;
        dashboardState.value.error = errorMessage(error, "Dashboard 汇总统计加载失败。");
      } finally {
        dashboardState.value.loading = false;
      }
    })(),
    (async () => {
      try {
        const response = await fetchMaxAverageLifespan(selectedTreeId.value);
        maxAverageLifespan.value = response.data;
      } catch (error) {
        maxAverageLifespan.value = null;
        lifespanState.value.error = errorMessage(error, "平均寿命统计加载失败。");
      } finally {
        lifespanState.value.loading = false;
      }
    })(),
    (async () => {
      try {
        const response = await fetchOlderThan50UnmarriedMale(selectedTreeId.value);
        olderThan50UnmarriedMale.value = response.data.items;
      } catch (error) {
        olderThan50UnmarriedMale.value = [];
        olderMaleState.value.error = errorMessage(error, "无配偶男性统计加载失败。");
      } finally {
        olderMaleState.value.loading = false;
      }
    })(),
    (async () => {
      try {
        const response = await fetchBeforeGenerationAverageBirthYear(selectedTreeId.value);
        beforeGenerationAverageBirthYear.value = response.data.items;
      } catch (error) {
        beforeGenerationAverageBirthYear.value = [];
        birthYearState.value.error = errorMessage(error, "出生年份统计加载失败。");
      } finally {
        birthYearState.value.loading = false;
      }
    })()
  ]);

  const anyError =
    dashboardState.value.error ||
    lifespanState.value.error ||
    olderMaleState.value.error ||
    birthYearState.value.error;

  feedbackType.value = anyError ? "error" : "success";
  feedback.value = anyError ? "部分统计加载失败，请查看各区块错误信息。" : "统计结果已刷新。";
}

async function handleTreeChange() {
  await syncTreeQuery(selectedTreeId.value);
  await reloadAnalytics();
}

onMounted(async () => {
  await loadFamilyTreeOptions();
  if (selectedTreeId.value) {
    await reloadAnalytics();
  }
});
</script>

<style scoped>
.stats-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.stat-box {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f8fafc;
}

.dashboard-blocks {
  grid-template-columns: 1fr;
}
</style>

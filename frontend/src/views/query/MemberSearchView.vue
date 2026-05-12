<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 5</p>
        <h1>成员搜索</h1>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-detail', params: { treeId } }">
        返回族谱详情
      </router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <form class="inline-form" @submit.prevent="handleSearch">
      <label class="field field--wide">
        <span>姓名关键字</span>
        <input v-model.trim="keyword" minlength="2" placeholder="例如：Stage4、Ming、Grand" required />
      </label>
      <label class="field">
        <span>页码</span>
        <input v-model.number="page" min="1" type="number" />
      </label>
      <label class="field">
        <span>每页数量</span>
        <input v-model.number="pageSize" max="50" min="1" type="number" />
      </label>
      <button class="button" :disabled="loading" type="submit">{{ loading ? "查询中..." : "执行搜索" }}</button>
    </form>

    <div v-if="loading" class="muted">正在查询成员...</div>
    <div v-else-if="hasSearched && results.length === 0" class="empty-state">
      <strong>没有匹配成员</strong>
      <p class="muted">可以尝试更长的关键字，或者直接输入完整姓名。</p>
    </div>
    <div v-else-if="results.length > 0" class="stack">
      <div class="section-heading">
        <div>
          <h3>搜索结果</h3>
          <p class="muted">共 {{ total }} 条，当前第 {{ currentPage }} 页。</p>
        </div>
      </div>
      <div class="card-grid">
        <article v-for="item in results" :key="item.member_id" class="record-card">
          <div class="record-card__meta">
            <h2>{{ item.name }}</h2>
            <span class="role-pill role-pill--muted">{{ genderLabel(item.gender) }}</span>
          </div>
          <p class="muted">成员编号：#{{ item.member_id }}</p>
          <p class="muted">代际：{{ item.generation_no ?? "未填写" }} / {{ item.generation_name ?? "未填写" }}</p>
          <p class="muted">父亲：{{ item.father_name ?? "未录入" }}</p>
          <p class="muted">母亲：{{ item.mother_name ?? "未录入" }}</p>
          <p class="muted">生卒：{{ item.birth_date ?? "?" }} / {{ item.death_date ?? (item.is_alive ? "在世" : "?") }}</p>
          <router-link
            class="button-link"
            :to="{ name: 'member-detail', params: { treeId, memberId: item.member_id } }"
          >
            查看成员详情
          </router-link>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { searchMembers, type SearchMemberItem } from "../../api/search";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const keyword = ref(typeof route.query.keyword === "string" ? route.query.keyword : "");
const page = ref(Number(route.query.page ?? 1) || 1);
const pageSize = ref(20);
const currentPage = ref(1);
const total = ref(0);
const results = ref<SearchMemberItem[]>([]);
const loading = ref(false);
const hasSearched = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

function genderLabel(gender: string) {
  if (gender === "male") {
    return "男";
  }
  if (gender === "female") {
    return "女";
  }
  return "未知";
}

async function handleSearch() {
  loading.value = true;
  feedback.value = "";
  try {
    const response = await searchMembers(treeId.value, keyword.value, page.value, pageSize.value);
    results.value = response.data.items;
    total.value = response.data.total;
    currentPage.value = response.data.page;
    hasSearched.value = true;
    feedbackType.value = "success";
    feedback.value = `已返回 ${response.data.items.length} 条结果。`;
  } catch (error) {
    feedbackType.value = "error";
    results.value = [];
    total.value = 0;
    hasSearched.value = true;
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "成员搜索失败。";
    } else {
      feedback.value = "成员搜索失败。";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (keyword.value.trim().length >= 2) {
    await handleSearch();
  }
});
</script>

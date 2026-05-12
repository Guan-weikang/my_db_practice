<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 5</p>
        <h1>祖先查询</h1>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-detail', params: { treeId } }">
        返回族谱详情
      </router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <form class="inline-form" @submit.prevent="handleLoadAncestors">
      <label class="field">
        <span>目标成员 ID</span>
        <input v-model.number="memberId" min="1" required type="number" />
      </label>
      <label class="field">
        <span>最大深度</span>
        <input v-model.number="maxDepth" max="100" min="1" type="number" />
      </label>
      <button class="button" :disabled="loading" type="submit">{{ loading ? "查询中..." : "查看祖先" }}</button>
    </form>

    <div v-if="loading" class="muted">正在加载祖先链...</div>
    <div v-else-if="data" class="stack">
      <div class="detail-item">
        <span class="muted">查询起点</span>
        <strong>{{ data.start_member.name }} (#{{ data.start_member.member_id }})</strong>
        <p class="muted">最大深度：{{ data.max_depth }}</p>
      </div>

      <div v-if="data.nodes.length === 0" class="empty-state">
        <strong>暂无祖先记录</strong>
        <p class="muted">当前成员没有录入父母关系，因此祖先链为空。</p>
      </div>

      <div v-else class="stack">
        <div
          v-for="node in data.nodes"
          :key="`${node.path_member_ids.join('-')}-${node.member_id}`"
          class="tree-node"
          :style="{ '--depth': String(node.depth) }"
        >
          <div class="tree-node__card">
            <strong>{{ node.name }}</strong>
            <div class="muted">#{{ node.member_id }} / 深度 {{ node.depth }} / {{ roleLabel(node.parent_role) }}</div>
            <div class="muted">来自子成员 #{{ node.child_member_id }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchAncestors, type AncestorResponse } from "../../api/kinship";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const memberId = ref(Number(route.query.memberId ?? 0) || 0);
const maxDepth = ref(Number(route.query.maxDepth ?? 30) || 30);
const data = ref<AncestorResponse | null>(null);
const loading = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

function roleLabel(role: string) {
  return role === "father" ? "父系祖先" : "母系祖先";
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
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "祖先查询失败。";
    } else {
      feedback.value = "祖先查询失败。";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (memberId.value > 0) {
    await handleLoadAncestors();
  }
});
</script>

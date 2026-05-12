<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 5</p>
        <h1>亲缘路径查询</h1>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-detail', params: { treeId } }">
        返回族谱详情
      </router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <form class="inline-form" @submit.prevent="handleLoadPath">
      <label class="field">
        <span>成员 A ID</span>
        <input v-model.number="memberA" min="1" required type="number" />
      </label>
      <label class="field">
        <span>成员 B ID</span>
        <input v-model.number="memberB" min="1" required type="number" />
      </label>
      <label class="field">
        <span>最大跳数</span>
        <input v-model.number="maxDepth" max="20" min="1" type="number" />
      </label>
      <label class="field">
        <span>纳入 ended 婚姻</span>
        <select v-model="includeEndedMarriages">
          <option :value="false">否</option>
          <option :value="true">是</option>
        </select>
      </label>
      <button class="button" :disabled="loading" type="submit">{{ loading ? "查询中..." : "查看最短路径" }}</button>
    </form>

    <div v-if="loading" class="muted">正在计算亲缘路径...</div>
    <div v-else-if="data" class="stack">
      <div v-if="!data.exists" class="empty-state">
        <strong>两名成员之间暂无路径</strong>
        <p class="muted">可以尝试提高最大跳数，或开启 ended 婚姻参与路径计算。</p>
      </div>

      <template v-else>
        <div class="detail-item">
          <span class="muted">最短链路</span>
          <strong>跳数：{{ data.hop_count }}</strong>
          <p class="muted">节点数：{{ data.nodes.length }} / 边数：{{ data.edges.length }}</p>
        </div>

        <div class="stack">
          <div v-for="(node, index) in data.nodes" :key="node.member_id" class="path-node">
            <div class="record-card">
              <div class="record-card__meta">
                <h2>{{ node.name }}</h2>
                <span class="role-pill role-pill--muted">#{{ node.member_id }}</span>
              </div>
              <p class="muted">代际：{{ node.generation_no ?? "未填写" }} / {{ node.generation_name ?? "未填写" }}</p>
            </div>
            <div v-if="data.edges[index]" class="path-edge">
              {{ edgeLabel(data.edges[index]) }}
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchKinshipPath, type KinshipPathEdge, type KinshipPathResponse } from "../../api/kinship";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const memberA = ref(Number(route.query.memberA ?? route.query.memberId ?? 0) || 0);
const memberB = ref(Number(route.query.memberB ?? 0) || 0);
const maxDepth = ref(Number(route.query.maxDepth ?? 12) || 12);
const includeEndedMarriages = ref(route.query.includeEndedMarriages === "true");
const data = ref<KinshipPathResponse | null>(null);
const loading = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

function edgeLabel(edge: KinshipPathEdge) {
  if (edge.relation_type === "parent") {
    return `${edge.parent_role === "father" ? "父系" : "母系"}向下`;
  }
  if (edge.relation_type === "child") {
    return `${edge.parent_role === "father" ? "父系" : "母系"}向上`;
  }
  return `婚姻关系 (${edge.marriage_status ?? "unknown"})`;
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
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "亲缘路径查询失败。";
    } else {
      feedback.value = "亲缘路径查询失败。";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (memberA.value > 0 && memberB.value > 0) {
    await handleLoadPath();
  }
});
</script>

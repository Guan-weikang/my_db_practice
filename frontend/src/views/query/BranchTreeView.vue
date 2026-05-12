<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 5</p>
        <h1>分支树预览</h1>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-detail', params: { treeId } }">
        返回族谱详情
      </router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <form class="inline-form" @submit.prevent="handleLoadTree">
      <label class="field">
        <span>根成员 ID</span>
        <input v-model.number="rootMemberId" min="1" required type="number" />
      </label>
      <label class="field">
        <span>最大深度</span>
        <input v-model.number="maxDepth" max="10" min="1" type="number" />
      </label>
      <button class="button" :disabled="loading" type="submit">{{ loading ? "加载中..." : "查看分支树" }}</button>
    </form>

    <div v-if="loading" class="muted">正在加载后代分支...</div>
    <div v-else-if="tree" class="stack">
      <div class="detail-item">
        <span class="muted">根成员</span>
        <strong>{{ tree.root_member.name }} (#{{ tree.root_member.member_id }})</strong>
        <p class="muted">最大深度：{{ tree.max_depth }}</p>
      </div>

      <div v-if="tree.nodes.length === 0" class="empty-state">
        <strong>未返回节点</strong>
        <p class="muted">当前根成员没有可展示的分支节点。</p>
      </div>

      <div v-else class="stack">
        <div
          v-for="node in tree.nodes"
          :key="`${node.path_member_ids.join('-')}-${node.member_id}`"
          class="tree-node"
          :style="{ '--depth': String(node.depth) }"
        >
          <div class="tree-node__card">
            <strong>{{ node.name }}</strong>
            <div class="muted">
              #{{ node.member_id }} / 深度 {{ node.depth }} / {{ relationshipLabel(node.incoming_parent_role) }}
            </div>
            <div class="muted">
              代际：{{ node.generation_no ?? "未填写" }} / {{ node.generation_name ?? "未填写" }}
            </div>
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

import { fetchBranchTree, type BranchTreeResponse } from "../../api/search";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const rootMemberId = ref(Number(route.query.rootMemberId ?? route.query.memberId ?? 0) || 0);
const maxDepth = ref(Number(route.query.maxDepth ?? 4) || 4);
const tree = ref<BranchTreeResponse | null>(null);
const loading = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

function relationshipLabel(role: string | null) {
  if (role === "father") {
    return "父系进入";
  }
  if (role === "mother") {
    return "母系进入";
  }
  return "根节点";
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
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "分支树加载失败。";
    } else {
      feedback.value = "分支树加载失败。";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (rootMemberId.value > 0) {
    await handleLoadTree();
  }
});
</script>

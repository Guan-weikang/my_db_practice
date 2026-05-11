<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 3</p>
        <h1>族谱列表</h1>
        <p class="muted">当前所有已登录用户都可以查看全部族谱，角色决定是否可编辑与管理协作者。</p>
      </div>
      <button class="button button--ghost" type="button" @click="refreshList">刷新列表</button>
    </div>

    <form class="inline-form" @submit.prevent="handleCreate">
      <label class="field">
        <span>族谱名称</span>
        <input v-model.trim="createForm.tree_name" required />
      </label>
      <label class="field">
        <span>姓氏</span>
        <input v-model.trim="createForm.surname" required />
      </label>
      <label class="field">
        <span>编修日期</span>
        <input v-model="createForm.compiled_at" type="date" />
      </label>
      <label class="field field--wide">
        <span>说明</span>
        <input v-model.trim="createForm.description" />
      </label>
      <button class="button" :disabled="submittingCreate" type="submit">
        {{ submittingCreate ? "创建中..." : "新建族谱" }}
      </button>
    </form>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <p v-if="familyTreeStore.loadingList" class="muted">正在加载族谱列表...</p>

    <div v-else-if="familyTreeStore.list.length === 0" class="empty-state">
      <strong>还没有族谱数据</strong>
      <p class="muted">先创建一个空族谱，后续可用于协作者管理和删除策略验证。</p>
    </div>

    <div v-else class="card-grid">
      <article v-for="tree in familyTreeStore.list" :key="tree.tree_id" class="record-card">
        <div class="record-card__meta">
          <span class="role-pill">{{ roleLabel(tree.access_role) }}</span>
          <span class="muted">#{{ tree.tree_id }}</span>
        </div>
        <h2>{{ tree.tree_name }}</h2>
        <p class="muted">姓氏：{{ tree.surname }}</p>
        <p class="muted">编修日期：{{ tree.compiled_at ?? "未填写" }}</p>
        <p>{{ tree.description || "暂无说明" }}</p>
        <router-link class="button-link" :to="{ name: 'family-tree-detail', params: { treeId: tree.tree_id } }">
          查看详情
        </router-link>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { onMounted, reactive, ref } from "vue";

import { useFamilyTreeStore } from "../../stores/familyTree";

const familyTreeStore = useFamilyTreeStore();
const submittingCreate = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const createForm = reactive({
  tree_name: "",
  surname: "",
  compiled_at: "",
  description: ""
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

async function refreshList() {
  feedback.value = "";
  await familyTreeStore.loadFamilyTrees();
}

async function handleCreate() {
  submittingCreate.value = true;
  feedback.value = "";

  try {
    await familyTreeStore.createFamilyTree({
      tree_name: createForm.tree_name,
      surname: createForm.surname,
      compiled_at: createForm.compiled_at || null,
      description: createForm.description || null
    });
    createForm.tree_name = "";
    createForm.surname = "";
    createForm.compiled_at = "";
    createForm.description = "";
    feedbackType.value = "success";
    feedback.value = "族谱创建成功。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "族谱创建失败。";
    } else {
      feedback.value = "族谱创建失败。";
    }
  } finally {
    submittingCreate.value = false;
  }
}

onMounted(async () => {
  await familyTreeStore.loadFamilyTrees();
});
</script>

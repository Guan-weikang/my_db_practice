<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Family Tree</p>
        <h1>族谱详情</h1>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-list' }">返回列表</router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <p v-if="familyTreeStore.loadingDetail" class="muted">正在加载族谱详情...</p>

    <div v-else-if="!familyTreeStore.currentTree" class="empty-state">
      <strong>未找到族谱详情</strong>
      <p class="muted">请从列表页重新进入，或确认当前族谱是否已被删除。</p>
    </div>

    <template v-else>
      <div class="detail-hero">
        <div>
          <h2>{{ familyTreeStore.currentTree.tree_name }}</h2>
          <p class="muted">族谱编号：#{{ familyTreeStore.currentTree.tree_id }}</p>
        </div>
        <div class="detail-hero__actions">
          <span class="role-pill">{{ roleLabel(familyTreeStore.currentTree.access_role) }}</span>
          <router-link
            v-if="canManageCollaborators(familyTreeStore.currentTree.access_role)"
            class="button-link"
            :to="{ name: 'collaborators', params: { treeId } }"
          >
            协作者管理
          </router-link>
        </div>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <span class="muted">姓氏</span>
          <strong>{{ familyTreeStore.currentTree.surname }}</strong>
        </div>
        <div class="detail-item">
          <span class="muted">编修日期</span>
          <strong>{{ familyTreeStore.currentTree.compiled_at ?? "未填写" }}</strong>
        </div>
        <div class="detail-item detail-item--wide">
          <span class="muted">说明</span>
          <p>{{ familyTreeStore.currentTree.description || "暂无说明" }}</p>
        </div>
      </div>

      <form v-if="canEdit(familyTreeStore.currentTree.access_role)" class="stack" @submit.prevent="handleUpdate">
        <h3>编辑族谱</h3>
        <div class="inline-form">
          <label class="field">
            <span>族谱名称</span>
            <input v-model.trim="editForm.tree_name" required />
          </label>
          <label class="field">
            <span>姓氏</span>
            <input v-model.trim="editForm.surname" required />
          </label>
          <label class="field">
            <span>编修日期</span>
            <input v-model="editForm.compiled_at" type="date" />
          </label>
          <label class="field field--wide">
            <span>说明</span>
            <input v-model.trim="editForm.description" />
          </label>
        </div>
        <div class="detail-actions">
          <button class="button" :disabled="submittingUpdate" type="submit">
            {{ submittingUpdate ? "保存中..." : "保存修改" }}
          </button>
          <button
            v-if="familyTreeStore.currentTree.access_role === 'creator'"
            class="button button--danger"
            :disabled="deletingTree"
            type="button"
            @click="handleDelete"
          >
            {{ deletingTree ? "删除中..." : "删除空族谱" }}
          </button>
        </div>
      </form>

      <div v-else class="empty-state">
        <strong>当前为只读视角</strong>
        <p class="muted">默认所有族谱可读，但只有创建者和协作者可以编辑。</p>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import client from "../../api/client";
import { useFamilyTreePermission } from "../../composables/useFamilyTreePermission";
import { useFamilyTreeStore } from "../../stores/familyTree";

const route = useRoute();
const router = useRouter();
const familyTreeStore = useFamilyTreeStore();
const { canEdit, canManageCollaborators } = useFamilyTreePermission();
const submittingUpdate = ref(false);
const deletingTree = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const editForm = reactive({
  tree_name: "",
  surname: "",
  compiled_at: "",
  description: ""
});

const treeId = computed(() => Number(route.params.treeId));

function roleLabel(role: string) {
  if (role === "creator") {
    return "创建者";
  }
  if (role === "collaborator") {
    return "协作者";
  }
  return "只读";
}

function syncForm() {
  const tree = familyTreeStore.currentTree;
  if (!tree) {
    return;
  }
  editForm.tree_name = tree.tree_name;
  editForm.surname = tree.surname;
  editForm.compiled_at = tree.compiled_at ?? "";
  editForm.description = tree.description ?? "";
}

async function loadDetail() {
  feedback.value = "";
  await familyTreeStore.loadFamilyTreeDetail(treeId.value);
  syncForm();
}

async function handleUpdate() {
  submittingUpdate.value = true;
  feedback.value = "";
  try {
    await familyTreeStore.updateFamilyTree(treeId.value, {
      tree_name: editForm.tree_name,
      surname: editForm.surname,
      compiled_at: editForm.compiled_at || null,
      description: editForm.description || null
    });
    syncForm();
    feedbackType.value = "success";
    feedback.value = "族谱修改已保存。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "保存失败。";
    } else {
      feedback.value = "保存失败。";
    }
  } finally {
    submittingUpdate.value = false;
  }
}

async function handleDelete() {
  deletingTree.value = true;
  feedback.value = "";
  try {
    await client.delete(`/family-trees/${treeId.value}`);
    await router.push({ name: "family-tree-list" });
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "删除失败。";
    } else {
      feedback.value = "删除失败。";
    }
  } finally {
    deletingTree.value = false;
  }
}

watch(treeId, async () => {
  await loadDetail();
});

onMounted(async () => {
  await loadDetail();
});
</script>

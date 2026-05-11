<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Collaboration</p>
        <h1>协作者管理</h1>
        <p class="muted">只有创建者可进入此页面。协作者与普通读者应在后端被拒绝。</p>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-detail', params: { treeId } }">
        返回族谱详情
      </router-link>
    </div>

    <form class="inline-form" @submit.prevent="handleInvite">
      <label class="field">
        <span>用户 ID</span>
        <input v-model.number="inviteForm.user_id" min="1" required type="number" />
      </label>
      <label class="field">
        <span>角色</span>
        <select v-model="inviteForm.access_role">
          <option value="collaborator">协作者</option>
          <option value="reader">读者</option>
        </select>
      </label>
      <button class="button" :disabled="submittingInvite" type="submit">
        {{ submittingInvite ? "邀请中..." : "添加协作者" }}
      </button>
    </form>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <p v-if="familyTreeStore.loadingCollaborators" class="muted">正在加载协作者列表...</p>

    <div v-else-if="familyTreeStore.collaborators.length === 0" class="empty-state">
      <strong>当前没有显式协作者</strong>
      <p class="muted">默认可读策略下，未授权用户仍可查看族谱详情，但不会出现在此列表中。</p>
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>用户</th>
          <th>角色</th>
          <th>状态</th>
          <th>邀请时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in familyTreeStore.collaborators" :key="item.user_id">
          <td>
            <strong>{{ item.display_name || item.username }}</strong>
            <div class="muted">@{{ item.username }} / #{{ item.user_id }}</div>
          </td>
          <td>
            <select :value="item.access_role" @change="handleRoleChange(item.user_id, $event)">
              <option value="collaborator">协作者</option>
              <option value="reader">读者</option>
            </select>
          </td>
          <td>
            <span class="role-pill" :class="item.status === 'revoked' ? 'role-pill--muted' : ''">{{ item.status }}</span>
          </td>
          <td>{{ formatTime(item.invited_at) }}</td>
          <td>
            <button class="button button--ghost" type="button" @click="handleRevoke(item.user_id)">撤销权限</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import { useFamilyTreeStore } from "../../stores/familyTree";

const route = useRoute();
const familyTreeStore = useFamilyTreeStore();
const treeId = Number(route.params.treeId);
const submittingInvite = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const inviteForm = reactive<{
  user_id: number | null;
  access_role: "collaborator" | "reader";
}>({
  user_id: null,
  access_role: "reader"
});

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN");
}

async function loadCollaborators() {
  feedback.value = "";
  await familyTreeStore.loadCollaborators(treeId);
}

async function handleInvite() {
  if (!inviteForm.user_id) {
    feedbackType.value = "error";
    feedback.value = "请输入有效的用户 ID。";
    return;
  }

  submittingInvite.value = true;
  feedback.value = "";
  try {
    await familyTreeStore.inviteCollaborator(treeId, {
      user_id: inviteForm.user_id,
      access_role: inviteForm.access_role
    });
    inviteForm.user_id = null;
    inviteForm.access_role = "reader";
    feedbackType.value = "success";
    feedback.value = "协作者已添加。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "添加协作者失败。";
    } else {
      feedback.value = "添加协作者失败。";
    }
  } finally {
    submittingInvite.value = false;
  }
}

async function handleRoleChange(userId: number, event: Event) {
  const value = (event.target as HTMLSelectElement).value as "collaborator" | "reader";
  feedback.value = "";
  try {
    await familyTreeStore.updateCollaborator(treeId, userId, { access_role: value });
    feedbackType.value = "success";
    feedback.value = "协作者角色已更新。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "角色更新失败。";
    } else {
      feedback.value = "角色更新失败。";
    }
  }
}

async function handleRevoke(userId: number) {
  feedback.value = "";
  try {
    await familyTreeStore.revokeCollaborator(treeId, userId);
    feedbackType.value = "success";
    feedback.value = "协作者权限已撤销。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "撤销失败。";
    } else {
      feedback.value = "撤销失败。";
    }
  }
}

onMounted(async () => {
  await loadCollaborators();
});
</script>

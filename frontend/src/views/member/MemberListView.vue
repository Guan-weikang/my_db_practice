<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 4</p>
        <h1>成员列表</h1>
        <p class="muted">成员列表默认对所有已登录用户可读；只有创建者和协作者可以新增成员。</p>
      </div>
      <div class="detail-hero__actions">
        <router-link class="button-link button-link--ghost" :to="{ name: 'family-tree-detail', params: { treeId } }">
          返回族谱
        </router-link>
        <button class="button button--ghost" type="button" @click="refreshList">刷新列表</button>
      </div>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <div v-if="familyTreeStore.currentTree" class="detail-item">
      <span class="muted">当前访问角色</span>
      <div class="detail-hero__actions">
        <strong>{{ familyTreeStore.currentTree.tree_name }}</strong>
        <span class="role-pill">{{ roleLabel(familyTreeStore.currentTree.access_role) }}</span>
      </div>
    </div>

    <form v-if="canCreate" class="inline-form" @submit.prevent="handleCreate">
      <label class="field">
        <span>姓名</span>
        <input v-model.trim="createForm.name" required />
      </label>
      <label class="field">
        <span>性别</span>
        <select v-model="createForm.gender">
          <option value="male">男</option>
          <option value="female">女</option>
          <option value="unknown">未知</option>
        </select>
      </label>
      <label class="field">
        <span>出生日期</span>
        <input v-model="createForm.birth_date" type="date" />
      </label>
      <label class="field">
        <span>去世日期</span>
        <input v-model="createForm.death_date" :disabled="createForm.is_alive" type="date" />
      </label>
      <label class="field">
        <span>在世</span>
        <select v-model="aliveSelect">
          <option value="true">是</option>
          <option value="false">否</option>
        </select>
      </label>
      <label class="field">
        <span>代际编号</span>
        <input v-model.number="createForm.generation_no" min="1" type="number" />
      </label>
      <label class="field">
        <span>字辈/派语</span>
        <input v-model.trim="createForm.generation_name" />
      </label>
      <label class="field field--wide">
        <span>生平简介</span>
        <textarea v-model.trim="createForm.biography" rows="3" />
      </label>
      <button class="button" :disabled="submittingCreate" type="submit">
        {{ submittingCreate ? "创建中..." : "新增成员" }}
      </button>
    </form>

    <div v-else class="empty-state">
      <strong>当前为只读视角</strong>
      <p class="muted">你仍可查看成员列表与详情，但不能新增成员。</p>
    </div>

    <p v-if="memberStore.loadingList" class="muted">正在加载成员列表...</p>

    <div v-else-if="memberStore.list.length === 0" class="empty-state">
      <strong>当前族谱还没有成员</strong>
      <p class="muted">先新增一位成员，后续才能继续维护父母子女和婚姻关系。</p>
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>姓名</th>
          <th>性别</th>
          <th>代际</th>
          <th>出生</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in memberStore.list" :key="member.member_id">
          <td>#{{ member.member_id }}</td>
          <td>
            <strong>{{ member.name }}</strong>
            <div class="muted">{{ member.generation_name || "无字辈" }}</div>
          </td>
          <td>{{ genderLabel(member.gender) }}</td>
          <td>{{ member.generation_no ?? "未填写" }}</td>
          <td>{{ member.birth_date ?? "未知" }}</td>
          <td>{{ member.is_alive ? "在世" : "已故" }}</td>
          <td>
            <router-link class="button-link" :to="{ name: 'member-detail', params: { treeId, memberId: member.member_id } }">
              查看详情
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useFamilyTreePermission } from "../../composables/useFamilyTreePermission";
import { useFamilyTreeStore } from "../../stores/familyTree";
import { useMemberStore } from "../../stores/member";

const route = useRoute();
const familyTreeStore = useFamilyTreeStore();
const memberStore = useMemberStore();
const { canEdit } = useFamilyTreePermission();
const treeId = computed(() => Number(route.params.treeId));
const submittingCreate = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const createForm = reactive({
  name: "",
  gender: "unknown" as "male" | "female" | "unknown",
  birth_date: "",
  death_date: "",
  is_alive: true,
  generation_no: null as number | null,
  generation_name: "",
  biography: ""
});

const aliveSelect = computed({
  get: () => (createForm.is_alive ? "true" : "false"),
  set: (value: string) => {
    createForm.is_alive = value === "true";
    if (createForm.is_alive) {
      createForm.death_date = "";
    }
  }
});

const canCreate = computed(() => canEdit(familyTreeStore.currentTree?.access_role ?? "reader"));

function roleLabel(role: string) {
  if (role === "creator") {
    return "创建者";
  }
  if (role === "collaborator") {
    return "协作者";
  }
  return "只读";
}

function genderLabel(gender: string) {
  if (gender === "male") {
    return "男";
  }
  if (gender === "female") {
    return "女";
  }
  return "未知";
}

async function loadPage() {
  feedback.value = "";
  await familyTreeStore.loadFamilyTreeDetail(treeId.value);
  await memberStore.loadMembers(treeId.value);
}

async function refreshList() {
  await loadPage();
}

async function handleCreate() {
  submittingCreate.value = true;
  feedback.value = "";
  try {
    const createdMember = await memberStore.createMember(treeId.value, {
      name: createForm.name,
      gender: createForm.gender,
      birth_date: createForm.birth_date || null,
      death_date: createForm.death_date || null,
      is_alive: createForm.is_alive,
      generation_no: createForm.generation_no,
      generation_name: createForm.generation_name || null,
      biography: createForm.biography || null
    });
    createForm.name = "";
    createForm.gender = "unknown";
    createForm.birth_date = "";
    createForm.death_date = "";
    createForm.is_alive = true;
    createForm.generation_no = null;
    createForm.generation_name = "";
    createForm.biography = "";
    feedbackType.value = "success";
    feedback.value = `成员 #${createdMember.member_id} 创建成功。`;
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "成员创建失败。";
    } else {
      feedback.value = "成员创建失败。";
    }
  } finally {
    submittingCreate.value = false;
  }
}

watch(treeId, async () => {
  await loadPage();
});

onMounted(async () => {
  await loadPage();
});
</script>

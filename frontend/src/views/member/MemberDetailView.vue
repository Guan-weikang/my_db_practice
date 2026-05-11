<template>
  <section class="panel stack">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Stage 4</p>
        <h1>成员详情</h1>
      </div>
      <router-link class="button-link button-link--ghost" :to="{ name: 'member-list', params: { treeId } }">
        返回成员列表
      </router-link>
    </div>

    <p v-if="feedback" class="feedback" :class="feedbackType === 'error' ? 'feedback--error' : 'feedback--success'">
      {{ feedback }}
    </p>

    <p v-if="memberStore.loadingDetail" class="muted">正在加载成员详情...</p>

    <div v-else-if="!memberStore.currentMember" class="empty-state">
      <strong>未找到成员详情</strong>
      <p class="muted">请从成员列表页重新进入，或确认该成员是否已被删除。</p>
    </div>

    <template v-else>
      <div class="detail-hero">
        <div>
          <h2>{{ memberStore.currentMember.name }}</h2>
          <p class="muted">成员编号：#{{ memberStore.currentMember.member_id }}</p>
        </div>
        <div class="detail-hero__actions">
          <span class="role-pill">{{ roleLabel(familyTreeStore.currentTree?.access_role ?? 'reader') }}</span>
          <span class="role-pill role-pill--muted">{{ genderLabel(memberStore.currentMember.gender) }}</span>
        </div>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <span class="muted">出生日期</span>
          <strong>{{ memberStore.currentMember.birth_date ?? "未填写" }}</strong>
        </div>
        <div class="detail-item">
          <span class="muted">去世日期</span>
          <strong>{{ memberStore.currentMember.death_date ?? "未填写" }}</strong>
        </div>
        <div class="detail-item">
          <span class="muted">代际编号</span>
          <strong>{{ memberStore.currentMember.generation_no ?? "未填写" }}</strong>
        </div>
        <div class="detail-item">
          <span class="muted">字辈/派语</span>
          <strong>{{ memberStore.currentMember.generation_name ?? "未填写" }}</strong>
        </div>
        <div class="detail-item">
          <span class="muted">状态</span>
          <strong>{{ memberStore.currentMember.is_alive ? "在世" : "已故" }}</strong>
        </div>
        <div class="detail-item detail-item--wide">
          <span class="muted">生平简介</span>
          <p>{{ memberStore.currentMember.biography || "暂无简介" }}</p>
        </div>
      </div>

      <form v-if="canModify" class="stack" @submit.prevent="handleUpdateMember">
        <h3>编辑成员</h3>
        <div class="inline-form">
          <label class="field">
            <span>姓名</span>
            <input v-model.trim="editForm.name" required />
          </label>
          <label class="field">
            <span>性别</span>
            <select v-model="editForm.gender">
              <option value="male">男</option>
              <option value="female">女</option>
              <option value="unknown">未知</option>
            </select>
          </label>
          <label class="field">
            <span>出生日期</span>
            <input v-model="editForm.birth_date" type="date" />
          </label>
          <label class="field">
            <span>去世日期</span>
            <input v-model="editForm.death_date" :disabled="editForm.is_alive" type="date" />
          </label>
          <label class="field">
            <span>在世</span>
            <select v-model="editAliveSelect">
              <option value="true">是</option>
              <option value="false">否</option>
            </select>
          </label>
          <label class="field">
            <span>代际编号</span>
            <input v-model.number="editForm.generation_no" min="1" type="number" />
          </label>
          <label class="field">
            <span>字辈/派语</span>
            <input v-model.trim="editForm.generation_name" />
          </label>
          <label class="field field--wide">
            <span>生平简介</span>
            <textarea v-model.trim="editForm.biography" rows="3" />
          </label>
        </div>
        <div class="detail-actions">
          <button class="button" :disabled="submittingMemberUpdate" type="submit">
            {{ submittingMemberUpdate ? "保存中..." : "保存成员修改" }}
          </button>
          <button class="button button--danger" :disabled="deletingMember" type="button" @click="handleDeleteMember">
            {{ deletingMember ? "删除中..." : "删除成员" }}
          </button>
        </div>
      </form>

      <div class="stack">
        <div class="section-heading">
          <div>
            <h3>父母关系</h3>
            <p class="muted">同一成员最多一个父亲、一个母亲。</p>
          </div>
        </div>

        <form v-if="canModify" class="inline-form" @submit.prevent="handleCreateParentChild">
          <label class="field">
            <span>父/母成员 ID</span>
            <input v-model.number="parentChildForm.parent_member_id" min="1" required type="number" />
          </label>
          <label class="field">
            <span>关系类型</span>
            <select v-model="parentChildForm.parent_role">
              <option value="father">父亲</option>
              <option value="mother">母亲</option>
            </select>
          </label>
          <button class="button" :disabled="submittingParentChild" type="submit">
            {{ submittingParentChild ? "提交中..." : "添加父母关系" }}
          </button>
        </form>

        <div v-if="memberStore.loadingRelations" class="muted">正在加载关系数据...</div>
        <div v-else-if="memberStore.parents.length === 0" class="empty-state">
          <strong>暂无父母关系</strong>
          <p class="muted">可以通过成员 ID 补录父亲或母亲。</p>
        </div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>关系</th>
              <th>成员</th>
              <th>代际</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in memberStore.parents" :key="`${item.parent_role}-${item.parent_member_id}`">
              <td>{{ item.parent_role === "father" ? "父亲" : "母亲" }}</td>
              <td>
                <strong>{{ item.name }}</strong>
                <div class="muted">#{{ item.parent_member_id }} / {{ genderLabel(item.gender) }}</div>
              </td>
              <td>{{ item.generation_no ?? "未填写" }}</td>
              <td>
                <button
                  v-if="canModify"
                  class="button button--ghost"
                  type="button"
                  @click="handleDeleteParentChild(item.parent_member_id, item.parent_role)"
                >
                  删除关系
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="stack">
        <div class="section-heading">
          <div>
            <h3>子女关系</h3>
            <p class="muted">这里展示当前成员作为父或母时关联到的子女。</p>
          </div>
        </div>
        <div v-if="memberStore.loadingRelations" class="muted">正在加载关系数据...</div>
        <div v-else-if="memberStore.children.length === 0" class="empty-state">
          <strong>暂无子女关系</strong>
          <p class="muted">当当前成员作为父亲或母亲被关联时，会自动显示在这里。</p>
        </div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>角色</th>
              <th>子女</th>
              <th>代际</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in memberStore.children" :key="`${item.parent_role}-${item.child_member_id}`">
              <td>{{ item.parent_role === "father" ? "父系" : "母系" }}</td>
              <td>
                <strong>{{ item.name }}</strong>
                <div class="muted">#{{ item.child_member_id }} / {{ genderLabel(item.gender) }}</div>
              </td>
              <td>{{ item.generation_no ?? "未填写" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="stack">
        <div class="section-heading">
          <div>
            <h3>婚姻关系</h3>
            <p class="muted">婚姻状态支持 `active` 与 `ended`。</p>
          </div>
        </div>

        <form v-if="canModify" class="inline-form" @submit.prevent="handleCreateMarriage">
          <label class="field">
            <span>配偶成员 ID</span>
            <input v-model.number="marriageForm.spouse_member_id" min="1" required type="number" />
          </label>
          <label class="field">
            <span>结婚日期</span>
            <input v-model="marriageForm.married_at" type="date" />
          </label>
          <label class="field">
            <span>状态</span>
            <select v-model="marriageForm.status">
              <option value="active">active</option>
              <option value="ended">ended</option>
            </select>
          </label>
          <label class="field">
            <span>结束日期</span>
            <input v-model="marriageForm.ended_at" :disabled="marriageForm.status === 'active'" type="date" />
          </label>
          <button class="button" :disabled="submittingMarriage" type="submit">
            {{ submittingMarriage ? "提交中..." : "新增婚姻关系" }}
          </button>
        </form>

        <div v-if="memberStore.loadingRelations" class="muted">正在加载关系数据...</div>
        <div v-else-if="memberStore.spouses.length === 0" class="empty-state">
          <strong>暂无婚姻关系</strong>
          <p class="muted">可通过配偶成员 ID 补录婚姻。</p>
        </div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>配偶</th>
              <th>状态</th>
              <th>日期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in memberStore.spouses" :key="item.spouse_member_id">
              <td>
                <strong>{{ item.name }}</strong>
                <div class="muted">#{{ item.spouse_member_id }} / {{ genderLabel(item.gender) }}</div>
              </td>
              <td>{{ item.status }}</td>
              <td>{{ item.married_at ?? "未填" }} / {{ item.ended_at ?? "未结束" }}</td>
              <td>
                <div class="detail-hero__actions">
                  <button
                    v-if="canModify"
                    class="button button--ghost"
                    type="button"
                    @click="handleMarkMarriageEnded(item.spouse_member_id, item.married_at)"
                  >
                    标记 ended
                  </button>
                  <button
                    v-if="canModify"
                    class="button button--ghost"
                    type="button"
                    @click="handleDeleteMarriage(item.spouse_member_id)"
                  >
                    删除婚姻
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useFamilyTreePermission } from "../../composables/useFamilyTreePermission";
import { useFamilyTreeStore } from "../../stores/familyTree";
import { useMemberStore } from "../../stores/member";

const route = useRoute();
const router = useRouter();
const familyTreeStore = useFamilyTreeStore();
const memberStore = useMemberStore();
const { canEdit } = useFamilyTreePermission();
const treeId = computed(() => Number(route.params.treeId));
const memberId = computed(() => Number(route.params.memberId));
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const submittingMemberUpdate = ref(false);
const deletingMember = ref(false);
const submittingParentChild = ref(false);
const submittingMarriage = ref(false);

const editForm = reactive({
  name: "",
  gender: "unknown" as "male" | "female" | "unknown",
  birth_date: "",
  death_date: "",
  is_alive: true,
  generation_no: null as number | null,
  generation_name: "",
  biography: ""
});

const parentChildForm = reactive({
  parent_member_id: null as number | null,
  parent_role: "father" as "father" | "mother"
});

const marriageForm = reactive({
  spouse_member_id: null as number | null,
  married_at: "",
  ended_at: "",
  status: "active" as "active" | "ended"
});

const canModify = computed(() => canEdit(familyTreeStore.currentTree?.access_role ?? "reader"));

const editAliveSelect = computed({
  get: () => (editForm.is_alive ? "true" : "false"),
  set: (value: string) => {
    editForm.is_alive = value === "true";
    if (editForm.is_alive) {
      editForm.death_date = "";
    }
  }
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

function genderLabel(gender: string) {
  if (gender === "male") {
    return "男";
  }
  if (gender === "female") {
    return "女";
  }
  return "未知";
}

function syncEditForm() {
  const member = memberStore.currentMember;
  if (!member) {
    return;
  }
  editForm.name = member.name;
  editForm.gender = member.gender;
  editForm.birth_date = member.birth_date ?? "";
  editForm.death_date = member.death_date ?? "";
  editForm.is_alive = member.is_alive;
  editForm.generation_no = member.generation_no;
  editForm.generation_name = member.generation_name ?? "";
  editForm.biography = member.biography ?? "";
}

async function loadPage() {
  feedback.value = "";
  await familyTreeStore.loadFamilyTreeDetail(treeId.value);
  await memberStore.loadMemberDetail(treeId.value, memberId.value);
  await memberStore.loadRelationships(treeId.value, memberId.value);
  syncEditForm();
}

async function handleUpdateMember() {
  submittingMemberUpdate.value = true;
  feedback.value = "";
  try {
    await memberStore.updateMember(treeId.value, memberId.value, {
      name: editForm.name,
      gender: editForm.gender,
      birth_date: editForm.birth_date || null,
      death_date: editForm.death_date || null,
      is_alive: editForm.is_alive,
      generation_no: editForm.generation_no,
      generation_name: editForm.generation_name || null,
      biography: editForm.biography || null
    });
    syncEditForm();
    feedbackType.value = "success";
    feedback.value = "成员修改已保存。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "成员修改失败。";
    } else {
      feedback.value = "成员修改失败。";
    }
  } finally {
    submittingMemberUpdate.value = false;
  }
}

async function handleDeleteMember() {
  deletingMember.value = true;
  feedback.value = "";
  try {
    await memberStore.deleteMember(treeId.value, memberId.value);
    await router.push({ name: "member-list", params: { treeId: treeId.value } });
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "成员删除失败。";
    } else {
      feedback.value = "成员删除失败。";
    }
  } finally {
    deletingMember.value = false;
  }
}

async function handleCreateParentChild() {
  if (!parentChildForm.parent_member_id) {
    feedbackType.value = "error";
    feedback.value = "请输入有效的父/母成员 ID。";
    return;
  }
  submittingParentChild.value = true;
  feedback.value = "";
  try {
    await memberStore.createParentChild(treeId.value, {
      parent_member_id: parentChildForm.parent_member_id,
      child_member_id: memberId.value,
      parent_role: parentChildForm.parent_role
    });
    parentChildForm.parent_member_id = null;
    parentChildForm.parent_role = "father";
    feedbackType.value = "success";
    feedback.value = "父母关系已添加。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "父母关系创建失败。";
    } else {
      feedback.value = "父母关系创建失败。";
    }
  } finally {
    submittingParentChild.value = false;
  }
}

async function handleDeleteParentChild(parentMemberId: number, parentRole: "father" | "mother") {
  feedback.value = "";
  try {
    await memberStore.deleteParentChild(treeId.value, {
      parent_member_id: parentMemberId,
      child_member_id: memberId.value,
      parent_role: parentRole
    });
    feedbackType.value = "success";
    feedback.value = "父母关系已删除。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "父母关系删除失败。";
    } else {
      feedback.value = "父母关系删除失败。";
    }
  }
}

async function handleCreateMarriage() {
  if (!marriageForm.spouse_member_id) {
    feedbackType.value = "error";
    feedback.value = "请输入有效的配偶成员 ID。";
    return;
  }
  submittingMarriage.value = true;
  feedback.value = "";
  try {
    await memberStore.createMarriage(treeId.value, {
      member_id_1: memberId.value,
      member_id_2: marriageForm.spouse_member_id,
      married_at: marriageForm.married_at || null,
      ended_at: marriageForm.status === "ended" ? marriageForm.ended_at || null : null,
      status: marriageForm.status
    });
    marriageForm.spouse_member_id = null;
    marriageForm.married_at = "";
    marriageForm.ended_at = "";
    marriageForm.status = "active";
    feedbackType.value = "success";
    feedback.value = "婚姻关系已创建。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "婚姻关系创建失败。";
    } else {
      feedback.value = "婚姻关系创建失败。";
    }
  } finally {
    submittingMarriage.value = false;
  }
}

async function handleMarkMarriageEnded(spouseMemberId: number, marriedAt: string | null) {
  feedback.value = "";
  try {
    await memberStore.updateMarriage(treeId.value, {
      member_id_1: memberId.value,
      member_id_2: spouseMemberId,
      married_at: marriedAt,
      ended_at: new Date().toISOString().slice(0, 10),
      status: "ended"
    });
    feedbackType.value = "success";
    feedback.value = "婚姻状态已更新为 ended。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "婚姻状态更新失败。";
    } else {
      feedback.value = "婚姻状态更新失败。";
    }
  }
}

async function handleDeleteMarriage(spouseMemberId: number) {
  feedback.value = "";
  try {
    await memberStore.deleteMarriage(treeId.value, {
      member_id_1: memberId.value,
      member_id_2: spouseMemberId
    });
    feedbackType.value = "success";
    feedback.value = "婚姻关系已删除。";
  } catch (error) {
    feedbackType.value = "error";
    if (axios.isAxiosError(error)) {
      feedback.value = (error.response?.data as { message?: string } | undefined)?.message ?? "婚姻关系删除失败。";
    } else {
      feedback.value = "婚姻关系删除失败。";
    }
  }
}

watch([treeId, memberId], async () => {
  await loadPage();
});

onMounted(async () => {
  await loadPage();
});
</script>

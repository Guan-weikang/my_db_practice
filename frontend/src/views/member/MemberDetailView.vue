<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">成员</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">
          {{ memberStore.currentMember?.name ?? "成员详情" }}
        </h1>
        <p class="mt-2 text-sm text-muted-foreground">查看成员资料、亲缘查询入口和关系维护信息。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button as-child variant="outline">
          <RouterLink :to="{ name: 'member-list', params: { treeId } }">返回成员列表</RouterLink>
        </Button>
        <Sheet v-if="memberStore.currentMember && canModify" v-model:open="editOpen">
          <SheetTrigger as-child>
            <Button variant="outline">
              <PencilIcon data-icon="inline-start" />
              编辑成员
            </Button>
          </SheetTrigger>
          <SheetContent class="overflow-y-auto sm:max-w-xl">
            <SheetHeader>
              <SheetTitle>编辑成员资料</SheetTitle>
              <SheetDescription>修改姓名、生卒日期、代际和简介。</SheetDescription>
            </SheetHeader>
            <form class="mt-6 grid gap-4" @submit.prevent="handleUpdateMember">
              <div class="grid gap-2">
                <Label for="member-name">姓名</Label>
                <Input id="member-name" v-model.trim="editForm.name" required />
              </div>
              <div class="grid gap-2">
                <Label>性别</Label>
                <Select v-model="editForm.gender">
                  <SelectTrigger class="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value="male">男</SelectItem>
                      <SelectItem value="female">女</SelectItem>
                      <SelectItem value="unknown">未知</SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>
              <div class="grid gap-4 sm:grid-cols-2">
                <div class="grid gap-2">
                  <Label for="birth-date">出生日期</Label>
                  <Input id="birth-date" v-model="editForm.birth_date" type="date" />
                </div>
                <div class="grid gap-2">
                  <Label for="death-date">去世日期</Label>
                  <Input id="death-date" v-model="editForm.death_date" :disabled="editForm.is_alive" type="date" />
                </div>
              </div>
              <label class="flex items-center gap-2 rounded-md border p-3 text-sm">
                <Checkbox v-model:checked="editForm.is_alive" />
                <span>当前在世</span>
              </label>
              <div class="grid gap-4 sm:grid-cols-2">
                <div class="grid gap-2">
                  <Label for="generation-no">代际编号</Label>
                  <Input id="generation-no" v-model.number="editForm.generation_no" min="1" type="number" />
                </div>
                <div class="grid gap-2">
                  <Label for="generation-name">字辈/派语</Label>
                  <Input id="generation-name" v-model.trim="editForm.generation_name" />
                </div>
              </div>
              <div class="grid gap-2">
                <Label for="biography">生平简介</Label>
                <Textarea id="biography" v-model.trim="editForm.biography" rows="4" />
              </div>
              <Alert v-if="feedback && feedbackType === 'error'" variant="destructive">
                <AlertTitle>保存失败</AlertTitle>
                <AlertDescription>{{ feedback }}</AlertDescription>
              </Alert>
              <SheetFooter>
                <Button type="submit" :disabled="submittingMemberUpdate">
                  <Spinner v-if="submittingMemberUpdate" data-icon="inline-start" />
                  {{ submittingMemberUpdate ? "保存中" : "保存修改" }}
                </Button>
              </SheetFooter>
            </form>
          </SheetContent>
        </Sheet>
      </div>
    </div>

    <Alert v-if="feedback && feedbackType === 'success'">
      <AlertTitle>已完成</AlertTitle>
      <AlertDescription>{{ feedback }}</AlertDescription>
    </Alert>
    <Alert v-else-if="feedback && feedbackType === 'error'" variant="destructive">
      <AlertTitle>操作失败</AlertTitle>
      <AlertDescription>{{ feedback }}</AlertDescription>
    </Alert>

    <Card v-if="memberStore.loadingDetail">
      <CardContent class="grid gap-3 p-6">
        <Skeleton class="h-8 w-48" />
        <Skeleton class="h-28 w-full" />
      </CardContent>
    </Card>

    <Card v-else-if="!memberStore.currentMember">
      <CardHeader>
        <CardTitle>未找到成员</CardTitle>
        <CardDescription>请从成员列表重新进入。</CardDescription>
      </CardHeader>
    </Card>

    <template v-else>
      <Card>
        <CardHeader>
          <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <CardTitle>{{ memberStore.currentMember.name }}</CardTitle>
              <CardDescription>#{{ memberStore.currentMember.member_id }}</CardDescription>
            </div>
            <div class="flex flex-wrap gap-2">
              <Badge :variant="canModify ? 'secondary' : 'outline'">
                {{ roleLabel(familyTreeStore.currentTree?.access_role ?? "reader") }}
              </Badge>
              <Badge variant="outline">{{ genderLabel(memberStore.currentMember.gender) }}</Badge>
              <Badge :variant="memberStore.currentMember.is_alive ? 'secondary' : 'outline'">
                {{ memberStore.currentMember.is_alive ? "在世" : "已故" }}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent class="grid gap-4 md:grid-cols-3">
          <InfoItem label="出生日期" :value="memberStore.currentMember.birth_date ?? '未填写'" />
          <InfoItem label="去世日期" :value="memberStore.currentMember.death_date ?? '未填写'" />
          <InfoItem label="代际编号" :value="formatNullable(memberStore.currentMember.generation_no)" />
          <InfoItem label="字辈/派语" :value="memberStore.currentMember.generation_name ?? '未填写'" />
          <InfoItem label="所属族谱" :value="familyTreeStore.currentTree?.tree_name ?? '当前族谱'" />
          <InfoItem label="成员状态" :value="memberStore.currentMember.is_alive ? '在世' : '已故'" />
          <div class="rounded-md border p-4 md:col-span-3">
            <p class="text-sm text-muted-foreground">生平简介</p>
            <p class="mt-2 text-sm leading-6">{{ memberStore.currentMember.biography || "暂无简介" }}</p>
          </div>
        </CardContent>
        <CardFooter v-if="canModify" class="border-t pt-4">
          <AlertDialog>
            <AlertDialogTrigger as-child>
              <Button variant="destructive">
                <Trash2Icon data-icon="inline-start" />
                删除成员
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>确认删除该成员？</AlertDialogTitle>
                <AlertDialogDescription>删除后，该成员资料将无法在页面中恢复。</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>取消</AlertDialogCancel>
                <AlertDialogAction :disabled="deletingMember" @click="handleDeleteMember">
                  {{ deletingMember ? "删除中" : "确认删除" }}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardFooter>
      </Card>

      <div class="grid gap-4 md:grid-cols-3">
        <Card v-for="action in queryActions" :key="action.title">
          <CardHeader>
            <div class="flex size-9 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
              <component :is="action.icon" class="size-4" />
            </div>
            <CardTitle class="text-base">{{ action.title }}</CardTitle>
            <CardDescription>{{ action.description }}</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button as-child class="w-full" variant="outline">
              <RouterLink :to="action.to">进入</RouterLink>
            </Button>
          </CardFooter>
        </Card>
      </div>

      <Alert v-if="!canModify">
        <AlertTitle>当前为只读权限</AlertTitle>
        <AlertDescription>你可以查看成员资料和关系，不能修改成员或维护关系。</AlertDescription>
      </Alert>

      <Tabs default-value="parents" class="grid gap-4">
        <TabsList class="w-fit">
          <TabsTrigger value="parents">父母</TabsTrigger>
          <TabsTrigger value="children">子女</TabsTrigger>
          <TabsTrigger value="marriages">婚姻</TabsTrigger>
        </TabsList>

        <TabsContent value="parents">
          <Card>
            <CardHeader>
              <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <CardTitle>父母关系</CardTitle>
                  <CardDescription>同一成员最多录入一位父亲和一位母亲。</CardDescription>
                </div>
                <Sheet v-if="canModify" v-model:open="parentOpen">
                  <SheetTrigger as-child>
                    <Button>
                      <PlusIcon data-icon="inline-start" />
                      添加父母
                    </Button>
                  </SheetTrigger>
                  <SheetContent class="sm:max-w-lg">
                    <SheetHeader>
                      <SheetTitle>添加父母关系</SheetTitle>
                      <SheetDescription>输入父亲或母亲的成员 ID。</SheetDescription>
                    </SheetHeader>
                    <form class="mt-6 grid gap-4" @submit.prevent="handleCreateParentChild">
                      <div class="grid gap-2">
                        <Label for="parent-id">父/母成员 ID</Label>
                        <Input id="parent-id" v-model.number="parentChildForm.parent_member_id" min="1" required type="number" />
                      </div>
                      <div class="grid gap-2">
                        <Label>关系类型</Label>
                        <Select v-model="parentChildForm.parent_role">
                          <SelectTrigger class="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              <SelectItem value="father">父亲</SelectItem>
                              <SelectItem value="mother">母亲</SelectItem>
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </div>
                      <SheetFooter>
                        <Button type="submit" :disabled="submittingParentChild">
                          <Spinner v-if="submittingParentChild" data-icon="inline-start" />
                          {{ submittingParentChild ? "添加中" : "添加" }}
                        </Button>
                      </SheetFooter>
                    </form>
                  </SheetContent>
                </Sheet>
              </div>
            </CardHeader>
            <CardContent>
              <RelationState :loading="memberStore.loadingRelations" :empty="memberStore.parents.length === 0" empty-text="暂无父母关系。">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>关系</TableHead>
                      <TableHead>成员</TableHead>
                      <TableHead>代际</TableHead>
                      <TableHead class="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="item in memberStore.parents" :key="`${item.parent_role}-${item.parent_member_id}`">
                      <TableCell>{{ item.parent_role === "father" ? "父亲" : "母亲" }}</TableCell>
                      <TableCell>
                        <div class="font-medium">{{ item.name }}</div>
                        <div class="text-xs text-muted-foreground">#{{ item.parent_member_id }} · {{ genderLabel(item.gender) }}</div>
                      </TableCell>
                      <TableCell>{{ item.generation_no ?? "未填写" }}</TableCell>
                      <TableCell class="text-right">
                        <Button v-if="canModify" size="sm" variant="outline" @click="handleDeleteParentChild(item.parent_member_id, item.parent_role)">
                          删除关系
                        </Button>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </RelationState>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="children">
          <Card>
            <CardHeader>
              <CardTitle>子女关系</CardTitle>
              <CardDescription>展示当前成员作为父亲或母亲时关联到的子女。</CardDescription>
            </CardHeader>
            <CardContent>
              <RelationState :loading="memberStore.loadingRelations" :empty="memberStore.children.length === 0" empty-text="暂无子女关系。">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>角色</TableHead>
                      <TableHead>子女</TableHead>
                      <TableHead>代际</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="item in memberStore.children" :key="`${item.parent_role}-${item.child_member_id}`">
                      <TableCell>{{ item.parent_role === "father" ? "父系" : "母系" }}</TableCell>
                      <TableCell>
                        <div class="font-medium">{{ item.name }}</div>
                        <div class="text-xs text-muted-foreground">#{{ item.child_member_id }} · {{ genderLabel(item.gender) }}</div>
                      </TableCell>
                      <TableCell>{{ item.generation_no ?? "未填写" }}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </RelationState>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="marriages">
          <Card>
            <CardHeader>
              <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <CardTitle>婚姻关系</CardTitle>
                  <CardDescription>维护当前成员的配偶和婚姻状态。</CardDescription>
                </div>
                <Sheet v-if="canModify" v-model:open="marriageOpen">
                  <SheetTrigger as-child>
                    <Button>
                      <PlusIcon data-icon="inline-start" />
                      添加婚姻
                    </Button>
                  </SheetTrigger>
                  <SheetContent class="sm:max-w-lg">
                    <SheetHeader>
                      <SheetTitle>添加婚姻关系</SheetTitle>
                      <SheetDescription>输入配偶成员 ID 和婚姻日期。</SheetDescription>
                    </SheetHeader>
                    <form class="mt-6 grid gap-4" @submit.prevent="handleCreateMarriage">
                      <div class="grid gap-2">
                        <Label for="spouse-id">配偶成员 ID</Label>
                        <Input id="spouse-id" v-model.number="marriageForm.spouse_member_id" min="1" required type="number" />
                      </div>
                      <div class="grid gap-2">
                        <Label for="married-at">结婚日期</Label>
                        <Input id="married-at" v-model="marriageForm.married_at" type="date" />
                      </div>
                      <div class="grid gap-2">
                        <Label>状态</Label>
                        <Select v-model="marriageForm.status">
                          <SelectTrigger class="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              <SelectItem value="active">持续中</SelectItem>
                              <SelectItem value="ended">已结束</SelectItem>
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </div>
                      <div class="grid gap-2">
                        <Label for="ended-at">结束日期</Label>
                        <Input id="ended-at" v-model="marriageForm.ended_at" :disabled="marriageForm.status === 'active'" type="date" />
                      </div>
                      <SheetFooter>
                        <Button type="submit" :disabled="submittingMarriage">
                          <Spinner v-if="submittingMarriage" data-icon="inline-start" />
                          {{ submittingMarriage ? "添加中" : "添加" }}
                        </Button>
                      </SheetFooter>
                    </form>
                  </SheetContent>
                </Sheet>
              </div>
            </CardHeader>
            <CardContent>
              <RelationState :loading="memberStore.loadingRelations" :empty="memberStore.spouses.length === 0" empty-text="暂无婚姻关系。">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>配偶</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>日期</TableHead>
                      <TableHead class="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="item in memberStore.spouses" :key="item.spouse_member_id">
                      <TableCell>
                        <div class="font-medium">{{ item.name }}</div>
                        <div class="text-xs text-muted-foreground">#{{ item.spouse_member_id }} · {{ genderLabel(item.gender) }}</div>
                      </TableCell>
                      <TableCell>
                        <Badge :variant="item.status === 'active' ? 'secondary' : 'outline'">
                          {{ marriageStatusLabel(item.status) }}
                        </Badge>
                      </TableCell>
                      <TableCell>{{ item.married_at ?? "未填写" }} / {{ item.ended_at ?? "未结束" }}</TableCell>
                      <TableCell class="text-right">
                        <div class="flex justify-end gap-2">
                          <Button
                            v-if="canModify && item.status !== 'ended'"
                            size="sm"
                            variant="outline"
                            @click="handleMarkMarriageEnded(item.spouse_member_id, item.married_at)"
                          >
                            标记已结束
                          </Button>
                          <Button v-if="canModify" size="sm" variant="outline" @click="handleDeleteMarriage(item.spouse_member_id)">
                            删除婚姻
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </RelationState>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import type { Component } from "vue";
import { computed, defineComponent, h, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { GitBranchIcon, NetworkIcon, PencilIcon, PlusIcon, RouteIcon, Trash2Icon } from "lucide-vue-next";
import { toast } from "vue-sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useFamilyTreePermission } from "@/composables/useFamilyTreePermission";
import { useFamilyTreeStore } from "@/stores/familyTree";
import { useMemberStore } from "@/stores/member";

const InfoItem = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true }
  },
  setup(props) {
    return () =>
      h("div", { class: "rounded-md border p-4" }, [
        h("p", { class: "text-sm text-muted-foreground" }, props.label),
        h("p", { class: "mt-2 font-medium" }, props.value)
      ]);
  }
});

const RelationState = defineComponent({
  props: {
    loading: { type: Boolean, required: true },
    empty: { type: Boolean, required: true },
    emptyText: { type: String, required: true }
  },
  setup(props, { slots }) {
    return () => {
      if (props.loading) {
        return h("div", { class: "grid gap-3" }, [
          h(Skeleton as Component, { class: "h-10 w-full" }),
          h(Skeleton as Component, { class: "h-10 w-full" })
        ]);
      }
      if (props.empty) {
        return h("div", { class: "rounded-md border border-dashed p-6 text-sm text-muted-foreground" }, props.emptyText);
      }
      return slots.default?.();
    };
  }
});

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
const editOpen = ref(false);
const parentOpen = ref(false);
const marriageOpen = ref(false);

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
const queryActions = computed<Array<{ title: string; description: string; icon: Component; to: { name: string; params: { treeId: number }; query: Record<string, number> } }>>(() => [
  {
    title: "查看祖先链",
    description: "以当前成员为起点向上追溯。",
    icon: NetworkIcon,
    to: { name: "ancestor-query", params: { treeId: treeId.value }, query: { memberId: memberId.value } }
  },
  {
    title: "查看后代分支",
    description: "以当前成员为根向下展开。",
    icon: GitBranchIcon,
    to: { name: "branch-tree", params: { treeId: treeId.value }, query: { rootMemberId: memberId.value } }
  },
  {
    title: "作为路径起点",
    description: "预填成员 A，继续查询亲缘路径。",
    icon: RouteIcon,
    to: { name: "kinship-query", params: { treeId: treeId.value }, query: { memberA: memberId.value } }
  }
]);

watch(
  () => editForm.is_alive,
  (isAlive) => {
    if (isAlive) {
      editForm.death_date = "";
    }
  }
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

function genderLabel(gender: string) {
  if (gender === "male") {
    return "男";
  }
  if (gender === "female") {
    return "女";
  }
  return "未知";
}

function marriageStatusLabel(status: string) {
  return status === "ended" ? "已结束" : "持续中";
}

function formatNullable(value: number | string | null) {
  if (value === null || value === "") {
    return "未填写";
  }
  return String(value);
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
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
  try {
    await familyTreeStore.loadFamilyTreeDetail(treeId.value);
    await memberStore.loadMemberDetail(treeId.value, memberId.value);
    await memberStore.loadRelationships(treeId.value, memberId.value);
    syncEditForm();
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "成员详情加载失败，请稍后重试。");
  }
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
    editOpen.value = false;
    feedbackType.value = "success";
    feedback.value = "成员资料已保存。";
    toast.success("成员资料已保存");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "成员资料保存失败，请检查填写内容后重试。");
  } finally {
    submittingMemberUpdate.value = false;
  }
}

async function handleDeleteMember() {
  deletingMember.value = true;
  feedback.value = "";
  try {
    await memberStore.deleteMember(treeId.value, memberId.value);
    toast.success("成员已删除");
    await router.push({ name: "member-list", params: { treeId: treeId.value } });
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "成员删除失败，请稍后重试。");
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
    parentOpen.value = false;
    feedbackType.value = "success";
    feedback.value = "父母关系已添加。";
    toast.success("父母关系已添加");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "父母关系添加失败，请稍后重试。");
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
    toast.success("父母关系已删除");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "父母关系删除失败，请稍后重试。");
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
    marriageOpen.value = false;
    feedbackType.value = "success";
    feedback.value = "婚姻关系已添加。";
    toast.success("婚姻关系已添加");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "婚姻关系添加失败，请稍后重试。");
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
    feedback.value = "婚姻状态已更新为已结束。";
    toast.success("婚姻状态已更新");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "婚姻状态更新失败，请稍后重试。");
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
    toast.success("婚姻关系已删除");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "婚姻关系删除失败，请稍后重试。");
  }
}

watch([treeId, memberId], loadPage);
onMounted(loadPage);
</script>

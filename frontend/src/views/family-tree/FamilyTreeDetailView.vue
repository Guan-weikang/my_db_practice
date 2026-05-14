<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">族谱详情</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">
          {{ familyTreeStore.currentTree?.tree_name ?? "族谱详情" }}
        </h1>
        <p class="mt-2 text-sm text-muted-foreground">查看族谱资料，并进入成员、查询和协作者管理。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button as-child variant="outline">
          <RouterLink :to="{ name: 'family-tree-list' }">返回列表</RouterLink>
        </Button>
        <Sheet v-if="familyTreeStore.currentTree && canEdit(familyTreeStore.currentTree.access_role)" v-model:open="editOpen">
          <SheetTrigger as-child>
            <Button variant="outline">
              <PencilIcon data-icon="inline-start" />
              编辑资料
            </Button>
          </SheetTrigger>
          <SheetContent class="overflow-y-auto sm:max-w-lg">
            <SheetHeader>
              <SheetTitle>编辑族谱资料</SheetTitle>
              <SheetDescription>修改名称、姓氏、编修日期和说明。</SheetDescription>
            </SheetHeader>
            <form class="mt-6 grid gap-4" @submit.prevent="handleUpdate">
              <div class="grid gap-2">
                <Label for="tree-name">族谱名称</Label>
                <Input id="tree-name" v-model.trim="editForm.tree_name" required />
              </div>
              <div class="grid gap-2">
                <Label for="tree-surname">姓氏</Label>
                <Input id="tree-surname" v-model.trim="editForm.surname" required />
              </div>
              <div class="grid gap-2">
                <Label for="compiled-at">编修日期</Label>
                <Input id="compiled-at" v-model="editForm.compiled_at" type="date" />
              </div>
              <div class="grid gap-2">
                <Label for="tree-description">说明</Label>
                <Textarea id="tree-description" v-model.trim="editForm.description" rows="4" />
              </div>
              <Alert v-if="feedback && feedbackType === 'error'" variant="destructive">
                <AlertTitle>保存失败</AlertTitle>
                <AlertDescription>{{ feedback }}</AlertDescription>
              </Alert>
              <SheetFooter>
                <Button type="submit" :disabled="submittingUpdate">
                  <Spinner v-if="submittingUpdate" data-icon="inline-start" />
                  {{ submittingUpdate ? "保存中" : "保存修改" }}
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

    <Card v-if="familyTreeStore.loadingDetail">
      <CardContent class="grid gap-3 p-6">
        <Skeleton class="h-8 w-48" />
        <Skeleton class="h-28 w-full" />
      </CardContent>
    </Card>

    <Card v-else-if="!familyTreeStore.currentTree">
      <CardHeader>
        <CardTitle>未找到族谱</CardTitle>
        <CardDescription>请从族谱列表重新进入。</CardDescription>
      </CardHeader>
    </Card>

    <template v-else>
      <Card>
        <CardHeader>
          <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <CardTitle>{{ familyTreeStore.currentTree.tree_name }}</CardTitle>
              <CardDescription>#{{ familyTreeStore.currentTree.tree_id }} · {{ familyTreeStore.currentTree.surname }}</CardDescription>
            </div>
            <Badge :variant="familyTreeStore.currentTree.access_role === 'reader' ? 'outline' : 'secondary'">
              {{ roleLabel(familyTreeStore.currentTree.access_role) }}
            </Badge>
          </div>
        </CardHeader>
        <CardContent class="grid gap-4 md:grid-cols-3">
          <div class="rounded-md border p-4">
            <p class="text-sm text-muted-foreground">姓氏</p>
            <p class="mt-2 font-medium">{{ familyTreeStore.currentTree.surname }}</p>
          </div>
          <div class="rounded-md border p-4">
            <p class="text-sm text-muted-foreground">编修日期</p>
            <p class="mt-2 font-medium">{{ familyTreeStore.currentTree.compiled_at ?? "未填写" }}</p>
          </div>
          <div class="rounded-md border p-4 md:col-span-1">
            <p class="text-sm text-muted-foreground">访问权限</p>
            <p class="mt-2 font-medium">{{ roleLabel(familyTreeStore.currentTree.access_role) }}</p>
          </div>
          <div class="rounded-md border p-4 md:col-span-3">
            <p class="text-sm text-muted-foreground">说明</p>
            <p class="mt-2 text-sm">{{ familyTreeStore.currentTree.description || "暂无说明" }}</p>
          </div>
        </CardContent>
      </Card>

      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card v-for="action in actions" :key="action.title">
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

      <Alert v-if="!canEdit(familyTreeStore.currentTree.access_role)">
        <AlertTitle>当前为只读权限</AlertTitle>
        <AlertDescription>你可以查看族谱、成员和查询结果，不能修改资料或维护成员。</AlertDescription>
      </Alert>

      <Card v-if="familyTreeStore.currentTree.access_role === 'creator'">
        <CardHeader>
          <CardTitle>危险操作</CardTitle>
          <CardDescription>只有空族谱可以删除，删除前请确认成员和关系已清理。</CardDescription>
        </CardHeader>
        <CardFooter>
          <AlertDialog>
            <AlertDialogTrigger as-child>
              <Button variant="destructive">删除空族谱</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>确认删除这棵族谱？</AlertDialogTitle>
                <AlertDialogDescription>
                  删除后无法在页面中恢复。如果族谱仍包含成员，后端会拒绝删除。
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>取消</AlertDialogCancel>
                <AlertDialogAction :disabled="deletingTree" @click="handleDelete">
                  {{ deletingTree ? "删除中" : "确认删除" }}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardFooter>
      </Card>
    </template>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import type { Component } from "vue";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { GitBranchIcon, NetworkIcon, PencilIcon, RouteIcon, SearchIcon, UsersIcon } from "lucide-vue-next";
import { toast } from "vue-sonner";

import client from "@/api/client";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useFamilyTreePermission } from "@/composables/useFamilyTreePermission";
import { useFamilyTreeStore } from "@/stores/familyTree";

const route = useRoute();
const router = useRouter();
const familyTreeStore = useFamilyTreeStore();
const { canEdit, canManageCollaborators } = useFamilyTreePermission();
const submittingUpdate = ref(false);
const deletingTree = ref(false);
const editOpen = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");
const editForm = reactive({
  tree_name: "",
  surname: "",
  compiled_at: "",
  description: ""
});

const treeId = computed(() => Number(route.params.treeId));

const actions = computed<Array<{ title: string; description: string; icon: Component; to: { name: string; params: { treeId: number } } }>>(() => {
  const items = [
    { title: "成员列表", description: "查看成员并进入详情。", icon: UsersIcon, name: "member-list" },
    { title: "成员搜索", description: "按姓名查找成员。", icon: SearchIcon, name: "member-search" },
    { title: "分支树", description: "查看后代分支。", icon: GitBranchIcon, name: "branch-tree" },
    { title: "祖先查询", description: "查看祖先链路。", icon: NetworkIcon, name: "ancestor-query" },
    { title: "亲缘路径", description: "查看两名成员的关系链。", icon: RouteIcon, name: "kinship-query" }
  ];

  if (canManageCollaborators(familyTreeStore.currentTree?.access_role ?? "reader")) {
    items.push({ title: "协作者", description: "维护族谱访问权限。", icon: UsersIcon, name: "collaborators" });
  }

  return items.map((item) => ({
    title: item.title,
    description: item.description,
    icon: item.icon,
    to: { name: item.name, params: { treeId: treeId.value } }
  }));
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

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function loadDetail() {
  feedback.value = "";
  try {
    await familyTreeStore.loadFamilyTreeDetail(treeId.value);
    syncForm();
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "族谱详情加载失败，请稍后重试。");
  }
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
    editOpen.value = false;
    feedbackType.value = "success";
    feedback.value = "族谱资料已保存。";
    toast.success("族谱资料已保存");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "保存失败，请检查填写内容后重试。");
  } finally {
    submittingUpdate.value = false;
  }
}

async function handleDelete() {
  deletingTree.value = true;
  feedback.value = "";
  try {
    await client.delete(`/family-trees/${treeId.value}`);
    toast.success("族谱已删除");
    await router.push({ name: "family-tree-list" });
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "删除失败，请确认族谱为空后重试。");
  } finally {
    deletingTree.value = false;
  }
}

watch(treeId, loadDetail);
onMounted(loadDetail);
</script>

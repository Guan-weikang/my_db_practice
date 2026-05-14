<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">协作</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">协作者管理</h1>
        <p class="mt-2 text-sm text-muted-foreground">维护当前族谱的协作者和只读成员。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button as-child variant="outline">
          <RouterLink :to="{ name: 'family-tree-detail', params: { treeId } }">返回族谱</RouterLink>
        </Button>
        <Button variant="outline" :disabled="familyTreeStore.loadingCollaborators" @click="loadCollaborators">
          <RefreshCwIcon data-icon="inline-start" />
          刷新
        </Button>
        <Sheet v-model:open="inviteOpen">
          <SheetTrigger as-child>
            <Button>
              <UserPlusIcon data-icon="inline-start" />
              添加协作者
            </Button>
          </SheetTrigger>
          <SheetContent class="overflow-y-auto sm:max-w-lg">
            <SheetHeader>
              <SheetTitle>添加协作者</SheetTitle>
              <SheetDescription>输入用户 ID，并选择在当前族谱中的访问角色。</SheetDescription>
            </SheetHeader>
            <form class="mt-6 grid gap-4" @submit.prevent="handleInvite">
              <div class="grid gap-2">
                <Label for="user-id">用户 ID</Label>
                <Input id="user-id" v-model.number="inviteForm.user_id" min="1" required type="number" />
              </div>
              <div class="grid gap-2">
                <Label>角色</Label>
                <Select v-model="inviteForm.access_role">
                  <SelectTrigger class="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value="collaborator">协作者</SelectItem>
                      <SelectItem value="reader">只读</SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>
              <Alert v-if="feedback && feedbackType === 'error'" variant="destructive">
                <AlertTitle>添加失败</AlertTitle>
                <AlertDescription>{{ feedback }}</AlertDescription>
              </Alert>
              <SheetFooter>
                <Button type="submit" :disabled="submittingInvite">
                  <Spinner v-if="submittingInvite" data-icon="inline-start" />
                  {{ submittingInvite ? "添加中" : "添加" }}
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

    <Card>
      <CardHeader>
        <CardTitle>协作者列表</CardTitle>
        <CardDescription>协作者可以编辑族谱；只读成员只能查看。</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="familyTreeStore.loadingCollaborators" class="grid gap-3">
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
        </div>
        <div v-else-if="familyTreeStore.collaborators.length === 0" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          当前没有单独添加的协作者。
        </div>
        <div v-else class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>用户</TableHead>
                <TableHead>角色</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>添加时间</TableHead>
                <TableHead class="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="item in familyTreeStore.collaborators" :key="item.user_id">
                <TableCell>
                  <div class="font-medium">{{ item.display_name || item.username }}</div>
                  <div class="text-xs text-muted-foreground">@{{ item.username }} · #{{ item.user_id }}</div>
                </TableCell>
                <TableCell>
                  <Select :model-value="item.access_role" @update:model-value="(value) => handleRoleChange(item.user_id, value)">
                    <SelectTrigger class="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="collaborator">协作者</SelectItem>
                        <SelectItem value="reader">只读</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Badge :variant="item.status === 'active' ? 'secondary' : 'outline'">
                    {{ statusLabel(item.status) }}
                  </Badge>
                </TableCell>
                <TableCell>{{ formatTime(item.invited_at) }}</TableCell>
                <TableCell class="text-right">
                  <AlertDialog>
                    <AlertDialogTrigger as-child>
                      <Button size="sm" variant="outline">
                        撤销权限
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>确认撤销权限？</AlertDialogTitle>
                        <AlertDialogDescription>
                          撤销后，该用户将不再作为协作者显示在当前族谱中。
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>取消</AlertDialogCancel>
                        <AlertDialogAction @click="handleRevoke(item.user_id)">确认撤销</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { RefreshCwIcon, UserPlusIcon } from "lucide-vue-next";
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useFamilyTreeStore } from "@/stores/familyTree";

const route = useRoute();
const familyTreeStore = useFamilyTreeStore();
const treeId = Number(route.params.treeId);
const submittingInvite = ref(false);
const inviteOpen = ref(false);
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

function statusLabel(status: string) {
  if (status === "active") {
    return "有效";
  }
  if (status === "pending") {
    return "待确认";
  }
  return "已撤销";
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function loadCollaborators() {
  feedback.value = "";
  try {
    await familyTreeStore.loadCollaborators(treeId);
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "协作者列表加载失败，请稍后重试。");
  }
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
    inviteOpen.value = false;
    feedbackType.value = "success";
    feedback.value = "协作者已添加。";
    toast.success("协作者已添加");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "添加协作者失败，请检查用户 ID 后重试。");
  } finally {
    submittingInvite.value = false;
  }
}

async function handleRoleChange(userId: number, value: string | number | null | undefined) {
  if (value !== "collaborator" && value !== "reader") {
    return;
  }

  feedback.value = "";
  try {
    await familyTreeStore.updateCollaborator(treeId, userId, { access_role: value });
    feedbackType.value = "success";
    feedback.value = "协作者角色已更新。";
    toast.success("协作者角色已更新");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "角色更新失败，请稍后重试。");
  }
}

async function handleRevoke(userId: number) {
  feedback.value = "";
  try {
    await familyTreeStore.revokeCollaborator(treeId, userId);
    feedbackType.value = "success";
    feedback.value = "协作者权限已撤销。";
    toast.success("协作者权限已撤销");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "撤销权限失败，请稍后重试。");
  }
}

onMounted(loadCollaborators);
</script>

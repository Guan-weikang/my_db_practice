<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">族谱</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">族谱列表</h1>
        <p class="mt-2 text-sm text-muted-foreground">查看可访问族谱，并按权限进入详情或维护资料。</p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" :disabled="familyTreeStore.loadingList" @click="refreshList">
          <RefreshCwIcon data-icon="inline-start" />
          刷新
        </Button>
        <Sheet v-model:open="createOpen">
          <SheetTrigger as-child>
            <Button>
              <PlusIcon data-icon="inline-start" />
              新建族谱
            </Button>
          </SheetTrigger>
          <SheetContent class="overflow-y-auto sm:max-w-lg">
            <SheetHeader>
              <SheetTitle>新建族谱</SheetTitle>
              <SheetDescription>填写族谱名称、姓氏和简要说明。</SheetDescription>
            </SheetHeader>
            <form class="mt-6 grid gap-4" @submit.prevent="handleCreate">
              <div class="grid gap-2">
                <Label for="tree-name">族谱名称</Label>
                <Input id="tree-name" v-model.trim="createForm.tree_name" required />
              </div>
              <div class="grid gap-2">
                <Label for="tree-surname">姓氏</Label>
                <Input id="tree-surname" v-model.trim="createForm.surname" required />
              </div>
              <div class="grid gap-2">
                <Label for="compiled-at">编修日期</Label>
                <Input id="compiled-at" v-model="createForm.compiled_at" type="date" />
              </div>
              <div class="grid gap-2">
                <Label for="tree-description">说明</Label>
                <Textarea id="tree-description" v-model.trim="createForm.description" rows="4" />
              </div>
              <Alert v-if="feedback && feedbackType === 'error'" variant="destructive">
                <AlertTitle>创建失败</AlertTitle>
                <AlertDescription>{{ feedback }}</AlertDescription>
              </Alert>
              <SheetFooter>
                <Button type="submit" :disabled="submittingCreate">
                  <Spinner v-if="submittingCreate" data-icon="inline-start" />
                  {{ submittingCreate ? "创建中" : "创建族谱" }}
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

    <Card>
      <CardHeader>
        <CardTitle>可访问族谱</CardTitle>
        <CardDescription>角色决定你可以查看、编辑或管理的范围。</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="familyTreeStore.loadingList" class="grid gap-3">
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
        </div>
        <div v-else-if="familyTreeStore.list.length === 0" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          暂无族谱。可以先新建一棵族谱，再添加成员和关系。
        </div>
        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead>族谱</TableHead>
              <TableHead>姓氏</TableHead>
              <TableHead>编修日期</TableHead>
              <TableHead>角色</TableHead>
              <TableHead class="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="tree in familyTreeStore.list" :key="tree.tree_id">
              <TableCell>
                <div class="font-medium">{{ tree.tree_name }}</div>
                <div class="text-xs text-muted-foreground">#{{ tree.tree_id }}</div>
                <div v-if="tree.description" class="mt-1 max-w-xl truncate text-xs text-muted-foreground">
                  {{ tree.description }}
                </div>
              </TableCell>
              <TableCell>{{ tree.surname }}</TableCell>
              <TableCell>{{ tree.compiled_at ?? "未填写" }}</TableCell>
              <TableCell>
                <Badge :variant="tree.access_role === 'reader' ? 'outline' : 'secondary'">
                  {{ roleLabel(tree.access_role) }}
                </Badge>
              </TableCell>
              <TableCell class="text-right">
                <Button as-child size="sm">
                  <RouterLink :to="{ name: 'family-tree-detail', params: { treeId: tree.tree_id } }">
                    查看详情
                  </RouterLink>
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { onMounted, reactive, ref } from "vue";
import { PlusIcon, RefreshCwIcon } from "lucide-vue-next";
import { toast } from "vue-sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useFamilyTreeStore } from "@/stores/familyTree";

const familyTreeStore = useFamilyTreeStore();
const submittingCreate = ref(false);
const createOpen = ref(false);
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

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function refreshList() {
  feedback.value = "";
  try {
    await familyTreeStore.loadFamilyTrees();
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "族谱列表加载失败，请稍后重试。");
  }
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
    createOpen.value = false;
    feedbackType.value = "success";
    feedback.value = "族谱创建成功。";
    toast.success("族谱创建成功");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "族谱创建失败，请检查填写内容后重试。");
  } finally {
    submittingCreate.value = false;
  }
}

onMounted(refreshList);
</script>

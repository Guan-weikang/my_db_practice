<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">成员</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">成员列表</h1>
        <p class="mt-2 text-sm text-muted-foreground">分页查看成员，避免一次加载过多数据。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button as-child variant="outline">
          <RouterLink :to="{ name: 'family-tree-detail', params: { treeId } }">返回族谱</RouterLink>
        </Button>
        <Button variant="outline" :disabled="memberStore.loadingList" @click="refreshList">
          <RefreshCwIcon data-icon="inline-start" />
          刷新
        </Button>
        <Sheet v-if="canCreate" v-model:open="createOpen">
          <SheetTrigger as-child>
            <Button>
              <PlusIcon data-icon="inline-start" />
              新增成员
            </Button>
          </SheetTrigger>
          <SheetContent class="overflow-y-auto sm:max-w-xl">
            <SheetHeader>
              <SheetTitle>新增成员</SheetTitle>
              <SheetDescription>填写成员基础信息，后续可在详情页维护关系。</SheetDescription>
            </SheetHeader>
            <form class="mt-6 grid gap-4" @submit.prevent="handleCreate">
              <div class="grid gap-2">
                <Label for="member-name">姓名</Label>
                <Input id="member-name" v-model.trim="createForm.name" required />
              </div>
              <div class="grid gap-2">
                <Label>性别</Label>
                <Select v-model="createForm.gender">
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
                  <Input id="birth-date" v-model="createForm.birth_date" type="date" />
                </div>
                <div class="grid gap-2">
                  <Label for="death-date">去世日期</Label>
                  <Input id="death-date" v-model="createForm.death_date" :disabled="createForm.is_alive" type="date" />
                </div>
              </div>
              <label class="flex items-center gap-2 rounded-md border p-3 text-sm">
                <Checkbox v-model:checked="createForm.is_alive" />
                <span>当前在世</span>
              </label>
              <div class="grid gap-4 sm:grid-cols-2">
                <div class="grid gap-2">
                  <Label for="generation-no">代际编号</Label>
                  <Input id="generation-no" v-model.number="createForm.generation_no" min="1" type="number" />
                </div>
                <div class="grid gap-2">
                  <Label for="generation-name">字辈/派语</Label>
                  <Input id="generation-name" v-model.trim="createForm.generation_name" />
                </div>
              </div>
              <div class="grid gap-2">
                <Label for="biography">生平简介</Label>
                <Textarea id="biography" v-model.trim="createForm.biography" rows="4" />
              </div>
              <Alert v-if="feedback && feedbackType === 'error'" variant="destructive">
                <AlertTitle>新增失败</AlertTitle>
                <AlertDescription>{{ feedback }}</AlertDescription>
              </Alert>
              <SheetFooter>
                <Button type="submit" :disabled="submittingCreate">
                  <Spinner v-if="submittingCreate" data-icon="inline-start" />
                  {{ submittingCreate ? "创建中" : "创建成员" }}
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

    <Alert v-if="familyTreeStore.currentTree && !canCreate">
      <AlertTitle>当前为只读权限</AlertTitle>
      <AlertDescription>你可以查看成员列表和详情，不能新增或编辑成员。</AlertDescription>
    </Alert>

    <Card>
      <CardHeader>
        <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <CardTitle>{{ familyTreeStore.currentTree?.tree_name ?? "成员" }}</CardTitle>
            <CardDescription>
              共 {{ memberStore.total.toLocaleString("zh-CN") }} 人，当前第 {{ page }} 页。
            </CardDescription>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-muted-foreground">每页</span>
            <Select :model-value="String(pageSize)" @update:model-value="changePageSize">
              <SelectTrigger class="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div v-if="memberStore.loadingList" class="grid gap-3">
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
        </div>
        <div v-else-if="memberStore.list.length === 0" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          当前族谱暂无成员。具备编辑权限时，可以先新增一位成员。
        </div>
        <div v-else class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>成员</TableHead>
                <TableHead>性别</TableHead>
                <TableHead>代际</TableHead>
                <TableHead>出生</TableHead>
                <TableHead>状态</TableHead>
                <TableHead class="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="member in memberStore.list" :key="member.member_id">
                <TableCell>
                  <div class="font-medium">{{ member.name }}</div>
                  <div class="text-xs text-muted-foreground">#{{ member.member_id }} · {{ member.generation_name || "无字辈" }}</div>
                </TableCell>
                <TableCell>{{ genderLabel(member.gender) }}</TableCell>
                <TableCell>{{ member.generation_no ?? "未填写" }}</TableCell>
                <TableCell>{{ member.birth_date ?? "未知" }}</TableCell>
                <TableCell>
                  <Badge :variant="member.is_alive ? 'secondary' : 'outline'">{{ member.is_alive ? "在世" : "已故" }}</Badge>
                </TableCell>
                <TableCell class="text-right">
                  <Button as-child size="sm">
                    <RouterLink :to="{ name: 'member-detail', params: { treeId, memberId: member.member_id } }">
                      查看详情
                    </RouterLink>
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <CardFooter class="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-sm text-muted-foreground">
          第 {{ page }} / {{ totalPages }} 页
        </p>
        <div class="flex gap-2">
          <Button variant="outline" :disabled="page <= 1 || memberStore.loadingList" @click="goPage(page - 1)">
            上一页
          </Button>
          <Button variant="outline" :disabled="page >= totalPages || memberStore.loadingList" @click="goPage(page + 1)">
            下一页
          </Button>
        </div>
      </CardFooter>
    </Card>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { PlusIcon, RefreshCwIcon } from "lucide-vue-next";
import { toast } from "vue-sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
import { Textarea } from "@/components/ui/textarea";
import { useFamilyTreePermission } from "@/composables/useFamilyTreePermission";
import { useFamilyTreeStore } from "@/stores/familyTree";
import { useMemberStore } from "@/stores/member";

const route = useRoute();
const familyTreeStore = useFamilyTreeStore();
const memberStore = useMemberStore();
const { canEdit } = useFamilyTreePermission();
const treeId = computed(() => Number(route.params.treeId));
const page = ref(1);
const pageSize = ref(20);
const submittingCreate = ref(false);
const createOpen = ref(false);
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

const canCreate = computed(() => canEdit(familyTreeStore.currentTree?.access_role ?? "reader"));
const totalPages = computed(() => Math.max(1, Math.ceil(memberStore.total / pageSize.value)));

function genderLabel(gender: string) {
  if (gender === "male") {
    return "男";
  }
  if (gender === "female") {
    return "女";
  }
  return "未知";
}

function errorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { message?: string } | undefined)?.message ?? fallback;
  }
  return fallback;
}

async function loadPage() {
  feedback.value = "";
  try {
    await familyTreeStore.loadFamilyTreeDetail(treeId.value);
    await memberStore.loadMembers(treeId.value, page.value, pageSize.value);
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "成员列表加载失败，请稍后重试。");
  }
}

async function refreshList() {
  await loadPage();
}

async function goPage(targetPage: number) {
  page.value = Math.min(Math.max(targetPage, 1), totalPages.value);
  await memberStore.loadMembers(treeId.value, page.value, pageSize.value);
}

async function changePageSize(value: string | number | null | undefined) {
  pageSize.value = Number(value) || 20;
  page.value = 1;
  await memberStore.loadMembers(treeId.value, page.value, pageSize.value);
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
    createOpen.value = false;
    feedbackType.value = "success";
    feedback.value = `成员 #${createdMember.member_id} 创建成功。`;
    toast.success("成员创建成功");
  } catch (error) {
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "成员创建失败，请检查填写内容后重试。");
  } finally {
    submittingCreate.value = false;
  }
}

watch(treeId, async () => {
  page.value = 1;
  await loadPage();
});

onMounted(loadPage);
</script>

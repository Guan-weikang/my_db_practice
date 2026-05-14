<template>
  <section class="grid gap-6">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">查询</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-normal">成员搜索</h1>
        <p class="mt-2 text-sm text-muted-foreground">输入至少两个字，查找同名成员并区分代际和父母信息。</p>
      </div>
      <Button as-child variant="outline">
        <RouterLink :to="{ name: 'family-tree-detail', params: { treeId } }">返回族谱</RouterLink>
      </Button>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>搜索条件</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="grid gap-4 md:grid-cols-[minmax(220px,1fr)_120px_120px_auto]" @submit.prevent="handleSearch">
          <div class="grid gap-2">
            <Label for="keyword">姓名关键字</Label>
            <Input id="keyword" v-model.trim="keyword" minlength="2" placeholder="例如：孔德、朱德、王仁" required />
          </div>
          <div class="grid gap-2">
            <Label for="page">页码</Label>
            <Input id="page" v-model.number="page" min="1" type="number" />
          </div>
          <div class="grid gap-2">
            <Label for="page-size">每页数量</Label>
            <Input id="page-size" v-model.number="pageSize" max="50" min="1" type="number" />
          </div>
          <div class="flex items-end">
            <Button class="w-full" :disabled="loading" type="submit">
              <Spinner v-if="loading" data-icon="inline-start" />
              {{ loading ? "查询中" : "搜索" }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <Alert v-if="feedback" :variant="feedbackType === 'error' ? 'destructive' : 'default'">
      <AlertTitle>{{ feedbackType === "error" ? "搜索失败" : "搜索完成" }}</AlertTitle>
      <AlertDescription>{{ feedback }}</AlertDescription>
    </Alert>

    <Card>
      <CardHeader>
        <CardTitle>搜索结果</CardTitle>
        <CardDescription>共 {{ total }} 条，当前第 {{ currentPage }} 页。</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="loading" class="grid gap-3">
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
          <Skeleton class="h-10 w-full" />
        </div>
        <div v-else-if="hasSearched && results.length === 0" class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          没有匹配成员。可以尝试更完整的姓名。
        </div>
        <div v-else-if="results.length > 0" class="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>成员</TableHead>
                <TableHead>性别</TableHead>
                <TableHead>代际</TableHead>
                <TableHead>父母</TableHead>
                <TableHead>生卒</TableHead>
                <TableHead class="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="item in results" :key="item.member_id">
                <TableCell>
                  <div class="font-medium">{{ item.name }}</div>
                  <div class="text-xs text-muted-foreground">#{{ item.member_id }}</div>
                </TableCell>
                <TableCell>{{ genderLabel(item.gender) }}</TableCell>
                <TableCell>{{ item.generation_no ?? "未填写" }} / {{ item.generation_name ?? "未填写" }}</TableCell>
                <TableCell>父：{{ item.father_name ?? "未录入" }} · 母：{{ item.mother_name ?? "未录入" }}</TableCell>
                <TableCell>{{ item.birth_date ?? "未知" }} / {{ item.death_date ?? (item.is_alive ? "在世" : "未知") }}</TableCell>
                <TableCell class="text-right">
                  <Button as-child size="sm">
                    <RouterLink :to="{ name: 'member-detail', params: { treeId, memberId: item.member_id } }">
                      查看详情
                    </RouterLink>
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
        <div v-else class="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
          输入姓名关键字后开始搜索。
        </div>
      </CardContent>
    </Card>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { searchMembers, type SearchMemberItem } from "@/api/search";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const route = useRoute();
const treeId = computed(() => Number(route.params.treeId));
const keyword = ref(typeof route.query.keyword === "string" ? route.query.keyword : "");
const page = ref(Number(route.query.page ?? 1) || 1);
const pageSize = ref(20);
const currentPage = ref(1);
const total = ref(0);
const results = ref<SearchMemberItem[]>([]);
const loading = ref(false);
const hasSearched = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

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

async function handleSearch() {
  if (keyword.value.trim().length < 2) {
    feedbackType.value = "error";
    feedback.value = "请输入至少两个字后再搜索。";
    return;
  }

  loading.value = true;
  feedback.value = "";
  try {
    const response = await searchMembers(treeId.value, keyword.value, page.value, pageSize.value);
    results.value = response.data.items;
    total.value = response.data.total;
    currentPage.value = response.data.page;
    hasSearched.value = true;
    feedbackType.value = "success";
    feedback.value = `已找到 ${response.data.total} 条匹配结果。`;
  } catch (error) {
    results.value = [];
    total.value = 0;
    hasSearched.value = true;
    feedbackType.value = "error";
    feedback.value = errorMessage(error, "成员搜索失败，请稍后重试。");
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (keyword.value.trim().length >= 2) {
    await handleSearch();
  }
});
</script>

<template>
  <SidebarProvider>
    <Sidebar collapsible="icon" variant="inset">
      <SidebarHeader>
        <div class="flex items-center gap-3 px-2 py-2">
          <div class="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <BookOpenTextIcon class="size-4" />
          </div>
          <div class="grid gap-0.5 group-data-[collapsible=icon]:hidden">
            <strong class="text-sm leading-none">寻根溯源</strong>
            <span class="text-xs text-muted-foreground">族谱档案工作台</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>总览</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <RouterLink v-slot="{ href, navigate, isActive }" :to="{ name: 'dashboard' }" custom>
                  <SidebarMenuButton
                    as="a"
                    :href="href"
                    :is-active="isActive"
                    tooltip="总览"
                    @click="navigate"
                  >
                    <LayoutDashboardIcon />
                    <span>总览</span>
                  </SidebarMenuButton>
                </RouterLink>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <RouterLink v-slot="{ href, navigate, isActive }" :to="{ name: 'family-tree-list' }" custom>
                  <SidebarMenuButton
                    as="a"
                    :href="href"
                    :is-active="isActive"
                    tooltip="族谱列表"
                    @click="navigate"
                  >
                    <ScrollTextIcon />
                    <span>族谱列表</span>
                  </SidebarMenuButton>
                </RouterLink>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel>当前族谱</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <RouterLink
                  v-if="currentTreeId"
                  v-slot="{ href, navigate, isActive }"
                  :to="{ name: 'family-tree-detail', params: { treeId: currentTreeId } }"
                  custom
                >
                  <SidebarMenuButton
                    as="a"
                    :href="href"
                    :is-active="isActive"
                    tooltip="族谱详情"
                    @click="navigate"
                  >
                    <BookMarkedIcon />
                    <span>族谱详情</span>
                  </SidebarMenuButton>
                </RouterLink>
                <SidebarMenuButton v-else disabled tooltip="族谱详情">
                  <BookMarkedIcon />
                  <span>族谱详情</span>
                </SidebarMenuButton>
              </SidebarMenuItem>

              <SidebarMenuItem>
                <RouterLink
                  v-if="currentTreeId"
                  v-slot="{ href, navigate, isActive }"
                  :to="{ name: 'member-list', params: { treeId: currentTreeId } }"
                  custom
                >
                  <SidebarMenuButton
                    as="a"
                    :href="href"
                    :is-active="isActive"
                    tooltip="成员列表"
                    @click="navigate"
                  >
                    <UsersIcon />
                    <span>成员列表</span>
                  </SidebarMenuButton>
                </RouterLink>
                <SidebarMenuButton v-else disabled tooltip="成员列表">
                  <UsersIcon />
                  <span>成员列表</span>
                </SidebarMenuButton>
              </SidebarMenuItem>

              <SidebarMenuItem>
                <RouterLink
                  v-if="currentTreeId && canManageCollaborators"
                  v-slot="{ href, navigate, isActive }"
                  :to="{ name: 'collaborators', params: { treeId: currentTreeId } }"
                  custom
                >
                  <SidebarMenuButton
                    as="a"
                    :href="href"
                    :is-active="isActive"
                    tooltip="协作者"
                    @click="navigate"
                  >
                    <ShieldCheckIcon />
                    <span>协作者</span>
                  </SidebarMenuButton>
                </RouterLink>
                <SidebarMenuButton v-else disabled tooltip="协作者">
                  <ShieldCheckIcon />
                  <span>协作者</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>查询</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem v-for="item in queryItems" :key="item.name">
                <RouterLink
                  v-if="currentTreeId"
                  v-slot="{ href, navigate, isActive }"
                  :to="{ name: item.name, params: { treeId: currentTreeId } }"
                  custom
                >
                  <SidebarMenuButton
                    as="a"
                    :href="href"
                    :is-active="isActive"
                    :tooltip="item.label"
                    @click="navigate"
                  >
                    <component :is="item.icon" />
                    <span>{{ item.label }}</span>
                  </SidebarMenuButton>
                </RouterLink>
                <SidebarMenuButton v-else disabled :tooltip="item.label">
                  <component :is="item.icon" />
                  <span>{{ item.label }}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div class="grid gap-2 p-2 group-data-[collapsible=icon]:hidden">
          <div v-if="currentTree" class="rounded-md border bg-sidebar-accent/50 p-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium">{{ currentTree.tree_name }}</p>
                <p class="text-xs text-muted-foreground">#{{ currentTree.tree_id }} · {{ currentTree.surname }}</p>
              </div>
              <Badge variant="secondary">{{ roleLabel(currentTree.access_role) }}</Badge>
            </div>
          </div>
          <p v-else class="rounded-md border border-dashed p-3 text-xs text-muted-foreground">
            请选择一棵族谱，继续查看成员和亲缘关系。
          </p>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>

    <SidebarInset class="min-w-0 bg-[linear-gradient(180deg,var(--page-surface)_0%,var(--background)_42%)]">
      <header class="sticky top-0 z-20 flex min-h-16 items-center gap-3 border-b bg-background/85 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/70">
        <SidebarTrigger />
        <Separator orientation="vertical" class="h-6" />

        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium leading-none">{{ pageTitle }}</p>
          <p class="mt-1 truncate text-xs text-muted-foreground">{{ pageDescription }}</p>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" class="hidden max-w-64 justify-between gap-2 md:inline-flex">
              <span class="truncate">{{ currentTree?.tree_name ?? "选择族谱" }}</span>
              <ChevronsUpDownIcon class="size-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-72">
            <DropdownMenuLabel>切换族谱</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem v-if="loadingTrees" disabled>
              <Spinner class="size-4" />
              正在加载族谱
            </DropdownMenuItem>
            <DropdownMenuItem v-else-if="trees.length === 0" disabled>
              暂无可访问族谱
            </DropdownMenuItem>
            <DropdownMenuGroup v-else>
              <DropdownMenuItem
                v-for="tree in trees"
                :key="tree.tree_id"
                class="items-start gap-3"
                @click="selectTree(tree.tree_id)"
              >
                <ScrollTextIcon class="mt-0.5 size-4 text-muted-foreground" />
                <span class="grid min-w-0 gap-1">
                  <span class="truncate font-medium">{{ tree.tree_name }}</span>
                  <span class="truncate text-xs text-muted-foreground">
                    #{{ tree.tree_id }} · {{ tree.surname }} · {{ roleLabel(tree.access_role) }}
                  </span>
                </span>
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        <Badge v-if="currentTree" variant="outline" class="hidden md:inline-flex">
          {{ roleLabel(currentTree.access_role) }}
        </Badge>

        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="icon" aria-label="账户菜单">
              <UserRoundIcon />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-64">
            <DropdownMenuLabel>
              <span class="block truncate">{{ authStore.currentUser?.display_name ?? "当前用户" }}</span>
              <span class="block truncate text-xs font-normal text-muted-foreground">
                {{ authStore.currentUser?.username ?? "" }}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="handleLogout">
              <LogOutIcon />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <div class="flex-1 p-4 md:p-6">
        <Alert v-if="treeLoadError" variant="destructive" class="mb-4">
          <AlertTitle>加载族谱失败</AlertTitle>
          <AlertDescription>{{ treeLoadError }}</AlertDescription>
        </Alert>
        <router-view />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import type { Component } from "vue";
import {
  BookMarkedIcon,
  BookOpenTextIcon,
  ChevronsUpDownIcon,
  GitBranchIcon,
  LayoutDashboardIcon,
  LogOutIcon,
  NetworkIcon,
  RouteIcon,
  ScrollTextIcon,
  SearchIcon,
  ShieldCheckIcon,
  UserRoundIcon,
  UsersIcon
} from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchFamilyTrees, type FamilyTreeListItem } from "@/api/familyTree";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger
} from "@/components/ui/sidebar";
import { Spinner } from "@/components/ui/spinner";
import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";
import { useFamilyTreeStore } from "@/stores/familyTree";

type QueryItem = {
  name: "member-search" | "branch-tree" | "ancestor-query" | "kinship-query";
  label: string;
  icon: Component;
};

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();
const familyTreeStore = useFamilyTreeStore();

const trees = ref<FamilyTreeListItem[]>([]);
const loadingTrees = ref(false);
const treeLoadError = ref("");

const queryItems: QueryItem[] = [
  { name: "member-search", label: "成员搜索", icon: SearchIcon },
  { name: "branch-tree", label: "分支树", icon: GitBranchIcon },
  { name: "ancestor-query", label: "祖先查询", icon: NetworkIcon },
  { name: "kinship-query", label: "亲缘路径", icon: RouteIcon }
];

const routeTreeId = computed(() => {
  const value = Number(route.params.treeId);
  return Number.isFinite(value) && value > 0 ? value : null;
});

const currentTreeId = computed(() => routeTreeId.value ?? appStore.currentTreeId);
const currentTree = computed(() => trees.value.find((tree) => tree.tree_id === currentTreeId.value) ?? null);
const canManageCollaborators = computed(() => currentTree.value?.access_role === "creator");

const pageTitle = computed(() => {
  if (typeof route.name !== "string") {
    return "族谱管理";
  }

  const titles: Record<string, string> = {
    dashboard: "总览",
    "family-tree-list": "族谱列表",
    "family-tree-detail": "族谱详情",
    collaborators: "协作者",
    "member-list": "成员列表",
    "member-detail": "成员详情",
    "member-search": "成员搜索",
    "branch-tree": "分支树",
    "ancestor-query": "祖先查询",
    "kinship-query": "亲缘路径"
  };

  return titles[route.name] ?? "族谱管理";
});

const pageDescription = computed(() => {
  if (currentTree.value) {
    return `${currentTree.value.tree_name} · ${roleLabel(currentTree.value.access_role)}`;
  }

  return "选择族谱后可继续查看成员、统计和亲缘关系。";
});

function roleLabel(role: FamilyTreeListItem["access_role"]) {
  if (role === "creator") {
    return "创建者";
  }
  if (role === "collaborator") {
    return "协作者";
  }
  return "只读";
}

async function loadTrees() {
  loadingTrees.value = true;
  treeLoadError.value = "";

  try {
    const response = await fetchFamilyTrees(1, 100);
    trees.value = response.data.items;

    if (routeTreeId.value) {
      appStore.setCurrentTreeId(routeTreeId.value);
      return;
    }

    const storedTreeExists = trees.value.some((tree) => tree.tree_id === appStore.currentTreeId);
    if (!storedTreeExists) {
      appStore.setCurrentTreeId(trees.value[0]?.tree_id ?? null);
    }
  } catch {
    treeLoadError.value = "暂时无法读取可访问族谱，请稍后重试。";
  } finally {
    loadingTrees.value = false;
  }
}

async function selectTree(treeId: number) {
  appStore.setCurrentTreeId(treeId);
  await router.push({ name: "family-tree-detail", params: { treeId } });
}

async function handleLogout() {
  await authStore.logoutCurrentUser();
  await router.push({ name: "login" });
}

watch(routeTreeId, (treeId) => {
  if (treeId) {
    appStore.setCurrentTreeId(treeId);
  }
});

onMounted(() => {
  void loadTrees();
});

watch(
  () => familyTreeStore.list,
  (list) => {
    if (list.length > 0) {
      trees.value = list;
    }
  },
  { deep: true }
);
</script>

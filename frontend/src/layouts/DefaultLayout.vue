<template>
  <div class="app-shell">
    <header class="panel topbar">
      <div class="topbar__brand">
        <strong>族谱管理系统</strong>
        <span class="muted">阶段二认证与权限基线</span>
      </div>
      <nav class="topbar__nav">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/family-trees">族谱列表</router-link>
      </nav>
      <div class="topbar__actions">
        <span v-if="authStore.currentUser" class="muted">
          {{ authStore.currentUser.display_name }} ({{ authStore.currentUser.username }})
        </span>
        <button class="button button--ghost" type="button" @click="handleLogout">退出登录</button>
      </div>
    </header>
    <main class="page">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const router = useRouter();

async function handleLogout() {
  await authStore.logoutCurrentUser();
  await router.push({ name: "login" });
}
</script>

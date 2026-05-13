<template>
  <section class="auth-card">
    <div>
      <h2>登录</h2>
      <p class="muted">登录后可查看总览、族谱和查询页面。</p>
    </div>

    <form class="auth-form" @submit.prevent="handleSubmit">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="form.username" autocomplete="username" required />
      </label>

      <label class="field">
        <span>密码</span>
        <input v-model="form.password" autocomplete="current-password" minlength="8" required type="password" />
      </label>

      <p v-if="errorMessage" class="feedback feedback--error">{{ errorMessage }}</p>
      <p v-if="authStore.authError" class="feedback feedback--error">{{ authStore.authError }}</p>

      <button class="button" :disabled="submitting" type="submit">
        {{ submitting ? "登录中..." : "登录" }}
      </button>
    </form>

    <p class="muted">
      还没有账号？
      <router-link class="text-link" :to="{ name: 'register', query: route.query.redirect }">去注册</router-link>
    </p>
  </section>
</template>

<script setup lang="ts">
import axios from "axios";
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const submitting = ref(false);
const errorMessage = ref("");
const form = reactive({
  username: "",
  password: ""
});

function resolveRedirect() {
  return typeof route.query.redirect === "string" ? route.query.redirect : "/";
}

async function handleSubmit() {
  submitting.value = true;
  errorMessage.value = "";

  try {
    await authStore.loginWithPassword({
      username: form.username,
      password: form.password
    });
    await router.push(resolveRedirect());
  } catch (error) {
    if (axios.isAxiosError(error)) {
      errorMessage.value = (error.response?.data as { message?: string } | undefined)?.message ?? "登录失败，请检查用户名和密码。";
    } else {
      errorMessage.value = "登录失败，请稍后重试。";
    }
  } finally {
    submitting.value = false;
  }
}
</script>

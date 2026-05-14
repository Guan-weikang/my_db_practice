<template>
  <section class="auth-card">
    <div>
      <h2>注册</h2>
      <p class="muted">注册成功后会自动进入登录态，并跳转回目标页面。</p>
    </div>

    <form class="auth-form" @submit.prevent="handleSubmit">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="form.username" autocomplete="username" required />
      </label>

      <label class="field">
        <span>显示名</span>
        <input v-model.trim="form.display_name" autocomplete="name" required />
      </label>

      <label class="field">
        <span>邮箱</span>
        <input v-model.trim="form.email" autocomplete="email" type="email" />
      </label>

      <label class="field">
        <span>密码</span>
        <input v-model="form.password" autocomplete="new-password" minlength="8" required type="password" />
      </label>

      <label class="field">
        <span>确认密码</span>
        <input v-model="confirmPassword" autocomplete="new-password" minlength="8" required type="password" />
      </label>

      <p v-if="errorMessage" class="feedback feedback--error">{{ errorMessage }}</p>

      <button class="button" :disabled="submitting" type="submit">
        {{ submitting ? "注册中..." : "注册并登录" }}
      </button>
    </form>

    <p class="muted">
      已有账号？
      <router-link class="text-link" :to="{ name: 'login', query: route.query.redirect }">去登录</router-link>
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
const confirmPassword = ref("");
const errorMessage = ref("");
const form = reactive({
  username: "",
  display_name: "",
  email: "",
  password: ""
});

function resolveRedirect() {
  return typeof route.query.redirect === "string" ? route.query.redirect : "/";
}

async function handleSubmit() {
  if (form.password !== confirmPassword.value) {
    errorMessage.value = "两次输入的密码不一致。";
    return;
  }

  submitting.value = true;
  errorMessage.value = "";

  try {
    await authStore.registerAccount({
      username: form.username,
      display_name: form.display_name,
      email: form.email || undefined,
      password: form.password
    });
    await router.push(resolveRedirect());
  } catch (error) {
    if (axios.isAxiosError(error)) {
      errorMessage.value = (error.response?.data as { message?: string } | undefined)?.message ?? "注册失败，请检查输入信息。";
    } else {
      errorMessage.value = "注册失败，请稍后重试。";
    }
  } finally {
    submitting.value = false;
  }
}
</script>

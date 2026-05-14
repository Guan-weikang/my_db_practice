<template>
  <router-view />
  <Toaster position="top-right" rich-colors close-button />
</template>

<script setup lang="ts">
import { Toaster } from "@/components/ui/sonner";
</script>

import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";
import { pinia } from "./stores/pinia";
import "./styles/main.css";

async function bootstrap() {
  const app = createApp(App);
  const authStore = useAuthStore(pinia);

  app.use(pinia);
  await authStore.initialize();
  app.use(router);
  app.mount("#app");
}

void bootstrap();

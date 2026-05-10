import { useAuthStore } from "../stores/auth";

export function useAuth() {
  const store = useAuthStore();
  return {
    store
  };
}


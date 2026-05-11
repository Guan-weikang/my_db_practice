import { useAuthStore } from "../stores/auth";

export function useAuth() {
  const store = useAuthStore();

  return {
    store,
    user: store.currentUser,
    isAuthenticated: store.isAuthenticated
  };
}

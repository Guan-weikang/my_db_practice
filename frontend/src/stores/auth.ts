import { defineStore } from "pinia";

import { fetchMe, login, logout, register, type LoginPayload, type RegisterPayload } from "../api/auth";
import {
  clearAuthSession,
  getStoredAuthSession,
  saveAuthSession,
  subscribeToAuthSession,
  type AuthUser,
  type PersistedAuthSession
} from "../utils/auth-session";

let authSessionListenerRegistered = false;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: "" as string,
    refreshToken: "" as string,
    currentUser: null as AuthUser | null,
    expiresIn: 0,
    initialized: false,
    restoring: false,
    authError: "" as string
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.currentUser)
  },
  actions: {
    applySession(session: PersistedAuthSession | null) {
      this.accessToken = session?.accessToken ?? "";
      this.refreshToken = session?.refreshToken ?? "";
      this.currentUser = session?.currentUser ?? null;
      this.expiresIn = session?.expiresIn ?? 0;
    },
    ensureSessionListener() {
      if (authSessionListenerRegistered) {
        return;
      }

      subscribeToAuthSession((session) => {
        this.applySession(session);
      });
      authSessionListenerRegistered = true;
    },
    async initialize() {
      if (this.initialized || this.restoring) {
        return;
      }

      this.ensureSessionListener();
      this.restoring = true;
      this.authError = "";
      this.applySession(getStoredAuthSession());

      if (!this.refreshToken) {
        this.initialized = true;
        this.restoring = false;
        return;
      }

      try {
        const response = await fetchMe();
        this.currentUser = response.data;
        saveAuthSession({
          accessToken: this.accessToken,
          refreshToken: this.refreshToken,
          currentUser: response.data,
          expiresIn: this.expiresIn
        });
      } catch {
        clearAuthSession();
        this.authError = "登录状态已失效，请重新登录。";
      } finally {
        this.initialized = true;
        this.restoring = false;
      }
    },
    async loginWithPassword(payload: LoginPayload) {
      const response = await login(payload);
      saveAuthSession({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        currentUser: response.data.user,
        expiresIn: response.data.expires_in
      });
      this.authError = "";
      return response.data;
    },
    async registerAccount(payload: RegisterPayload) {
      const response = await register(payload);
      saveAuthSession({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        currentUser: response.data.user,
        expiresIn: response.data.expires_in
      });
      this.authError = "";
      return response.data;
    },
    async logoutCurrentUser() {
      const refreshToken = this.refreshToken;
      try {
        if (refreshToken) {
          await logout({ refresh_token: refreshToken });
        }
      } finally {
        clearAuthSession();
      }
    },
    clearSession() {
      clearAuthSession();
    }
  }
});

import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { clearAuthSession, getStoredAuthSession, saveAuthSession } from "../utils/auth-session";

declare module "axios" {
  interface AxiosRequestConfig {
    skipAuthRefresh?: boolean;
    _retry?: boolean;
  }
}

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
});

const refreshClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
});

let refreshPromise: Promise<string | null> | null = null;

function shouldSkipRefresh(config: InternalAxiosRequestConfig | undefined) {
  if (!config) {
    return true;
  }

  if (config.skipAuthRefresh || config._retry) {
    return true;
  }

  return Boolean(config.url?.includes("/auth/login") || config.url?.includes("/auth/register"));
}

async function refreshAccessToken() {
  const session = getStoredAuthSession();
  if (!session?.refreshToken) {
    clearAuthSession();
    return null;
  }

  const response = await refreshClient.post("/auth/refresh", {
    refresh_token: session.refreshToken
  });
  const payload = response.data;

  saveAuthSession({
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    currentUser: payload.user,
    expiresIn: payload.expires_in
  });

  return payload.access_token as string;
}

client.interceptors.request.use((config) => {
  const session = getStoredAuthSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const responseStatus = error.response?.status;
    const originalRequest = error.config as InternalAxiosRequestConfig | undefined;

    if (responseStatus !== 401 || shouldSkipRefresh(originalRequest)) {
      throw error;
    }

    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    try {
      const nextAccessToken = await refreshPromise;
      if (!nextAccessToken || !originalRequest) {
        clearAuthSession();
        throw error;
      }

      originalRequest._retry = true;
      originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;
      return await client(originalRequest);
    } catch (refreshError) {
      clearAuthSession();
      throw refreshError;
    }
  }
);

export default client;

import client from "./client";
import type { AuthUser } from "../utils/auth-session";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  display_name: string;
  email?: string;
}

export interface AuthSessionResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface RefreshTokenPayload {
  refresh_token: string;
}

export function login(payload: LoginPayload) {
  return client.post<AuthSessionResponse>("/auth/login", payload);
}

export function register(payload: RegisterPayload) {
  return client.post<AuthSessionResponse>("/auth/register", payload);
}

export function refresh(payload: RefreshTokenPayload) {
  return client.post<AuthSessionResponse>("/auth/refresh", payload, {
    skipAuthRefresh: true
  });
}

export function logout(payload: RefreshTokenPayload) {
  return client.post<{ message: string }>("/auth/logout", payload, {
    skipAuthRefresh: true
  });
}

export function fetchMe() {
  return client.get<AuthUser>("/auth/me");
}

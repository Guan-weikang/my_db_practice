import client from "./client";

export function login(payload: { username: string; password: string }) {
  return client.post("/auth/login", payload);
}

export function register(payload: { username: string; password: string; display_name: string; email?: string }) {
  return client.post("/auth/register", payload);
}


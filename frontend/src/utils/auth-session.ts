export interface AuthUser {
  user_id: number;
  username: string;
  display_name: string;
  email: string | null;
  status: string;
  created_at?: string | null;
}

export interface PersistedAuthSession {
  accessToken: string;
  refreshToken: string;
  currentUser: AuthUser | null;
  expiresIn: number;
}

const AUTH_SESSION_STORAGE_KEY = "family-tree-auth-session";
let currentSession: PersistedAuthSession | null = readSessionFromStorage();
const listeners = new Set<(session: PersistedAuthSession | null) => void>();

function isBrowser() {
  return typeof window !== "undefined";
}

function readSessionFromStorage(): PersistedAuthSession | null {
  if (!isBrowser()) {
    return null;
  }

  const rawValue = window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as PersistedAuthSession;
    if (!parsed.accessToken || !parsed.refreshToken) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function notifyListeners() {
  for (const listener of listeners) {
    listener(currentSession);
  }
}

export function getStoredAuthSession(): PersistedAuthSession | null {
  if (!currentSession) {
    currentSession = readSessionFromStorage();
  }
  return currentSession;
}

export function saveAuthSession(session: PersistedAuthSession) {
  currentSession = session;
  if (isBrowser()) {
    window.localStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify(session));
  }
  notifyListeners();
}

export function clearAuthSession() {
  currentSession = null;
  if (isBrowser()) {
    window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  }
  notifyListeners();
}

export function subscribeToAuthSession(listener: (session: PersistedAuthSession | null) => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

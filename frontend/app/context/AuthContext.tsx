"use client";

import { createContext, useContext, useSyncExternalStore } from "react";
import type { ReactNode } from "react";
import { clearLocalSession, setLocalAccountSessionRequired } from "@/lib/api-client/runtime";

interface User {
  businessName: string;
  ownerName: string;
  email: string;
  businessSlug?: string;
}

interface AuthContextType {
  user: User | null;
  login: (user: User, sessionType?: "demo" | "local") => void;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const STORAGE_KEY = "bizsaathi_user";
const CHANGE_EVENT = "bizsaathi-auth-change";

let cachedUserJson: string | null | undefined;
let cachedUser: User | null = null;

function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "businessName" in value &&
    typeof value.businessName === "string" &&
    "ownerName" in value &&
    typeof value.ownerName === "string" &&
    "email" in value &&
    typeof value.email === "string" &&
    (!("businessSlug" in value) || typeof value.businessSlug === "string")
  );
}

function getUserSnapshot(): User | null {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === cachedUserJson) {
    return cachedUser;
  }

  cachedUserJson = stored;
  if (!stored) {
    cachedUser = null;
    return cachedUser;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(stored);
  } catch {
    localStorage.removeItem(STORAGE_KEY);
    cachedUserJson = null;
    cachedUser = null;
    return null;
  }

  if (!isUser(parsed)) {
    localStorage.removeItem(STORAGE_KEY);
    cachedUserJson = null;
    cachedUser = null;
    return null;
  }

  cachedUser = parsed;
  return cachedUser;
}

function subscribeToUser(callback: () => void) {
  const handleStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY || event.key === null) {
      callback();
    }
  };

  window.addEventListener("storage", handleStorage);
  window.addEventListener(CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(CHANGE_EVENT, callback);
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const user = useSyncExternalStore(
    subscribeToUser,
    getUserSnapshot,
    () => null,
  );

  const login = (userData: User, sessionType: "demo" | "local" = "demo") => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    setLocalAccountSessionRequired(sessionType === "local");
    window.dispatchEvent(new Event(CHANGE_EVENT));
  };

  const logout = async () => {
    await clearLocalSession();
    localStorage.removeItem(STORAGE_KEY);
    setLocalAccountSessionRequired(false);
    window.dispatchEvent(new Event(CHANGE_EVENT));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

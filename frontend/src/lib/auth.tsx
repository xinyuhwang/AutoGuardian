"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ApiError } from "@/lib/api";

export type User = { id: number; email: string };

type AuthState = {
  /** undefined = still checking, null = logged out */
  user: User | null | undefined;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null | undefined>(undefined);

  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch((error) => {
        // 401 just means "not logged in"; anything else is also treated as logged out.
        if (!(error instanceof ApiError && error.status === 401)) console.error(error);
        setUser(null);
      });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setUser(await api<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }));
  }, []);

  const signup = useCallback(async (email: string, password: string) => {
    setUser(await api<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }));
  }, []);

  const logout = useCallback(async () => {
    await api<void>("/auth/logout", { method: "POST" });
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}

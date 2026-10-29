"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import type { Utilisateur } from "@/lib/types";

type AuthContextValue = {
  user: Utilisateur | null;
  loading: boolean;
  setUser: (user: Utilisateur | null) => void;
  refreshUser: () => Promise<Utilisateur | null>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Utilisateur | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const response = await fetch("/api/auth/session", {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!response.ok) {
        setUser(null);
        return null;
      }
      const account = (await response.json()) as Utilisateur;
      setUser(account);
      return account;
    } catch {
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshUser();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshUser]);

  const signOut = useCallback(async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "same-origin",
    });
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, setUser, refreshUser, signOut }),
    [user, loading, refreshUser, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth doit être utilisé dans AuthProvider.");
  return context;
}

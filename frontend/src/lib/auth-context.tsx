"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { supabase } from "./supabase";

export interface User {
  id: string;
  email: string;
  business_id: string;
  business_name: string;
  access_token: string;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  logout: () => Promise<void>;
  login: (u: User) => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  logout: async () => {},
  login: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("engagesphere_user");
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  const login = (u: User) => {
    localStorage.setItem("engagesphere_user", JSON.stringify(u));
    setUser(u);
  };

  const logout = async () => {
    localStorage.removeItem("engagesphere_user");
    setUser(null);
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, login }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

// Keep for backward compat
export function saveUser(user: User) {
  localStorage.setItem("engagesphere_user", JSON.stringify(user));
}

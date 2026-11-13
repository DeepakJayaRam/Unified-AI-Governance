"use client";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { makeApi } from "@/lib/api";
export type Membership = {
  tenant_id: string;
  tenant_name: string;
  role: string;
};
export type LoginData = {
  access_token: string;
  user: { id: string; email: string; name: string; platform_admin?: boolean };
  memberships: Membership[];
};
type Session = {
  data: LoginData | null;
  tenant: string;
  setTenant: (id: string) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshIdentity: () => Promise<void>;
  api: ReturnType<typeof makeApi>;
};
const Context = createContext<Session | null>(null);
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<LoginData | null>(null);
  const [tenant, setTenant] = useState("");
  const expire = useCallback(() => {
    setData(null);
    setTenant("");
  }, []);
  const api = useMemo(
    () => makeApi(data?.access_token || "", tenant, expire),
    [data?.access_token, tenant, expire],
  );
  const login = async (email: string, password: string) => {
    const result = await makeApi("", "")<LoginData>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setData(result);
    setTenant(result.memberships?.[0]?.tenant_id || "");
  };
  const logout = async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } finally {
      expire();
    }
  };
  const refreshIdentity = async () => {
    const identity = await api<Omit<LoginData, "access_token">>("/auth/me");
    setData((current) => (current ? { ...current, ...identity } : null));
    if (!identity.memberships.some((m) => m.tenant_id === tenant))
      setTenant(identity.memberships[0]?.tenant_id || "");
  };
  return (
    <Context.Provider
      value={{ data, tenant, setTenant, login, logout, api, refreshIdentity }}
    >
      {children}
    </Context.Provider>
  );
}
export function useSession() {
  const session = useContext(Context);
  if (!session) throw new Error("Session provider missing");
  return session;
}

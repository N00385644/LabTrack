import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api, clearSession, getStoredToken, getStoredUser, storeSession } from '../lib/api';
import type { User } from '../lib/types';

export interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (code: string, password: string) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  readonly children: ReactNode;
  readonly initialUser?: User | null;
  readonly initialToken?: string | null;
}

export function AuthProvider({ children, initialUser = null, initialToken = null }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(() => initialUser ?? getStoredUser());
  const [token, setToken] = useState<string | null>(() => initialToken ?? getStoredToken());
  const [loading, setLoading] = useState<boolean>(() => Boolean((initialToken ?? getStoredToken()) && !initialUser));

  useEffect(() => {
    if (!token || initialUser) {
      setLoading(false);
      return;
    }
    let active = true;
    api
      .me()
      .then(({ user: freshUser }) => {
        if (active) {
          setUser(freshUser);
          storeSession(token, freshUser);
        }
      })
      .catch(() => {
        if (active) {
          clearSession();
          setUser(null);
          setToken(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, initialUser]);

  const login = useCallback(async (code: string, password: string) => {
    const response = await api.login(code, password);
    storeSession(response.accessToken, response.user);
    setToken(response.accessToken);
    setUser(response.user);
    return response.user;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    const response = await api.me();
    setUser(response.user);
    if (token) storeSession(token, response.user);
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, loading, login, logout, refresh }),
    [user, token, loading, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
}

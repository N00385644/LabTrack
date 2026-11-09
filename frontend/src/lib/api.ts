import type {
  AdminStats,
  AuditEvent,
  CatalogStats,
  Equipment,
  LoginResponse,
  Reservation,
  User,
} from './types';

export const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:3000/api';

const TOKEN_KEY = 'labtrack_token';
const USER_KEY = 'labtrack_user';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function storeSession(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) {
    headers.set('Content-Type', 'application/json');
  }
  const token = getStoredToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor de LabTrack.');
  }

  const payload = (await response.json().catch(() => null)) as
    | { message?: string | string[]; code?: string }
    | null;

  if (!response.ok) {
    let message = payload?.message ?? 'Ocurrió un error inesperado.';
    if (Array.isArray(message)) {
      message = message.join(' ');
    }
    if (response.status === 401 && !path.includes('/auth/login')) {
      message = 'Tu sesión expiró. Inicia sesión nuevamente.';
    }
    throw new ApiError(response.status, message, payload?.code);
  }

  return payload as T;
}

export const api = {
  login(code: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ code, password }),
    });
  },

  me(): Promise<{ user: User }> {
    return request<{ user: User }>('/auth/me');
  },

  equipment: {
    list(category?: string): Promise<Equipment[]> {
      const query = category ? `?category=${encodeURIComponent(category)}` : '';
      return request<Equipment[]>(`/equipment${query}`);
    },
    available(): Promise<Equipment[]> {
      return request<Equipment[]>('/equipment/available');
    },
    stats(): Promise<CatalogStats> {
      return request<CatalogStats>('/equipment/stats');
    },
  },

  reservations: {
    mine(): Promise<Reservation[]> {
      return request<Reservation[]>('/reservations/me');
    },
    create(input: {
      equipmentId: string;
      date: string;
      startTime: string;
      endTime: string;
    }): Promise<Reservation> {
      return request<Reservation>('/reservations', {
        method: 'POST',
        body: JSON.stringify(input),
      });
    },
  },

  admin: {
    stats(): Promise<AdminStats> {
      return request<AdminStats>('/admin/stats');
    },
    reservations(status: string): Promise<Reservation[]> {
      return request<Reservation[]>(`/admin/reservations?status=${status}`);
    },
    audit(limit = 20): Promise<AuditEvent[]> {
      return request<AuditEvent[]>(`/admin/audit?limit=${limit}`);
    },
    approve(id: string): Promise<Reservation> {
      return request<Reservation>(`/admin/reservations/${id}/approve`, {
        method: 'PATCH',
      });
    },
    reject(id: string, reason: string): Promise<Reservation> {
      return request<Reservation>(`/admin/reservations/${id}/reject`, {
        method: 'PATCH',
        body: JSON.stringify({ reason }),
      });
    },
    markReturned(id: string): Promise<Reservation & { late: boolean }> {
      return request<Reservation & { late: boolean }>(
        `/admin/reservations/${id}/return`,
        { method: 'PATCH' },
      );
    },
  },
};

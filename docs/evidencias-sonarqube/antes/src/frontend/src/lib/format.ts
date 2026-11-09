import type { Reservation, ReservationStatus } from './types';

export const STATUS_LABELS: Record<ReservationStatus, string> = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  RETURNED: 'Devuelta',
};

export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.slice(0, 10).split('-');
  return `${day}/${month}/${year}`;
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  return date.toLocaleString('es-PE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function isOverdue(reservation: Reservation): boolean {
  if (reservation.status !== 'APPROVED') return false;
  const end = new Date(`${reservation.date}T${reservation.endTime}:00`);
  return Date.now() > end.getTime();
}

export function tomorrow(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function today(): string {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export const AUDIT_LABELS: Record<string, string> = {
  LOGIN_SUCCESS: 'Inicio de sesión',
  LOGIN_FAILED: 'Intento fallido',
  LOGIN_LOCKED: 'Cuenta bloqueada',
  LOGIN_BLOCKED: 'Acceso bloqueado',
  RESERVATION_CREATED: 'Reserva creada',
  RESERVATION_APPROVED: 'Reserva aprobada',
  RESERVATION_REJECTED: 'Reserva rechazada',
  RESERVATION_RETURNED: 'Devolución registrada',
  PENALTY_APPLIED: 'Penalización aplicada',
};

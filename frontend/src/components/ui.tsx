import { useEffect, type ReactNode } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Inbox,
  Loader2,
  RotateCcw,
  X,
  XCircle,
} from 'lucide-react';
import type { EquipmentStatus, ReservationStatus } from '../lib/types';
import { STATUS_LABELS } from '../lib/format';

const RESERVATION_STYLES: Record<ReservationStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-800 ring-1 ring-inset ring-amber-200',
  APPROVED: 'bg-sky-100 text-sky-800 ring-1 ring-inset ring-sky-200',
  REJECTED: 'bg-red-100 text-red-800 ring-1 ring-inset ring-red-200',
  RETURNED: 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200',
};

const RESERVATION_ICONS: Record<ReservationStatus, ReactNode> = {
  PENDING: <Clock3 className="h-3.5 w-3.5" />,
  APPROVED: <CheckCircle2 className="h-3.5 w-3.5" />,
  REJECTED: <XCircle className="h-3.5 w-3.5" />,
  RETURNED: <RotateCcw className="h-3.5 w-3.5" />,
};

export function StatusBadge({ status }: Readonly<{ status: ReservationStatus }>) {
  return (
    <span className={`badge ${RESERVATION_STYLES[status]}`} data-testid={`status-${status.toLowerCase()}`}>
      {RESERVATION_ICONS[status]}
      {STATUS_LABELS[status]}
    </span>
  );
}

export function EquipmentStatusBadge({ status }: Readonly<{ status: EquipmentStatus }>) {
  const available = status === 'AVAILABLE';
  return (
    <span
      className={`badge ${
        available
          ? 'bg-emerald-100 text-emerald-800 ring-1 ring-inset ring-emerald-200'
          : 'bg-amber-100 text-amber-800 ring-1 ring-inset ring-amber-200'
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${available ? 'bg-emerald-500' : 'bg-amber-500'}`} />
      {available ? 'Disponible' : 'Prestado'}
    </span>
  );
}

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  actions,
}: Readonly<{
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}>) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">{eyebrow}</p>
        ) : null}
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-navy-950 sm:text-3xl">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-2xl text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

const TONE_STYLES = {
  navy: 'bg-navy-50 text-navy-700',
  teal: 'bg-teal-50 text-teal-700',
  amber: 'bg-amber-50 text-amber-700',
  rose: 'bg-rose-50 text-rose-700',
} as const;

export function StatCard({
  label,
  value,
  icon,
  tone = 'navy',
  hint,
}: Readonly<{
  label: string;
  value: number | string;
  icon: ReactNode;
  tone?: keyof typeof TONE_STYLES;
  hint?: string;
}>) {
  return (
    <div className="card flex items-center gap-4 p-4">
      <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${TONE_STYLES[tone]}`}>
        {icon}
      </span>
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <p className="text-2xl font-bold leading-tight text-navy-950">{value}</p>
        {hint ? <p className="truncate text-xs text-slate-500">{hint}</p> : null}
      </div>
    </div>
  );
}

export function LoadingBlock({ label = 'Cargando información…' }: Readonly<{ label?: string }>) {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 p-12 text-slate-500">
      <Loader2 className="h-7 w-7 animate-spin text-teal-600" />
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}

export function FullPageLoader() {
  return (
    <div className="grid min-h-screen place-items-center bg-slate-100">
      <div className="flex flex-col items-center gap-3 text-slate-500">
        <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
        <p className="text-sm font-medium">Verificando sesión…</p>
      </div>
    </div>
  );
}

export function ErrorAlert({
  message,
  onRetry,
}: Readonly<{
  message: string;
  onRetry?: () => void;
}>) {
  return (
    <div
      role="alert"
      data-testid="error-alert"
      className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between"
    >
      <span className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{message}</span>
      </span>
      {onRetry ? (
        <button type="button" className="btn-ghost btn-sm shrink-0" onClick={onRetry}>
          Reintentar
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  title,
  message,
  icon,
  action,
  testId,
}: Readonly<{
  title: string;
  message?: string;
  icon?: ReactNode;
  action?: ReactNode;
  testId?: string;
}>) {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center" data-testid={testId}>
      <span className="grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-400">
        {icon ?? <Inbox className="h-6 w-6" />}
      </span>
      <div>
        <p className="font-semibold text-slate-800">{title}</p>
        {message ? <p className="mt-1 text-sm text-slate-500">{message}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Modal({
  open,
  title,
  subtitle,
  onClose,
  children,
  footer,
}: Readonly<{
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}>) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        aria-label="Cerrar modal"
        onClick={onClose}
        className="absolute inset-0 bg-navy-950/50 backdrop-blur-sm"
      />
      <dialog
        open
        aria-modal="true"
        aria-label={title}
        className="relative m-0 w-full max-w-lg animate-fade-up rounded-2xl border-0 bg-white p-0 shadow-lift"
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-navy-950">{title}</h2>
            {subtitle ? <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
        {footer ? (
          <div className="flex flex-wrap justify-end gap-2 rounded-b-2xl border-t border-slate-200 bg-slate-50 px-5 py-3">
            {footer}
          </div>
        ) : null}
      </dialog>
    </div>
  );
}

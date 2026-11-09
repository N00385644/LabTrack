import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock3,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDate, formatDateTime } from '../lib/format';
import type { Reservation, ReservationStatus } from '../lib/types';
import { useAuth } from '../contexts/AuthContext';
import { EmptyState, ErrorAlert, LoadingBlock, PageHeader, StatusBadge } from '../components/ui';

const MONTHS_SHORT = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SET', 'OCT', 'NOV', 'DIC'];

const FILTERS = [
  { value: 'ALL', label: 'Todas' },
  { value: 'PENDING', label: 'Pendientes' },
  { value: 'APPROVED', label: 'Aprobadas' },
  { value: 'REJECTED', label: 'Rechazadas' },
  { value: 'RETURNED', label: 'Devueltas' },
] as const;

type FilterValue = (typeof FILTERS)[number]['value'];

export default function MyReservationsPage() {
  const { user } = useAuth();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [filter, setFilter] = useState<FilterValue>('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.reservations.mine();
      setReservations(data);
      setError('');
    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught
      setError(caught instanceof Error ? caught.message : 'No se pudieron cargar tus reservas.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const counts = useMemo(() => {
    const base: Record<string, number> = { ALL: reservations.length };
    for (const status of ['PENDING', 'APPROVED', 'REJECTED', 'RETURNED'] as ReservationStatus[]) {
      base[status] = reservations.filter((reservation) => reservation.status === status).length;
    }
    return base;
  }, [reservations]);

  const visible = useMemo(
    () => (filter === 'ALL' ? reservations : reservations.filter((item) => item.status === filter)),
    [filter, reservations],
  );

  return (
    <div>
      <PageHeader
        eyebrow="HU-03 · Seguimiento"
        title="Mis reservas"
        subtitle="Consulta el estado de cada solicitud, los motivos de rechazo y las penalizaciones asociadas a tus devoluciones."
        actions={
          <button type="button" onClick={() => void load()} className="btn-ghost" data-testid="reservations-refresh">
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </button>
        }
      />

      {user?.status === 'PENALIZED' ? (
        <div
          role="alert"
          data-testid="penalty-banner"
          className="mb-5 flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        >
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">Tu cuenta está penalizada</p>
            <p className="text-xs">
              Registramos una devolución fuera del horario acordado. Contacta al encargado del
              laboratorio para regularizar tu situación antes de registrar nuevas reservas.
            </p>
          </div>
        </div>
      ) : null}

      {/* DEFECTO SEMBRADO (demostracion) S6819 - role="group" en div nativo */}
      <div role="group" aria-label="Filtrar mis reservas" className="mb-4 flex flex-wrap gap-2">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            type="button"
            aria-pressed={filter === item.value}
            data-testid={`my-filter-${item.value.toLowerCase()}`}
            onClick={() => setFilter(item.value)}
            className={`inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold transition ${
              filter === item.value
                ? 'bg-navy-900 text-white shadow-sm'
                : 'border border-slate-200 bg-white text-slate-600 hover:border-teal-300'
            }`}
          >
            {item.label}
            <span
              className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                filter === item.value ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'
              }`}
            >
              {counts[item.value] ?? 0}
            </span>
          </button>
        ))}
      </div>

      {error ? <ErrorAlert message={error} onRetry={() => void load()} /> : null}

      {loading ? <LoadingBlock label="Cargando tus reservas…" /> : null}

      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading
        ? visible.length === 0
          ? (
              <EmptyState
                testId="empty-reservations"
                icon={<ClipboardList className="h-6 w-6" />}
                title={
                  filter === 'ALL'
                    ? 'Todavía no tienes reservas registradas'
                    : 'No tienes reservas con este estado'
                }
                message="Cuando solicites un equipo, podrás seguir aquí su aprobación y devolución."
                action={
                  <Link to="/catalogo" className="btn-teal btn-sm mt-1">
                    Explorar catálogo
                  </Link>
                }
              />
            )
          : null
        : null}

      {!loading && visible.length > 0 ? (
        <div className="space-y-3" data-testid="my-reservations-list">
          {visible.map((reservation) => {
            const [year, month, day] = reservation.date.slice(0, 10).split('-');
            const monthLabel = MONTHS_SHORT[Math.max(0, Number(month) - 1)] ?? '';
            return (
              <article
                key={reservation.id}
                data-testid="reservation-row"
                className="card animate-fade-up p-5"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex gap-4">
                    <div className="flex h-16 w-16 shrink-0 flex-col items-center justify-center rounded-xl bg-navy-50 text-navy-900">
                      <span className="text-xl font-bold leading-none">{day}</span>
                      <span className="mt-1 text-[10px] font-bold tracking-wider">{monthLabel}</span>
                      <span className="text-[10px] text-slate-500">{year}</span>
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="font-semibold text-navy-950">{reservation.equipment.name}</h2>
                        <StatusBadge status={reservation.status} />
                      </div>
                      <p className="mt-0.5 font-mono text-xs font-semibold text-teal-700">
                        {reservation.equipment.inventoryCode} · {reservation.equipment.category}
                      </p>
                      <p className="mt-1.5 inline-flex items-center gap-1.5 text-sm text-slate-600">
                        <Clock3 className="h-4 w-4 text-slate-400" />
                        {reservation.startTime} – {reservation.endTime}
                      </p>
                    </div>
                  </div>

                  <div className="text-xs leading-relaxed text-slate-500 sm:text-right">
                    <p className="inline-flex items-center gap-1">
                      <CalendarDays className="h-3.5 w-3.5" />
                      Solicitada: {formatDateTime(reservation.createdAt)}
                    </p>
                    {reservation.reviewedBy ? (
                      <p>
                        Revisada por <span className="font-medium text-slate-600">{reservation.reviewedBy}</span>
                      </p>
                    ) : (
                      <p>En espera de revisión</p>
                    )}
                  </div>
                </div>

                {reservation.status === 'REJECTED' && reservation.rejectionReason ? (
                  <div
                    data-testid="rejection-reason"
                    className="mt-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
                  >
                    <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>
                      <strong className="font-semibold">Motivo del rechazo:</strong>{' '}
                      {reservation.rejectionReason}
                    </span>
                  </div>
                ) : null}

                {reservation.status === 'RETURNED' ? (
                  <div
                    className={`mt-4 flex items-start gap-2 rounded-xl border px-4 py-3 text-sm ${
                      reservation.penaltyApplied
                        ? 'border-amber-200 bg-amber-50 text-amber-800'
                        : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                    }`}
                  >
                    {reservation.penaltyApplied ? (
                      <>
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                        <span>
                          <strong className="font-semibold">Devolución tardía.</strong> Se aplicó una
                          penalización automática a tu cuenta el {formatDateTime(reservation.returnedAt)}.
                        </span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                        <span>Equipo devuelto en plazo el {formatDateTime(reservation.returnedAt)}.</span>
                      </>
                    )}
                  </div>
                ) : null}

                {reservation.status === 'APPROVED' ? (
                  <p className="mt-3 text-xs text-slate-500">
                    Presenta tu código de estudiante al recoger el equipo en {reservation.equipment.location}.
                    Fecha de uso: {formatDate(reservation.date)}.
                  </p>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

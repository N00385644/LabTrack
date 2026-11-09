import { useCallback, useEffect, useState } from 'react';
import { CalendarDays, FileClock, History, ListChecks, RefreshCw, ShieldCheck } from 'lucide-react';
import { api } from '../lib/api';
import { AUDIT_LABELS, formatDate, formatDateTime } from '../lib/format';
import type { AuditEvent, Reservation } from '../lib/types';
import {
  EmptyState,
  ErrorAlert,
  LoadingBlock,
  PageHeader,
  StatusBadge,
} from '../components/ui';

type Tab = 'reservations' | 'audit';

function auditTone(event: string): string {
  if (event === 'LOGIN_FAILED' || event === 'LOGIN_BLOCKED') return 'bg-amber-500';
  if (event === 'LOGIN_LOCKED' || event === 'RESERVATION_REJECTED' || event === 'PENALTY_APPLIED') {
    return 'bg-red-500';
  }
  if (event === 'LOGIN_SUCCESS' || event === 'RESERVATION_APPROVED' || event === 'RESERVATION_RETURNED') {
    return 'bg-emerald-500';
  }
  return 'bg-sky-500';
}

export default function AdminHistoryPage() {
  const [tab, setTab] = useState<Tab>('reservations');
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [allReservations, events] = await Promise.all([
        api.admin.reservations('ALL'),
        api.admin.audit(60),
      ]);
      setReservations(allReservations);
      setAudit(events);
      setError('');
    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught
      setError(caught instanceof Error ? caught.message : 'No se pudo cargar el historial.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <PageHeader
        eyebrow="Trazabilidad · Auditoría"
        title="Historial del laboratorio"
        subtitle={
          // DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado
          tab === 'reservations'
            ? `${reservations.length} reservas registradas`
            : tab === 'audit'
              ? `${audit.length} eventos de auditoría`
              : 'Historial del laboratorio'
        }
        actions={
          <button type="button" onClick={() => void load()} className="btn-ghost" data-testid="history-refresh">
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </button>
        }
      />

      <div className="mb-4 inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
        <button
          type="button"
          onClick={() => setTab('reservations')}
          data-testid="tab-reservations"
          className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold transition ${
            tab === 'reservations' ? 'bg-navy-900 text-white shadow-sm' : 'text-slate-600 hover:text-navy-900'
          }`}
        >
          <ListChecks className="h-4 w-4" />
          Reservas ({reservations.length})
        </button>
        <button
          type="button"
          onClick={() => setTab('audit')}
          data-testid="tab-audit"
          className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold transition ${
            tab === 'audit' ? 'bg-navy-900 text-white shadow-sm' : 'text-slate-600 hover:text-navy-900'
          }`}
        >
          <FileClock className="h-4 w-4" />
          Bitácora ({audit.length})
        </button>
      </div>

      {error ? <ErrorAlert message={error} onRetry={() => void load()} /> : null}

      {loading ? <LoadingBlock label="Cargando historial…" /> : null}

      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading && tab === 'reservations'
        ? reservations.length === 0
          ? (
              <EmptyState
                icon={<History className="h-6 w-6" />}
                title="Todavía no hay reservas registradas"
                message="Las solicitudes de los estudiantes aparecerán en este historial."
              />
            )
          : null
        : null}

      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading && tab === 'reservations'
        ? reservations.length > 0
          ? (
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="table-head">
                  <tr>
                    <th className="px-5 py-3">Fecha</th>
                    <th className="px-5 py-3">Estudiante</th>
                    <th className="px-5 py-3">Equipo</th>
                    <th className="px-5 py-3">Horario</th>
                    <th className="px-5 py-3">Estado</th>
                    <th className="px-5 py-3">Revisión</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {reservations.map((reservation) => (
                    <tr key={reservation.id} className="transition hover:bg-slate-50/70">
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 text-slate-700">
                          <CalendarDays className="h-3.5 w-3.5 text-slate-400" />
                          {formatDate(reservation.date)}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <p className="font-medium text-slate-800">{reservation.student.fullName}</p>
                        <p className="font-mono text-xs text-slate-500">{reservation.student.code}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="text-slate-800">{reservation.equipment.name}</p>
                        <p className="font-mono text-xs font-semibold text-teal-700">
                          {reservation.equipment.inventoryCode}
                        </p>
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-slate-700">
                        {reservation.startTime} – {reservation.endTime}
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge status={reservation.status} />
                      </td>
                      <td className="px-5 py-4 text-xs text-slate-500">
                        {reservation.reviewedBy ?? 'Sin revisar'}
                        {reservation.reviewedAt ? (
                          <span className="block text-[11px] text-slate-400">
                            {formatDateTime(reservation.reviewedAt)}
                          </span>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
            )
          : null
        : null}

      {!loading && tab === 'audit' && audit.length === 0 ? (
        <EmptyState
          icon={<ShieldCheck className="h-6 w-6" />}
          title="La bitácora está vacía"
          message="Los eventos de login, reservas, aprobaciones y devoluciones se registrarán aquí."
        />
      ) : null}

      {!loading && tab === 'audit' && audit.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
            <ShieldCheck className="h-4 w-4 text-teal-600" />
            <h2 className="font-semibold text-navy-950">Bitácora de auditoría</h2>
            <span className="ml-auto text-xs text-slate-500">Últimos {audit.length} eventos</span>
          </div>
          <ol className="divide-y divide-slate-100">
            {audit.map((event) => (
              <li key={event.id} className="flex gap-3 px-5 py-3.5">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${auditTone(event.event)}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-slate-800">
                      {AUDIT_LABELS[event.event] ?? event.event}
                    </p>
                    <span className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
                      {event.event}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">{event.detail || 'Sin detalle registrado.'}</p>
                  <p className="mt-0.5 text-[11px] text-slate-400">
                    {formatDateTime(event.createdAt)} · Actor: {event.actorCode || 'sistema'} · IP:{' '}
                    {event.ipAddress || '—'}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </div>
  );
}

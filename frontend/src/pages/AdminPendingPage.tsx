import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Loader2,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  XCircle,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDate } from '../lib/format';
import type { AdminStats, Reservation } from '../lib/types';
import { useToast } from '../contexts/ToastContext';
import {
  EmptyState,
  ErrorAlert,
  LoadingBlock,
  Modal,
  PageHeader,
  StatCard,
} from '../components/ui';

export default function AdminPendingPage() {
  const toast = useToast();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectTarget, setRejectTarget] = useState<Reservation | null>(null);
  const [reason, setReason] = useState('');
  const [rejectError, setRejectError] = useState('');
  const [rejecting, setRejecting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pending, metrics] = await Promise.all([
        api.admin.reservations('PENDING'),
        api.admin.stats(),
      ]);
      setReservations(pending);
      setStats(metrics);
      setError('');
    } catch (error_) {
      setError(error_ instanceof Error ? error_.message : 'No se pudieron cargar las solicitudes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleApprove = async (reservation: Reservation) => {
    setProcessingId(reservation.id);
    try {
      await api.admin.approve(reservation.id);
      toast.push(
        `Reserva de ${reservation.student.fullName} aprobada. El equipo quedó marcado como prestado.`,
        'success',
      );
      await load();
    } catch (error_) {
      toast.push(error_ instanceof Error ? error_.message : 'No se pudo aprobar la reserva.', 'error');
    } finally {
      setProcessingId(null);
    }
  };

  const openReject = (reservation: Reservation) => {
    setRejectTarget(reservation);
    setReason('');
    setRejectError('');
  };

  const handleReject = async () => {
    if (!rejectTarget) return;
    const cleanReason = reason.trim();
    if (cleanReason.length < 5) {
      setRejectError('Debes ingresar un motivo de rechazo de al menos 5 caracteres.');
      return;
    }
    setRejecting(true);
    setRejectError('');
    try {
      await api.admin.reject(rejectTarget.id, cleanReason);
      toast.push('Solicitud rechazada. El estudiante podrá ver el motivo en su panel.', 'warning');
      setRejectTarget(null);
      await load();
    } catch (error_) {
      setRejectError(error_ instanceof Error ? error_.message : 'No se pudo rechazar la solicitud.');
    } finally {
      setRejecting(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="HU-04 · Panel de administrador"
        title="Solicitudes pendientes"
        subtitle="Revisa las reservas solicitadas por los estudiantes, aprueba las viables o rechaza indicando un motivo obligatorio."
        actions={
          <button type="button" onClick={() => void load()} className="btn-ghost" data-testid="pending-refresh">
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </button>
        }
      />

      <section className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores administrativos">
        <StatCard
          label="Pendientes"
          value={stats?.pending ?? '—'}
          icon={<ClipboardCheck className="h-5 w-5" />}
          tone="rose"
          hint="Requieren revisión"
        />
        <StatCard
          label="Aprobadas"
          value={stats?.approved ?? '—'}
          icon={<CheckCircle2 className="h-5 w-5" />}
          tone="teal"
          hint="Préstamos activos"
        />
        <StatCard
          label="Devoluciones hoy"
          value={stats?.returnsToday ?? '—'}
          icon={<RotateCcw className="h-5 w-5" />}
          tone="navy"
          hint="Equipos reintegrados"
        />
        <StatCard
          label="Penalizados"
          value={stats?.penalized ?? '—'}
          icon={<ShieldAlert className="h-5 w-5" />}
          tone="amber"
          hint="Estudiantes sancionados"
        />
      </section>

      {error ? <ErrorAlert message={error} onRetry={() => void load()} /> : null}

      {loading ? <LoadingBlock label="Cargando solicitudes pendientes…" /> : null}

      {!loading && reservations.length === 0 ? (
        <EmptyState
          testId="empty-pending"
          icon={<CheckCircle2 className="h-6 w-6" />}
          title="No hay solicitudes pendientes"
          message="Todas las reservas han sido revisadas. Las nuevas solicitudes aparecerán aquí."
        />
      ) : null}

      {!loading && reservations.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <h2 className="flex items-center gap-2 font-semibold text-navy-950">
              <Clock3 className="h-4 w-4 text-amber-500" />
              {reservations.length} solicitud{reservations.length === 1 ? '' : 'es'} en espera
            </h2>
            <span className="text-xs text-slate-500">Ordenadas por fecha de uso</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="table-head">
                <tr>
                  <th className="px-5 py-3">Estudiante</th>
                  <th className="px-5 py-3">Equipo</th>
                  <th className="px-5 py-3">Fecha de uso</th>
                  <th className="px-5 py-3">Horario</th>
                  <th className="px-5 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reservations.map((reservation) => {
                  const busy = processingId === reservation.id;
                  return (
                    <tr
                      key={reservation.id}
                      data-testid="pending-row"
                      className="transition hover:bg-slate-50/70"
                    >
                      <td className="px-5 py-4">
                        <p className="font-semibold text-navy-950">{reservation.student.fullName}</p>
                        <p className="font-mono text-xs text-slate-500">{reservation.student.code}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="font-medium text-slate-800">{reservation.equipment.name}</p>
                        <p className="text-xs text-slate-500">
                          <span className="font-mono font-semibold text-teal-700">
                            {reservation.equipment.inventoryCode}
                          </span>{' '}
                          · {reservation.equipment.category}
                        </p>
                      </td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 text-slate-700">
                          <CalendarDays className="h-3.5 w-3.5 text-slate-400" />
                          {formatDate(reservation.date)}
                        </span>
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-slate-700">
                        {reservation.startTime} – {reservation.endTime}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => void handleApprove(reservation)}
                            disabled={busy}
                            data-action="approve"
                            data-testid={`approve-${reservation.id}`}
                            className="btn-teal btn-sm"
                          >
                            {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                            Aprobar
                          </button>
                          <button
                            type="button"
                            onClick={() => openReject(reservation)}
                            disabled={busy}
                            data-action="reject"
                            data-testid={`reject-${reservation.id}`}
                            className="btn-ghost btn-sm text-red-700 hover:border-red-300 hover:bg-red-50"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            Rechazar
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      <Modal
        open={Boolean(rejectTarget)}
        title="Rechazar solicitud"
        subtitle={
          rejectTarget
            ? `${rejectTarget.student.fullName} · ${rejectTarget.equipment.name}`
            : undefined
        }
        onClose={() => setRejectTarget(null)}
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={() => setRejectTarget(null)} disabled={rejecting}>
              Cancelar
            </button>
            <button
              type="button"
              className="btn-danger"
              onClick={() => void handleReject()}
              disabled={rejecting}
              data-testid="reject-confirm"
            >
              {rejecting ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
              Confirmar rechazo
            </button>
          </>
        }
      >
        <p className="mb-2 text-sm text-slate-600">
          El motivo es obligatorio y será visible para el estudiante en su panel de reservas.
        </p>
        <label htmlFor="reject-reason" className="label">
          Motivo del rechazo
        </label>
        <textarea
          id="reject-reason"
          value={reason}
          onChange={(event) => {
            setReason(event.target.value);
            if (rejectError) setRejectError('');
          }}
          rows={3}
          maxLength={300}
          placeholder="Ej. Equipo en mantenimiento preventivo"
          className="input resize-none"
          data-testid="reject-reason"
        />
        <div className="mt-1 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">Mínimo 5 caracteres.</span>
          <span className="text-[11px] text-slate-400">{reason.trim().length}/300</span>
        </div>
        {rejectError ? (
          <p
            role="alert"
            data-testid="reject-error"
            className="mt-2 flex items-start gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-800"
          >
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {rejectError}
          </p>
        ) : null}
      </Modal>
    </div>
  );
}

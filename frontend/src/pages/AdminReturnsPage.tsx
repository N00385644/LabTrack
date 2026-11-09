import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Loader2,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldAlert,
  Undo2,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDate } from '../lib/format';
import type { Reservation } from '../lib/types';
import { useToast } from '../contexts/ToastContext';
import {
  EmptyState,
  ErrorAlert,
  LoadingBlock,
  Modal,
  PageHeader,
} from '../components/ui';

function minutesLate(reservation: Reservation): number {
  const end = new Date(`${reservation.date}T${reservation.endTime}:00`);
  return Math.max(0, Math.floor((Date.now() - end.getTime()) / 60_000));
}

function lateLabel(minutes: number): string {
  if (minutes < 1) return 'En plazo';
  if (minutes < 60) return `Vencida hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `Vencida hace ${hours} h ${rest} min`;
}

export default function AdminReturnsPage() {
  const toast = useToast();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [target, setTarget] = useState<Reservation | null>(null);
  const [returning, setReturning] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.admin.reservations('APPROVED');
      setReservations(data);
      setError('');
    } catch (error_) {
      setError(error_ instanceof Error ? error_.message : 'No se pudieron cargar los préstamos activos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return reservations;
    return reservations.filter((reservation) =>
      [
        reservation.student.fullName,
        reservation.student.code,
        reservation.equipment.name,
        reservation.equipment.inventoryCode,
      ]
        .join(' ')
        .toLowerCase()
        .includes(term),
    );
  }, [reservations, search]);

  const handleReturn = async () => {
    if (!target) return;
    setReturning(true);
    try {
      const result = await api.admin.markReturned(target.id);
      toast.push(
        result.late
          ? 'Devolución registrada con retraso. Se aplicó la penalización automática al estudiante.'
          : 'Devolución registrada. El equipo vuelve a estar disponible.',
        result.late ? 'warning' : 'success',
      );
      setTarget(null);
      await load();
    } catch (error_) {
      toast.push(error_ instanceof Error ? error_.message : 'No se pudo registrar la devolución.', 'error');
    } finally {
      setReturning(false);
    }
  };

  const targetLate = target ? minutesLate(target) : 0;

  return (
    <div>
      <PageHeader
        eyebrow="HU-05 · Devolución y penalización"
        title="Devoluciones"
        subtitle="Registra la devolución física de un equipo. Si la hora actual supera el fin acordado, la cuenta del estudiante se penaliza automáticamente."
        actions={
          <button type="button" onClick={() => void load()} className="btn-ghost" data-testid="returns-refresh">
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </button>
        }
      />

      <div className="card mb-4 flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por estudiante, código o equipo…"
            aria-label="Buscar préstamo activo"
            data-testid="returns-search"
            className="input pl-10"
          />
        </div>
        <p className="text-xs text-slate-500">
          {filtered.length} préstamo{filtered.length === 1 ? '' : 's'} activo{filtered.length === 1 ? '' : 's'}
        </p>
      </div>

      {error ? <ErrorAlert message={error} onRetry={() => void load()} /> : null}

      {loading ? <LoadingBlock label="Cargando préstamos activos…" /> : null}

      {!loading && filtered.length === 0 ? (
        <EmptyState
          testId="empty-returns"
          icon={<Undo2 className="h-6 w-6" />}
          title="No hay préstamos activos por devolver"
          message="Cuando se apruebe una reserva, el equipo aparecerá aquí hasta que registres su devolución."
        />
      ) : null}

      {!loading && filtered.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[840px] text-left text-sm">
              <thead className="table-head">
                <tr>
                  <th className="px-5 py-3">Estudiante</th>
                  <th className="px-5 py-3">Equipo</th>
                  <th className="px-5 py-3">Horario acordado</th>
                  <th className="px-5 py-3">Puntualidad</th>
                  <th className="px-5 py-3 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((reservation) => {
                  const minutes = minutesLate(reservation);
                  const late = minutes >= 1;
                  return (
                    <tr
                      key={reservation.id}
                      data-testid="return-row"
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
                        <p className="inline-flex items-center gap-1.5 text-slate-700">
                          <CalendarDays className="h-3.5 w-3.5 text-slate-400" />
                          {formatDate(reservation.date)}
                        </p>
                        <p className="font-mono text-xs text-slate-500">
                          {reservation.startTime} – {reservation.endTime}
                        </p>
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`badge ${
                            late
                              ? 'bg-amber-100 text-amber-800 ring-1 ring-inset ring-amber-200'
                              : 'bg-emerald-100 text-emerald-800 ring-1 ring-inset ring-emerald-200'
                          }`}
                        >
                          {late ? <AlertTriangle className="h-3.5 w-3.5" /> : <Clock3 className="h-3.5 w-3.5" />}
                          {lateLabel(minutes)}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          type="button"
                          onClick={() => setTarget(reservation)}
                          data-action="return"
                          data-testid={`return-${reservation.id}`}
                          className="btn-primary btn-sm"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Marcar devolución
                        </button>
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
        open={Boolean(target)}
        title="Registrar devolución"
        subtitle="El equipo volverá al estado Disponible de inmediato."
        onClose={() => setTarget(null)}
        footer={
          <>
            <button type="button" className="btn-ghost" onClick={() => setTarget(null)} disabled={returning}>
              Cancelar
            </button>
            <button
              type="button"
              className={targetLate >= 1 ? 'btn-danger' : 'btn-teal'}
              onClick={() => void handleReturn()}
              disabled={returning}
              data-testid="return-confirm"
            >
              {returning ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
              Confirmar devolución
            </button>
          </>
        }
      >
        {target ? (
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
              <p className="font-semibold text-navy-950">{target.student.fullName}</p>
              <p className="text-xs text-slate-500">{target.student.code}</p>
              <p className="mt-2 text-slate-700">
                {target.equipment.name} ·{' '}
                <span className="font-mono text-xs font-semibold text-teal-700">
                  {target.equipment.inventoryCode}
                </span>
              </p>
              <p className="text-xs text-slate-500">
                {formatDate(target.date)} · {target.startTime} – {target.endTime}
              </p>
            </div>

            {targetLate >= 1 ? (
              <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  La devolución está fuera del horario acordado ({lateLabel(targetLate)}). Al
                  confirmar, el estudiante cambiará automáticamente al estado <strong>Penalizado</strong>.
                </span>
              </div>
            ) : (
              <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                <span>La devolución está dentro del plazo. No se aplicará penalización.</span>
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

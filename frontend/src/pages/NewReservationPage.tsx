import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Info,
  MapPin,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDate, today, tomorrow } from '../lib/format';
import type { Equipment } from '../lib/types';
import { useToast } from '../contexts/ToastContext';
import { CategoryIconLabel } from '../components/CategoryIconLabel';
import { ErrorAlert, LoadingBlock, PageHeader } from '../components/ui';

const LAB_OPEN = 7 * 60;
const LAB_CLOSE = 22 * 60;
const MAX_MINUTES = 4 * 60;

function timeToMinutes(value: string): number {
  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
}

function minutesToTime(total: number): string {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

const RULES = [
  'El laboratorio atiende de 07:00 a 22:00 y cada reserva dura como máximo 4 horas.',
  'No se pueden cruzar horarios con otra reserva aprobada del mismo equipo.',
  'Solo puedes mantener una reserva activa en un mismo bloque de horario.',
  'Una devolución tardía cambia tu estado a penalizado automáticamente.',
];

export default function NewReservationPage() {
  const [searchParams] = useSearchParams();
  const preselectedId = searchParams.get('equipo') ?? '';
  const navigate = useNavigate();
  const toast = useToast();

  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [equipmentId, setEquipmentId] = useState(preselectedId);
  const [date, setDate] = useState(tomorrow());
  const [startTime, setStartTime] = useState('08:00');
  const [endTime, setEndTime] = useState('10:00');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.equipment
      .available()
      .then((list) => {
        if (!active) return;
        setEquipment(list);
        setLoadError('');
        if (preselectedId && list.some((item) => item.id === preselectedId)) {
          setEquipmentId(preselectedId);
        }
      })
      .catch((error_) => {
        if (active) {
          setLoadError(error_ instanceof Error ? error_.message : 'No se pudo cargar la disponibilidad.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [preselectedId]);

  const selected = useMemo(
    () => equipment.find((item) => item.id === equipmentId) ?? null,
    [equipment, equipmentId],
  );

  const duration = timeToMinutes(endTime) - timeToMinutes(startTime);

  const handleStartChange = (value: string) => {
    setStartTime(value);
    if (timeToMinutes(value) >= timeToMinutes(endTime)) {
      setEndTime(minutesToTime(Math.min(timeToMinutes(value) + 120, LAB_CLOSE)));
    }
  };

  const applyDuration = (hours: number) => {
    const proposed = timeToMinutes(startTime) + hours * 60;
    setEndTime(minutesToTime(Math.min(proposed, LAB_CLOSE)));
  };

  const validate = (): string | null => {
    if (!equipmentId) return 'Selecciona un equipo disponible.';
    if (!date) return 'Selecciona la fecha de la reserva.';
    if (!startTime || !endTime) return 'Define la hora de inicio y de fin.';
    const start = timeToMinutes(startTime);
    const end = timeToMinutes(endTime);
    if (start >= end) return 'La hora de inicio debe ser anterior a la hora de fin.';
    if (start < LAB_OPEN || end > LAB_CLOSE) {
      return 'El horario de atención del laboratorio es de 07:00 a 22:00.';
    }
    if (end - start > MAX_MINUTES) return 'La reserva no puede exceder 4 horas continuas.';
    const startDate = new Date(`${date}T${startTime}:00`);
    if (Number.isNaN(startDate.getTime())) return 'La fecha u hora ingresada no es válida.';
    if (startDate.getTime() <= Date.now()) return 'La reserva debe iniciar en una fecha y hora futuras.';
    return null;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validation = validate();
    if (validation) {
      setFormError(validation);
      return;
    }
    setFormError('');
    setSubmitting(true);
    try {
      await api.reservations.create({ equipmentId, date, startTime, endTime });
      toast.push('Reserva registrada. Queda pendiente de aprobación.', 'success');
      navigate('/mis-reservas');
    } catch (error_) {
      setFormError(error_ instanceof Error ? error_.message : 'No se pudo registrar la reserva.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="HU-03 · Reserva de equipos"
        title="Nueva reserva"
        subtitle="Selecciona un equipo disponible y define el bloque exacto de uso. La solicitud quedará pendiente hasta la aprobación del encargado."
      />

      {loading ? (
        <LoadingBlock label="Cargando equipos disponibles…" />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <form onSubmit={handleSubmit} className="card p-5 sm:p-6" noValidate data-testid="reservation-form">
            {loadError ? <ErrorAlert message={loadError} /> : null}

            <section aria-labelledby="equipment-heading">
              <div className="flex items-start gap-3">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-teal-50 text-teal-700">
                  <Sparkles className="h-4 w-4" />
                </span>
                <div>
                  <h2 id="equipment-heading" className="font-semibold text-navy-950">
                    1. Elige el equipo
                  </h2>
                  <p className="text-xs text-slate-500">Solo se muestran equipos en estado Disponible.</p>
                </div>
              </div>

              <div className="mt-4">
                <label htmlFor="equipment" className="label">
                  Equipo del laboratorio
                </label>
                <select
                  id="equipment"
                  value={equipmentId}
                  onChange={(event) => setEquipmentId(event.target.value)}
                  className="input"
                  data-testid="reservation-equipment"
                  required
                >
                  <option value="">Selecciona un equipo…</option>
                  {equipment.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} · {item.inventoryCode} ({item.category})
                    </option>
                  ))}
                </select>
              </div>

              {equipment.length === 0 ? (
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-800">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>
                    No hay equipos disponibles en este momento.{' '}
                    <Link to="/catalogo" className="font-semibold underline">
                      Revisa el catálogo
                    </Link>
                    .
                  </span>
                </div>
              ) : null}
            </section>

            <hr className="my-6 border-slate-200" />

            <section aria-labelledby="schedule-heading">
              <div className="flex items-start gap-3">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-navy-50 text-navy-700">
                  <CalendarDays className="h-4 w-4" />
                </span>
                <div>
                  <h2 id="schedule-heading" className="font-semibold text-navy-950">
                    2. Define fecha y horario
                  </h2>
                  <p className="text-xs text-slate-500">Atención de 07:00 a 22:00 · máximo 4 horas.</p>
                </div>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="date" className="label">
                    Fecha de uso
                  </label>
                  <input
                    id="date"
                    type="date"
                    value={date}
                    min={today()}
                    onChange={(event) => setDate(event.target.value)}
                    className="input"
                    data-testid="reservation-date"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="startTime" className="label">
                    Hora de inicio
                  </label>
                  <input
                    id="startTime"
                    type="time"
                    value={startTime}
                    min="07:00"
                    max="21:59"
                    step={300}
                    onChange={(event) => handleStartChange(event.target.value)}
                    className="input"
                    data-testid="reservation-start"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="endTime" className="label">
                    Hora de fin
                  </label>
                  <input
                    id="endTime"
                    type="time"
                    value={endTime}
                    min="07:01"
                    max="22:00"
                    step={300}
                    onChange={(event) => setEndTime(event.target.value)}
                    className="input"
                    data-testid="reservation-end"
                    required
                  />
                </div>
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium text-slate-500">Duración rápida:</span>
                {[1, 2, 3, 4].map((hours) => (
                  <button
                    key={hours}
                    type="button"
                    onClick={() => applyDuration(hours)}
                    className={`rounded-full border px-3 py-1 text-xs font-semibold transition ${
                      duration === hours * 60
                        ? 'border-teal-500 bg-teal-50 text-teal-700'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-teal-300'
                    }`}
                  >
                    {hours} h
                  </button>
                ))}
              </div>

              {duration > 0 ? (
                <p className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600">
                  <Clock3 className="h-3.5 w-3.5 text-teal-600" />
                  Reserva de {formatDate(date)} · {startTime} a {endTime} ({duration / 60} h)
                </p>
              ) : null}
            </section>

            {formError ? (
              <div className="mt-5">
                <div data-testid="reservation-error">
                  <ErrorAlert message={formError} />
                </div>
              </div>
            ) : null}

            <div className="mt-6 flex flex-wrap items-center justify-end gap-2 border-t border-slate-200 pt-4">
              <Link to="/catalogo" className="btn-ghost">
                Cancelar
              </Link>
              <button
                type="submit"
                disabled={submitting || equipment.length === 0}
                className="btn-teal"
                data-testid="reservation-submit"
              >
                {submitting ? 'Registrando…' : 'Solicitar reserva'}
              </button>
            </div>
          </form>

          <aside className="space-y-4">
            <div className="card p-5">
              <h2 className="flex items-center gap-2 font-semibold text-navy-950">
                <Info className="h-4 w-4 text-teal-600" />
                Equipo seleccionado
              </h2>
              {selected ? (
                <div className="mt-3" data-testid="selected-equipment">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-navy-950">{selected.name}</p>
                      <p className="font-mono text-xs font-semibold text-teal-700">
                        {selected.inventoryCode}
                      </p>
                    </div>
                    <CategoryIconLabel category={selected.category} />
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{selected.description}</p>
                  <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
                    <MapPin className="h-3.5 w-3.5" />
                    {selected.location}
                  </p>
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-500">
                  Aún no has elegido un equipo. Selecciónalo en el formulario para ver su detalle.
                </p>
              )}
            </div>

            <div className="card border-navy-100 bg-gradient-to-b from-white to-slate-50 p-5">
              <h2 className="flex items-center gap-2 font-semibold text-navy-950">
                <ShieldCheck className="h-4 w-4 text-teal-600" />
                Reglas del laboratorio
              </h2>
              <ul className="mt-3 space-y-2.5">
                {RULES.map((rule) => (
                  <li key={rule} className="flex items-start gap-2 text-xs leading-relaxed text-slate-600">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600" />
                    {rule}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

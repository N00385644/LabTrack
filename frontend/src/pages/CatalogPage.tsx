import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Boxes,
  CheckCircle2,
  CircuitBoard,
  Clock3,
  Inbox,
  Laptop,
  MapPin,
  Network,
  Plus,
  RefreshCw,
  Search,
  Wrench,
} from 'lucide-react';
import { api } from '../lib/api';
import type { CatalogStats, Equipment } from '../lib/types';
import { useAuth } from '../contexts/AuthContext';
import {
  EmptyState,
  EquipmentStatusBadge,
  ErrorAlert,
  LoadingBlock,
  PageHeader,
  StatCard,
} from '../components/ui';

const CATEGORY_FILTERS = [
  { value: 'Todos', testId: 'filter-todos' },
  { value: 'Cómputo', testId: 'filter-computo' },
  { value: 'Electrónica', testId: 'filter-electronica' },
  { value: 'Redes', testId: 'filter-redes' },
] as const;

function CategoryIcon({ category, className }: Readonly<{ category: string; className?: string }>) {
  if (category === 'Cómputo') return <Laptop className={className} />;
  if (category === 'Electrónica') return <CircuitBoard className={className} />;
  if (category === 'Redes') return <Network className={className} />;
  return <Boxes className={className} />;
}

export default function CatalogPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [category, setCategory] = useState<string>('Todos');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.equipment
      .list(category === 'Todos' ? undefined : category)
      .then((data) => {
        if (active) {
          setEquipment(data);
          setError('');
        }
      })
      .catch((error_) => {
        if (active) {
          setError(error_ instanceof Error ? error_.message : 'No se pudo cargar el catálogo.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [category, refreshKey]);

  useEffect(() => {
    let active = true;
    api.equipment
      .stats()
      .then((data) => {
        if (active) setStats(data);
      })
      .catch(() => {
        /* Las métricas son complementarias; no bloquean el catálogo. */
      });
    return () => {
      active = false;
    };
  }, [refreshKey]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return equipment;
    return equipment.filter((item) =>
      [item.name, item.inventoryCode, item.description, item.location]
        .join(' ')
        .toLowerCase()
        .includes(term),
    );
  }, [equipment, search]);

  const statCards: Array<{ label: string; value: number | string; icon: ReactNode; tone: 'navy' | 'teal' | 'amber' | 'rose'; hint: string }> = [
    {
      label: 'Equipos totales',
      value: stats?.total ?? '—',
      icon: <Boxes className="h-5 w-5" />,
      tone: 'navy',
      hint: 'Inventario del laboratorio',
    },
    {
      label: 'Disponibles',
      value: stats?.available ?? '—',
      icon: <CheckCircle2 className="h-5 w-5" />,
      tone: 'teal',
      hint: 'Listos para reservar',
    },
    {
      label: 'En préstamo',
      value: stats?.borrowed ?? '—',
      icon: <Wrench className="h-5 w-5" />,
      tone: 'amber',
      hint: 'Con reserva aprobada',
    },
    {
      label: 'Solicitudes pendientes',
      value: stats?.pending ?? '—',
      icon: <Clock3 className="h-5 w-5" />,
      tone: 'rose',
      hint: 'En espera de revisión',
    },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="HU-02 · Catálogo y filtrado"
        title={`Hola, ${user?.fullName.split(' ')[0] ?? 'estudiante'}`}
        subtitle="Explora los equipos del laboratorio, revisa su disponibilidad y solicita una reserva en segundos."
        actions={
          <>
            <button
              type="button"
              onClick={() => setRefreshKey((key) => key + 1)}
              className="btn-ghost"
              data-testid="catalog-refresh"
            >
              <RefreshCw className="h-4 w-4" />
              Actualizar
            </button>
            <Link to="/reservar" className="btn-teal" data-testid="catalog-new-reservation">
              <Plus className="h-4 w-4" />
              Nueva reserva
            </Link>
          </>
        }
      />

      <section className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores del catálogo">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </section>

      <section className="card mb-6 p-4" aria-label="Filtros del catálogo">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <fieldset className="flex flex-wrap items-center gap-2">
            <legend className="sr-only">Filtrar por categoría</legend>
            {CATEGORY_FILTERS.map((filter) => {
              const active = category === filter.value;
              return (
                <button
                  key={filter.value}
                  type="button"
                  aria-pressed={active}
                  data-testid={filter.testId}
                  onClick={() => setCategory(filter.value)}
                  className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
                    active
                      ? 'bg-navy-900 text-white shadow-sm'
                      : 'border border-slate-200 bg-white text-slate-600 hover:border-teal-300 hover:text-navy-900'
                  }`}
                >
                  <CategoryIcon category={filter.value} className="h-4 w-4" />
                  {filter.value}
                </button>
              );
            })}
          </fieldset>

          <div className="relative w-full lg:w-72">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por nombre o código…"
              aria-label="Buscar equipos"
              data-testid="catalog-search"
              className="input pl-10"
            />
          </div>
        </div>

        <p className="mt-3 text-xs text-slate-500" data-testid="catalog-count">
          Mostrando {filtered.length} de {equipment.length} equipos
          {category !== 'Todos' ? ` en la categoría ${category}` : ''}.
        </p>
      </section>

      {error ? <ErrorAlert message={error} onRetry={() => setRefreshKey((key) => key + 1)} /> : null}

      {loading ? <LoadingBlock label="Cargando catálogo de equipos…" /> : null}

      {!loading && filtered.length === 0 ? (
        <EmptyState
          testId="empty-catalog"
          icon={<Inbox className="h-6 w-6" />}
          title="No hay equipos disponibles en esta categoría"
          message="Prueba con otra categoría o limpia el término de búsqueda."
          action={
            <button
              type="button"
              onClick={() => {
                setCategory('Todos');
                setSearch('');
              }}
              className="btn-ghost btn-sm mt-1"
            >
              Ver todos los equipos
            </button>
          }
        />
      ) : null}

      {!loading && filtered.length > 0 ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Equipos del catálogo">
          {filtered.map((item) => {
            const available = item.status === 'AVAILABLE';
            return (
              <article
                key={item.id}
                data-testid="equipment-card"
                className="card flex flex-col p-5 transition hover:-translate-y-0.5 hover:shadow-lift"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="grid h-11 w-11 place-items-center rounded-xl bg-navy-50 text-navy-700">
                    <CategoryIcon category={item.category} className="h-5 w-5" />
                  </span>
                  <EquipmentStatusBadge status={item.status} />
                </div>

                <h2 className="mt-4 text-base font-semibold leading-snug text-navy-950">
                  {item.name}
                </h2>
                <p className="mt-0.5 font-mono text-xs font-semibold text-teal-700">
                  {item.inventoryCode}
                </p>
                <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-600">
                  {item.description}
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span className="badge bg-slate-100 text-slate-600">{item.category}</span>
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {item.location}
                  </span>
                </div>

                <div className="mt-auto pt-5">
                  {available ? (
                    <button
                      type="button"
                      onClick={() => navigate(`/reservar?equipo=${encodeURIComponent(item.id)}`)}
                      className="btn-teal w-full"
                      data-testid={`reserve-${item.inventoryCode}`}
                    >
                      Reservar equipo
                    </button>
                  ) : (
                    <button type="button" disabled className="btn-ghost w-full">
                      No disponible
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </section>
      ) : null}
    </div>
  );
}

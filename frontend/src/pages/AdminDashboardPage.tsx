import { useEffect, useState } from 'react';
import { BarChart3, CheckCircle2, Clock3, ShieldAlert } from 'lucide-react';
import { api } from '../lib/api';
import type { AdminStats } from '../lib/types';
import { ErrorAlert, LoadingBlock, PageHeader, StatCard } from '../components/ui';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { api.admin.dashboard().then(setStats).catch((e) => setError(e instanceof Error ? e.message : 'No se pudieron cargar las métricas.')); }, []);
  return <div><PageHeader eyebrow="HU-11 · Indicadores" title="Dashboard operativo" subtitle="Distribución del inventario y puntualidad de devoluciones." />{error ? <ErrorAlert message={error} /> : null}{!stats ? <LoadingBlock label="Cargando indicadores…" /> : <><section className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><StatCard label="Disponibles" value={stats.equipmentAvailable} icon={<CheckCircle2 className="h-5 w-5" />} tone="teal" hint="Equipos listos" /><StatCard label="Pendientes" value={stats.pending} icon={<Clock3 className="h-5 w-5" />} tone="amber" hint="Por revisar" /><StatCard label="Penalizados" value={stats.penalized} icon={<ShieldAlert className="h-5 w-5" />} tone="rose" hint="Cuentas activas" /><StatCard label="Puntualidad" value={`${stats.punctualityRate ?? 100}%`} icon={<BarChart3 className="h-5 w-5" />} tone="navy" hint="Devoluciones a tiempo" /></section><section className="card p-5"><h2 className="font-semibold text-navy-950">Distribución disponible por categoría</h2><div className="mt-4 space-y-3">{(stats.inventoryDistribution ?? []).map((item) => <div key={item.category} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 text-sm"><span>{item.category}</span><strong>{item.available}</strong></div>)}</div></section></>}</div>;
}

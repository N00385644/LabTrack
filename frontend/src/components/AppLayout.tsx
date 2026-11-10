import { useState, type ReactNode } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Boxes,
  CalendarPlus,
  ClipboardCheck,
  ClipboardList,
  FlaskConical,
  History,
  LogOut,
  Menu,
  ShieldCheck,
  ScanLine,
  Undo2,
  X,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface NavItem {
  to: string;
  label: string;
  description: string;
  icon: ReactNode;
  testId: string;
}

const STUDENT_NAV: NavItem[] = [
  {
    to: '/carnet',
    label: 'Carnet digital',
    description: 'QR de estudiante',
    icon: <ShieldCheck className="h-4 w-4" />,
    testId: 'nav-carnet',
  },
  {
    to: '/catalogo',
    label: 'Catálogo',
    description: 'Equipos del laboratorio',
    icon: <Boxes className="h-4 w-4" />,
    testId: 'nav-catalogo',
  },
  {
    to: '/reservar',
    label: 'Nueva reserva',
    description: 'Solicitar un equipo',
    icon: <CalendarPlus className="h-4 w-4" />,
    testId: 'nav-reservar',
  },
  {
    to: '/mis-reservas',
    label: 'Mis reservas',
    description: 'Historial y estados',
    icon: <ClipboardList className="h-4 w-4" />,
    testId: 'nav-mis-reservas',
  },
];

const ADMIN_NAV: NavItem[] = [
  {
    to: '/admin/dashboard',
    label: 'Dashboard',
    description: 'Indicadores operativos',
    icon: <Boxes className="h-4 w-4" />,
    testId: 'nav-dashboard',
  },
  {
    to: '/admin/operaciones',
    label: 'Operaciones',
    description: 'Usuarios y escaneo',
    icon: <ScanLine className="h-4 w-4" />,
    testId: 'nav-operaciones',
  },
  {
    to: '/admin/pendientes',
    label: 'Solicitudes',
    description: 'Aprobar o rechazar',
    icon: <ClipboardCheck className="h-4 w-4" />,
    testId: 'nav-pendientes',
  },
  {
    to: '/admin/devoluciones',
    label: 'Devoluciones',
    description: 'Cerrar préstamos activos',
    icon: <Undo2 className="h-4 w-4" />,
    testId: 'nav-devoluciones',
  },
  {
    to: '/admin/historial',
    label: 'Historial y bitácora',
    description: 'Trazabilidad completa',
    icon: <History className="h-4 w-4" />,
    testId: 'nav-historial',
  },
];

function initials(fullName: string): string {
  return fullName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

function SidebarContent({ onNavigate }: Readonly<{ onNavigate?: () => void }>) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const items = user.role === 'ADMIN' ? ADMIN_NAV : STUDENT_NAV;

  const handleLogout = () => {
    logout();
    onNavigate?.();
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 px-6 pb-5 pt-6">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-teal-500/15 ring-1 ring-inset ring-teal-400/30">
          <FlaskConical className="h-5 w-5 text-teal-300" />
        </span>
        <div>
          <p className="text-base font-bold tracking-tight text-white">LabTrack</p>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
            Gestión de laboratorios
          </p>
        </div>
      </div>

      <div className="mx-4 mb-5 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-teal-300">
          <ShieldCheck className="h-3.5 w-3.5" />
          {user.role === 'ADMIN' ? 'Panel administrativo' : 'Portal del estudiante'}
        </div>
        <p className="mt-1 text-xs text-slate-400">
          {user.role === 'ADMIN'
            ? 'Revisa solicitudes y registra devoluciones.'
            : 'Reserva equipos y consulta tus solicitudes.'}
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-3" aria-label="Navegación principal">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            data-testid={item.testId}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-xl px-3 py-2.5 transition ${
                isActive
                  ? 'bg-teal-500/15 text-white ring-1 ring-inset ring-teal-400/30'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className={isActive ? 'text-teal-300' : 'text-slate-400 group-hover:text-teal-300'}>
                  {item.icon}
                </span>
                <span className="flex-1">
                  <span className="block text-sm font-semibold leading-tight">{item.label}</span>
                  <span className="block text-[11px] text-slate-400">{item.description}</span>
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-4 border-t border-white/10 p-4">
        <div className="flex items-center gap-3 rounded-xl bg-white/5 px-3 py-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-teal-500 text-xs font-bold text-navy-950">
            {initials(user.fullName)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-white">{user.fullName}</p>
            <p className="truncate text-[11px] text-slate-400">
              {user.code} · {user.role === 'ADMIN' ? 'Administrador' : 'Estudiante'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            data-testid="logout"
            title="Cerrar sesión"
            aria-label="Cerrar sesión"
            className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-3 text-center text-[10px] uppercase tracking-[0.18em] text-slate-500">
          T3 · Calidad 2026
        </p>
      </div>
    </div>
  );
}

export function AppLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 flex-col bg-navy-950 lg:flex">
        <SidebarContent />
      </aside>

      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-navy-950/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] animate-fade-up flex-col bg-navy-950 shadow-lift">
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Cerrar menú"
              className="absolute right-3 top-3 rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
            <SidebarContent onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="flex min-h-screen flex-col lg:pl-72">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:hidden">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-navy-950">
              <FlaskConical className="h-4 w-4 text-teal-300" />
            </span>
            <div>
              <p className="text-sm font-bold text-navy-950">LabTrack</p>
              <p className="text-[10px] uppercase tracking-wider text-slate-500">Laboratorios UPN</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setOpen(true)}
            data-testid="open-menu"
            aria-label="Abrir menú"
            className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
          >
            <Menu className="h-5 w-5" />
          </button>
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <Outlet />
          </div>
        </main>

        <footer className="border-t border-slate-200 bg-white/60 px-6 py-3 text-center text-xs text-slate-400">
          LabTrack · Calidad y Pruebas de Software · UPN 2026
        </footer>
      </div>
    </div>
  );
}

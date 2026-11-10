import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  FlaskConical,
  Layers,
  Loader2,
  Lock,
  ShieldCheck,
  UserRound,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import type { Role } from '../lib/types';
import { homeFor } from '../lib/routes';

interface DemoAccount {
  label: string;
  code: string;
  password: string;
  name: string;
  role: Role;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    label: 'Estudiante',
    code: 'N00385644',
    password: import.meta.env.VITE_DEMO_STUDENT_PASSWORD ?? '',
    name: 'Valeria Ramos',
    role: 'STUDENT' as const,
  },
  {
    label: 'Administrador',
    code: 'ADMIN01',
    password: import.meta.env.VITE_DEMO_ADMIN_PASSWORD ?? '',
    name: 'Carlos Mendoza',
    role: 'ADMIN' as const,
  },
].filter((account) => account.password.length > 0);

const FEATURES = [
  'Catálogo con filtros exactos por categoría.',
  'Reservas sin cruces de horario ni dobles préstamos.',
  'Aprobación y rechazo con motivo obligatorio.',
  'Penalización automática por devoluciones tardías.',
];

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (user) {
    return <Navigate to={homeFor(user.role)} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const authenticated = await login(code, password);
      navigate(homeFor(authenticated.role), { replace: true });
    } catch (error_) {
      setError(error_ instanceof Error ? error_.message : 'No se pudo iniciar sesión.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen bg-slate-50 lg:grid-cols-[1.05fr_1fr]">
      <section className="relative hidden overflow-hidden bg-navy-950 p-12 lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-sky-500/10 blur-3xl" />

        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-teal-500/15 ring-1 ring-inset ring-teal-400/30">
              <FlaskConical className="h-6 w-6 text-teal-300" />
            </span>
            <div>
              <p className="text-lg font-bold tracking-tight text-white">LabTrack</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                Gestión de laboratorios
              </p>
            </div>
          </div>

          <p className="mt-16 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-300">
            <Layers className="h-3.5 w-3.5" />
            Caso de estudio T3
          </p>
          <h1 className="mt-5 max-w-lg text-4xl font-bold leading-tight tracking-tight text-white">
            El control del laboratorio, en tiempo real.
          </h1>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-300">
            Préstamo de equipos con trazabilidad completa: autenticación segura, reservas sin
            cruces, aprobación administrativa y devoluciones controladas.
          </p>

          <ul className="mt-8 space-y-3">
            {FEATURES.map((feature) => (
              <li key={feature} className="flex items-start gap-3 text-sm text-slate-200">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-teal-400" />
                {feature}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative grid max-w-md grid-cols-3 gap-3">
          {[
            { value: '5', label: 'Historias de usuario' },
            { value: '18', label: 'Equipos registrados' },
            { value: 'JWT', label: 'Sesiones protegidas' },
          ].map((stat) => (
            <div key={stat.label} className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
              <p className="text-xl font-bold text-white">{stat.value}</p>
              <p className="mt-0.5 text-[11px] leading-tight text-slate-400">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="flex min-h-screen flex-col justify-center px-5 py-10 sm:px-10">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-navy-950">
              <FlaskConical className="h-6 w-6 text-teal-300" />
            </span>
            <div>
              <p className="text-lg font-bold text-navy-950">LabTrack</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                Gestión de laboratorios
              </p>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">
              Acceso seguro
            </p>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-navy-950 sm:text-3xl">
              Iniciar sesión
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Ingresa con tu código de estudiante o tu cuenta administrativa.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="card p-6" noValidate>
            <div className="space-y-4">
              <div>
                <label htmlFor="code" className="label">
                  Código de usuario
                </label>
                <div className="relative">
                  <UserRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="code"
                    name="code"
                    type="text"
                    autoComplete="username"
                    required
                    value={code}
                    onChange={(event) => setCode(event.target.value)}
                    className="input pl-10"
                    placeholder="Ej. N00385644"
                    data-testid="login-code"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="label">
                  Contraseña
                </label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="input pl-10 pr-11"
                    placeholder="••••••••••"
                    data-testid="login-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            {error ? (
              <div
                role="alert"
                data-testid="login-error"
                className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800"
              >
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={submitting}
              data-testid="login-submit"
              className="btn-primary mt-5 w-full"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Verificando…
                </>
              ) : (
                <>
                  Ingresar
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>

            <p className="mt-4 flex items-start gap-2 text-[11px] leading-relaxed text-slate-500">
              <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600" />
              Tras 3 intentos fallidos la cuenta se bloquea temporalmente y el evento queda
              registrado en la bitácora de auditoría.
            </p>
          </form>

          {DEMO_ACCOUNTS.length > 0 ? (
          <div className="mt-6">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Cuentas de demostración
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.code}
                  type="button"
                  data-testid={`demo-${account.role.toLowerCase()}`}
                  onClick={() => {
                    setCode(account.code);
                    setPassword(account.password);
                    setError('');
                  }}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left shadow-sm transition hover:border-teal-400 hover:bg-teal-50/40"
                >
                  <span className="block text-[11px] font-semibold uppercase tracking-wide text-teal-700">
                    {account.label}
                  </span>
                  <span className="mt-0.5 block font-mono text-xs text-slate-700">{account.code}</span>
                  <span className="block text-[11px] text-slate-400">{account.name}</span>
                </button>
              ))}
            </div>
            <p className="mt-3 text-center text-[11px] text-slate-400">
              Selecciona una cuenta para completar el formulario automáticamente.
            </p>
          </div>
          ) : null}

          <p className="mt-8 text-center text-[11px] text-slate-400">
            LabTrack v1.0 · Calidad y Pruebas de Software · UPN 2026
          </p>
        </div>
      </section>
    </div>
  );
}

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react';

export type ToastKind = 'success' | 'error' | 'warning' | 'info';

interface ToastItem {
  id: number;
  message: string;
  kind: ToastKind;
}

interface ToastContextValue {
  push: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const STYLES: Record<ToastKind, string> = {
  success: 'border-emerald-500 text-emerald-800 bg-white',
  error: 'border-red-500 text-red-800 bg-white',
  warning: 'border-amber-500 text-amber-800 bg-white',
  info: 'border-sky-500 text-sky-800 bg-white',
};

let toastSequence = 0;

const ICONS: Record<ToastKind, ReactNode> = {
  success: <CheckCircle2 className="h-5 w-5 text-emerald-600" />,
  error: <XCircle className="h-5 w-5 text-red-600" />,
  warning: <AlertTriangle className="h-5 w-5 text-amber-600" />,
  info: <Info className="h-5 w-5 text-sky-600" />,
};

export function ToastProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback(
    (message: string, kind: ToastKind = 'success') => {
      const id = ++toastSequence;
      setToasts((current) => [...current, { id, message, kind }]);
      window.setTimeout(() => remove(id), 5500);
    },
    [remove],
  );

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-24 z-[100] flex w-[min(380px,calc(100vw-32px))] flex-col gap-2">
        {toasts.map((toast) => (
          <output
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-xl border-l-4 px-4 py-3 text-sm font-medium shadow-lift animate-fade-up ${STYLES[toast.kind]}`}
          >
            <span className="mt-0.5 shrink-0">{ICONS[toast.kind]}</span>
            <span className="flex-1">{toast.message}</span>
            <button
              type="button"
              onClick={() => remove(toast.id)}
              className="text-slate-400 transition hover:text-slate-700"
              aria-label="Cerrar mensaje"
            >
              <X className="h-4 w-4" />
            </button>
          </output>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast debe usarse dentro de ToastProvider');
  }
  return context;
}

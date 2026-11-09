import { Link } from 'react-router-dom';
import { Compass, FlaskConical } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="grid min-h-screen place-items-center bg-navy-950 px-6 text-center">
      <div>
        <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-teal-500/15 ring-1 ring-inset ring-teal-400/30">
          <FlaskConical className="h-7 w-7 text-teal-300" />
        </span>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.2em] text-teal-300">Error 404</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Esta página no existe</h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
          La ruta que intentaste abrir no pertenece a LabTrack o fue movida. Vuelve al panel para
          continuar operando.
        </p>
        <Link to="/" className="btn-teal mt-6">
          <Compass className="h-4 w-4" />
          Ir al inicio
        </Link>
      </div>
    </div>
  );
}

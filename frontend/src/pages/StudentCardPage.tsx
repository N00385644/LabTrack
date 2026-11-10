import { QrCode } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { PageHeader } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';

export default function StudentCardPage() {
  const { user } = useAuth();
  if (!user) return null;
  return <div><PageHeader eyebrow="HU-06 · Identificación" title="Carnet digital" subtitle="Presenta este código QR para identificarte en el laboratorio." /><section className="card mx-auto max-w-sm p-8 text-center"><div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl bg-teal-50 text-teal-700"><QrCode /></div><h2 className="font-semibold text-navy-950">{user.fullName}</h2><p className="font-mono text-sm text-slate-500">{user.code}</p><div className="mt-6 flex justify-center rounded-xl bg-white p-4">  <QRCodeSVG value={user.code} size={190} aria-label={`QR de ${user.code}`} /></div><p className="mt-4 text-xs text-slate-500">Código de estudiante para despacho y devolución.</p></section></div>;
}

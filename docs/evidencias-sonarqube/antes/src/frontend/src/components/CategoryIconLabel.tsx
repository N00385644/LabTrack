import { CircuitBoard, Laptop, Network, Boxes } from 'lucide-react';

export function CategoryIconLabel({ category }: { category: string }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly
  const common = 'inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600';
  if (category === 'Cómputo') {
    return (
      <span className={common}>
        <Laptop className="h-3.5 w-3.5" /> {category}
      </span>
    );
  }
  if (category === 'Electrónica') {
    return (
      <span className={common}>
        <CircuitBoard className="h-3.5 w-3.5" /> {category}
      </span>
    );
  }
  if (category === 'Redes') {
    return (
      <span className={common}>
        <Network className="h-3.5 w-3.5" /> {category}
      </span>
    );
  }
  return (
    <span className={common}>
      <Boxes className="h-3.5 w-3.5" /> {category}
    </span>
  );
}

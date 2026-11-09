import type { Role } from './types';

export function homeFor(role: Role): string {
  return role === 'ADMIN' ? '/admin/pendientes' : '/catalogo';
}

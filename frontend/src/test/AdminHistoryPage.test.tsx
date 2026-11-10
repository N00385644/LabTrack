import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../lib/api';
import type { AuditEvent } from '../lib/types';
import AdminHistoryPage from '../pages/AdminHistoryPage';
import { adminUser, renderWithProviders, reservation } from './utils';

const approved = reservation({
  id: 'res-approved',
  status: 'APPROVED',
  reviewedBy: 'Carlos Mendoza Ríos',
  reviewedAt: new Date().toISOString(),
});

const auditEvent: AuditEvent = {
  id: 'audit-1',
  event: 'PENALTY_APPLIED',
  actorCode: 'ADMIN01',
  detail: 'Penalización aplicada al estudiante N00385645 por devolución tardía.',
  ipAddress: '127.0.0.1',
  createdAt: new Date().toISOString(),
};

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api.admin, 'reservations').mockResolvedValue([approved]);
  vi.spyOn(api.admin, 'audit').mockResolvedValue([auditEvent]);
});

describe('AdminHistoryPage · trazabilidad', () => {
  it('lista las reservas con su estado y revisor', async () => {
    renderWithProviders(<AdminHistoryPage />, { user: adminUser });

    expect(await screen.findByText('Valeria Ramos Quispe')).toBeInTheDocument();
    expect(screen.getByText('Laptop de prueba')).toBeInTheDocument();
    expect(screen.getByText('Aprobada')).toBeInTheDocument();
    expect(screen.getByText('Carlos Mendoza Ríos')).toBeInTheDocument();
  });

  it('muestra la bitácora de auditoría al cambiar de pestaña', async () => {
    renderWithProviders(<AdminHistoryPage />, { user: adminUser });
    await screen.findByText('Valeria Ramos Quispe');

    await userEvent.click(screen.getByTestId('tab-audit'));

    expect(await screen.findByText('Penalización aplicada')).toBeInTheDocument();
    expect(screen.getByText(/Actor: ADMIN01/)).toBeInTheDocument();
    expect(screen.getByText(/IP: 127.0.0.1/)).toBeInTheDocument();
  });

  it('muestra estados vacíos cuando no hay datos', async () => {
    vi.spyOn(api.admin, 'reservations').mockResolvedValue([]);
    vi.spyOn(api.admin, 'audit').mockResolvedValue([]);

    renderWithProviders(<AdminHistoryPage />, { user: adminUser });

    expect(await screen.findByText('Todavía no hay reservas registradas')).toBeInTheDocument();

    await userEvent.click(screen.getByTestId('tab-audit'));
    expect(await screen.findByText('La bitácora está vacía')).toBeInTheDocument();
  });
});

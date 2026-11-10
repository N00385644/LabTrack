import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../lib/api';
import AdminPendingPage from '../pages/AdminPendingPage';
import { adminUser, renderWithProviders, reservation } from './utils';

const pending = reservation({ id: 'res-pending', status: 'PENDING' });

const stats = {
  pending: 1,
  approved: 0,
  returnsToday: 0,
  penalized: 0,
  equipmentTotal: 2,
  equipmentAvailable: 2,
};

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api.admin, 'stats').mockResolvedValue(stats);
  vi.spyOn(api.admin, 'reservations').mockResolvedValue([pending]);
});

describe('AdminPendingPage · HU-04', () => {
  it('lista las solicitudes con los datos del estudiante y del equipo', async () => {
    renderWithProviders(<AdminPendingPage />, { user: adminUser });

    expect(await screen.findByText('Valeria Ramos Quispe')).toBeInTheDocument();
    expect(screen.getByText('Laptop de prueba')).toBeInTheDocument();
    expect(screen.getByText('N00385644')).toBeInTheDocument();
  });

  it('exige un motivo antes de rechazar una solicitud', async () => {
    const rejectSpy = vi.spyOn(api.admin, 'reject').mockResolvedValue({
      ...pending,
      status: 'REJECTED',
      rejectionReason: 'Equipo en mantenimiento',
    });

    renderWithProviders(<AdminPendingPage />, { user: adminUser });
    await screen.findByTestId('pending-row');

    await userEvent.click(screen.getByTestId(`reject-${pending.id}`));
    await userEvent.click(screen.getByTestId('reject-confirm'));

    expect(await screen.findByTestId('reject-error')).toHaveTextContent('al menos 5 caracteres');
    expect(rejectSpy).not.toHaveBeenCalled();

    await userEvent.type(screen.getByTestId('reject-reason'), 'Equipo en mantenimiento');
    await userEvent.click(screen.getByTestId('reject-confirm'));

    await waitFor(() =>
      expect(rejectSpy).toHaveBeenCalledWith(pending.id, 'Equipo en mantenimiento'),
    );
  });

  it('aprueba una solicitud pendiente', async () => {
    const approveSpy = vi.spyOn(api.admin, 'approve').mockResolvedValue({
      ...pending,
      status: 'APPROVED',
      reviewedBy: adminUser.fullName,
    });

    renderWithProviders(<AdminPendingPage />, { user: adminUser });
    await screen.findByTestId('pending-row');

    await userEvent.click(screen.getByTestId(`approve-${pending.id}`));

    await waitFor(() => expect(approveSpy).toHaveBeenCalledWith(pending.id));
    expect(await screen.findByRole('status')).toHaveTextContent('aprobada');
  });
});

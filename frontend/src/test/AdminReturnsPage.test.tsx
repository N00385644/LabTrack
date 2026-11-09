import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../lib/api';
import AdminReturnsPage from '../pages/AdminReturnsPage';
import { adminUser, isoDate, renderWithProviders, reservation } from './utils';

const overdue = reservation({
  id: 'res-overdue',
  date: isoDate(-1),
  startTime: '08:00',
  endTime: '10:00',
  status: 'APPROVED',
});

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api.admin, 'reservations').mockResolvedValue([overdue]);
});

describe('AdminReturnsPage · HU-05', () => {
  it('marca visualmente un préstamo vencido', async () => {
    renderWithProviders(<AdminReturnsPage />, { user: adminUser });

    expect(await screen.findByText(/Vencida hace/)).toBeInTheDocument();
  });

  it('advierte la penalización y registra la devolución tardía', async () => {
    const returnSpy = vi.spyOn(api.admin, 'markReturned').mockResolvedValue({
      ...overdue,
      status: 'RETURNED',
      penaltyApplied: true,
      late: true,
    });
    vi.spyOn(api.admin, 'reservations')
      .mockResolvedValueOnce([overdue])
      .mockResolvedValue([]);

    renderWithProviders(<AdminReturnsPage />, { user: adminUser });
    await screen.findByTestId('return-row');

    await userEvent.click(screen.getByTestId(`return-${overdue.id}`));
    expect(screen.getByText(/cambiará automáticamente al estado/)).toBeInTheDocument();

    await userEvent.click(screen.getByTestId('return-confirm'));

    await waitFor(() => expect(returnSpy).toHaveBeenCalledWith(overdue.id));
    expect(await screen.findByRole('status')).toHaveTextContent('penalización');
  });
});

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../lib/api';
import MyReservationsPage from '../pages/MyReservationsPage';
import { renderWithProviders, reservation } from './utils';

const rejected = reservation({
  id: 'res-rejected',
  status: 'REJECTED',
  rejectionReason: 'Equipo en mantenimiento preventivo',
  reviewedBy: 'Carlos Mendoza',
});

const lateReturn = reservation({
  id: 'res-late',
  status: 'RETURNED',
  penaltyApplied: true,
  returnedAt: new Date().toISOString(),
  reviewedBy: 'Carlos Mendoza',
});

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api.reservations, 'mine').mockResolvedValue([rejected, lateReturn]);
});

describe('MyReservationsPage · seguimiento', () => {
  it('muestra el motivo de rechazo al estudiante', async () => {
    renderWithProviders(<MyReservationsPage />);

    const reason = await screen.findByTestId('rejection-reason');
    expect(reason).toHaveTextContent('Equipo en mantenimiento preventivo');
  });

  it('informa una devolución tardía penalizada', async () => {
    renderWithProviders(<MyReservationsPage />);

    expect(await screen.findByText(/Devolución tardía/)).toBeInTheDocument();
    expect(screen.getByText(/penalización automática/)).toBeInTheDocument();
  });

  it('filtra las reservas por estado', async () => {
    renderWithProviders(<MyReservationsPage />);
    await screen.findByText(/Devolución tardía/);

    await userEvent.click(screen.getByTestId('my-filter-rejected'));

    expect(screen.getAllByTestId('reservation-row')).toHaveLength(1);
    expect(screen.getByText(/Equipo en mantenimiento preventivo/)).toBeInTheDocument();
  });

  it('muestra el estado vacío cuando no hay reservas', async () => {
    vi.spyOn(api.reservations, 'mine').mockResolvedValue([]);

    renderWithProviders(<MyReservationsPage />);

    expect(await screen.findByTestId('empty-reservations')).toHaveTextContent(
      'Todavía no tienes reservas registradas',
    );
  });
});

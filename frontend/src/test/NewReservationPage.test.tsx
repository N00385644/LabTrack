import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../lib/api';
import NewReservationPage from '../pages/NewReservationPage';
import { laptop, renderWithProviders, reservation } from './utils';

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api.equipment, 'available').mockResolvedValue([laptop]);
  vi.spyOn(api.reservations, 'create').mockResolvedValue(reservation({ status: 'PENDING' }));
});

describe('NewReservationPage · HU-03', () => {
  it('preselecciona el equipo enviado desde el catálogo', async () => {
    renderWithProviders(<NewReservationPage />, {
      route: `/reservar?equipo=${laptop.id}`,
    });

    const select = await screen.findByTestId('reservation-equipment');
    await waitFor(() => expect(select).toHaveValue(laptop.id));
    expect(screen.getByTestId('selected-equipment')).toHaveTextContent('Laptop de prueba');
  });

  it('valida que la hora de inicio sea anterior a la hora de fin', async () => {
    renderWithProviders(<NewReservationPage />, {
      route: `/reservar?equipo=${laptop.id}`,
    });
    await screen.findByTestId('reservation-equipment');

    fireEvent.change(screen.getByTestId('reservation-end'), { target: { value: '08:00' } });
    await userEvent.click(screen.getByTestId('reservation-submit'));

    expect(await screen.findByTestId('reservation-error')).toHaveTextContent(
      'anterior a la hora de fin',
    );
    expect(api.reservations.create).not.toHaveBeenCalled();
  });

  it('valida el máximo de 4 horas continuas', async () => {
    renderWithProviders(<NewReservationPage />, {
      route: `/reservar?equipo=${laptop.id}`,
    });
    await screen.findByTestId('reservation-equipment');

    fireEvent.change(screen.getByTestId('reservation-end'), { target: { value: '13:00' } });
    await userEvent.click(screen.getByTestId('reservation-submit'));

    expect(await screen.findByTestId('reservation-error')).toHaveTextContent('4 horas');
    expect(api.reservations.create).not.toHaveBeenCalled();
  });

  it('envía una reserva válida y muestra la confirmación', async () => {
    const createSpy = vi.mocked(api.reservations.create);

    renderWithProviders(<NewReservationPage />, {
      route: `/reservar?equipo=${laptop.id}`,
    });
    await screen.findByTestId('reservation-equipment');

    await userEvent.click(screen.getByTestId('reservation-submit'));

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith({
        equipmentId: laptop.id,
        date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
        startTime: '08:00',
        endTime: '10:00',
      }),
    );
    expect(await screen.findByRole('status')).toHaveTextContent('pendiente de aprobación');
  });
});

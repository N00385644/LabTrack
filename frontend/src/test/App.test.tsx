import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { api, storeSession } from '../lib/api';
import { adminUser, laptop, studentUser } from './utils';

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe('App · enrutamiento y sesión', () => {
  it('muestra el login cuando no hay sesión', () => {
    window.history.replaceState(null, '', '/login');
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument();
  });

  it('restaura la sesión del estudiante y abre el catálogo', async () => {
    window.history.replaceState(null, '', '/catalogo');
    storeSession('token-de-prueba', studentUser);
    vi.spyOn(api, 'me').mockResolvedValue({ user: studentUser });
    vi.spyOn(api.equipment, 'list').mockResolvedValue([laptop]);
    vi.spyOn(api.equipment, 'stats').mockResolvedValue({
      total: 1,
      available: 1,
      borrowed: 0,
      pending: 0,
      students: 3,
    });

    render(<App />);

    expect(await screen.findByText('Laptop de prueba')).toBeInTheDocument();
    expect(screen.getByTestId('nav-catalogo')).toBeInTheDocument();
  });

  it('redirige al administrador a su panel de solicitudes', async () => {
    window.history.replaceState(null, '', '/');
    storeSession('token-admin', adminUser);
    vi.spyOn(api, 'me').mockResolvedValue({ user: adminUser });
    vi.spyOn(api.admin, 'reservations').mockResolvedValue([]);
    vi.spyOn(api.admin, 'stats').mockResolvedValue({
      pending: 0,
      approved: 0,
      returnsToday: 0,
      penalized: 0,
      equipmentTotal: 1,
      equipmentAvailable: 1,
    });

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Solicitudes pendientes' })).toBeInTheDocument();
    expect(screen.getByTestId('nav-pendientes')).toBeInTheDocument();
  });
});

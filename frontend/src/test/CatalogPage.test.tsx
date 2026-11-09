import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../lib/api';
import CatalogPage from '../pages/CatalogPage';
import { laptop, renderWithProviders, routerEquipment } from './utils';

const stats = { total: 2, available: 2, borrowed: 0, pending: 0, students: 3 };

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api.equipment, 'stats').mockResolvedValue(stats);
  vi.spyOn(api.equipment, 'list').mockImplementation(async (category?: string) => {
    if (category === 'Redes') return [routerEquipment];
    if (category === 'Electrónica') return [];
    return [laptop, routerEquipment];
  });
});

describe('CatalogPage · HU-02', () => {
  it('muestra las tarjetas con nombre, código, categoría y estado', async () => {
    renderWithProviders(<CatalogPage />);

    expect(await screen.findByText('Laptop de prueba')).toBeInTheDocument();
    expect(screen.getByText('Router de prueba')).toBeInTheDocument();
    expect(screen.getAllByText('COMP-T01').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Disponible').length).toBeGreaterThan(0);
    expect(screen.getAllByTestId('equipment-card')).toHaveLength(2);
  });

  it('aplica el filtro exacto por categoría', async () => {
    renderWithProviders(<CatalogPage />);
    await screen.findByText('Laptop de prueba');

    await userEvent.click(screen.getByTestId('filter-redes'));

    await waitFor(() => expect(api.equipment.list).toHaveBeenLastCalledWith('Redes'));
    expect(await screen.findByText('Router de prueba')).toBeInTheDocument();
    expect(screen.queryByText('Laptop de prueba')).not.toBeInTheDocument();
  });

  it('muestra el mensaje vacío exigido cuando una categoría no tiene equipos', async () => {
    renderWithProviders(<CatalogPage />);
    await screen.findByText('Laptop de prueba');

    await userEvent.click(screen.getByTestId('filter-electronica'));

    const empty = await screen.findByTestId('empty-catalog');
    expect(empty).toHaveTextContent('No hay equipos disponibles en esta categoría');
  });

  it('permite buscar por nombre o código de inventario', async () => {
    renderWithProviders(<CatalogPage />);
    await screen.findByText('Laptop de prueba');

    await userEvent.type(screen.getByTestId('catalog-search'), 'router');

    expect(await screen.findByText('Router de prueba')).toBeInTheDocument();
    expect(screen.queryByText('Laptop de prueba')).not.toBeInTheDocument();
  });

  it('deshabilita la reserva de equipos prestados', async () => {
    vi.spyOn(api.equipment, 'list').mockResolvedValue([
      { ...laptop, status: 'BORROWED' },
    ]);

    renderWithProviders(<CatalogPage />);

    expect(await screen.findByText('No disponible')).toBeDisabled();
    expect(screen.queryByTestId('reserve-COMP-T01')).not.toBeInTheDocument();
  });
});

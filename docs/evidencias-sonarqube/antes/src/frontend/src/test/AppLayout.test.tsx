import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import { AppLayout } from '../components/AppLayout';
import { adminUser, renderWithProviders, studentUser } from './utils';

beforeEach(() => {
  localStorage.clear();
});

function renderLayout(user: typeof studentUser, route: string, outlet = 'Contenido interno') {
  return renderWithProviders(
    <Routes>
      <Route element={<AppLayout />}>
        <Route path={route} element={<p>{outlet}</p>} />
      </Route>
      <Route path="/login" element={<p>Pantalla de login</p>} />
    </Routes>,
    { user, route },
  );
}

describe('AppLayout · navegación', () => {
  it('muestra la navegación del estudiante y su identidad', () => {
    renderLayout(studentUser, '/catalogo');

    expect(screen.getByText('Contenido interno')).toBeInTheDocument();
    expect(screen.getByTestId('nav-catalogo')).toBeInTheDocument();
    expect(screen.getByTestId('nav-reservar')).toBeInTheDocument();
    expect(screen.getByTestId('nav-mis-reservas')).toBeInTheDocument();
    expect(screen.getAllByText('Valeria Ramos Quispe').length).toBeGreaterThan(0);
    expect(screen.getByText('Portal del estudiante')).toBeInTheDocument();
  });

  it('muestra la navegación administrativa', () => {
    renderLayout(adminUser, '/admin/pendientes', 'Panel de solicitudes');

    expect(screen.getByTestId('nav-pendientes')).toBeInTheDocument();
    expect(screen.getByTestId('nav-devoluciones')).toBeInTheDocument();
    expect(screen.getByTestId('nav-historial')).toBeInTheDocument();
    expect(screen.getByText('Panel administrativo')).toBeInTheDocument();
  });

  it('cierra la sesión y vuelve al login', async () => {
    renderLayout(studentUser, '/catalogo');

    await userEvent.click(screen.getByTestId('logout'));

    expect(screen.getByText('Pantalla de login')).toBeInTheDocument();
    expect(localStorage.getItem('labtrack_token')).toBeNull();
  });

  it('abre y cierra el menú móvil', async () => {
    renderLayout(studentUser, '/catalogo');

    await userEvent.click(screen.getByTestId('open-menu'));
    expect(screen.getByLabelText('Cerrar menú')).toBeInTheDocument();

    await userEvent.click(screen.getByLabelText('Cerrar menú'));
    expect(screen.queryByLabelText('Cerrar menú')).not.toBeInTheDocument();
  });
});

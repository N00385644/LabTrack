import { screen } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { adminUser, renderWithProviders, studentUser } from './utils';

function renderRoutes(route: string, user: typeof studentUser | typeof adminUser | null) {
  return renderWithProviders(
    <Routes>
      <Route path="/login" element={<p>Pantalla de login</p>} />
      <Route path="/catalogo" element={<p>Catálogo privado</p>} />
      <Route path="/admin/pendientes" element={<p>Panel administrativo</p>} />
      <Route element={<ProtectedRoute />}>
        <Route path="/protegida" element={<p>Contenido protegido</p>} />
      </Route>
      <Route element={<ProtectedRoute role="ADMIN" />}>
        <Route path="/solo-admin" element={<p>Solo administradores</p>} />
      </Route>
    </Routes>,
    { user, route },
  );
}

describe('ProtectedRoute · control de acceso', () => {
  it('redirige al login cuando no hay sesión', () => {
    renderRoutes('/protegida', null);

    expect(screen.getByText('Pantalla de login')).toBeInTheDocument();
  });

  it('permite el acceso al rol autorizado', () => {
    renderRoutes('/protegida', studentUser);

    expect(screen.getByText('Contenido protegido')).toBeInTheDocument();
  });

  it('redirige al estudiante lejos del panel administrativo', () => {
    renderRoutes('/solo-admin', studentUser);

    expect(screen.getByText('Catálogo privado')).toBeInTheDocument();
  });

  it('permite al administrador acceder a su panel', () => {
    renderRoutes('/solo-admin', adminUser);

    expect(screen.getByText('Solo administradores')).toBeInTheDocument();
  });
});

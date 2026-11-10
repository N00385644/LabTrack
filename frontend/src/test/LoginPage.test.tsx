import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from '../lib/api';
import LoginPage from '../pages/LoginPage';
import { renderWithProviders, studentUser } from './utils';

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe('LoginPage · HU-01', () => {
  it('muestra el formulario y completa las credenciales de demostración', async () => {
    renderWithProviders(<LoginPage />, { user: null });

    expect(screen.getByTestId('login-code')).toBeInTheDocument();
    expect(screen.getByTestId('login-password')).toBeInTheDocument();

    await userEvent.click(screen.getByTestId('demo-student'));

    expect(screen.getByTestId('login-code')).toHaveValue('N00385644');
    expect(screen.getByTestId('login-password')).toHaveValue('Estudiante2026!');
  });

  it('muestra el mensaje "Credenciales inválidas" ante un rechazo del API', async () => {
    vi.spyOn(api, 'login').mockRejectedValue(new ApiError(401, 'Credenciales inválidas.'));

    renderWithProviders(<LoginPage />, { user: null });
    await userEvent.type(screen.getByTestId('login-code'), 'N00385644');
    await userEvent.type(screen.getByTestId('login-password'), 'Incorrecta1!');
    await userEvent.click(screen.getByTestId('login-submit'));

    const error = await screen.findByTestId('login-error');
    expect(error).toHaveTextContent('Credenciales inválidas');
  });

  it('muestra la alerta de bloqueo temporal', async () => {
    vi.spyOn(api, 'login').mockRejectedValue(
      new ApiError(423, 'Cuenta bloqueada temporalmente por seguridad.', 'ACCOUNT_LOCKED'),
    );

    renderWithProviders(<LoginPage />, { user: null });
    await userEvent.type(screen.getByTestId('login-code'), 'N00385644');
    await userEvent.type(screen.getByTestId('login-password'), 'Incorrecta1!');
    await userEvent.click(screen.getByTestId('login-submit'));

    expect(await screen.findByTestId('login-error')).toHaveTextContent('bloqueada temporalmente');
  });

  it('guarda la sesión cuando las credenciales son válidas', async () => {
    vi.spyOn(api, 'login').mockResolvedValue({
      accessToken: 'jwt-de-prueba',
      expiresIn: '8h',
      user: studentUser,
    });

    renderWithProviders(<LoginPage />, { user: null });
    await userEvent.type(screen.getByTestId('login-code'), 'N00385644');
    await userEvent.type(screen.getByTestId('login-password'), 'Estudiante2026!');
    await userEvent.click(screen.getByTestId('login-submit'));

    expect(api.login).toHaveBeenCalledWith('N00385644', 'Estudiante2026!');
    expect(localStorage.getItem('labtrack_token')).toBe('jwt-de-prueba');
  });
});

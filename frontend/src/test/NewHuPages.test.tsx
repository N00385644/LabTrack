import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import StudentCardPage from '../pages/StudentCardPage';
import { renderWithProviders, studentUser } from './utils';

describe('HU-06 · Carnet digital', () => {
  it('muestra la identidad y el QR del código del estudiante', () => {
    renderWithProviders(<StudentCardPage />, { user: studentUser });
    expect(screen.getByText(studentUser.fullName)).toBeInTheDocument();
    expect(screen.getByText(studentUser.code)).toBeInTheDocument();
    expect(screen.getByRole('img', { name: /qr/i })).toBeInTheDocument();
  });
});

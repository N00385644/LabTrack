import type { ReactElement } from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import { ToastProvider } from '../contexts/ToastContext';
import type { Equipment, Reservation, User } from '../lib/types';

export const studentUser: User = {
  id: 'user-student',
  code: '20240001',
  fullName: 'Valeria Ramos Quispe',
  email: 'valeria@labtrack.pe',
  role: 'STUDENT',
  status: 'ACTIVE',
};

export const adminUser: User = {
  id: 'user-admin',
  code: 'ADMIN01',
  fullName: 'Carlos Mendoza Ríos',
  email: 'admin@labtrack.pe',
  role: 'ADMIN',
  status: 'ACTIVE',
};

export const laptop: Equipment = {
  id: 'eq-laptop',
  name: 'Laptop de prueba',
  inventoryCode: 'COMP-T01',
  category: 'Cómputo',
  status: 'AVAILABLE',
  description: 'Equipo para pruebas de interfaz',
  location: 'Laboratorio de prueba',
};

export const routerEquipment: Equipment = {
  id: 'eq-router',
  name: 'Router de prueba',
  inventoryCode: 'RED-T01',
  category: 'Redes',
  status: 'AVAILABLE',
  description: 'Router para pruebas de interfaz',
  location: 'Laboratorio de redes',
};

export function isoDate(offsetDays: number): string {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
    date.getDate(),
  ).padStart(2, '0')}`;
}

export function reservation(overrides: Partial<Reservation> = {}): Reservation {
  return {
    id: 'res-1',
    date: isoDate(1),
    startTime: '08:00',
    endTime: '10:00',
    status: 'PENDING',
    rejectionReason: null,
    penaltyApplied: false,
    reviewedBy: null,
    reviewedAt: null,
    returnedAt: null,
    createdAt: new Date().toISOString(),
    student: {
      id: studentUser.id,
      code: studentUser.code,
      fullName: studentUser.fullName,
      status: 'ACTIVE',
    },
    equipment: {
      id: laptop.id,
      name: laptop.name,
      inventoryCode: laptop.inventoryCode,
      category: laptop.category,
      status: 'AVAILABLE',
      location: laptop.location,
    },
    ...overrides,
  };
}

export function renderWithProviders(
  ui: ReactElement,
  options: { user?: User | null; route?: string } = {},
) {
  const user = options.user === undefined ? studentUser : options.user;
  return render(
    <MemoryRouter initialEntries={[options.route ?? '/']}>
      <AuthProvider initialUser={user} initialToken={user ? 'test-token' : null}>
        <ToastProvider>{ui}</ToastProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

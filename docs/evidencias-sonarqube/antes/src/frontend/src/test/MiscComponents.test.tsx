import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CategoryIconLabel } from '../components/CategoryIconLabel';
import { EmptyState, EquipmentStatusBadge, StatusBadge } from '../components/ui';
import NotFoundPage from '../pages/NotFoundPage';
import { renderWithProviders } from './utils';

describe('Componentes compartidos', () => {
  it('representa las tres categorías y una categoría genérica', () => {
    render(
      <div>
        <CategoryIconLabel category="Cómputo" />
        <CategoryIconLabel category="Electrónica" />
        <CategoryIconLabel category="Redes" />
        <CategoryIconLabel category="Otros" />
      </div>,
    );

    expect(screen.getByText('Cómputo')).toBeInTheDocument();
    expect(screen.getByText('Electrónica')).toBeInTheDocument();
    expect(screen.getByText('Redes')).toBeInTheDocument();
    expect(screen.getByText('Otros')).toBeInTheDocument();
  });

  it('muestra las etiquetas de estado de equipos y reservas', () => {
    render(
      <div>
        <EquipmentStatusBadge status="AVAILABLE" />
        <EquipmentStatusBadge status="BORROWED" />
        <StatusBadge status="PENDING" />
        <StatusBadge status="APPROVED" />
        <StatusBadge status="REJECTED" />
        <StatusBadge status="RETURNED" />
      </div>,
    );

    expect(screen.getByText('Disponible')).toBeInTheDocument();
    expect(screen.getByText('Prestado')).toBeInTheDocument();
    expect(screen.getByText('Pendiente')).toBeInTheDocument();
    expect(screen.getByText('Aprobada')).toBeInTheDocument();
    expect(screen.getByText('Rechazada')).toBeInTheDocument();
    expect(screen.getByText('Devuelta')).toBeInTheDocument();
  });

  it('renderiza un estado vacío con su mensaje', () => {
    render(<EmptyState title="Sin datos" message="No hay registros para mostrar." testId="vacio" />);

    expect(screen.getByTestId('vacio')).toHaveTextContent('Sin datos');
    expect(screen.getByTestId('vacio')).toHaveTextContent('No hay registros para mostrar.');
  });

  it('la página 404 informa el error y ofrece volver al inicio', () => {
    renderWithProviders(<NotFoundPage />, { user: null });

    expect(screen.getByText('Esta página no existe')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Ir al inicio/i })).toHaveAttribute('href', '/');
  });
});

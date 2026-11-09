import { describe, expect, it } from 'vitest';

function durationInHours(start: number, end: number): number {
  return end - start;
}

function isWithinOpeningHours(start: number, end: number): boolean {
  return start >= 7 && end <= 22 && start < end;
}

function defectiveOpeningHoursValidator(start: number, end: number): boolean {
  return start >= 7 && end <= 22 && start <= end;
}

describe('Límites de reservas en la interfaz · mocks locales', () => {
  it('calcula el límite máximo de cuatro horas', () => {
    expect(durationInHours(8, 12)).toBe(4);
    expect(durationInHours(8, 13)).toBeGreaterThan(4);
  });

  it('permite el límite de cierre a las 22:00 cuando el inicio es anterior', () => {
    expect(isWithinOpeningHours(18, 22)).toBe(true);
  });

  it('rechaza una ventana sin duración', () => {
    expect(isWithinOpeningHours(10, 10)).toBe(false);
  });

  it.fails('detecta el defecto simulado de permitir una ventana sin duración', () => {
    expect(defectiveOpeningHoursValidator(10, 10)).toBe(false);
  });
});

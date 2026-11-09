import { describe, expect, it } from 'vitest';

type ReservationWindow = {
  start: number;
  end: number;
};

function isValidWindow(window: ReservationWindow): boolean {
  return window.start < window.end && window.end - window.start <= 4;
}

function overlaps(left: ReservationWindow, right: ReservationWindow): boolean {
  return left.start < right.end && right.start < left.end;
}

function defectiveWindowValidator(window: ReservationWindow): boolean {
  return window.start <= window.end && window.end - window.start <= 4;
}

function defectiveOverlapValidator(left: ReservationWindow, right: ReservationWindow): boolean {
  return left.start <= right.end && right.start <= left.end;
}

describe('Límites de reservas · mocks locales', () => {
  it('acepta reservas contiguas sin considerar cruce', () => {
    expect(overlaps({ start: 8, end: 10 }, { start: 10, end: 12 })).toBe(false);
  });

  it('rechaza una ventana con inicio y fin iguales', () => {
    expect(isValidWindow({ start: 10, end: 10 })).toBe(false);
  });

  it.fails('detecta el defecto simulado de aceptar una ventana de duración cero', () => {
    expect(defectiveWindowValidator({ start: 10, end: 10 })).toBe(false);
  });

  it.fails('detecta el defecto simulado de tratar reservas contiguas como cruce', () => {
    expect(defectiveOverlapValidator({ start: 8, end: 10 }, { start: 10, end: 12 })).toBe(false);
  });
});

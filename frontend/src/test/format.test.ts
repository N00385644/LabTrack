import { describe, expect, it } from 'vitest';
import { formatDate, formatDateTime, isOverdue, today, tomorrow } from '../lib/format';
import { reservation } from './utils';

describe('Utilidades de formato', () => {
  it('formatea fechas ISO al formato peruano', () => {
    expect(formatDate('2026-11-09')).toBe('09/11/2026');
  });

  it('devuelve un guion cuando no hay fecha de revisión', () => {
    expect(formatDateTime(null)).toBe('—');
  });

  it('calcula fechas de hoy y mañana en formato ISO', () => {
    expect(today()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(tomorrow()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(tomorrow() > today()).toBe(true);
  });

  it('detecta reservas aprobadas vencidas y no vencidas', () => {
    const past = reservation({
      status: 'APPROVED',
      date: '2020-01-01',
      startTime: '08:00',
      endTime: '09:00',
    });
    const future = reservation({ status: 'APPROVED', date: tomorrow() });
    const pending = reservation({ status: 'PENDING', date: '2020-01-01' });

    expect(isOverdue(past)).toBe(true);
    expect(isOverdue(future)).toBe(false);
    expect(isOverdue(pending)).toBe(false);
  });
});

import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { API, auth, createTestApp, tokenFor } from './helpers/test-app';
import {
  createReservation,
  dateOffset,
  prisma,
  resetDatabase,
  seedBase,
  TEST_PASSWORD,
  type BaseFixture,
} from './helpers/test-db';

let app: INestApplication;
let base: BaseFixture;
let adminToken: string;
let studentToken: string;

beforeAll(async () => {
  app = await createTestApp();
});

afterAll(async () => {
  await app.close();
});

beforeEach(async () => {
  await resetDatabase();
  base = await seedBase();
  adminToken = await tokenFor(app, base.admin.code, TEST_PASSWORD);
  studentToken = await tokenFor(app, base.student.code, TEST_PASSWORD);
});

async function createApproved(offsetDays: number, equipmentId = base.laptop.id) {
  const reservation = await createReservation({
    userId: base.student.id,
    equipmentId,
    date: dateOffset(offsetDays),
    startTime: '08:00',
    endTime: '10:00',
    status: 'APPROVED',
  });
  await prisma.equipment.update({ where: { id: equipmentId }, data: { status: 'BORROWED' } });
  return reservation;
}

describe('HU-04 · Gestión de solicitudes (administrador)', () => {
  it('prohíbe a los estudiantes consultar o modificar el panel administrativo', async () => {
    const list = await request(app.getHttpServer())
      .get(`${API}/admin/reservations`)
      .set(auth(studentToken));
    expect(list.status).toBe(403);

    const stats = await request(app.getHttpServer())
      .get(`${API}/admin/stats`)
      .set(auth(studentToken));
    expect(stats.status).toBe(403);
  });

  it('lista las solicitudes pendientes por defecto', async () => {
    await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });
    await createReservation({
      userId: base.otherStudent.id,
      equipmentId: base.scope.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
      status: 'APPROVED',
    });

    const response = await request(app.getHttpServer())
      .get(`${API}/admin/reservations`)
      .set(auth(adminToken));

    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(1);
    expect(response.body[0].status).toBe('PENDING');
    expect(response.body[0].student.fullName).toBe(base.student.fullName);
  });

  it('filtra por estado y devuelve todo con ALL', async () => {
    await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });
    await createReservation({
      userId: base.otherStudent.id,
      equipmentId: base.scope.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
      status: 'APPROVED',
    });

    const approved = await request(app.getHttpServer())
      .get(`${API}/admin/reservations?status=APPROVED`)
      .set(auth(adminToken));
    expect(approved.status).toBe(200);
    expect(approved.body).toHaveLength(1);
    expect(approved.body[0].status).toBe('APPROVED');

    const all = await request(app.getHttpServer())
      .get(`${API}/admin/reservations?status=ALL`)
      .set(auth(adminToken));
    expect(all.status).toBe(200);
    expect(all.body).toHaveLength(2);
  });

  it('aprueba una reserva y marca el equipo como prestado', async () => {
    const pending = await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${pending.id}/approve`)
      .set(auth(adminToken));

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('APPROVED');
    expect(response.body.reviewedBy).toBe(base.admin.fullName);
    expect(response.body.reviewedAt).toEqual(expect.any(String));

    const equipment = await prisma.equipment.findUniqueOrThrow({ where: { id: base.laptop.id } });
    expect(equipment.status).toBe('BORROWED');

    const audit = await prisma.auditLog.findMany({ where: { event: 'RESERVATION_APPROVED' } });
    expect(audit).toHaveLength(1);
  });

  it('impide aprobar una reserva que se cruza con otra ya aprobada', async () => {
    await createReservation({
      userId: base.otherStudent.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '09:00',
      endTime: '11:00',
      status: 'APPROVED',
    });
    const pending = await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '10:00',
      endTime: '12:00',
    });

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${pending.id}/approve`)
      .set(auth(adminToken));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('otra reserva aprobada');
  });

  it('solo permite aprobar reservas pendientes', async () => {
    const approved = await createApproved(1);

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${approved.id}/approve`)
      .set(auth(adminToken));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('pendientes');
  });

  it('exige un motivo de rechazo de al menos 5 caracteres', async () => {
    const pending = await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });

    const empty = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${pending.id}/reject`)
      .set(auth(adminToken))
      .send({});
    expect(empty.status).toBe(400);

    const short = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${pending.id}/reject`)
      .set(auth(adminToken))
      .send({ reason: 'abc' });
    expect(short.status).toBe(400);

    const stillPending = await prisma.reservation.findUniqueOrThrow({ where: { id: pending.id } });
    expect(stillPending.status).toBe('PENDING');
  });

  it('rechaza una reserva y conserva el motivo para el estudiante', async () => {
    const pending = await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${pending.id}/reject`)
      .set(auth(adminToken))
      .send({ reason: 'Equipo en mantenimiento preventivo' });

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('REJECTED');
    expect(response.body.rejectionReason).toBe('Equipo en mantenimiento preventivo');
    expect(response.body.reviewedBy).toBe(base.admin.fullName);

    const audit = await prisma.auditLog.findMany({ where: { event: 'RESERVATION_REJECTED' } });
    expect(audit).toHaveLength(1);
  });

  it('registra una devolución puntual sin penalizar', async () => {
    const approved = await createApproved(1);

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${approved.id}/return`)
      .set(auth(adminToken));

    expect(response.status).toBe(200);
    expect(response.body.late).toBe(false);
    expect(response.body.status).toBe('RETURNED');
    expect(response.body.penaltyApplied).toBe(false);

    const equipment = await prisma.equipment.findUniqueOrThrow({ where: { id: base.laptop.id } });
    expect(equipment.status).toBe('AVAILABLE');

    const student = await prisma.user.findUniqueOrThrow({ where: { id: base.student.id } });
    expect(student.status).toBe('ACTIVE');
  });

  it('penaliza automáticamente una devolución tardía', async () => {
    const approved = await createApproved(-1);

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${approved.id}/return`)
      .set(auth(adminToken));

    expect(response.status).toBe(200);
    expect(response.body.late).toBe(true);
    expect(response.body.penaltyApplied).toBe(true);

    const equipment = await prisma.equipment.findUniqueOrThrow({ where: { id: base.laptop.id } });
    expect(equipment.status).toBe('AVAILABLE');

    const student = await prisma.user.findUniqueOrThrow({ where: { id: base.student.id } });
    expect(student.status).toBe('PENALIZED');
    expect(student.penaltyUntil).toEqual(expect.any(Date));
    expect(student.penaltyUntil!.getTime()).toBeGreaterThan(Date.now() + 6 * 24 * 60 * 60 * 1000);
    expect(student.penaltyUntil!.getTime()).toBeLessThan(Date.now() + 8 * 24 * 60 * 60 * 1000);

    const audit = await prisma.auditLog.findMany({ where: { event: 'PENALTY_APPLIED' } });
    expect(audit).toHaveLength(1);
    expect(audit[0].detail).toContain(base.student.code);
  });

  it('permite levantar una penalización solo con justificación', async () => {
    await prisma.user.update({ where: { id: base.student.id }, data: { status: 'PENALIZED', penaltyUntil: new Date(Date.now() + 86400000) } });
    const invalid = await request(app.getHttpServer())
      .patch(`${API}/admin/users/${base.student.id}/lift-penalty`)
      .set(auth(adminToken))
      .send({ justification: 'no' });
    expect(invalid.status).toBe(400);

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/users/${base.student.id}/lift-penalty`)
      .set(auth(adminToken))
      .send({ justification: 'Se verificó la devolución del equipo.' });
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ACTIVE');
    const student = await prisma.user.findUniqueOrThrow({ where: { id: base.student.id } });
    expect(student.penaltyUntil).toBeNull();
  });

  it('crea usuarios y valida el formato del código de alumno', async () => {
    const invalid = await request(app.getHttpServer())
      .post(`${API}/admin/users`)
      .set(auth(adminToken))
      .send({ code: 'ABC', fullName: 'Nuevo alumno', password: TEST_PASSWORD, role: 'STUDENT' });
    expect(invalid.status).toBe(400);

    const response = await request(app.getHttpServer())
      .post(`${API}/admin/users`)
      .set(auth(adminToken))
      .send({ code: '20249999', fullName: 'Nuevo alumno', password: TEST_PASSWORD, role: 'STUDENT' });
    expect(response.status).toBe(201);
    expect(response.body.code).toBe('20249999');
  });

  it('solo permite devolver reservas aprobadas', async () => {
    const pending = await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });

    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/${pending.id}/return`)
      .set(auth(adminToken));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('aprobadas');
  });

  it('calcula las métricas administrativas', async () => {
    await createReservation({
      userId: base.student.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
    });
    await createReservation({
      userId: base.otherStudent.id,
      equipmentId: base.scope.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
      status: 'APPROVED',
    });

    const response = await request(app.getHttpServer())
      .get(`${API}/admin/stats`)
      .set(auth(adminToken));

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      pending: 1,
      approved: 1,
      returnsToday: 0,
      penalized: 1,
      equipmentTotal: 4,
      equipmentAvailable: 3,
    });
  });

  it('expone la bitácora de auditoría', async () => {
    const response = await request(app.getHttpServer())
      .get(`${API}/admin/audit?limit=10`)
      .set(auth(adminToken));

    expect(response.status).toBe(200);
    expect(response.body.length).toBeGreaterThan(0);
    expect(response.body[0]).toEqual(
      expect.objectContaining({
        event: expect.any(String),
        actorCode: expect.any(String),
        createdAt: expect.any(String),
      }),
    );
  });

  it('responde 404 al aprobar una reserva inexistente', async () => {
    const response = await request(app.getHttpServer())
      .patch(`${API}/admin/reservations/no-existe/approve`)
      .set(auth(adminToken));

    expect(response.status).toBe(404);
  });
});

import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { API, auth, createTestApp, tokenFor } from './helpers/test-app';
import {
  createReservation,
  dateOffset,
  isoDateOffset,
  prisma,
  resetDatabase,
  seedBase,
  TEST_PASSWORD,
  type BaseFixture,
} from './helpers/test-db';

let app: INestApplication;
let base: BaseFixture;
let studentToken: string;
let adminToken: string;

beforeAll(async () => {
  app = await createTestApp();
});

afterAll(async () => {
  await app.close();
});

beforeEach(async () => {
  await resetDatabase();
  base = await seedBase();
  studentToken = await tokenFor(app, base.student.code, TEST_PASSWORD);
  adminToken = await tokenFor(app, base.admin.code, TEST_PASSWORD);
});

function createPayload(overrides: Record<string, unknown> = {}) {
  return {
    equipmentId: base.laptop.id,
    date: isoDateOffset(1),
    startTime: '08:00',
    endTime: '10:00',
    ...overrides,
  };
}

describe('HU-03 · Reserva de equipos', () => {
  it('registra una reserva pendiente con un equipo disponible', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload());

    expect(response.status).toBe(201);
    expect(response.body).toMatchObject({
      status: 'PENDING',
      date: isoDateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
      penaltyApplied: false,
    });
    expect(response.body.equipment.inventoryCode).toBe('COMP-T01');
    expect(response.body.student.code).toBe('20240001');
  });

  it('bloquea una reserva que se cruza con otra aprobada del mismo equipo', async () => {
    await createReservation({
      userId: base.otherStudent.id,
      equipmentId: base.laptop.id,
      date: dateOffset(1),
      startTime: '09:00',
      endTime: '11:00',
      status: 'APPROVED',
    });

    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload());

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('reserva aprobada');
  });

  it('impide que un estudiante tenga dos reservas activas simultáneas', async () => {
    const first = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload());
    expect(first.status).toBe(201);

    const second = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ equipmentId: base.scope.id, startTime: '09:00', endTime: '11:00' }));

    expect(second.status).toBe(400);
    expect(second.body.message).toContain('una reserva activa');
  });

  it('permite reservas contiguas sin cruce de horario', async () => {
    await createReservation({
      userId: base.student.id,
      equipmentId: base.scope.id,
      date: dateOffset(1),
      startTime: '08:00',
      endTime: '10:00',
      status: 'APPROVED',
    });

    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ startTime: '10:00', endTime: '12:00' }));

    expect(response.status).toBe(201);
  });

  it('rechaza equipos que no están disponibles', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ equipmentId: base.borrowedLaptop.id }));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('no está disponible');
  });

  it('rechaza una reserva en fecha pasada', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ date: '2020-01-01' }));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('fechas pasadas');
  });

  it('valida que la hora de inicio sea anterior a la hora de fin', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ startTime: '12:00', endTime: '10:00' }));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('anterior a la hora de fin');
  });

  it('rechaza reservas que excedan 4 horas continuas', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ startTime: '08:00', endTime: '13:00' }));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('4 horas');
  });

  it('rechaza horarios fuera de la atención del laboratorio', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ startTime: '06:00', endTime: '08:00' }));

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('07:00 a 22:00');
  });

  it('rechaza formatos de hora inválidos mediante validación', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ startTime: '8:00' }));

    expect(response.status).toBe(400);
    expect(Array.isArray(response.body.message)).toBe(true);
  });

  it('impide reservar a una cuenta penalizada', async () => {
    const penalizedToken = await tokenFor(app, base.penalizedStudent.code, TEST_PASSWORD);

    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(penalizedToken))
      .send(createPayload());

    expect(response.status).toBe(400);
    expect(response.body.message).toContain('penalizada');
  });

  it('reactiva automáticamente una penalización vencida', async () => {
    await prisma.user.update({
      where: { id: base.student.id },
      data: { status: 'PENALIZED', penaltyUntil: new Date(Date.now() - 1000) },
    });
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload());
    expect(response.status).toBe(201);
    const student = await prisma.user.findUniqueOrThrow({ where: { id: base.student.id } });
    expect(student.status).toBe('ACTIVE');
    expect(student.penaltyUntil).toBeNull();
  });

  it('impide que un administrador registre reservas', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(adminToken))
      .send(createPayload());

    expect(response.status).toBe(403);
  });

  it('rechaza un equipo inexistente', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .set(auth(studentToken))
      .send(createPayload({ equipmentId: 'equipo-inexistente' }));

    expect(response.status).toBe(404);
    expect(response.body.message).toContain('no existe');
  });

  it('lista únicamente las reservas del estudiante autenticado', async () => {
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
    });

    const response = await request(app.getHttpServer())
      .get(`${API}/reservations/me`)
      .set(auth(studentToken));

    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(1);
    expect(response.body[0].student.code).toBe(base.student.code);
  });

  it('exige autenticación para crear reservas', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/reservations`)
      .send(createPayload());

    expect(response.status).toBe(401);
  });
});

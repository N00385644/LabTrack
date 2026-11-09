import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { API, auth, createTestApp, loginRequest, tokenFor } from './helpers/test-app';
import {
  prisma,
  resetDatabase,
  seedBase,
  TEST_PASSWORD,
  type BaseFixture,
} from './helpers/test-db';

let app: INestApplication;
let base: BaseFixture;

beforeAll(async () => {
  app = await createTestApp();
});

afterAll(async () => {
  await app.close();
});

beforeEach(async () => {
  await resetDatabase();
  base = await seedBase();
});

describe('HU-01 · Autenticación segura', () => {
  it('expone un endpoint de salud público', async () => {
    const response = await request(app.getHttpServer()).get(`${API}/health`);

    expect(response.status).toBe(200);
    expect(response.body).toMatchObject({ status: 'ok', service: 'LabTrack API' });
  });

  it('inicia sesión con credenciales válidas y devuelve un JWT', async () => {
    const response = await loginRequest(app, base.student.code, TEST_PASSWORD);

    expect(response.status).toBe(200);
    expect(response.body.accessToken).toEqual(expect.any(String));
    expect(response.body.user).toMatchObject({
      code: '20240001',
      fullName: 'Estudiante Uno',
      role: 'STUDENT',
      status: 'ACTIVE',
    });
    expect(response.body.user.passwordHash).toBeUndefined();
  });

  it('normaliza el código con espacios y minúsculas', async () => {
    const response = await loginRequest(app, '  20240001  ', TEST_PASSWORD);

    expect(response.status).toBe(200);
    expect(response.body.user.code).toBe('20240001');
  });

  it('rechaza una contraseña incorrecta con el mensaje institucional', async () => {
    const response = await loginRequest(app, base.student.code, 'ContraseñaIncorrecta1!');

    expect(response.status).toBe(401);
    expect(response.body.message).toBe('Credenciales inválidas.');
  });

  it('rechaza un usuario inexistente sin revelar su existencia', async () => {
    const response = await loginRequest(app, '99999999', TEST_PASSWORD);

    expect(response.status).toBe(401);
    expect(response.body.message).toBe('Credenciales inválidas.');
  });

  it('valida los campos obligatorios del login', async () => {
    const response = await request(app.getHttpServer())
      .post(`${API}/auth/login`)
      .send({ code: '', password: '' });

    expect(response.status).toBe(400);
    expect(Array.isArray(response.body.message)).toBe(true);
  });

  it('bloquea la cuenta tras 3 intentos fallidos consecutivos', async () => {
    const first = await loginRequest(app, base.student.code, 'Mala1!');
    const second = await loginRequest(app, base.student.code, 'Mala2!');
    const third = await loginRequest(app, base.student.code, 'Mala3!');

    expect([first.status, second.status, third.status]).toEqual([401, 401, 423]);
    expect(third.body.code).toBe('ACCOUNT_LOCKED');
    expect(third.body.message).toContain('bloqueada temporalmente');

    const stillBlocked = await loginRequest(app, base.student.code, TEST_PASSWORD);
    expect(stillBlocked.status).toBe(423);

    const user = await prisma.user.findUniqueOrThrow({ where: { id: base.student.id } });
    expect(user.lockedUntil).not.toBeNull();

    const audit = await prisma.auditLog.findMany({ where: { event: 'LOGIN_LOCKED' } });
    expect(audit).toHaveLength(1);
    expect(audit[0].actorCode).toBe(base.student.code);
  });

  it('devuelve el perfil autenticado y rechaza peticiones sin token', async () => {
    const token = await tokenFor(app, base.student.code, TEST_PASSWORD);

    const authenticated = await request(app.getHttpServer())
      .get(`${API}/auth/me`)
      .set(auth(token));
    expect(authenticated.status).toBe(200);
    expect(authenticated.body.user.code).toBe(base.student.code);

    const anonymous = await request(app.getHttpServer()).get(`${API}/auth/me`);
    expect(anonymous.status).toBe(401);
  });

  it('cierra sesión correctamente', async () => {
    const token = await tokenFor(app, base.student.code, TEST_PASSWORD);

    const response = await request(app.getHttpServer())
      .post(`${API}/auth/logout`)
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(response.body.message).toContain('Sesión cerrada');
  });

  it('impide que un estudiante acceda al panel administrativo', async () => {
    const token = await tokenFor(app, base.student.code, TEST_PASSWORD);

    const response = await request(app.getHttpServer())
      .get(`${API}/admin/reservations`)
      .set(auth(token));

    expect(response.status).toBe(403);
  });

  it('permite que un administrador acceda a su panel', async () => {
    const token = await tokenFor(app, base.admin.code, TEST_PASSWORD);

    const response = await request(app.getHttpServer())
      .get(`${API}/admin/reservations`)
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(Array.isArray(response.body)).toBe(true);
  });
});

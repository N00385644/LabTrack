import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { API, auth, createTestApp, tokenFor } from './helpers/test-app';
import {
  resetDatabase,
  seedBase,
  TEST_PASSWORD,
  type BaseFixture,
} from './helpers/test-db';

let app: INestApplication;
let base: BaseFixture;
let token: string;

beforeAll(async () => {
  app = await createTestApp();
});

afterAll(async () => {
  await app.close();
});

beforeEach(async () => {
  await resetDatabase();
  base = await seedBase();
  token = await tokenFor(app, base.student.code, TEST_PASSWORD);
});

describe('HU-02 · Catálogo y filtrado de equipos', () => {
  it('lista el catálogo con nombre, código, categoría y estado', async () => {
    const response = await request(app.getHttpServer())
      .get(`${API}/equipment`)
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(4);
    expect(response.body[0]).toEqual(
      expect.objectContaining({
        name: expect.any(String),
        inventoryCode: expect.any(String),
        category: expect.any(String),
        status: expect.any(String),
      }),
    );
  });

  it.each([
    ['Cómputo', 'COMP-T01', 2],
    ['Electrónica', 'ELEC-T01', 1],
    ['Redes', 'RED-T01', 1],
  ])('aplica el filtro exacto por categoría %s', async (category, expectedCode, expectedCount) => {
    const response = await request(app.getHttpServer())
      .get(`${API}/equipment`)
      .query({ category })
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(expectedCount);
    expect(
      response.body.some((item: { inventoryCode: string }) => item.inventoryCode === expectedCode),
    ).toBe(true);
    expect(response.body.every((item: { category: string }) => item.category === category)).toBe(true);
  });

  it('ignora categorías desconocidas para no romper el catálogo', async () => {
    const response = await request(app.getHttpServer())
      .get(`${API}/equipment`)
      .query({ category: 'Categoría inexistente' })
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(4);
  });

  it('filtra únicamente los equipos disponibles', async () => {
    const response = await request(app.getHttpServer())
      .get(`${API}/equipment/available`)
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(response.body).toHaveLength(3);
    expect(response.body.every((item: { status: string }) => item.status === 'AVAILABLE')).toBe(true);
    expect(
      response.body.some((item: { inventoryCode: string }) => item.inventoryCode === 'COMP-T02'),
    ).toBe(false);
  });

  it('calcula los indicadores del catálogo', async () => {
    const response = await request(app.getHttpServer())
      .get(`${API}/equipment/stats`)
      .set(auth(token));

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      total: 4,
      available: 3,
      borrowed: 1,
      pending: 0,
      students: 3,
    });
  });

  it('consulta el detalle de un equipo y responde 404 si no existe', async () => {
    const found = await request(app.getHttpServer())
      .get(`${API}/equipment/${base.laptop.id}`)
      .set(auth(token));
    expect(found.status).toBe(200);
    expect(found.body.inventoryCode).toBe('COMP-T01');

    const missing = await request(app.getHttpServer())
      .get(`${API}/equipment/no-existe`)
      .set(auth(token));
    expect(missing.status).toBe(404);
  });

  it('exige autenticación para consultar el catálogo', async () => {
    const response = await request(app.getHttpServer()).get(`${API}/equipment`);

    expect(response.status).toBe(401);
  });
});

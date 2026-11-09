import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../../src/app.module';

export const API = '/api';

export async function createTestApp(): Promise<INestApplication> {
  const moduleRef = await Test.createTestingModule({ imports: [AppModule] }).compile();
  const app = moduleRef.createNestApplication();
  app.setGlobalPrefix('api');
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );
  await app.init();
  return app;
}

export async function loginRequest(
  app: INestApplication,
  code: string,
  password: string,
) {
  return request(app.getHttpServer()).post(`${API}/auth/login`).send({ code, password });
}

export async function tokenFor(
  app: INestApplication,
  code: string,
  password: string,
): Promise<string> {
  const response = await loginRequest(app, code, password);
  if (response.status !== 200) {
    throw new Error(`Login de prueba falló para ${code}: ${response.status}`);
  }
  return response.body.accessToken as string;
}

export function auth(token: string): { Authorization: string } {
  return { Authorization: `Bearer ${token}` };
}

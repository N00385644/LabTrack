import { PrismaClient, ReservationStatus } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

export const TEST_DATABASE_URL =
  'postgresql://labtrack@127.0.0.1:55432/labtrack_test?schema=public';

export const TEST_PASSWORD = 'Prueba2026!';

export const prisma = new PrismaClient({
  datasources: { db: { url: TEST_DATABASE_URL } },
});

export interface BaseFixture {
  admin: { id: string; code: string; fullName: string };
  student: { id: string; code: string; fullName: string };
  otherStudent: { id: string; code: string; fullName: string };
  penalizedStudent: { id: string; code: string; fullName: string };
  laptop: { id: string; inventoryCode: string; name: string };
  scope: { id: string; inventoryCode: string; name: string };
  router: { id: string; inventoryCode: string; name: string };
  borrowedLaptop: { id: string; inventoryCode: string; name: string };
}

export async function resetDatabase(): Promise<void> {
  await prisma.auditLog.deleteMany();
  await prisma.reservation.deleteMany();
  await prisma.equipment.deleteMany();
  await prisma.user.deleteMany();
}

export async function seedBase(): Promise<BaseFixture> {
  const passwordHash = await bcrypt.hash(TEST_PASSWORD, 4);

  const admin = await prisma.user.create({
    data: {
      code: 'ADMIN01',
      fullName: 'Admin de Prueba',
      email: 'admin@test.labtrack.pe',
      passwordHash,
      role: 'ADMIN',
    },
  });

  const student = await prisma.user.create({
    data: {
      code: 'N00385644',
      fullName: 'Estudiante Uno',
      email: 'uno@test.labtrack.pe',
      passwordHash,
      role: 'STUDENT',
    },
  });

  const otherStudent = await prisma.user.create({
    data: {
      code: 'N00385645',
      fullName: 'Estudiante Dos',
      email: 'dos@test.labtrack.pe',
      passwordHash,
      role: 'STUDENT',
    },
  });

  const penalizedStudent = await prisma.user.create({
    data: {
      code: 'N00385646',
      fullName: 'Estudiante Penalizado',
      email: 'tres@test.labtrack.pe',
      passwordHash,
      role: 'STUDENT',
      status: 'PENALIZED',
    },
  });

  const laptop = await prisma.equipment.create({
    data: {
      name: 'Laptop de pruebas',
      inventoryCode: 'COMP-T01',
      category: 'Cómputo',
      description: 'Equipo para pruebas automatizadas',
      location: 'Laboratorio de prueba',
    },
  });

  const scope = await prisma.equipment.create({
    data: {
      name: 'Osciloscopio de pruebas',
      inventoryCode: 'ELEC-T01',
      category: 'Electrónica',
      description: 'Equipo para pruebas automatizadas',
      location: 'Laboratorio de prueba',
    },
  });

  const router = await prisma.equipment.create({
    data: {
      name: 'Router de pruebas',
      inventoryCode: 'RED-T01',
      category: 'Redes',
      description: 'Equipo para pruebas automatizadas',
      location: 'Laboratorio de prueba',
    },
  });

  const borrowedLaptop = await prisma.equipment.create({
    data: {
      name: 'Laptop prestada',
      inventoryCode: 'COMP-T02',
      category: 'Cómputo',
      description: 'Equipo no disponible',
      location: 'Laboratorio de prueba',
      status: 'BORROWED',
    },
  });

  return {
    admin,
    student,
    otherStudent,
    penalizedStudent,
    laptop,
    scope,
    router,
    borrowedLaptop,
  };
}

export function dateOffset(days: number): Date {
  const now = new Date();
  return new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate() + days));
}

export function isoDateOffset(days: number): string {
  return dateOffset(days).toISOString().slice(0, 10);
}

export async function createReservation(input: {
  userId: string;
  equipmentId: string;
  date: Date;
  startTime: string;
  endTime: string;
  status?: ReservationStatus;
}) {
  return prisma.reservation.create({
    data: {
      userId: input.userId,
      equipmentId: input.equipmentId,
      date: input.date,
      startTime: input.startTime,
      endTime: input.endTime,
      status: input.status ?? 'PENDING',
    },
  });
}

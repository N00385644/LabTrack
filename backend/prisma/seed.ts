import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

const CATEGORIES = ['Cómputo', 'Electrónica', 'Redes'] as const;

const EQUIPMENT: Array<{
  name: string;
  inventoryCode: string;
  category: string;
  description: string;
  location: string;
}> = [
  { name: 'Laptop Dell Latitude 5440', inventoryCode: 'COMP-001', category: 'Cómputo', description: 'Laptop i7, 16 GB RAM, 512 GB SSD', location: 'Laboratorio de Cómputo A' },
  { name: 'Workstation HP Z2 G9', inventoryCode: 'COMP-002', category: 'Cómputo', description: 'Estación de trabajo para diseño y simulación', location: 'Laboratorio de Cómputo A' },
  { name: 'Monitor LG UltraFine 27"', inventoryCode: 'COMP-003', category: 'Cómputo', description: 'Monitor 4K con conexión USB-C', location: 'Laboratorio de Cómputo A' },
  { name: 'Laptop Lenovo ThinkPad E14', inventoryCode: 'COMP-004', category: 'Cómputo', description: 'Laptop para desarrollo de software', location: 'Laboratorio de Cómputo B' },
  { name: 'MacBook Air M2', inventoryCode: 'COMP-005', category: 'Cómputo', description: 'Equipo para desarrollo móvil', location: 'Laboratorio de Cómputo B' },
  { name: 'Teclado mecánico Logitech MX', inventoryCode: 'COMP-006', category: 'Cómputo', description: 'Teclado inalámbrico para prácticas', location: 'Laboratorio de Cómputo B' },
  { name: 'Osciloscopio Tektronix TBS1052B', inventoryCode: 'ELEC-001', category: 'Electrónica', description: 'Osciloscopio digital de 2 canales, 50 MHz', location: 'Laboratorio de Electrónica' },
  { name: 'Multímetro Fluke 87V', inventoryCode: 'ELEC-002', category: 'Electrónica', description: 'Multímetro industrial True RMS', location: 'Laboratorio de Electrónica' },
  { name: 'Fuente de alimentación DC', inventoryCode: 'ELEC-003', category: 'Electrónica', description: 'Fuente regulable 0-30 V / 5 A', location: 'Laboratorio de Electrónica' },
  { name: 'Generador de señales', inventoryCode: 'ELEC-004', category: 'Electrónica', description: 'Generador de funciones 2 MHz', location: 'Laboratorio de Electrónica' },
  { name: 'Kit Arduino Mega 2560', inventoryCode: 'ELEC-005', category: 'Electrónica', description: 'Kit de desarrollo con sensores y actuadores', location: 'Laboratorio de Electrónica' },
  { name: 'Raspberry Pi 5', inventoryCode: 'ELEC-006', category: 'Electrónica', description: 'Placa SBC para proyectos de IoT', location: 'Laboratorio de Electrónica' },
  { name: 'Router Cisco 2911', inventoryCode: 'RED-001', category: 'Redes', description: 'Router modular para prácticas de routing', location: 'Laboratorio de Redes' },
  { name: 'Switch Cisco Catalyst 2960', inventoryCode: 'RED-002', category: 'Redes', description: 'Switch administrable de 24 puertos', location: 'Laboratorio de Redes' },
  { name: 'Access Point Ubiquiti U6', inventoryCode: 'RED-003', category: 'Redes', description: 'Punto de acceso Wi-Fi 6', location: 'Laboratorio de Redes' },
  { name: 'Analizador de red Fluke LinkIQ', inventoryCode: 'RED-004', category: 'Redes', description: 'Tester de cables y certificación de red', location: 'Laboratorio de Redes' },
  { name: 'Patch panel 24 puertos', inventoryCode: 'RED-005', category: 'Redes', description: 'Panel de parcheo categoría 6', location: 'Laboratorio de Redes' },
  { name: 'Probador de cables RJ45', inventoryCode: 'RED-006', category: 'Redes', description: 'Tester de continuidad para cables de red', location: 'Laboratorio de Redes' },
];

function dateOnly(offsetDays: number): Date {
  const now = new Date();
  return new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate() + offsetDays));
}

async function main() {
  const existing = await prisma.user.count();
  if (existing > 0) {
    console.log(`Seed omitido: ya existen ${existing} usuarios.`);
    return;
  }

  console.log('Creando usuarios y equipos de LabTrack...');
  const adminHash = await bcrypt.hash('Admin2026!', 10);
  const studentHash = await bcrypt.hash('Estudiante2026!', 10);
  const loadHash = await bcrypt.hash('Carga2026!', 10);

  const admin = await prisma.user.create({
    data: {
      code: 'ADMIN01',
      fullName: 'Carlos Mendoza Ríos',
      email: 'admin@labtrack.edu.pe',
      passwordHash: adminHash,
      role: 'ADMIN',
    },
  });

  const demo = await prisma.user.create({
    data: {
      code: '20240001',
      fullName: 'Valeria Ramos Quispe',
      email: 'valeria.ramos@labtrack.edu.pe',
      passwordHash: studentHash,
      role: 'STUDENT',
    },
  });

  const diego = await prisma.user.create({
    data: {
      code: '20240002',
      fullName: 'Diego Fernández Soto',
      email: 'diego.fernandez@labtrack.edu.pe',
      passwordHash: studentHash,
      role: 'STUDENT',
    },
  });

  const camila = await prisma.user.create({
    data: {
      code: '20240003',
      fullName: 'Camila Torres Vega',
      email: 'camila.torres@labtrack.edu.pe',
      passwordHash: studentHash,
      role: 'STUDENT',
    },
  });

  if (process.env.SEED_LOAD_USERS !== 'false') {
    for (let index = 1; index <= 60; index += 1) {
      const code = `2024${String(1000 + index).padStart(4, '0')}`;
      await prisma.user.create({
        data: {
          code,
          fullName: `Estudiante de Carga ${String(index).padStart(2, '0')}`,
          email: `${code}@labtrack.edu.pe`,
          passwordHash: loadHash,
          role: 'STUDENT',
        },
      });
    }
  }

  await prisma.equipment.createMany({ data: EQUIPMENT });
  const equipment = await prisma.equipment.findMany();
  const byCode = new Map(equipment.map((item) => [item.inventoryCode, item]));

  await prisma.equipment.update({
    where: { inventoryCode: 'COMP-002' },
    data: { status: 'BORROWED' },
  });
  await prisma.equipment.update({
    where: { inventoryCode: 'RED-002' },
    data: { status: 'BORROWED' },
  });
  await prisma.equipment.update({
    where: { inventoryCode: 'ELEC-003' },
    data: { status: 'BORROWED' },
  });

  if (process.env.SEED_DEMO_RESERVATIONS !== 'false') {
    await prisma.reservation.createMany({
      data: [
        {
          userId: demo.id,
          equipmentId: byCode.get('ELEC-001')!.id,
          date: dateOnly(1),
          startTime: '10:00',
          endTime: '12:00',
          status: 'PENDING',
        },
        {
          userId: camila.id,
          equipmentId: byCode.get('COMP-001')!.id,
          date: dateOnly(1),
          startTime: '14:00',
          endTime: '16:00',
          status: 'PENDING',
        },
        {
          userId: diego.id,
          equipmentId: byCode.get('COMP-002')!.id,
          date: dateOnly(0),
          startTime: '08:00',
          endTime: '10:00',
          status: 'APPROVED',
          reviewedBy: admin.fullName,
          reviewedAt: new Date(),
        },
        {
          userId: camila.id,
          equipmentId: byCode.get('RED-002')!.id,
          date: dateOnly(1),
          startTime: '08:00',
          endTime: '10:00',
          status: 'APPROVED',
          reviewedBy: admin.fullName,
          reviewedAt: new Date(),
        },
        {
          userId: diego.id,
          equipmentId: byCode.get('ELEC-003')!.id,
          date: dateOnly(-1),
          startTime: '08:00',
          endTime: '10:00',
          status: 'APPROVED',
          reviewedBy: admin.fullName,
          reviewedAt: new Date(Date.now() - 172_800_000),
        },
        {
          userId: demo.id,
          equipmentId: byCode.get('ELEC-002')!.id,
          date: dateOnly(-1),
          startTime: '10:00',
          endTime: '12:00',
          status: 'RETURNED',
          reviewedBy: admin.fullName,
          reviewedAt: new Date(Date.now() - 86_400_000),
          returnedAt: new Date(Date.now() - 82_800_000),
        },
      ],
    });
  }

  console.log(`Seed completado: ${await prisma.user.count()} usuarios, ${await prisma.equipment.count()} equipos.`);
  console.log('Categorías:', CATEGORIES.join(', '));
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main(): Promise<void> {
  await prisma.auditLog.deleteMany();
  await prisma.reservation.deleteMany();
  await prisma.equipment.deleteMany();
  await prisma.user.deleteMany();
  console.log('Base de datos de LabTrack limpia. Ejecuta el seed para recargar los datos demo.');
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

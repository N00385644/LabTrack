import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

export const CATEGORIES = ['Cómputo', 'Electrónica', 'Redes'] as const;

@Injectable()
export class EquipmentService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(category?: string) {
    const where = category && CATEGORIES.includes(category as never) ? { category } : {};
    return this.prisma.equipment.findMany({
      where,
      orderBy: [{ category: 'asc' }, { name: 'asc' }],
    });
  }

  async findAvailable() {
    return this.prisma.equipment.findMany({
      where: { status: 'AVAILABLE' },
      orderBy: [{ category: 'asc' }, { name: 'asc' }],
    });
  }

  async findOne(id: string) {
    const equipment = await this.prisma.equipment.findUnique({ where: { id } });
    if (!equipment) {
      throw new NotFoundException('Equipo no encontrado.');
    }
    return equipment;
  }

  async stats() {
    const [total, available, pending, students] = await Promise.all([
      this.prisma.equipment.count(),
      this.prisma.equipment.count({ where: { status: 'AVAILABLE' } }),
      this.prisma.reservation.count({ where: { status: 'PENDING' } }),
      this.prisma.user.count({ where: { role: 'STUDENT' } }),
    ]);
    return {
      total,
      available,
      borrowed: total - available,
      pending,
      students,
    };
  }
}

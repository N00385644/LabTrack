import { HttpStatus, Injectable } from '@nestjs/common';
import { Prisma, ReservationStatus } from '@prisma/client';
import * as bcrypt from 'bcryptjs';
import { AuditService } from '../audit/audit.service';
import { DomainException } from '../common/exceptions/domain.exception';
import {
  reservationInclude,
  serializeReservation,
} from '../common/serializers/reservation.serializer';
import { AuthUser } from '../common/types/auth-user';
import { PrismaService } from '../prisma/prisma.service';
import { CreateUserDto } from './dto/create-user.dto';
import { CreateEquipmentDto, UpdateEquipmentDto } from './dto/equipment.dto';

@Injectable()
export class AdminService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly audit: AuditService,
  ) {}

  async listReservations(status?: string) {
    const validStatuses: ReservationStatus[] = [
      'PENDING',
      'APPROVED',
      'REJECTED',
      'RETURNED',
    ];
    const isKnownStatus =
      status && status !== 'ALL' && validStatuses.includes(status as ReservationStatus);
    let where: Prisma.ReservationWhereInput = { status: 'PENDING' };
    if (status === 'ALL') {
      where = {};
    } else if (isKnownStatus) {
      where = { status: status as ReservationStatus };
    }

    const reservations = await this.prisma.reservation.findMany({
      where,
      include: reservationInclude,
      orderBy: [{ date: 'asc' }, { startTime: 'asc' }],
      take: status === 'ALL' ? 100 : undefined,
    });
    return reservations.map(serializeReservation);
  }

  async stats() {
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const [pending, approved, returnsToday, penalized, total, available] =
      await Promise.all([
        this.prisma.reservation.count({ where: { status: 'PENDING' } }),
        this.prisma.reservation.count({ where: { status: 'APPROVED' } }),
        this.prisma.reservation.count({
          where: { status: 'RETURNED', returnedAt: { gte: startOfDay } },
        }),
        this.prisma.user.count({ where: { status: 'PENALIZED' } }),
        this.prisma.equipment.count(),
        this.prisma.equipment.count({ where: { status: 'AVAILABLE' } }),
      ]);

    return {
      pending,
      approved,
      returnsToday,
      penalized,
      equipmentTotal: total,
      equipmentAvailable: available,
    };
  }

  async dashboardStats() {
    const base = await this.stats();
    const [availableByCategory, punctualReturns, returnedReservations] = await Promise.all([
      this.prisma.equipment.groupBy({ by: ['category'], _count: { _all: true }, where: { status: 'AVAILABLE' } }),
      this.prisma.reservation.count({ where: { status: 'RETURNED', penaltyApplied: false } }),
      this.prisma.reservation.count({ where: { status: 'RETURNED' } }),
    ]);
    return {
      ...base,
      inventoryDistribution: availableByCategory.map((item) => ({
        category: item.category,
        available: item._count._all,
      })),
      punctualityRate: returnedReservations ? Math.round((punctualReturns / returnedReservations) * 100) : 100,
    };
  }

  async createUser(dto: CreateUserDto, admin: AuthUser) {
    const isStudent = dto.role === 'STUDENT';
    const validCode = isStudent ? /^\d{8}$/.test(dto.code) : /^[A-Z0-9]+$/i.test(dto.code);
    if (!validCode) {
      throw new DomainException(isStudent ? 'El código de alumno debe tener exactamente 8 dígitos.' : 'El código administrativo debe ser alfanumérico.');
    }
    const passwordHash = await bcrypt.hash(dto.password, 10);
    try {
      const user = await this.prisma.user.create({
        data: {
          code: dto.code,
          fullName: dto.fullName,
          email: dto.email ?? '',
          passwordHash,
          role: dto.role,
        },
      });
      await this.audit.record('USER_CREATED', { actorCode: admin.code, detail: `Usuario ${user.code}`, userId: user.id });
      return this.safeUser(user);
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002') {
        throw new DomainException('El código de usuario ya está registrado.', HttpStatus.CONFLICT);
      }
      throw error;
    }
  }

  async listUsers() {
    const users = await this.prisma.user.findMany({ orderBy: { createdAt: 'desc' } });
    return users.map((user) => this.safeUser(user));
  }

  async resetPassword(userId: string, password: string, admin: AuthUser) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new DomainException('Usuario no encontrado.', HttpStatus.NOT_FOUND);
    await this.prisma.user.update({ where: { id: userId }, data: { passwordHash: await bcrypt.hash(password, 10), failedAttempts: 0, lockedUntil: null } });
    await this.audit.record('PASSWORD_RESET', { actorCode: admin.code, detail: `Usuario ${user.code}`, userId });
    return { message: 'Contraseña restablecida correctamente.' };
  }

  async unlockUser(userId: string, admin: AuthUser) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new DomainException('Usuario no encontrado.', HttpStatus.NOT_FOUND);
    await this.prisma.user.update({ where: { id: userId }, data: { failedAttempts: 0, lockedUntil: null } });
    await this.audit.record('ACCOUNT_UNLOCKED', { actorCode: admin.code, detail: `Usuario ${user.code}`, userId });
    return { message: 'Cuenta desbloqueada correctamente.' };
  }

  async liftPenalty(userId: string, justification: string, admin: AuthUser) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new DomainException('Usuario no encontrado.', HttpStatus.NOT_FOUND);
    const clean = justification.trim();
    if (clean.length < 5) throw new DomainException('La justificación es obligatoria.');
    const updated = await this.prisma.user.update({ where: { id: userId }, data: { status: 'ACTIVE', penaltyUntil: null } });
    await this.audit.record('PENALTY_LIFTED', { actorCode: admin.code, detail: `Usuario ${user.code}: ${clean}`, userId });
    return this.safeUser(updated);
  }

  async createEquipment(dto: CreateEquipmentDto, admin: AuthUser) {
    const equipment = await this.prisma.equipment.create({ data: { ...dto, description: dto.description ?? '', location: dto.location ?? '', photoUrl: dto.photoUrl ?? '', qrCode: dto.qrCode ?? '' } });
    await this.audit.record('EQUIPMENT_CREATED', { actorCode: admin.code, detail: equipment.inventoryCode, userId: admin.id });
    return equipment;
  }

  async listEquipment() {
    return this.prisma.equipment.findMany({ orderBy: { createdAt: 'desc' } });
  }

  async updateEquipment(id: string, dto: UpdateEquipmentDto, admin: AuthUser) {
    try {
      const equipment = await this.prisma.equipment.update({ where: { id }, data: dto });
      await this.audit.record('EQUIPMENT_UPDATED', { actorCode: admin.code, detail: equipment.inventoryCode, userId: admin.id });
      return equipment;
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2025') {
        throw new DomainException('Equipo no encontrado.', HttpStatus.NOT_FOUND);
      }
      throw error;
    }
  }

  async deleteEquipment(id: string, admin: AuthUser) {
    try {
      const equipment = await this.prisma.equipment.delete({ where: { id } });
      await this.audit.record('EQUIPMENT_DELETED', { actorCode: admin.code, detail: equipment.inventoryCode, userId: admin.id });
      return { message: 'Equipo eliminado correctamente.' };
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2025') {
        throw new DomainException('Equipo no encontrado.', HttpStatus.NOT_FOUND);
      }
      throw error;
    }
  }

  private safeUser(user: { id: string; code: string; fullName: string; email: string; role: string; status: string; penaltyUntil?: Date | null; lockedUntil?: Date | null }) {
    return { id: user.id, code: user.code, fullName: user.fullName, email: user.email, role: user.role, status: user.status, penaltyUntil: user.penaltyUntil?.toISOString() ?? null, lockedUntil: user.lockedUntil?.toISOString() ?? null };
  }

  async approve(reservationId: string, admin: AuthUser) {
    const reservation = await this.prisma.$transaction(
      async (tx) => {
        const current = await tx.reservation.findUnique({
          where: { id: reservationId },
          include: reservationInclude,
        });
        if (!current) {
          throw new DomainException('La reserva no existe.', HttpStatus.NOT_FOUND);
        }
        if (current.status !== 'PENDING') {
          throw new DomainException('Solo se pueden aprobar reservas pendientes.');
        }

        const equipmentOverlap = await tx.reservation.findFirst({
          where: {
            id: { not: reservationId },
            equipmentId: current.equipmentId,
            date: current.date,
            status: 'APPROVED',
            startTime: { lt: current.endTime },
            endTime: { gt: current.startTime },
          },
          select: { id: true },
        });
        if (equipmentOverlap) {
          throw new DomainException('El equipo ya tiene otra reserva aprobada en ese horario.');
        }

        const studentOverlap = await tx.reservation.findFirst({
          where: {
            id: { not: reservationId },
            userId: current.userId,
            date: current.date,
            status: 'APPROVED',
            startTime: { lt: current.endTime },
            endTime: { gt: current.startTime },
          },
          select: { id: true },
        });
        if (studentOverlap) {
          throw new DomainException('El estudiante ya tiene otra reserva aprobada en ese horario.');
        }

        await tx.equipment.update({
          where: { id: current.equipmentId },
          data: { status: 'BORROWED' },
        });

        return tx.reservation.update({
          where: { id: reservationId },
          data: {
            status: 'APPROVED',
            reviewedBy: admin.fullName,
            reviewedAt: new Date(),
          },
          include: reservationInclude,
        });
      },
      { isolationLevel: Prisma.TransactionIsolationLevel.Serializable },
    );

    await this.audit.record('RESERVATION_APPROVED', {
      actorCode: admin.code,
      detail: `Reserva #${reservationId} | Estudiante ${reservation.user.code}`,
      userId: admin.id,
    });
    return serializeReservation(reservation);
  }

  async reject(reservationId: string, admin: AuthUser, reason: string) {
    const cleanReason = reason.trim();
    if (cleanReason.length < 5) {
      throw new DomainException(
        'Debes ingresar un motivo de rechazo de al menos 5 caracteres.',
      );
    }

    const reservation = await this.prisma.$transaction(async (tx) => {
      const current = await tx.reservation.findUnique({
        where: { id: reservationId },
        include: reservationInclude,
      });
      if (!current) {
        throw new DomainException('La reserva no existe.', HttpStatus.NOT_FOUND);
      }
      if (current.status !== 'PENDING') {
        throw new DomainException('Solo se pueden rechazar reservas pendientes.');
      }
      return tx.reservation.update({
        where: { id: reservationId },
        data: {
          status: 'REJECTED',
          rejectionReason: cleanReason,
          reviewedBy: admin.fullName,
          reviewedAt: new Date(),
        },
        include: reservationInclude,
      });
    });

    await this.audit.record('RESERVATION_REJECTED', {
      actorCode: admin.code,
      detail: `Reserva #${reservationId} | Motivo: ${cleanReason}`,
      userId: admin.id,
    });
    return serializeReservation(reservation);
  }

  async markReturned(reservationId: string, admin: AuthUser) {
    const result = await this.prisma.$transaction(async (tx) => {
      const current = await tx.reservation.findUnique({
        where: { id: reservationId },
        include: reservationInclude,
      });
      if (!current) {
        throw new DomainException('La reserva no existe.', HttpStatus.NOT_FOUND);
      }
      if (current.status !== 'APPROVED') {
        throw new DomainException('Solo se pueden devolver reservas aprobadas.');
      }

      const now = new Date();
      const dateString = current.date.toISOString().slice(0, 10);
      const endDateTime = new Date(`${dateString}T${current.endTime}:00`);
      const late = now.getTime() > endDateTime.getTime();

      const reservation = await tx.reservation.update({
        where: { id: reservationId },
        data: {
          status: 'RETURNED',
          returnedAt: now,
          penaltyApplied: late,
        },
        include: reservationInclude,
      });
      await tx.equipment.update({
        where: { id: current.equipmentId },
        data: { status: 'AVAILABLE' },
      });
      if (late) {
        const penaltyUntil = new Date(now);
        penaltyUntil.setDate(penaltyUntil.getDate() + 7);
        await tx.user.update({
          where: { id: current.userId },
          data: { status: 'PENALIZED', penaltyUntil },
        });
      }
      return { reservation, late };
    });

    await this.audit.record('RESERVATION_RETURNED', {
      actorCode: admin.code,
      detail: `Reserva #${reservationId} | Tardía: ${result.late ? 'sí' : 'no'}`,
      userId: admin.id,
    });
    if (result.late) {
      await this.audit.record('PENALTY_APPLIED', {
        actorCode: admin.code,
        detail: `Devolución tardía | Reserva #${reservationId} | Estudiante ${result.reservation.user.code}`,
        userId: admin.id,
      });
    }

    return { ...serializeReservation(result.reservation), late: result.late };
  }

  async recentAudit(limit = 20) {
    return this.audit.recent(limit);
  }

  async findReservation(id: string) {
    const reservation = await this.prisma.reservation.findUnique({
      where: { id },
      include: reservationInclude,
    });
    if (!reservation) throw new DomainException('La reserva no existe.', HttpStatus.NOT_FOUND);
    return serializeReservation(reservation);
  }

  async scan(code: string, action: 'DISPATCH' | 'RETURN', admin: AuthUser) {
    const clean = code.trim();
    if (!clean) throw new DomainException('Debes ingresar un código QR.');
    const reservation = await this.prisma.reservation.findFirst({
      where: {
        status: 'APPROVED',
        OR: [{ user: { code: clean } }, { equipment: { qrCode: clean } }, { equipment: { inventoryCode: clean } }],
      },
      include: reservationInclude,
      orderBy: { date: 'asc' },
    });
    if (!reservation) throw new DomainException('No se encontró un préstamo aprobado para ese código.', HttpStatus.NOT_FOUND);
    if (action === 'RETURN') return this.markReturned(reservation.id, admin);
    return serializeReservation(reservation);
  }
}

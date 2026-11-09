import { HttpStatus, Injectable } from '@nestjs/common';
import { Prisma, ReservationStatus } from '@prisma/client';
import { AuditService } from '../audit/audit.service';
import { DomainException } from '../common/exceptions/domain.exception';
import {
  reservationInclude,
  serializeReservation,
} from '../common/serializers/reservation.serializer';
import { AuthUser } from '../common/types/auth-user';
import { PrismaService } from '../prisma/prisma.service';

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
        await tx.user.update({
          where: { id: current.userId },
          data: { status: 'PENALIZED' },
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
}

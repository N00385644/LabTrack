import { HttpStatus, Injectable } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { AuditService } from '../audit/audit.service';
import { DomainException } from '../common/exceptions/domain.exception';
import {
  reservationInclude,
  serializeReservation,
} from '../common/serializers/reservation.serializer';
import { PrismaService } from '../prisma/prisma.service';
import { CreateReservationDto } from './dto/create-reservation.dto';

const LAB_OPEN = '07:00';
const LAB_CLOSE = '22:00';
const MAX_RESERVATION_HOURS = 4;

export function localDateString(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function timeToMinutes(value: string): number {
  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
}

function parseDateOnly(value: string): Date {
  const date = new Date(`${value}T00:00:00.000Z`);
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new DomainException('La fecha ingresada no es válida.');
  }
  return date;
}

function validateSchedule(dto: CreateReservationDto, date: Date): void {
  const startMinutes = timeToMinutes(dto.startTime);
  const endMinutes = timeToMinutes(dto.endTime);

  if (startMinutes >= endMinutes) {
    throw new DomainException('La hora de inicio debe ser anterior a la hora de fin.');
  }
  if (startMinutes < timeToMinutes(LAB_OPEN) || endMinutes > timeToMinutes(LAB_CLOSE)) {
    throw new DomainException(
      `El horario de atención del laboratorio es de ${LAB_OPEN} a ${LAB_CLOSE}.`,
    );
  }
  if (endMinutes - startMinutes > MAX_RESERVATION_HOURS * 60) {
    throw new DomainException(
      `La reserva no puede exceder ${MAX_RESERVATION_HOURS} horas continuas.`,
    );
  }
  if (dto.date < localDateString()) {
    throw new DomainException('No se pueden registrar reservas en fechas pasadas.');
  }
  const start = new Date(`${dto.date}T${dto.startTime}:00`);
  if (start.getTime() <= Date.now()) {
    throw new DomainException('La reserva debe iniciar en una fecha y hora futuras.');
  }
  if (Number.isNaN(date.getTime())) {
    throw new DomainException('La fecha ingresada no es válida.');
  }
}

@Injectable()
export class ReservationsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly audit: AuditService,
  ) {}

  async create(userId: string, dto: CreateReservationDto, ipAddress = '') {
    const date = parseDateOnly(dto.date);
    validateSchedule(dto, date);

    const reservation = await this.prisma.$transaction(
      async (tx) => {
        const user = await tx.user.findUnique({ where: { id: userId } });
        if (!user) {
          throw new DomainException('Usuario no válido.', HttpStatus.UNAUTHORIZED);
        }
        if (user.role === 'ADMIN') {
          throw new DomainException('Las cuentas administrativas no pueden registrar reservas.');
        }
        if (user.status === 'PENALIZED' && user.penaltyUntil && user.penaltyUntil <= new Date()) {
          await tx.user.update({
            where: { id: user.id },
            data: { status: 'ACTIVE', penaltyUntil: null },
          });
          user.status = 'ACTIVE';
          user.penaltyUntil = null;
        }
        if (user.status === 'PENALIZED') {
          throw new DomainException(
            `Tu cuenta está penalizada hasta el ${user.penaltyUntil?.toISOString().slice(0, 10) ?? 'la fecha indicada'}.`,
          );
        }

        const equipment = await tx.equipment.findUnique({ where: { id: dto.equipmentId } });
        if (!equipment) {
          throw new DomainException('El equipo seleccionado no existe.', HttpStatus.NOT_FOUND);
        }
        if (equipment.status !== 'AVAILABLE') {
          throw new DomainException('El equipo seleccionado no está disponible para reserva.');
        }

        const equipmentOverlap = await tx.reservation.findFirst({
          where: {
            equipmentId: dto.equipmentId,
            date,
            status: 'APPROVED',
            startTime: { lt: dto.endTime },
            endTime: { gt: dto.startTime },
          },
          select: { id: true },
        });
        if (equipmentOverlap) {
          throw new DomainException(
            'El equipo ya tiene una reserva aprobada que se cruza con ese horario.',
          );
        }

        const studentOverlap = await tx.reservation.findFirst({
          where: {
            userId,
            date,
            status: { in: ['PENDING', 'APPROVED'] },
            startTime: { lt: dto.endTime },
            endTime: { gt: dto.startTime },
          },
          select: { id: true },
        });
        if (studentOverlap) {
          throw new DomainException('Solo puedes tener una reserva activa en el mismo horario.');
        }

        return tx.reservation.create({
          data: {
            userId,
            equipmentId: dto.equipmentId,
            date,
            startTime: dto.startTime,
            endTime: dto.endTime,
            status: 'PENDING',
          },
          include: reservationInclude,
        });
      },
      { isolationLevel: Prisma.TransactionIsolationLevel.Serializable },
    );

    await this.audit.record('RESERVATION_CREATED', {
      actorCode: reservation.user.code,
      detail: `Equipo ${reservation.equipment.inventoryCode} | ${dto.date} ${dto.startTime}-${dto.endTime}`,
      ipAddress,
      userId,
    });

    return serializeReservation(reservation);
  }

  async findMine(userId: string) {
    const reservations = await this.prisma.reservation.findMany({
      where: { userId },
      include: reservationInclude,
      orderBy: [{ date: 'desc' }, { startTime: 'desc' }],
    });
    return reservations.map(serializeReservation);
  }
}

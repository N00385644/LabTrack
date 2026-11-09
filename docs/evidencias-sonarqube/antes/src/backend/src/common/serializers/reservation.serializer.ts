import { Prisma } from '@prisma/client';

export const reservationInclude = {
  user: {
    select: {
      id: true,
      code: true,
      fullName: true,
      status: true,
    },
  },
  equipment: {
    select: {
      id: true,
      name: true,
      inventoryCode: true,
      category: true,
      status: true,
      location: true,
    },
  },
} satisfies Prisma.ReservationInclude;

type ReservationWithRelations = Prisma.ReservationGetPayload<{
  include: typeof reservationInclude;
}>;

export function serializeReservation(reservation: ReservationWithRelations) {
  return {
    id: reservation.id,
    date: reservation.date.toISOString().slice(0, 10),
    startTime: reservation.startTime,
    endTime: reservation.endTime,
    status: reservation.status,
    rejectionReason: reservation.rejectionReason,
    penaltyApplied: reservation.penaltyApplied,
    reviewedBy: reservation.reviewedBy,
    reviewedAt: reservation.reviewedAt,
    returnedAt: reservation.returnedAt,
    createdAt: reservation.createdAt,
    student: reservation.user,
    equipment: reservation.equipment,
  };
}

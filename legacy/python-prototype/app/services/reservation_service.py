"""Reglas de negocio de reservas, aprobación, rechazo y devolución."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .. import config
from ..dependencies import DomainError
from ..models import Equipment, Reservation, User
from .auth_service import record_audit


def _overlap_filter(start: time, end: time):
    return (Reservation.start_time < end) & (Reservation.end_time > start)


def _equipment_overlap(
    db: Session,
    equipment_id: int,
    day: date_type,
    start: time,
    end: time,
    exclude_id: int | None = None,
) -> bool:
    query = select(Reservation.id).where(
        Reservation.equipment_id == equipment_id,
        Reservation.date == day,
        Reservation.status == config.RES_APPROVED,
        _overlap_filter(start, end),
    )
    if exclude_id is not None:
        query = query.where(Reservation.id != exclude_id)
    return db.scalar(query) is not None


def _student_overlap(
    db: Session,
    user_id: int,
    day: date_type,
    start: time,
    end: time,
    exclude_id: int | None = None,
) -> bool:
    query = select(Reservation.id).where(
        Reservation.user_id == user_id,
        Reservation.date == day,
        Reservation.status.in_((config.RES_PENDING, config.RES_APPROVED)),
        _overlap_filter(start, end),
    )
    if exclude_id is not None:
        query = query.where(Reservation.id != exclude_id)
    return db.scalar(query) is not None


def _validate_schedule(day: date_type, start: time, end: time) -> None:
    if start >= end:
        raise DomainError("La hora de inicio debe ser anterior a la hora de fin.")
    if start < time(config.LAB_OPEN_HOUR, 0) or end > time(config.LAB_CLOSE_HOUR, 0):
        raise DomainError(
            f"El horario de atención del laboratorio es de {config.LAB_OPEN_HOUR}:00 a "
            f"{config.LAB_CLOSE_HOUR}:00."
        )
    duration = datetime.combine(day, end) - datetime.combine(day, start)
    if duration > timedelta(hours=config.MAX_RESERVATION_HOURS):
        raise DomainError(
            f"La reserva no puede exceder {config.MAX_RESERVATION_HOURS} horas continuas."
        )
    if day < date_type.today():
        raise DomainError("No se pueden registrar reservas en fechas pasadas.")
    if datetime.combine(day, start) <= datetime.now():
        raise DomainError("La reserva debe iniciar en una fecha y hora futuras.")


def create_reservation(
    db: Session,
    user: User,
    equipment_id: int,
    day: date_type,
    start: time,
    end: time,
    ip_address: str = "",
) -> Reservation:
    if user.is_admin:
        raise DomainError("Las cuentas administrativas no pueden registrar reservas.")
    if user.is_penalized:
        raise DomainError(
            "Tu cuenta está penalizada por una devolución tardía. Contacta al encargado del laboratorio."
        )
    _validate_schedule(day, start, end)

    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise DomainError("El equipo seleccionado no existe.")
    if equipment.status != config.EQUIPMENT_AVAILABLE:
        raise DomainError("El equipo seleccionado no está disponible para reserva.")

    if _equipment_overlap(db, equipment.id, day, start, end):
        raise DomainError("El equipo ya tiene una reserva aprobada que se cruza con ese horario.")

    if _student_overlap(db, user.id, day, start, end):
        raise DomainError("Solo puedes tener una reserva activa en el mismo horario.")

    reservation = Reservation(
        user_id=user.id,
        equipment_id=equipment.id,
        date=day,
        start_time=start,
        end_time=end,
        status=config.RES_PENDING,
    )
    db.add(reservation)
    record_audit(
        db,
        "reservation_created",
        user.code,
        f"Equipo {equipment.inventory_code} | {day} {start}-{end}",
        ip_address,
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def get_reservation(db: Session, reservation_id: int) -> Reservation | None:
    return db.scalar(
        select(Reservation)
        .options(joinedload(Reservation.user), joinedload(Reservation.equipment))
        .where(Reservation.id == reservation_id)
    )


def student_reservations(db: Session, user_id: int) -> list[Reservation]:
    return list(
        db.scalars(
            select(Reservation)
            .options(joinedload(Reservation.equipment))
            .where(Reservation.user_id == user_id)
            .order_by(Reservation.date.desc(), Reservation.start_time.desc())
        )
    )


def pending_reservations(db: Session) -> list[Reservation]:
    return list(
        db.scalars(
            select(Reservation)
            .options(joinedload(Reservation.user), joinedload(Reservation.equipment))
            .where(Reservation.status == config.RES_PENDING)
            .order_by(Reservation.date, Reservation.start_time)
        )
    )


def approved_reservations(db: Session) -> list[Reservation]:
    return list(
        db.scalars(
            select(Reservation)
            .options(joinedload(Reservation.user), joinedload(Reservation.equipment))
            .where(Reservation.status == config.RES_APPROVED)
            .order_by(Reservation.date, Reservation.start_time)
        )
    )


def all_reservations(db: Session, limit: int = 60) -> list[Reservation]:
    return list(
        db.scalars(
            select(Reservation)
            .options(joinedload(Reservation.user), joinedload(Reservation.equipment))
            .order_by(Reservation.id.desc())
            .limit(limit)
        )
    )


def approve_reservation(db: Session, reservation_id: int, admin: User) -> Reservation:
    reservation = get_reservation(db, reservation_id)
    if reservation is None:
        raise DomainError("La reserva no existe.", status_code=404)
    if reservation.status != config.RES_PENDING:
        raise DomainError("Solo se pueden aprobar reservas pendientes.")

    if _equipment_overlap(
        db,
        reservation.equipment_id,
        reservation.date,
        reservation.start_time,
        reservation.end_time,
        exclude_id=reservation.id,
    ):
        raise DomainError("El equipo ya tiene otra reserva aprobada en ese horario.")

    if _student_overlap(
        db,
        reservation.user_id,
        reservation.date,
        reservation.start_time,
        reservation.end_time,
        exclude_id=reservation.id,
    ):
        raise DomainError("El estudiante ya tiene otra reserva aprobada en ese horario.")

    reservation.status = config.RES_APPROVED
    reservation.reviewed_by = admin.full_name
    reservation.reviewed_at = datetime.now()
    reservation.equipment.status = config.EQUIPMENT_BORROWED
    record_audit(
        db,
        "reservation_approved",
        admin.code,
        f"Reserva #{reservation.id} | Estudiante {reservation.user.code}",
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def reject_reservation(
    db: Session, reservation_id: int, admin: User, reason: str
) -> Reservation:
    reservation = get_reservation(db, reservation_id)
    if reservation is None:
        raise DomainError("La reserva no existe.", status_code=404)
    if reservation.status != config.RES_PENDING:
        raise DomainError("Solo se pueden rechazar reservas pendientes.")

    clean_reason = (reason or "").strip()
    if len(clean_reason) < 5:
        raise DomainError("Debes ingresar un motivo de rechazo de al menos 5 caracteres.")
    if len(clean_reason) > 300:
        raise DomainError("El motivo de rechazo no puede superar los 300 caracteres.")

    reservation.status = config.RES_REJECTED
    reservation.rejection_reason = clean_reason
    reservation.reviewed_by = admin.full_name
    reservation.reviewed_at = datetime.now()
    record_audit(
        db,
        "reservation_rejected",
        admin.code,
        f"Reserva #{reservation.id} | Motivo: {clean_reason}",
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def return_reservation(db: Session, reservation_id: int, admin: User) -> tuple[Reservation, bool]:
    """Registra la devolución y aplica penalización si corresponde.

    Retorna (reserva, fue_tardia).
    """
    reservation = get_reservation(db, reservation_id)
    if reservation is None:
        raise DomainError("La reserva no existe.", status_code=404)
    if reservation.status != config.RES_APPROVED:
        raise DomainError("Solo se pueden devolver reservas aprobadas.")

    now = datetime.now()
    late = now > reservation.end_datetime

    reservation.status = config.RES_RETURNED
    reservation.returned_at = now
    reservation.equipment.status = config.EQUIPMENT_AVAILABLE
    if late:
        reservation.penalty_applied = True
        reservation.user.status = config.USER_PENALIZED
        record_audit(
            db,
            "penalty_applied",
            admin.code,
            f"Devolución tardía | Reserva #{reservation.id} | Estudiante {reservation.user.code}",
        )
    record_audit(
        db,
        "reservation_returned",
        admin.code,
        f"Reserva #{reservation.id} | Tardía: {'sí' if late else 'no'}",
    )
    db.commit()
    db.refresh(reservation)
    return reservation, late


def admin_stats(db: Session) -> dict[str, int]:
    pending = len(pending_reservations(db))
    approved = len(approved_reservations(db))
    returns_today = sum(
        1
        for reservation in db.scalars(
            select(Reservation).where(Reservation.status == config.RES_RETURNED)
        )
        if reservation.returned_at and reservation.returned_at.date() == date_type.today()
    )
    penalized = (
        db.scalar(
            select(User.id).where(User.status == config.USER_PENALIZED).limit(1)
        )
        is not None
    )
    return {
        "pending": pending,
        "approved": approved,
        "returns_today": returns_today,
        "penalized": int(penalized),
    }

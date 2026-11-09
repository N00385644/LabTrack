"""Consultas de catálogo y estadísticas."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import config
from ..models import Equipment, Reservation, User


def list_equipment(db: Session, category: str | None = None) -> list[Equipment]:
    query = select(Equipment).order_by(Equipment.category, Equipment.name)
    if category in config.CATEGORIES:
        query = query.where(Equipment.category == category)
    return list(db.scalars(query))


def get_equipment(db: Session, equipment_id: int) -> Equipment | None:
    return db.get(Equipment, equipment_id)


def available_equipment(db: Session) -> list[Equipment]:
    return list(
        db.scalars(
            select(Equipment)
            .where(Equipment.status == config.EQUIPMENT_AVAILABLE)
            .order_by(Equipment.category, Equipment.name)
        )
    )


def catalog_stats(db: Session) -> dict[str, int]:
    total = db.scalar(select(func.count(Equipment.id))) or 0
    available = (
        db.scalar(
            select(func.count(Equipment.id)).where(Equipment.status == config.EQUIPMENT_AVAILABLE)
        )
        or 0
    )
    borrowed = total - available
    pending = (
        db.scalar(
            select(func.count(Reservation.id)).where(Reservation.status == config.RES_PENDING)
        )
        or 0
    )
    students = db.scalar(select(func.count(User.id)).where(User.role == config.ROLE_STUDENT)) or 0
    return {
        "total": total,
        "available": available,
        "borrowed": borrowed,
        "pending": pending,
        "students": students,
    }


def category_counts(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(Equipment.category, func.count(Equipment.id)).group_by(Equipment.category)
    ).all()
    counts = {category: 0 for category in config.CATEGORIES}
    for category, count in rows:
        counts[category] = count
    return counts

"""Modelos de dominio de LabTrack."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(150), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")
    status: Mapped[str] = mapped_column(String(20), default="Activo")
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_penalized(self) -> bool:
        return self.status == "Penalizado"


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    inventory_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(20), default="Disponible")
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(80), default="Laboratorio principal")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="equipment")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20), default="Pendiente", index=True)
    rejection_reason: Mapped[str] = mapped_column(String(300), default="")
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    penalty_applied: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped[User] = relationship(back_populates="reservations")
    equipment: Mapped[Equipment] = relationship(back_populates="reservations")

    @property
    def is_overdue(self) -> bool:
        return self.status == "Aprobada" and datetime.now() > datetime.combine(self.date, self.end_time)

    @property
    def start_datetime(self) -> datetime:
        return datetime.combine(self.date, self.start_time)

    @property
    def end_datetime(self) -> datetime:
        return datetime.combine(self.date, self.end_time)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(50), index=True)
    actor_code: Mapped[str] = mapped_column(String(20), default="")
    detail: Mapped[str] = mapped_column(String(300), default="")
    ip_address: Mapped[str] = mapped_column(String(60), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

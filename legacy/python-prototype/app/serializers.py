"""Serializadores JSON para la API (consumida por JMeter y Selenium)."""

from __future__ import annotations

from .models import Equipment, Reservation, User


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "code": user.code,
        "full_name": user.full_name,
        "role": user.role,
        "status": user.status,
    }


def equipment_payload(equipment: Equipment) -> dict:
    return {
        "id": equipment.id,
        "name": equipment.name,
        "inventory_code": equipment.inventory_code,
        "category": equipment.category,
        "status": equipment.status,
        "location": equipment.location,
        "description": equipment.description,
    }


def reservation_payload(reservation: Reservation) -> dict:
    return {
        "id": reservation.id,
        "date": reservation.date.isoformat(),
        "start_time": reservation.start_time.strftime("%H:%M"),
        "end_time": reservation.end_time.strftime("%H:%M"),
        "status": reservation.status,
        "rejection_reason": reservation.rejection_reason,
        "penalty_applied": reservation.penalty_applied,
        "student_code": reservation.user.code,
        "student_name": reservation.user.full_name,
        "equipment_id": reservation.equipment_id,
        "equipment_name": reservation.equipment.name,
        "inventory_code": reservation.equipment.inventory_code,
        "category": reservation.equipment.category,
    }

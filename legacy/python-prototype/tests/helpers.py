"""Utilidades compartidas por las pruebas."""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Equipment, Reservation, User

STUDENT_CODE = "20240001"
STUDENT_PASSWORD = "Estudiante2026!"
ADMIN_CODE = "ADMIN01"
ADMIN_PASSWORD = "Admin2026!"


def extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "No se encontró el token CSRF en el HTML"
    return match.group(1)


def get_csrf(client: TestClient, path: str = "/login") -> str:
    response = client.get(path)
    assert response.status_code == 200
    return extract_csrf(response.text)


def login(
    client: TestClient,
    code: str = STUDENT_CODE,
    password: str = STUDENT_PASSWORD,
):
    token = get_csrf(client, "/login")
    return client.post(
        "/login",
        data={"code": code, "password": password, "csrf_token": token},
    )


def login_admin(client: TestClient):
    return login(client, ADMIN_CODE, ADMIN_PASSWORD)


def api_login(client: TestClient, code: str = STUDENT_CODE, password: str = STUDENT_PASSWORD):
    return client.post("/api/auth/login", json={"code": code, "password": password})


def future_date(days: int = 1) -> date:
    return date.today() + timedelta(days=days)


def get_equipment(db, inventory_code: str) -> Equipment:
    equipment = db.scalar(select(Equipment).where(Equipment.inventory_code == inventory_code))
    assert equipment is not None
    return equipment


def get_user(db, code: str) -> User:
    user = db.scalar(select(User).where(User.code == code))
    assert user is not None
    return user


def add_reservation(
    db,
    *,
    user_code: str = STUDENT_CODE,
    inventory_code: str = "ELEC-001",
    status: str = "Aprobada",
    day: date | None = None,
    start: time = time(10, 0),
    end: time = time(12, 0),
    equipment_status: str | None = None,
    penalty_applied: bool = False,
) -> Reservation:
    user = get_user(db, user_code)
    equipment = get_equipment(db, inventory_code)
    reservation = Reservation(
        user_id=user.id,
        equipment_id=equipment.id,
        date=day or future_date(),
        start_time=start,
        end_time=end,
        status=status,
        penalty_applied=penalty_applied,
        reviewed_by="Carlos Mendoza Ríos" if status in ("Aprobada", "Devuelta") else None,
        reviewed_at=datetime.now() if status in ("Aprobada", "Devuelta") else None,
        returned_at=datetime.now() if status == "Devuelta" else None,
    )
    if equipment_status:
        equipment.status = equipment_status
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation

"""Pruebas de HU-03: reserva de equipos y reglas de negocio."""

from __future__ import annotations

from datetime import date, time, timedelta

from sqlalchemy import func, select

from app.models import Equipment, Reservation, User

from .helpers import (
    STUDENT_CODE,
    add_reservation,
    get_csrf,
    get_equipment,
    get_user,
    login,
    login_admin,
)


def _submit(
    client,
    equipment_id: int,
    day: date,
    start: str = "13:00",
    end: str = "15:00",
    token: str | None = None,
):
    if token is None:
        token = get_csrf(client, f"/reservations/new?equipment_id={equipment_id}")
    return client.post(
        "/reservations",
        data={
            "equipment_id": equipment_id,
            "reservation_date": day.isoformat(),
            "start_time": start,
            "end_time": end,
            "csrf_token": token,
        },
    )


def test_student_can_create_reservation(client, db):
    login(client)
    equipment = get_equipment(db, "ELEC-001")
    tomorrow = date.today() + timedelta(days=1)
    response = _submit(client, equipment.id, tomorrow)
    assert response.status_code == 200
    assert "Reserva registrada correctamente" in response.text
    assert "Pendiente" in response.text

    reservation = db.scalar(select(Reservation).where(Reservation.equipment_id == equipment.id))
    assert reservation is not None
    assert reservation.status == "Pendiente"
    assert reservation.date == tomorrow


def test_reservation_requires_equipment_selection(client):
    login(client)
    tomorrow = date.today() + timedelta(days=1)
    token = get_csrf(client, "/reservations/new")
    response = client.post(
        "/reservations",
        data={
            "equipment_id": "",
            "reservation_date": tomorrow.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00",
            "csrf_token": token,
        },
    )
    assert response.status_code == 422


def test_approved_overlap_is_blocked(client, db):
    login(client)
    tomorrow = date.today() + timedelta(days=1)
    add_reservation(
        db,
        user_code="20240002",
        inventory_code="ELEC-002",
        day=tomorrow,
        start=time(10, 0),
        end=time(12, 0),
    )
    equipment = get_equipment(db, "ELEC-002")
    response = _submit(client, equipment.id, tomorrow, "11:00", "13:00")
    assert "ya tiene una reserva aprobada" in response.text


def test_student_cannot_have_two_active_reservations_in_same_slot(client, db):
    login(client)
    tomorrow = date.today() + timedelta(days=1)
    add_reservation(
        db,
        user_code=STUDENT_CODE,
        inventory_code="ELEC-003",
        status="Pendiente",
        day=tomorrow,
        start=time(10, 0),
        end=time(12, 0),
    )
    equipment = get_equipment(db, "COMP-001")
    response = _submit(client, equipment.id, tomorrow, "10:30", "11:30")
    assert "una reserva activa en el mismo horario" in response.text


def test_non_overlapping_second_reservation_is_allowed(client, db):
    login(client)
    tomorrow = date.today() + timedelta(days=1)
    add_reservation(
        db,
        user_code=STUDENT_CODE,
        inventory_code="ELEC-003",
        status="Pendiente",
        day=tomorrow,
        start=time(10, 0),
        end=time(12, 0),
    )
    equipment = get_equipment(db, "COMP-001")
    response = _submit(client, equipment.id, tomorrow, "13:00", "15:00")
    assert "Reserva registrada correctamente" in response.text
    total = db.scalar(
        select(func.count(Reservation.id)).where(Reservation.user_id == get_user(db, STUDENT_CODE).id)
    )
    assert total == 2


def test_past_date_is_rejected(client, db):
    login(client)
    equipment = get_equipment(db, "COMP-001")
    response = _submit(client, equipment.id, date.today() - timedelta(days=1))
    assert "fechas pasadas" in response.text


def test_start_time_must_be_before_end_time(client, db):
    login(client)
    equipment = get_equipment(db, "COMP-001")
    tomorrow = date.today() + timedelta(days=1)
    response = _submit(client, equipment.id, tomorrow, "15:00", "14:00")
    assert "hora de inicio debe ser anterior" in response.text


def test_reservation_must_be_within_lab_hours(client, db):
    login(client)
    equipment = get_equipment(db, "COMP-001")
    tomorrow = date.today() + timedelta(days=1)
    response = _submit(client, equipment.id, tomorrow, "05:00", "07:30")
    assert "horario de atención" in response.text


def test_reservation_cannot_exceed_four_hours(client, db):
    login(client)
    equipment = get_equipment(db, "COMP-001")
    tomorrow = date.today() + timedelta(days=1)
    response = _submit(client, equipment.id, tomorrow, "10:00", "15:00")
    assert "no puede exceder 4 horas" in response.text


def test_borrowed_equipment_cannot_be_reserved(client, db):
    login(client)
    equipment = get_equipment(db, "COMP-002")
    equipment.status = "Prestado"
    db.commit()
    tomorrow = date.today() + timedelta(days=1)
    response = _submit(client, equipment.id, tomorrow)
    assert "no está disponible para reserva" in response.text


def test_penalized_student_cannot_reserve(client, db):
    login(client)
    user = get_user(db, STUDENT_CODE)
    user.status = "Penalizado"
    db.commit()
    equipment = get_equipment(db, "COMP-001")
    tomorrow = date.today() + timedelta(days=1)
    response = _submit(client, equipment.id, tomorrow)
    assert "cuenta está penalizada" in response.text


def test_admin_cannot_create_reservation(client):
    login_admin(client)
    response = client.get("/reservations/new")
    assert response.url.path == "/admin/pending"
    assert "panel administrativo no registra reservas" in response.text


def test_my_reservations_only_shows_own_records(client, db):
    login(client)
    add_reservation(db, user_code="20240002", inventory_code="COMP-003")
    own = add_reservation(db, user_code=STUDENT_CODE, inventory_code="ELEC-004")
    response = client.get("/reservations/mine")
    assert "Electrónica" in response.text
    assert own.equipment.name in response.text
    assert "COMP-003" not in response.text


def test_reservation_form_preselects_equipment(client, db):
    login(client)
    equipment = get_equipment(db, "ELEC-005")
    response = client.get(f"/reservations/new?equipment_id={equipment.id}")
    assert "Kit Arduino Mega 2560" in response.text
    assert "ELEC-005" in response.text

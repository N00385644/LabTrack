"""Pruebas de HU-05: devolución de equipos y penalización automática."""

from __future__ import annotations

from datetime import date, time, timedelta

from sqlalchemy import select

from app.models import Reservation, User

from .helpers import add_reservation, get_csrf, get_equipment, get_user, login_admin


def test_returns_panel_lists_active_loans(client, db):
    add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-001",
        status="Aprobada",
        equipment_status="Prestado",
    )
    login_admin(client)
    response = client.get("/admin/returns")
    assert response.status_code == 200
    assert "Préstamos activos" in response.text
    assert "Valeria Ramos Quispe" in response.text
    assert "Dentro del plazo" in response.text
    assert "Marcar devolución" in response.text


def test_on_time_return_makes_equipment_available(client, db):
    reservation = add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-001",
        status="Aprobada",
        equipment_status="Prestado",
        day=date.today() + timedelta(days=1),
    )
    login_admin(client)
    token = get_csrf(client, "/admin/returns")
    response = client.post(
        f"/admin/reservations/{reservation.id}/return", data={"csrf_token": token}
    )
    assert response.status_code == 200
    assert "vuelve a estar disponible" in response.text

    db.refresh(reservation)
    assert reservation.status == "Devuelta"
    assert reservation.penalty_applied is False
    assert get_equipment(db, "ELEC-001").status == "Disponible"
    assert get_user(db, "20240001").status == "Activo"


def test_late_return_applies_penalty(client, db):
    reservation = add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-002",
        status="Aprobada",
        equipment_status="Prestado",
        day=date.today() - timedelta(days=1),
        start=time(8, 0),
        end=time(10, 0),
    )
    login_admin(client)
    token = get_csrf(client, "/admin/returns")
    response = client.post(
        f"/admin/reservations/{reservation.id}/return", data={"csrf_token": token}
    )
    assert response.status_code == 200
    assert "Devolución registrada con retraso" in response.text
    assert "Penalizado" in response.text

    db.refresh(reservation)
    assert reservation.status == "Devuelta"
    assert reservation.penalty_applied is True
    assert get_equipment(db, "ELEC-002").status == "Disponible"
    assert get_user(db, "20240001").status == "Penalizado"


def test_overdue_loan_is_highlighted_before_return(client, db):
    add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-002",
        status="Aprobada",
        equipment_status="Prestado",
        day=date.today() - timedelta(days=1),
        start=time(8, 0),
        end=time(10, 0),
    )
    login_admin(client)
    response = client.get("/admin/returns")
    assert "Devolución atrasada" in response.text
    assert "Se aplicará penalización" in response.text


def test_pending_reservation_cannot_be_returned(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    token = get_csrf(client, "/admin/returns")
    response = client.post(
        f"/admin/reservations/{reservation.id}/return", data={"csrf_token": token}
    )
    assert "Solo se pueden devolver reservas aprobadas" in response.text
    db.refresh(reservation)
    assert reservation.status == "Pendiente"


def test_returned_reservation_cannot_be_returned_twice(client, db):
    reservation = add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-001",
        status="Aprobada",
        equipment_status="Prestado",
        day=date.today() + timedelta(days=1),
    )
    login_admin(client)
    token = get_csrf(client, "/admin/returns")
    client.post(f"/admin/reservations/{reservation.id}/return", data={"csrf_token": token})
    response = client.post(
        f"/admin/reservations/{reservation.id}/return", data={"csrf_token": token}
    )
    assert "Solo se pueden devolver reservas aprobadas" in response.text


def test_return_without_csrf_is_rejected(client, db):
    reservation = add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-001",
        status="Aprobada",
        equipment_status="Prestado",
        day=date.today() + timedelta(days=1),
    )
    login_admin(client)
    response = client.post(f"/admin/reservations/{reservation.id}/return", data={})
    assert "La sesión expiró" in response.text
    db.refresh(reservation)
    assert reservation.status == "Aprobada"


def test_penalized_student_sees_warning_on_my_reservations(client, db):
    user = get_user(db, "20240001")
    user.status = "Penalizado"
    db.commit()
    from .helpers import login

    login(client)
    response = client.get("/reservations/mine")
    assert "Cuenta penalizada" in response.text
    assert "No podrás crear nuevas reservas" in response.text

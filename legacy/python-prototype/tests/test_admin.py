"""Pruebas de HU-04: panel de administraciÃ³n y gestiÃ³n de solicitudes."""

from __future__ import annotations

from datetime import date, time, timedelta

from sqlalchemy import select

from app.models import Reservation

from .helpers import add_reservation, get_csrf, get_equipment, login, login_admin


def test_pending_panel_lists_requests_with_required_columns(client, db):
    add_reservation(db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente")
    login_admin(client)
    response = client.get("/admin/pending")
    assert response.status_code == 200
    assert "Valeria Ramos Quispe" in response.text
    assert "Osciloscopio Tektronix TBS1052B" in response.text
    assert "Aprobar" in response.text
    assert "Rechazar" in response.text
    assert "Motivo del rechazo" in response.text


def test_admin_can_approve_reservation(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    token = get_csrf(client, "/admin/pending")
    response = client.post(
        f"/admin/reservations/{reservation.id}/approve",
        data={"csrf_token": token},
    )
    assert response.status_code == 200
    assert "aprobada" in response.text.lower()
    assert "quedÃ³ marcado como prestado" in response.text

    db.refresh(reservation)
    assert reservation.status == "Aprobada"
    assert reservation.reviewed_by == "Carlos Mendoza RÃ­os"
    equipment = get_equipment(db, "ELEC-001")
    assert equipment.status == "Prestado"


def test_reject_requires_a_reason(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    token = get_csrf(client, "/admin/pending")
    response = client.post(
        f"/admin/reservations/{reservation.id}/reject",
        data={"reason": "", "csrf_token": token},
    )
    assert "motivo de rechazo" in response.text
    db.refresh(reservation)
    assert reservation.status == "Pendiente"


def test_reject_with_short_reason_is_blocked(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    token = get_csrf(client, "/admin/pending")
    response = client.post(
        f"/admin/reservations/{reservation.id}/reject",
        data={"reason": "abc", "csrf_token": token},
    )
    assert "al menos 5 caracteres" in response.text
    db.refresh(reservation)
    assert reservation.status == "Pendiente"


def test_admin_can_reject_with_reason(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    token = get_csrf(client, "/admin/pending")
    response = client.post(
        f"/admin/reservations/{reservation.id}/reject",
        data={"reason": "Equipo en mantenimiento preventivo", "csrf_token": token},
    )
    assert "rechazada" in response.text.lower()
    db.refresh(reservation)
    assert reservation.status == "Rechazada"
    assert reservation.rejection_reason == "Equipo en mantenimiento preventivo"


def test_approved_reservation_cannot_be_approved_again(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    token = get_csrf(client, "/admin/pending")
    client.post(f"/admin/reservations/{reservation.id}/approve", data={"csrf_token": token})
    response = client.post(
        f"/admin/reservations/{reservation.id}/approve", data={"csrf_token": token}
    )
    assert "Solo se pueden aprobar reservas pendientes" in response.text


def test_approval_blocks_second_overlapping_equipment_reservation(client, db):
    tomorrow = date.today() + timedelta(days=1)
    first = add_reservation(
        db,
        user_code="20240001",
        inventory_code="ELEC-001",
        status="Pendiente",
        day=tomorrow,
        start=time(10, 0),
        end=time(12, 0),
    )
    second = add_reservation(
        db,
        user_code="20240002",
        inventory_code="ELEC-001",
        status="Pendiente",
        day=tomorrow,
        start=time(11, 0),
        end=time(13, 0),
    )
    login_admin(client)
    token = get_csrf(client, "/admin/pending")
    client.post(f"/admin/reservations/{first.id}/approve", data={"csrf_token": token})
    response = client.post(
        f"/admin/reservations/{second.id}/approve", data={"csrf_token": token}
    )
    assert "ya tiene otra reserva aprobada" in response.text
    db.refresh(second)
    assert second.status == "Pendiente"


def test_approve_without_csrf_token_is_rejected(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    login_admin(client)
    response = client.post(f"/admin/reservations/{reservation.id}/approve", data={})
    assert "La sesiÃ³n expirÃ³" in response.text
    db.refresh(reservation)
    assert reservation.status == "Pendiente"


def test_student_cannot_access_admin_panel(client):
    login(client)
    response = client.get("/admin/pending")
    assert response.status_code == 403
    assert "Acceso restringido" in response.text


def test_admin_cannot_access_student_reservation_form(client):
    login_admin(client)
    response = client.get("/reservations/new")
    assert response.url.path == "/admin/pending"


def test_admin_history_shows_reservations_and_audit(client, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Rechazada"
    )
    reservation.rejection_reason = "Sin disponibilidad"
    db.commit()
    login_admin(client)
    response = client.get("/admin/history")
    assert response.status_code == 200
    assert "Historial y auditorÃ­a" in response.text
    assert "Sin disponibilidad" in response.text
    assert "Eventos recientes" in response.text

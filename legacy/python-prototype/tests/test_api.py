"""Pruebas de la API JSON usada por JMeter y automatizaciones."""

from __future__ import annotations

from datetime import date, time, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Reservation

from .helpers import (
    ADMIN_CODE,
    ADMIN_PASSWORD,
    STUDENT_CODE,
    STUDENT_PASSWORD,
    add_reservation,
    api_login,
    get_equipment,
    future_date,
    login,
)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "LabTrack"}


def test_api_login_success_returns_csrf_token(client):
    response = api_login(client)
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["code"] == STUDENT_CODE
    assert payload["user"]["role"] == "student"
    assert len(payload["csrf_token"]) > 20


def test_api_login_invalid_returns_401(client):
    response = api_login(client, STUDENT_CODE, "incorrecta")
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas."


def test_api_login_lockout_returns_423(client):
    for _ in range(2):
        assert api_login(client, STUDENT_CODE, "incorrecta").status_code == 401
    third = api_login(client, STUDENT_CODE, "incorrecta")
    assert third.status_code == 423
    assert "bloqueada" in third.json()["detail"].lower()
    correct = api_login(client)
    assert correct.status_code == 423


def test_api_equipment_requires_session(client):
    assert client.get("/api/equipment").status_code == 401


def test_api_equipment_filter_and_count(client):
    api_login(client)
    response = client.get("/api/equipment?category=Redes")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 6
    assert all(item["category"] == "Redes" for item in payload["items"])

    all_items = client.get("/api/equipment").json()
    assert all_items["count"] == 18


def test_api_equipment_detail(client):
    api_login(client)
    response = client.get("/api/equipment/1")
    assert response.status_code == 200
    assert response.json()["item"]["inventory_code"] == "COMP-001"


def test_api_create_reservation_with_csrf(client, db):
    login_response = api_login(client)
    csrf = login_response.json()["csrf_token"]
    equipment = get_equipment(db, "COMP-001")
    response = client.post(
        "/api/reservations",
        headers={"X-CSRF-Token": csrf},
        json={
            "equipment_id": equipment.id,
            "date": future_date().isoformat(),
            "start_time": "16:00:00",
            "end_time": "18:00:00",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["item"]["status"] == "Pendiente"
    assert payload["item"]["inventory_code"] == "COMP-001"


def test_api_create_reservation_without_csrf_is_forbidden(client, db):
    api_login(client)
    equipment = get_equipment(db, "COMP-001")
    response = client.post(
        "/api/reservations",
        json={
            "equipment_id": equipment.id,
            "date": future_date().isoformat(),
            "start_time": "16:00:00",
            "end_time": "18:00:00",
        },
    )
    assert response.status_code == 403


def test_api_my_reservations(client, db):
    api_login(client)
    add_reservation(db, user_code=STUDENT_CODE, inventory_code="ELEC-001")
    response = client.get("/api/reservations/mine")
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["student_code"] == STUDENT_CODE


def test_api_admin_approve_and_return_flow(app, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    with TestClient(app) as admin_client:
        login_response = api_login(admin_client, ADMIN_CODE, ADMIN_PASSWORD)
        csrf = login_response.json()["csrf_token"]
        headers = {"X-CSRF-Token": csrf}

        pending = admin_client.get("/api/admin/reservations?status=Pendiente")
        assert pending.status_code == 200
        assert pending.json()["count"] == 1

        approved = admin_client.post(
            f"/api/admin/reservations/{reservation.id}/approve", headers=headers
        )
        assert approved.status_code == 200
        assert approved.json()["item"]["status"] == "Aprobada"

        returns = admin_client.get("/api/admin/reservations?status=Aprobada")
        assert returns.json()["count"] == 1

        returned = admin_client.post(
            f"/api/admin/reservations/{reservation.id}/return", headers=headers
        )
        assert returned.status_code == 200
        assert returned.json()["item"]["status"] == "Devuelta"
        assert returned.json()["late"] is False


def test_api_admin_reject_validates_reason_length(app, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    with TestClient(app) as admin_client:
        csrf = api_login(admin_client, ADMIN_CODE, ADMIN_PASSWORD).json()["csrf_token"]
        response = admin_client.post(
            f"/api/admin/reservations/{reservation.id}/reject",
            headers={"X-CSRF-Token": csrf},
            json={"reason": "abc"},
        )
        assert response.status_code == 422


def test_api_reject_with_valid_reason(app, db):
    reservation = add_reservation(
        db, user_code="20240001", inventory_code="ELEC-001", status="Pendiente"
    )
    with TestClient(app) as admin_client:
        csrf = api_login(admin_client, ADMIN_CODE, ADMIN_PASSWORD).json()["csrf_token"]
        response = admin_client.post(
            f"/api/admin/reservations/{reservation.id}/reject",
            headers={"X-CSRF-Token": csrf},
            json={"reason": "Equipo reservado para mantenimiento"},
        )
        assert response.status_code == 200
        assert response.json()["item"]["status"] == "Rechazada"
        assert "mantenimiento" in response.json()["item"]["rejection_reason"]


def test_api_student_cannot_access_admin_endpoint(client):
    csrf = api_login(client).json()["csrf_token"]
    response = client.get("/api/admin/reservations", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 403


def test_api_logout_requires_csrf(client):
    csrf = api_login(client).json()["csrf_token"]
    assert client.post("/api/auth/logout").status_code == 403
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200


def test_api_rejects_invalid_time_format(client, db):
    csrf = api_login(client).json()["csrf_token"]
    equipment = get_equipment(db, "COMP-001")
    response = client.post(
        "/api/reservations",
        headers={"X-CSRF-Token": csrf},
        json={
            "equipment_id": equipment.id,
            "date": future_date().isoformat(),
            "start_time": "25:99",
            "end_time": "18:00:00",
        },
    )
    assert response.status_code == 422

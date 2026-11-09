"""Pruebas de seguridad, CSRF, cabeceras y controles de acceso."""

from __future__ import annotations

from datetime import date, time, timedelta

from sqlalchemy import func, select

from app.models import AuditLog, Reservation, User
from app.security import hash_password, verify_password

from .helpers import (
    ADMIN_CODE,
    ADMIN_PASSWORD,
    STUDENT_CODE,
    STUDENT_PASSWORD,
    add_reservation,
    get_csrf,
    get_equipment,
    get_user,
    login,
    login_admin,
)


def test_security_headers_are_present(client):
    response = client.get("/login")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_session_cookie_is_http_only_and_same_site(client):
    token = get_csrf(client, "/login")
    response = client.post(
        "/login",
        data={"code": STUDENT_CODE, "password": STUDENT_PASSWORD, "csrf_token": token},
        follow_redirects=False,
    )
    cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_reservation_post_without_csrf_is_blocked(client, db):
    login(client)
    equipment = get_equipment(db, "COMP-001")
    response = client.post(
        "/reservations",
        data={
            "equipment_id": equipment.id,
            "reservation_date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "10:00",
            "end_time": "12:00",
            "csrf_token": "token-falso",
        },
    )
    assert "La sesión expiró" in response.text
    total = db.scalar(select(func.count(Reservation.id)))
    assert total == 0


def test_unauthenticated_api_returns_401_json(client):
    response = client.get("/api/equipment")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_student_cannot_use_admin_api(client):
    login(client)
    response = client.get("/api/admin/reservations")
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_open_redirect_in_next_parameter_is_ignored(client):
    token = get_csrf(client, "/login")
    response = client.post(
        "/login",
        data={
            "code": STUDENT_CODE,
            "password": STUDENT_PASSWORD,
            "csrf_token": token,
            "next": "//evil.example.com/robo",
        },
    )
    assert response.url.host == "testserver"
    assert response.url.path == "/catalog"


def test_rejection_reason_is_escaped_in_student_view(client, db):
    reservation = add_reservation(
        db, user_code=STUDENT_CODE, inventory_code="ELEC-001", status="Rechazada"
    )
    reservation.rejection_reason = "<script>alert('xss')</script>"
    db.commit()
    login(client)
    response = client.get("/reservations/mine")
    assert "<script>alert('xss')</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_audit_log_records_lockout_event(client, db):
    token = get_csrf(client, "/login")
    for _ in range(3):
        client.post(
            "/login",
            data={"code": STUDENT_CODE, "password": "mala", "csrf_token": token},
        )
    events = [row.event for row in db.scalars(select(AuditLog))]
    assert "login_locked" in events


def test_api_404_returns_json(client):
    login(client)
    response = client.get("/api/equipment/999999")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_html_404_returns_error_page(client):
    response = client.get("/ruta-inexistente")
    assert response.status_code == 404
    assert "Página no encontrada" in response.text


def test_password_hash_roundtrip_and_wrong_password():
    encoded = hash_password("ClaveSegura2026!")
    assert verify_password("ClaveSegura2026!", encoded)
    assert not verify_password("clave-segura-2026", encoded)
    assert not verify_password("", encoded)


def test_tampered_session_cookie_is_rejected(client):
    client.cookies.set("labtrack_session", "cookie-manipulada")
    response = client.get("/catalog", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_admin_password_is_not_exposed_in_html(client):
    login_admin(client)
    response = client.get("/admin/history")
    assert ADMIN_PASSWORD not in response.text
    assert "pbkdf2" not in response.text


def test_user_enumeration_uses_same_message(client):
    first = login(client, "00000000", "clave")
    second = login(client, STUDENT_CODE, "clave")
    assert "Credenciales inválidas." in first.text
    assert "Credenciales inválidas." in second.text


def test_penalized_user_record_not_modified_by_failed_login(client, db):
    user = get_user(db, STUDENT_CODE)
    user.status = "Penalizado"
    db.commit()
    login(client, STUDENT_CODE, "incorrecta")
    db.refresh(user)
    assert user.status == "Penalizado"

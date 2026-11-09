"""Pruebas de HU-01: autenticaciÃ³n segura y bloqueo de cuenta."""

from __future__ import annotations

from sqlalchemy import select

from app.models import AuditLog, User
from app.security import hash_password, verify_password

from .helpers import (
    ADMIN_CODE,
    ADMIN_PASSWORD,
    STUDENT_CODE,
    STUDENT_PASSWORD,
    get_csrf,
    login,
    login_admin,
)


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Inicia sesiÃ³n" in response.text
    assert 'name="csrf_token"' in response.text


def test_student_login_success_redirects_to_catalog(client):
    response = login(client)
    assert response.status_code == 200
    assert response.url.path == "/catalog"
    assert "CatÃ¡logo de equipos" in response.text
    assert "Valeria Ramos Quispe" in response.text


def test_admin_login_success_redirects_to_admin_panel(client):
    response = login_admin(client)
    assert response.status_code == 200
    assert response.url.path == "/admin/pending"
    assert "Solicitudes pendientes" in response.text
    assert "Encargado de laboratorio" in response.text


def test_invalid_credentials_show_generic_error(client):
    response = login(client, STUDENT_CODE, "clave-incorrecta")
    assert response.status_code == 200
    assert "Credenciales invÃ¡lidas." in response.text


def test_unknown_user_shows_same_generic_error(client):
    response = login(client, "99999999", "cualquier-clave")
    assert "Credenciales invÃ¡lidas." in response.text
    assert "99999999" not in response.text or "Credenciales invÃ¡lidas." in response.text


def test_three_failed_attempts_lock_the_account(client, db):
    token = get_csrf(client, "/login")
    for _ in range(3):
        response = client.post(
            "/login",
            data={"code": STUDENT_CODE, "password": "incorrecta", "csrf_token": token},
        )
    assert response.status_code == 200
    assert "Cuenta bloqueada temporalmente" in response.text

    user = db.scalar(select(User).where(User.code == STUDENT_CODE))
    assert user.locked_until is not None
    assert user.failed_attempts == 0

    blocked = client.post(
        "/login",
        data={"code": STUDENT_CODE, "password": STUDENT_PASSWORD, "csrf_token": token},
    )
    assert "Cuenta bloqueada temporalmente" in blocked.text


def test_successful_login_resets_failed_attempts(client, db):
    token = get_csrf(client, "/login")
    client.post(
        "/login",
        data={"code": STUDENT_CODE, "password": "incorrecta", "csrf_token": token},
    )
    user = db.scalar(select(User).where(User.code == STUDENT_CODE))
    assert user.failed_attempts == 1

    response = client.post(
        "/login",
        data={"code": STUDENT_CODE, "password": STUDENT_PASSWORD, "csrf_token": token},
    )
    assert response.url.path == "/catalog"
    db.refresh(user)
    assert user.failed_attempts == 0
    assert user.locked_until is None


def test_audit_log_records_login_events(client, db):
    login(client, STUDENT_CODE, "mala")
    login(client)
    events = [row.event for row in db.scalars(select(AuditLog).order_by(AuditLog.id))]
    assert "login_failed" in events
    assert "login_success" in events


def test_logout_clears_session(client):
    login(client)
    token = get_csrf(client, "/catalog")
    response = client.post("/logout", data={"csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    protected = client.get("/catalog", follow_redirects=False)
    assert protected.status_code == 303
    assert protected.headers["location"].startswith("/login")


def test_protected_route_without_session_redirects_to_login(client):
    response = client.get("/catalog", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/catalog"


def test_login_without_csrf_token_is_rejected(client):
    response = client.post(
        "/login",
        data={"code": STUDENT_CODE, "password": STUDENT_PASSWORD},
    )
    assert response.url.path == "/login"
    assert "La sesiÃ³n expirÃ³" in response.text


def test_sql_injection_does_not_bypass_login(client):
    response = login(client, "' OR '1'='1", "' OR '1'='1")
    assert response.status_code == 200
    assert "Credenciales invÃ¡lidas." in response.text
    assert response.url.path == "/login"


def test_password_hash_is_not_plaintext(db):
    user = db.scalar(select(User).where(User.code == ADMIN_CODE))
    assert user.password_hash != ADMIN_PASSWORD
    assert user.password_hash.startswith("pbkdf2_sha256$")
    assert verify_password(ADMIN_PASSWORD, user.password_hash)
    assert not verify_password("otra-clave", user.password_hash)


def test_password_hash_is_salted():
    first = hash_password("misma-clave")
    second = hash_password("misma-clave")
    assert first != second
    assert verify_password("misma-clave", first)
    assert verify_password("misma-clave", second)

"""Primitivas de seguridad: hash de contraseñas, CSRF y cabeceras."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets

from fastapi import Request

PBKDF2_ITERATIONS = 260_000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    """Genera un hash PBKDF2-SHA256 con sal aleatoria por usuario."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    """Verifica una contraseña sin filtrar información por tiempo de respuesta."""
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        candidate = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM, password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError):
        return False


# Hash de relleno para igualar el tiempo de respuesta cuando el usuario no existe.
DUMMY_PASSWORD_HASH = hash_password("dummy-password-not-used")


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, token: str | None) -> bool:
    expected = request.session.get("csrf_token")
    if not expected or not token:
        return False
    return hmac.compare_digest(expected, token)


def add_flash(request: Request, message: str, category: str = "success") -> None:
    flashes = request.session.setdefault("flashes", [])
    flashes.append({"message": message, "category": category})
    request.session["flashes"] = flashes


def pop_flashes(request: Request) -> list[dict[str, str]]:
    return request.session.pop("flashes", [])


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "style-src 'self'; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'"
    ),
}

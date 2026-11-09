"""Servicios de autenticación y auditoría."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import config
from ..models import AuditLog, User
from ..security import DUMMY_PASSWORD_HASH, verify_password


def record_audit(
    db: Session,
    event: str,
    actor_code: str = "",
    detail: str = "",
    ip_address: str = "",
) -> None:
    db.add(
        AuditLog(
            event=event,
            actor_code=actor_code,
            detail=detail[:300],
            ip_address=ip_address[:60],
        )
    )


def authenticate(
    db: Session,
    code: str,
    password: str,
    ip_address: str = "",
) -> tuple[User | None, str | None, str]:
    """Valida credenciales aplicando bloqueo tras 3 intentos fallidos.

    Retorna (usuario, mensaje_error, código_error).
    """
    normalized = (code or "").strip().upper()
    now = datetime.now()
    user = db.scalar(select(User).where(func.upper(User.code) == normalized))

    if user is None:
        # Igualar el costo de verificación para no filtrar si el usuario existe.
        verify_password(password or "", DUMMY_PASSWORD_HASH)
        record_audit(db, "login_failed", normalized, "Usuario inexistente", ip_address)
        db.commit()
        return None, "Credenciales inválidas.", "invalid"

    if user.locked_until and user.locked_until > now:
        minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        record_audit(db, "login_blocked", user.code, "Intento en cuenta bloqueada", ip_address)
        db.commit()
        return (
            None,
            f"Cuenta bloqueada temporalmente por seguridad. Intenta nuevamente en {minutes} minuto(s).",
            "locked",
        )

    if user.locked_until and user.locked_until <= now:
        user.locked_until = None
        user.failed_attempts = 0

    if not verify_password(password or "", user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= config.MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=config.LOCKOUT_MINUTES)
            user.failed_attempts = 0
            record_audit(
                db,
                "login_locked",
                user.code,
                f"Bloqueo automático por {config.MAX_FAILED_ATTEMPTS} intentos fallidos",
                ip_address,
            )
            db.commit()
            return (
                None,
                "Cuenta bloqueada temporalmente por seguridad. "
                f"Intenta nuevamente en {config.LOCKOUT_MINUTES} minutos.",
                "locked",
            )
        record_audit(db, "login_failed", user.code, "Contraseña incorrecta", ip_address)
        db.commit()
        return None, "Credenciales inválidas.", "invalid"

    user.failed_attempts = 0
    user.locked_until = None
    record_audit(db, "login_success", user.code, "Inicio de sesión exitoso", ip_address)
    db.commit()
    db.refresh(user)
    return user, None, ""


def recent_audit_events(db: Session, limit: int = 8) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)))

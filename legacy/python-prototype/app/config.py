"""Configuración central de LabTrack.

Las credenciales y secretos se leen desde variables de entorno. En desarrollo,
si no existe LABTRACK_SECRET_KEY, se genera una clave efímera (las sesiones se
invalidan al reiniciar), evitando secretos hardcodeados en el repositorio.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_DATABASE_URL = f"sqlite:///{(INSTANCE_DIR / 'labtrack.db').as_posix()}"

APP_NAME = "LabTrack"
APP_SUBTITLE = "Gestión de laboratorios"
SESSION_COOKIE = "labtrack_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 8

MAX_FAILED_ATTEMPTS = 3
LOCKOUT_MINUTES = 5

LAB_OPEN_HOUR = 7
LAB_CLOSE_HOUR = 22
MAX_RESERVATION_HOURS = 4

CATEGORIES = ("Cómputo", "Electrónica", "Redes")
EQUIPMENT_AVAILABLE = "Disponible"
EQUIPMENT_BORROWED = "Prestado"

ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"

USER_ACTIVE = "Activo"
USER_PENALIZED = "Penalizado"

RES_PENDING = "Pendiente"
RES_APPROVED = "Aprobada"
RES_REJECTED = "Rechazada"
RES_RETURNED = "Devuelta"


def get_database_url() -> str:
    return os.getenv("LABTRACK_DATABASE_URL", DEFAULT_DATABASE_URL)


def get_secret_key() -> str:
    return os.getenv("LABTRACK_SECRET_KEY") or secrets.token_hex(32)

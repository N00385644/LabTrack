"""API JSON de LabTrack.

Diseñada para ser consumida por las pruebas de carga de JMeter y por
integraciones externas. Los endpoints de escritura exigen el token CSRF
entregado en el login.
"""

from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..dependencies import DomainError, require_admin, require_user
from ..models import User
from ..security import add_flash, get_csrf_token, validate_csrf
from ..serializers import equipment_payload, reservation_payload, user_payload
from ..services.auth_service import authenticate
from ..services.catalog_service import get_equipment, list_equipment
from ..services.reservation_service import (
    all_reservations,
    approve_reservation,
    approved_reservations,
    create_reservation,
    pending_reservations,
    reject_reservation,
    return_reservation,
    student_reservations,
)

router = APIRouter(prefix="/api")


class LoginPayload(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=128)


class ReservationPayload(BaseModel):
    equipment_id: int
    date: date
    start_time: time
    end_time: time


class RejectPayload(BaseModel):
    reason: str = Field(min_length=5, max_length=300)


def require_csrf(
    request: Request,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    if not validate_csrf(request, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token CSRF inválido o ausente.",
        )


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "LabTrack"}


@router.post("/auth/login")
def api_login(payload: LoginPayload, request: Request, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else ""
    user, error, error_code = authenticate(db, payload.code, payload.password, ip_address)
    if error:
        code = status.HTTP_423_LOCKED if error_code == "locked" else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=code, detail=error)
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    return {
        "message": "Autenticación exitosa",
        "user": user_payload(user),
        "csrf_token": get_csrf_token(request),
    }


@router.post("/auth/logout")
def api_logout(request: Request, _: None = Depends(require_csrf)):
    request.session.clear()
    return {"message": "Sesión cerrada"}


@router.get("/auth/me")
def api_me(user: User = Depends(require_user)):
    return {"user": user_payload(user)}


@router.get("/equipment")
def api_equipment(
    category: str | None = Query(default=None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    items = list_equipment(db, category)
    return {
        "category": category if category in config.CATEGORIES else None,
        "count": len(items),
        "items": [equipment_payload(item) for item in items],
    }


@router.get("/equipment/{equipment_id}")
def api_equipment_detail(
    equipment_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    equipment = get_equipment(db, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")
    return {"item": equipment_payload(equipment)}


@router.get("/reservations/mine")
def api_my_reservations(user: User = Depends(require_user), db: Session = Depends(get_db)):
    reservations = student_reservations(db, user.id)
    return {"count": len(reservations), "items": [reservation_payload(r) for r in reservations]}


@router.post("/reservations", status_code=status.HTTP_201_CREATED)
def api_create_reservation(
    payload: ReservationPayload,
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
):
    ip_address = request.client.host if request.client else ""
    try:
        reservation = create_reservation(
            db,
            user,
            payload.equipment_id,
            payload.date,
            payload.start_time,
            payload.end_time,
            ip_address,
        )
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"message": "Reserva registrada", "item": reservation_payload(reservation)}


@router.get("/admin/reservations")
def api_admin_reservations(
    status_filter: str = Query(default="Pendiente", alias="status"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if status_filter == config.RES_APPROVED:
        items = approved_reservations(db)
    elif status_filter == config.RES_PENDING:
        items = pending_reservations(db)
    else:
        items = all_reservations(db)
    return {"count": len(items), "items": [reservation_payload(r) for r in items]}


@router.post("/admin/reservations/{reservation_id}/approve")
def api_approve(
    reservation_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
):
    try:
        reservation = approve_reservation(db, reservation_id, admin)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"message": "Reserva aprobada", "item": reservation_payload(reservation)}


@router.post("/admin/reservations/{reservation_id}/reject")
def api_reject(
    reservation_id: int,
    payload: RejectPayload,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
):
    try:
        reservation = reject_reservation(db, reservation_id, admin, payload.reason)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"message": "Reserva rechazada", "item": reservation_payload(reservation)}


@router.post("/admin/reservations/{reservation_id}/return")
def api_return(
    reservation_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
):
    try:
        reservation, late = return_reservation(db, reservation_id, admin)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {
        "message": "Devolución registrada",
        "late": late,
        "penalty_applied": reservation.penalty_applied,
        "item": reservation_payload(reservation),
    }

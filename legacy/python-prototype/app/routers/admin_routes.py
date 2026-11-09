"""Rutas HTML del panel de administración."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import DomainError, require_admin
from ..security import add_flash, validate_csrf
from ..services.auth_service import recent_audit_events
from ..services.reservation_service import (
    admin_stats,
    all_reservations,
    approve_reservation,
    approved_reservations,
    pending_reservations,
    reject_reservation,
    return_reservation,
)
from ..templating import render

router = APIRouter(prefix="/admin")


def _guard_csrf(request: Request, token: str, fallback: str) -> RedirectResponse | None:
    if validate_csrf(request, token):
        return None
    add_flash(request, "La sesión expiró. Vuelve a intentarlo.", "error")
    return RedirectResponse(fallback, status_code=303)


@router.get("/pending")
def pending_panel(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return render(
        request,
        "admin_pending.html",
        {
            "reservations": pending_reservations(db),
            "stats": admin_stats(db),
            "section": "pending",
        },
    )


@router.post("/reservations/{reservation_id}/approve")
def approve(
    reservation_id: int,
    request: Request,
    csrf_token: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    redirect = _guard_csrf(request, csrf_token, "/admin/pending")
    if redirect:
        return redirect
    try:
        reservation = approve_reservation(db, reservation_id, admin)
        add_flash(
            request,
            f"Reserva #{reservation.id} aprobada. El equipo quedó marcado como prestado.",
            "success",
        )
    except DomainError as exc:
        add_flash(request, exc.message, "error")
    return RedirectResponse("/admin/pending", status_code=303)


@router.post("/reservations/{reservation_id}/reject")
def reject(
    reservation_id: int,
    request: Request,
    reason: str = Form(""),
    csrf_token: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    redirect = _guard_csrf(request, csrf_token, "/admin/pending")
    if redirect:
        return redirect
    try:
        reservation = reject_reservation(db, reservation_id, admin, reason)
        add_flash(
            request,
            f"Reserva #{reservation.id} rechazada. Se notificó el motivo registrado.",
            "success",
        )
    except DomainError as exc:
        add_flash(request, exc.message, "error")
    return RedirectResponse("/admin/pending", status_code=303)


@router.get("/returns")
def returns_panel(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return render(
        request,
        "admin_returns.html",
        {
            "reservations": approved_reservations(db),
            "stats": admin_stats(db),
            "section": "returns",
        },
    )


@router.post("/reservations/{reservation_id}/return")
def mark_return(
    reservation_id: int,
    request: Request,
    csrf_token: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    redirect = _guard_csrf(request, csrf_token, "/admin/returns")
    if redirect:
        return redirect
    try:
        reservation, late = return_reservation(db, reservation_id, admin)
        if late:
            add_flash(
                request,
                f"Devolución registrada con retraso. El estudiante {reservation.user.code} "
                "fue marcado como Penalizado.",
                "warning",
            )
        else:
            add_flash(
                request,
                f"Devolución registrada a tiempo. El equipo {reservation.equipment.inventory_code} "
                "vuelve a estar disponible.",
                "success",
            )
    except DomainError as exc:
        add_flash(request, exc.message, "error")
    return RedirectResponse("/admin/returns", status_code=303)


@router.get("/history")
def history_panel(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return render(
        request,
        "admin_history.html",
        {
            "reservations": all_reservations(db),
            "events": recent_audit_events(db, limit=10),
            "stats": admin_stats(db),
            "section": "history",
        },
    )

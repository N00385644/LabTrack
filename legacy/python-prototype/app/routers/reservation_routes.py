"""Rutas HTML de reservas del estudiante."""

from __future__ import annotations

from datetime import date, time, timedelta

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import DomainError, require_user
from ..security import add_flash, validate_csrf
from ..services.catalog_service import available_equipment, get_equipment
from ..services.reservation_service import create_reservation, student_reservations
from ..templating import render

router = APIRouter()


@router.get("/reservations/new")
def new_reservation_page(
    request: Request,
    equipment_id: int | None = Query(default=None),
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    if user.is_admin:
        add_flash(request, "El panel administrativo no registra reservas.", "warning")
        return RedirectResponse("/admin/pending", status_code=303)
    selected = get_equipment(db, equipment_id) if equipment_id else None
    if selected is not None and selected.status != "Disponible":
        selected = None
    return render(
        request,
        "reservation_form.html",
        {
            "equipment_list": available_equipment(db),
            "selected_equipment": selected,
            "today": date.today().isoformat(),
            "tomorrow": (date.today() + timedelta(days=1)).isoformat(),
        },
    )


@router.post("/reservations")
def create_reservation_submit(
    request: Request,
    equipment_id: int = Form(...),
    reservation_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    csrf_token: str = Form(""),
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    if not validate_csrf(request, csrf_token):
        add_flash(request, "La sesión expiró. Vuelve a intentarlo.", "error")
        return RedirectResponse("/reservations/new", status_code=303)

    try:
        day = date.fromisoformat(reservation_date)
        start = time.fromisoformat(start_time)
        end = time.fromisoformat(end_time)
    except ValueError:
        add_flash(request, "La fecha u hora ingresada no es válida.", "error")
        return RedirectResponse("/reservations/new", status_code=303)

    ip_address = request.client.host if request.client else ""
    try:
        create_reservation(db, user, equipment_id, day, start, end, ip_address)
    except DomainError as exc:
        add_flash(request, exc.message, "error")
        return RedirectResponse(
            f"/reservations/new?equipment_id={equipment_id}", status_code=303
        )

    add_flash(
        request,
        "Reserva registrada correctamente. Queda pendiente de aprobación por el encargado.",
        "success",
    )
    return RedirectResponse("/reservations/mine", status_code=303)


@router.get("/reservations/mine")
def my_reservations(
    request: Request,
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    if user.is_admin:
        return RedirectResponse("/admin/history", status_code=303)
    return render(
        request,
        "my_reservations.html",
        {
            "reservations": student_reservations(db, user.id),
            "today": date.today(),
        },
    )

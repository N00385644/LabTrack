"""Rutas HTML de autenticación."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_optional_user
from ..security import add_flash, validate_csrf
from ..services.auth_service import authenticate
from ..templating import render

router = APIRouter()


def _safe_next(value: str | None) -> str | None:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return None


@router.get("/login")
def login_page(request: Request, next: str | None = None, user=Depends(get_optional_user)):
    if user is not None:
        target = "/admin/pending" if user.is_admin else "/catalog"
        return RedirectResponse(target, status_code=303)
    return render(request, "login.html", {"next_url": _safe_next(next), "hide_nav": True})


@router.post("/login")
def login_submit(
    request: Request,
    code: str = Form(""),
    password: str = Form(""),
    csrf_token: str = Form(""),
    next: str = Form(""),
    db: Session = Depends(get_db),
):
    if not validate_csrf(request, csrf_token):
        add_flash(request, "La sesión expiró. Vuelve a intentarlo.", "error")
        return RedirectResponse("/login", status_code=303)

    ip_address = request.client.host if request.client else ""
    user, error, error_code = authenticate(db, code, password, ip_address)
    if error:
        add_flash(request, error, "error" if error_code == "invalid" else "warning")
        return RedirectResponse("/login", status_code=303)

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    add_flash(request, f"Bienvenido(a), {user.full_name}.", "success")
    target = _safe_next(next) or ("/admin/pending" if user.is_admin else "/catalog")
    return RedirectResponse(target, status_code=303)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form("")):
    if validate_csrf(request, csrf_token):
        request.session.clear()
    return RedirectResponse("/login", status_code=303)

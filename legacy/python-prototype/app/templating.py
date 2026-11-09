"""Renderizado de plantillas con contexto común."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from . import config
from .security import get_csrf_token, pop_flashes

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
):
    current_user = getattr(request.state, "user", None)
    ctx: dict[str, Any] = {
        "request": request,
        "app_name": config.APP_NAME,
        "app_subtitle": config.APP_SUBTITLE,
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
        "flashes": pop_flashes(request),
        "categories": config.CATEGORIES,
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=ctx,
        status_code=status_code,
    )

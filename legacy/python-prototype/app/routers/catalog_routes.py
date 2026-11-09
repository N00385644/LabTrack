"""Rutas HTML del catálogo de equipos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..dependencies import require_user
from ..services.catalog_service import catalog_stats, category_counts, list_equipment
from ..templating import render

router = APIRouter()


@router.get("/")
def home(user=Depends(require_user)):
    from fastapi.responses import RedirectResponse

    target = "/admin/pending" if user.is_admin else "/catalog"
    return RedirectResponse(target, status_code=303)


@router.get("/catalog")
def catalog(
    request: Request,
    category: str | None = Query(default=None),
    user=Depends(require_user),
    db: Session = Depends(get_db),
):
    selected = category if category in config.CATEGORIES else None
    equipment = list_equipment(db, selected)
    return render(
        request,
        "catalog.html",
        {
            "equipment": equipment,
            "selected_category": selected,
            "stats": catalog_stats(db),
            "category_counts": category_counts(db),
            "is_empty_filter": selected is not None and len(equipment) == 0,
        },
    )

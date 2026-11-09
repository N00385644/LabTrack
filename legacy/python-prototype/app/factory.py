"""Fábrica de la aplicación FastAPI de LabTrack."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import config
from .database import Base, build_engine, build_session_factory
from .routers import admin_routes, api, auth_routes, catalog_routes, reservation_routes
from .security import SECURITY_HEADERS, add_flash
from .seed import seed_database
from .templating import render

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(
    database_url: str | None = None,
    secret_key: str | None = None,
    seed: bool = True,
    include_load_users: bool = True,
) -> FastAPI:
    app = FastAPI(
        title="LabTrack API",
        description="Sistema de gestión de laboratorios - Calidad y Pruebas de Software",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    engine = build_engine(database_url or config.get_database_url())
    Base.metadata.create_all(engine)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    if seed:
        with app.state.session_factory() as db:
            seed_database(db, include_load_users=include_load_users)

    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key or config.get_secret_key(),
        session_cookie=config.SESSION_COOKIE,
        max_age=config.SESSION_MAX_AGE_SECONDS,
        same_site="lax",
        https_only=False,
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        return response

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(auth_routes.router)
    app.include_router(catalog_routes.router)
    app.include_router(reservation_routes.router)
    app.include_router(admin_routes.router)
    app.include_router(api.router)

    @app.exception_handler(status.HTTP_401_UNAUTHORIZED)
    async def unauthorized_handler(request: Request, exc):
        detail = getattr(exc, "detail", "Sesión requerida")
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=401,
                content={"detail": detail, "code": "unauthorized"},
            )
        add_flash(request, "Debes iniciar sesión para continuar.", "warning")
        return RedirectResponse(f"/login?next={request.url.path}", status_code=303)

    @app.exception_handler(status.HTTP_403_FORBIDDEN)
    async def forbidden_handler(request: Request, exc):
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=403,
                content={"detail": "No tienes permisos para esta acción.", "code": "forbidden"},
            )
        return render(
            request,
            "error.html",
            {
                "error_code": 403,
                "error_title": "Acceso restringido",
                "error_message": "Tu cuenta no tiene permisos para acceder a esta sección.",
            },
            status_code=403,
        )

    @app.exception_handler(status.HTTP_404_NOT_FOUND)
    async def not_found_handler(request: Request, exc):
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=404, content={"detail": "Recurso no encontrado.", "code": "not_found"}
            )
        return render(
            request,
            "error.html",
            {
                "error_code": 404,
                "error_title": "Página no encontrada",
                "error_message": "La dirección solicitada no existe en LabTrack.",
            },
            status_code=404,
        )

    return app

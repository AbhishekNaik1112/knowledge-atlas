"""FastAPI application factory. Registers routers and maps domain errors to HTTP responses."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config import get_settings
from app.errors import ConflictError, NotFoundError
from app.middleware import BodySizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.routers import auth, concepts, export, graph, ingest, mcp, search, ui, validate, webhooks
from app.security import require_private_access


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Cloud has no manual migration step; create the schema on boot (idempotent) when asked.
    if get_settings().auto_init_db:
        from app.db import init_db, make_engine

        init_db(make_engine())
    yield


def create_app() -> FastAPI:
    private = get_settings().private_mode
    app = FastAPI(
        title="OKF Knowledge Catalog API",
        version="0.1.0",
        lifespan=_lifespan,
        docs_url=None if private else "/docs",
        redoc_url=None if private else "/redoc",
        openapi_url=None if private else "/openapi.json",
    )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/ui")

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if private:
        @app.get(
            "/openapi.json",
            include_in_schema=False,
            dependencies=[Depends(require_private_access)],
        )
        def private_openapi() -> JSONResponse:
            return JSONResponse(app.openapi())

        @app.get(
            "/docs",
            include_in_schema=False,
            dependencies=[Depends(require_private_access)],
        )
        def private_docs() -> HTMLResponse:
            return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} - Docs")

    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc), "code": "not_found"})

    @app.exception_handler(ConflictError)
    async def _conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc), "code": "conflict"})

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(RateLimitMiddleware)

    app.include_router(auth.router)
    app.include_router(mcp.router)
    app.include_router(concepts.router)
    app.include_router(search.router)
    app.include_router(ingest.router)
    app.include_router(validate.router)
    app.include_router(webhooks.router)
    app.include_router(graph.router)
    app.include_router(export.router)
    app.include_router(ui.router)

    return app


app = create_app()

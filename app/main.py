"""FastAPI application factory.

Responsibilities:
- Configure logging on startup (NFR-8)
- Create the async DB engine connection pool (lifespan)
- Register all routers under /api/v1
- Install global exception handlers mapping domain errors to HTTP codes
- Serve OpenAPI docs at /docs
"""
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.session import engine

settings = get_settings()

# Configure logging before anything else
configure_logging(level="DEBUG" if settings.debug else "INFO")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage DB connection pool lifecycle."""
    logger.info("Starting Ticket Triage System", extra={"env": settings.app_env})
    yield
    await engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI-Powered Support Ticket Triage System — "
            "classifies tickets and generates resolution suggestions using LLM + RAG."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Routers ───────────────────────────────────────────────
    app.include_router(api_v1_router)

    # ── Exception handlers ────────────────────────────────────

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Map Pydantic validation errors to FR-8 compliant 400 responses."""
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "data": None,
                "error": {"code": "VALIDATION_ERROR", "message": str(errors)},
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Return generic 500 — full detail is in server logs only (NFR-7)."""
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "data": None,
                "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
            },
        )

    return app


app = create_app()

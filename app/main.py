import logging
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings
from app.db.session import init_db
from app.schemas.quote import ErrorResponse

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend for AI quotation parsing and supplier comparison.",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error_code" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
            )

        error_response = ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
            details=exc.detail if isinstance(exc.detail, dict) else None,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        error_details = []
        for error in exc.errors():
            loc = " -> ".join(str(e) for e in error.get("loc", []))
            msg = error.get("msg", "Unknown error")
            error_details.append(f"{loc}: {msg}")

        error_response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": error_details},
        )
        logger.warning(f"Validation error: {error_details}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_traceback = traceback.format_exc()
        logger.error(f"Unhandled exception: {str(exc)}\n{error_traceback}")

        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={
                "error_type": type(exc).__name__,
                "error_message": str(exc) if settings.app_env == "dev" else "Internal error",
            } if settings.app_env == "dev" else None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

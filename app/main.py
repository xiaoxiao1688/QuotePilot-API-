from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.db.session import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend for AI quotation parsing and supplier comparison.",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

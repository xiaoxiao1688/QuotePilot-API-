from fastapi import APIRouter

from app.api.routes.ai import router as ai_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.quotes import router as quotes_router
from app.api.routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(quotes_router, prefix="/quotes", tags=["quotes"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])

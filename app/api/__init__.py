from fastapi import APIRouter

from app.api.routes.ai import router as ai_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.quotes import router as quotes_router
from app.api.routes.quote_crud import router as quote_crud_router
from app.api.routes.suppliers import router as suppliers_router
from app.api.routes.substitute_material import router as substitute_material_router
from app.api.routes.supplier_certificate import router as supplier_certificate_router
from app.api.routes.upload import router as upload_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(quotes_router, prefix="/quotes", tags=["quotes"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(quote_crud_router, prefix="/quote-crud", tags=["quote-crud"])
api_router.include_router(substitute_material_router, prefix="/substitute-materials", tags=["substitute-materials"])
api_router.include_router(supplier_certificate_router, prefix="/supplier-certificates", tags=["supplier-certificates"])

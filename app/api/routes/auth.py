from fastapi import APIRouter

from app.schemas.auth import DemoLoginRequest, DemoLoginResponse

router = APIRouter()


@router.post("/demo-login", response_model=DemoLoginResponse)
def demo_login(payload: DemoLoginRequest) -> DemoLoginResponse:
    display_name = payload.nickname or "demo-user"
    return DemoLoginResponse(
        user_id="demo-user-001",
        company_id="demo-company-001",
        nickname=display_name,
        role="buyer",
        token="demo-token-for-local-development",
    )


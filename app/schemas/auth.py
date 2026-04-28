from pydantic import BaseModel, Field


class DemoLoginRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)


class DemoLoginResponse(BaseModel):
    user_id: str
    company_id: str
    nickname: str
    role: str
    token: str


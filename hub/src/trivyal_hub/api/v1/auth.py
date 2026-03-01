"""Auth endpoints — login to get an API token."""

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status

from trivyal_hub.config import settings
from trivyal_hub.core.auth import generate_admin_token

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def login(body: TokenRequest):
    if body.username != "admin" or body.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(access_token=generate_admin_token(settings.secret_key))

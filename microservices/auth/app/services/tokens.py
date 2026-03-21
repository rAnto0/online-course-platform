from datetime import timedelta

from app.core.security import create_jwt
from app.schemas.users import UserRead
from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_access_token(
    user: UserRead,
) -> str:
    jwt_payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }

    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def create_refresh_token(
    user: UserRead,
) -> str:
    jwt_payload = {"sub": str(user.id)}

    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

from typing import Annotated
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    username: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Никнейм пользователя")
    ]
    email: Annotated[
        EmailStr, Field(..., max_length=50, description="Email пользователя")
    ]

    model_config = {"str_strip_whitespace": True}


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    role: UserRole

    model_config = {"from_attributes": True}


class UserCreate(UserBase):
    password: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Пароль пользователя")
    ]


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

from typing import Annotated

from fastapi import APIRouter, Form, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.schemas.users import UserCreate, UserRead, TokenInfo
from app.services import auth
from app.helpers.tokens import create_access_refresh_tokens

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="Регистрация пользователя",
)
async def register(
    data: UserCreate,
    auth_service: auth.AuthService = Depends(auth.get_auth_service),
):
    return await auth_service.register_user(data=data)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfo,
    summary="Авторизация пользователя",
)
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth_service: auth.AuthService = Depends(auth.get_auth_service),
):
    user = UserRead.model_validate(
        await auth_service.authenticate_user(username=username, password=password)
    )

    return create_access_refresh_tokens(user=user)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfo,
    summary="Обновление access токена по refresh токену",
)
async def refresh(
    token: str = Depends(oauth2_scheme),
    auth_service: auth.AuthService = Depends(auth.get_auth_service),
):
    user = UserRead.model_validate(
        await auth_service.get_current_refresh_user(token=token)
    )

    return create_access_refresh_tokens(user=user)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    summary="Информация о текущем пользователе",
)
async def me(
    token: str = Depends(oauth2_scheme),
    auth_service: auth.AuthService = Depends(auth.get_auth_service),
):
    user = UserRead.model_validate(
        await auth_service.get_current_auth_user(token=token)
    )

    return user

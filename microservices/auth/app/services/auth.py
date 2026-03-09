from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_async_session
from app.core.security import get_password_hash
from app.services.tokens import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from app.validations.users import validate_user_unique, validate_password
from app.validations.tokens import validate_token_type
from app.helpers.users import get_user_by_username, get_user_from_sub
from app.helpers.tokens import get_current_token_payload
from app.models.users import User
from app.schemas.users import UserRead, UserCreate


class AuthService:
    """Сервис авторизации, регистрации и получения пользователя на основе токена

    Предоставляет методы для регистрации, аутентификации, получения пользователя на основе токена.

    Attributes:
        session (AsyncSession): Асинхронная сессия БД
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def authenticate_user(self, username: str, password: str) -> User:
        """Сервис - аутентификации пользователя

        Args:
            username (str): Никнейм пользователя
            password (str): Пароль пользователя

        Returns:
            User: Пользователь
        """
        user = await get_user_by_username(
            username=username,
            session=self.session,
        )

        await validate_password(password=password, user=user)

        return user

    async def register_user(self, data: UserCreate) -> User:
        """Сервис - регистрация пользователя

        Args:
            data (UserCreate): Данные для регистрации.

        Raises:
            HTTPException: 400 - Email или Username уже существуют

        Returns:
            User: пользователя
        """
        # Проверяем, нет ли пользователя с таким email и username
        await validate_user_unique(
            email=data.email,
            username=data.username,
            session=self.session,
        )

        hashed_password: bytes = get_password_hash(data.password)
        new_user = User(
            username=data.username, email=data.email, hashed_password=hashed_password
        )

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user

    async def get_current_auth_user(self, token: str) -> User:
        """Сервис - получения пользователя по access токену

        Returns:
            User: Аутентифицированный пользователь
        """
        return await self._user_getter_from_token(
            token=token, token_type=ACCESS_TOKEN_TYPE
        )

    async def get_current_refresh_user(self, token: str) -> User:
        """Сервис - получения пользователя по refresh токену

        Returns:
            User: Аутентифицированный пользователь
        """
        return await self._user_getter_from_token(
            token=token, token_type=REFRESH_TOKEN_TYPE
        )

    async def _user_getter_from_token(self, token: str, token_type: str) -> User:
        """Вспомогательная функция - получает пользователя на основе токена

        Args:
            token: JWT-токен из заголовка Authorization
            token_type: Тип токена

        Returns:
            User: Аутентифицированный пользователь
        """
        payload = get_current_token_payload(token=token)

        validate_token_type(
            payload=payload,
            token_type=token_type,
        )

        return await get_user_from_sub(
            payload=payload,
            session=self.session,
        )


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Фабрика для создания экземпляра AuthService с внедренными зависимостями

    Args:
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        AuthService: Экземпляр сервиса auth
    """
    return AuthService(session=session)

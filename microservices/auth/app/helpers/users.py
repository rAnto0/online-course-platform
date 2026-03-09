from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


async def get_user_by_username(
    username: str,
    session: AsyncSession,
) -> User:
    """Получает пользователя по username

    Args:
        username (str): Никнейм пользователя
        session (AsyncSession): Асинхронная сессия БД

    Raises:
        HTTPException: 401 - Такого пользователя не существует

    Returns:
        User: Пользователя
    """
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Такого пользователя не существует",
        )

    return user


async def get_user_from_sub(
    payload: dict[str, Any],
    session: AsyncSession,
) -> User:
    """Получает пользователя на основе sub (subject) из JWT-токена

    Args:
        payload: Полезная нагрузка JWT-токена
        session: Асинхронная сессия БД

    Returns:
        User: Пользователя

    Raises:
        HTTPException: 401 - Пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Получаем пользователя из БД
    result = await session.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user

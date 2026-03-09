from uuid import UUID

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.core.security import verify_password


async def validate_email_unique(
    email: EmailStr,
    session: AsyncSession,
    exclude_user_id: UUID | None = None,
) -> None:
    """Проверяет уникальность email пользователя.

    Args:
        email (EmailStr): Почта пользователя
        session (AsyncSession): Асинхронная сессия БД
        exclude_user_id (UUID | None, optional): ID пользователя, которого не нужно учитывать. Defaults to None.

    Raises:
        HTTPException: 400 - Пользователь с таким email уже существует
    """
    query = select(User).where(User.email == email)
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)

    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )


async def validate_username_unique(
    username: str,
    session: AsyncSession,
    exclude_user_id: UUID | None = None,
) -> None:
    """Проверяет уникальность username пользователя.

    Args:
        username (str): Никнейм пользователя
        session (AsyncSession): Асинхронная сессия БД
        exclude_user_id (UUID | None, optional): ID пользователя, которого не нужно учитывать. Defaults to None.

    Raises:
        HTTPException: 400 - Пользователь с таким username уже существует
    """
    query = select(User).where(User.username == username)
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)

    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким username уже существует",
        )


async def validate_user_unique(
    session: AsyncSession,
    email: EmailStr | None = None,
    username: str | None = None,
    exclude_user_id: UUID | None = None,
) -> None:
    """Проверяет уникальность username и email пользователя.

    Args:
        session (AsyncSession): Асинхронная сессия БД
        email (EmailStr): Почта пользователя
        username (str): Никнейм пользователя
        exclude_user_id (UUID | None, optional): ID пользователя, которого не нужно учитывать. Defaults to None.

    Raises:
        HTTPException: 400 - Пользователь с таким email или username уже существует
    """
    if email:
        await validate_email_unique(email, session, exclude_user_id)
    if username:
        await validate_username_unique(username, session, exclude_user_id)


async def validate_password(password: str, user: User) -> None:
    """Проверяет пароль

    Args:
        password (str): Пароль
        user (User): Пользователь

    Raises:
        HTTPException: 401 - Неверный пароль
    """
    if not verify_password(
        plain_password=password, hashed_password=user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль",
        )

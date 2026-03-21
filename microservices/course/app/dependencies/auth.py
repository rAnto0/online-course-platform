from typing import Any
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.security import decode_jwt, oauth2_scheme
from app.services.courses import CourseService, get_course_service

ACCESS_TOKEN_TYPE = "access"
TOKEN_TYPE_FIELD = "type"

logger = logging.getLogger("app.dependencies.auth")


def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """
    Получает полезную нагрузку из JWT-токена.

    Args:
        token: JWT-токен из заголовка Authorization

    Returns:
        dict: Полезная нагрузка токена

    Raises:
        HTTPException: Если токен недействителен или истек
    """
    try:
        payload: dict[str, Any] = decode_jwt(token)
        if payload.get(TOKEN_TYPE_FIELD) != ACCESS_TOKEN_TYPE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except HTTPException:
        raise
    except ExpiredSignatureError:
        logger.warning("JWT validation failed: expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as exc:
        logger.warning("JWT validation failed: invalid token (%s)", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.exception("JWT validation failed: unexpected error (%s)", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    payload: dict[str, Any] = Depends(get_current_token_payload),
) -> dict[str, Any]:
    try:
        user_id = UUID(payload["sub"])
        role = payload["role"]
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("JWT payload missing or invalid fields: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"id": user_id, "role": role}


async def require_authentication(
    _: dict[str, Any] = Depends(get_current_user),
) -> None:
    pass


async def require_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> None:
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции",
        )


async def require_teacher_or_admin(
    user: dict[str, Any] = Depends(get_current_user),
) -> None:
    if user["role"] not in ("teacher", "admin"):
        raise HTTPException(403, "Недостаточно прав")


async def require_course_owner_or_admin(
    course_id: UUID,
    course_service: CourseService = Depends(get_course_service),
    user: dict = Depends(get_current_user),
) -> None:
    if user["role"] not in ("teacher", "admin"):
        raise HTTPException(403, "Недостаточно прав")

    # проверяем, является ли пользователь админом или владельцем курса
    course = await course_service.get_course_or_404(course_id)
    if user["role"] != "admin" and course.author_id != user["id"]:
        raise HTTPException(403, "Недостаточно прав")

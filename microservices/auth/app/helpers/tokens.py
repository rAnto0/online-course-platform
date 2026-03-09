from typing import Any

from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.security import decode_jwt
from app.schemas.users import TokenInfo, UserRead
from app.services.tokens import create_access_token, create_refresh_token


def create_access_refresh_tokens(user: UserRead) -> TokenInfo:
    """Создает access и refresh токены.

    Args:
        user (UserRead): Аутентифицированный пользователь

    Returns:
        TokenInfo: Токены
    """
    access_token = create_access_token(user=user)
    refresh_token = create_refresh_token(user=user)

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def get_current_token_payload(
    token: str,
) -> dict[str, Any]:
    """Получает полезную нагрузку из JWT-токена.

    Args:
        token: JWT-токен из заголовка Authorization

    Returns:
        dict: Полезная нагрузка токена

    Raises:
        HTTPException: 401 - Токен недействителен или истек
    """
    try:
        payload: dict[str, Any] = decode_jwt(token)

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

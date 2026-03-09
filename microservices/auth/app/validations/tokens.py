from typing import Any
from fastapi import HTTPException, status

from app.core.security import TOKEN_TYPE_FIELD


def validate_token_type(
    payload: dict[str, Any],
    token_type: str,
) -> None:
    """
    Проверяет, что тип токена соответствует ожидаемому

    Args:
        payload: Полезная нагрузка JWT-токена
        token_type: Ожидаемый тип токена

    Raises:
        HTTPException: 401 - Тип токена не соответствует ожидаемому
    """
    token_type_payload: str | None = payload.get(TOKEN_TYPE_FIELD)
    if token_type_payload != token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Неверный тип токена - {token_type_payload}. Ожидался {token_type}",
            headers={"WWW-Authenticate": "Bearer"},
        )

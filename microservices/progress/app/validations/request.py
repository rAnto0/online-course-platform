from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel


def validate_non_empty_body(
    request_data: BaseModel,
    error_detail: str = "Пустое тело запроса",
    exclude_none: bool = True,
) -> dict[str, Any]:
    data = request_data.model_dump(exclude_unset=True, exclude_none=exclude_none)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail,
        )

    return data

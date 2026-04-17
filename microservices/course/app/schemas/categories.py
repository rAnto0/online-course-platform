from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.pagination import PaginatedResponse


class CategoryBase(BaseModel):
    name: Annotated[
        str, Field(..., min_length=1, max_length=100, description="Название категории")
    ]

    model_config = {"str_strip_whitespace": True}


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Annotated[
        str | None,
        Field(None, min_length=1, max_length=100, description="Название категории"),
    ] = None

    model_config = {"str_strip_whitespace": True}


class CategoryRead(CategoryBase):
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


CategoryListResponse = PaginatedResponse[CategoryRead]

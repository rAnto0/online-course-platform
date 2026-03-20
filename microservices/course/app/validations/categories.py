from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categories import Category


async def validate_category_name_unique(
    name: str,
    session: AsyncSession,
    exclude_category_id: UUID | None = None,
) -> None:
    query = select(Category).where(Category.name == name)
    if exclude_category_id:
        query = query.where(Category.id != exclude_category_id)

    result = await session.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категория с таким названием уже существует",
        )

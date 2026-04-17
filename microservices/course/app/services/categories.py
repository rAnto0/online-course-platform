from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import Depends, HTTPException, status

from app.core.database import get_async_session
from app.models.categories import Category
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.helpers.slug import slugify_name
from app.validations.categories import validate_category_name_unique
from app.validations.request import validate_non_empty_body


class CategoryService:
    """Сервис категорий

    Предоставляет CRUD для категорий.

    Attributes:
        session (AsyncSession): Асинхронная сессия БД
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_categories(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Category], int]:
        """Сервис - получить список категорий

        Args:
            skip (int)
            limit (int)

        Returns:
            Sequence[Category]: Список категорий
        """
        total_query = select(func.count()).select_from(Category)
        total = await self.session.scalar(total_query)

        query = select(Category).order_by(Category.created_at).offset(skip).limit(limit)
        result = await self.session.execute(query)

        return result.scalars().all(), int(total or 0)

    async def get_category_by_id_or_404(
        self,
        category_id: UUID,
    ) -> Category:
        """Сервис - получить категорию по id

        Args:
            category_id (UUID): id категории

        Raises:
            HTTPException: 404 - категория не найдена

        Returns:
            Category: категория
        """
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена",
            )

        return category

    async def get_category_by_slug_or_404(
        self,
        category_slug: str,
    ) -> Category:
        """Сервис - получить категорию по slug

        Args:
            category_slug (str): slug категории

        Raises:
            HTTPException: 404 - категория не найдена

        Returns:
            Category: категория
        """
        result = await self.session.execute(
            select(Category).where(Category.slug == category_slug)
        )
        category = result.scalar_one_or_none()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категория не найдена",
            )

        return category

    async def create_category(self, data: CategoryCreate) -> Category:
        """Сервис - создание категории, слаг генерируется автоматически на основе названия категории

        Args:
            data (CategoryCreate): Данные для создания категории.

        Raises:
            HTTPException: 400 - Категория с таким slug уже существует

        Returns:
            Category: новая категория
        """
        await validate_category_name_unique(name=data.name, session=self.session)

        slug = await self._generate_unique_slug(name=data.name, session=self.session)

        category = Category(name=data.name, slug=slug)
        self.session.add(category)

        try:
            await self.session.commit()
            await self.session.refresh(category)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Категория с таким названием или slug уже существует",
            )

        return category

    async def update_category(
        self,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> Category:
        """Сервис - обновление категории

        Args:
            category_id (UUID): id категории
            data (CategoryUpdate): данные для обновления

        Raises:
            HTTPException: 404 - категория не найдена
            HTTPException: 400 - Категория с таким названием уже существует

        Returns:
            Category: обновленная категория
        """
        category = await self.get_category_by_id_or_404(category_id=category_id)

        update_data = validate_non_empty_body(data)

        if "name" in update_data and update_data["name"] != category.name:
            await validate_category_name_unique(
                name=update_data["name"],
                session=self.session,
                exclude_category_id=category.id,
            )

            update_data["slug"] = await self._generate_unique_slug(
                name=update_data["name"],
                session=self.session,
                exclude_category_id=category.id,
            )

        for key, value in update_data.items():
            setattr(category, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(category)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Категория с таким названием или slug уже существует",
            )

        return category

    async def delete_category(self, category_id: UUID) -> None:
        """Сервис - удаление категории

        Args:
            category_id (UUID): id категории

        Raises:
            HTTPException: 404 - категория не найдена
        """
        category = await self.get_category_by_id_or_404(category_id=category_id)

        await self.session.delete(category)
        await self.session.commit()

    async def _generate_unique_slug(
        self,
        name: str,
        session: AsyncSession,
        exclude_category_id: UUID | None = None,
    ) -> str:
        """
        Генерирует уникальный slug из названия. Если слаг существует, добавляет суффикс
        """
        base_slug = slugify_name(name)
        if not base_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно сгенерировать slug из названия",
            )

        candidate = base_slug
        suffix = 2
        while True:
            query = select(Category).where(Category.slug == candidate)
            if exclude_category_id:
                query = query.where(Category.id != exclude_category_id)
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if existing is None:
                return candidate
            candidate = f"{base_slug}-{suffix}"
            suffix += 1


async def get_category_service(
    session: AsyncSession = Depends(get_async_session),
) -> CategoryService:
    """Фабрика для создания экземпляра CategoryService с внедренными зависимостями

    Args:
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        CategoryService: Экземпляр сервиса категорий
    """
    return CategoryService(session=session)

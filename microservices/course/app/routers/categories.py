from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.schemas.categories import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.categories import CategoryService, get_category_service
from app.dependencies.auth import require_admin

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)

admin_deps = [Depends(require_admin)]


@router.get(
    "/",
    response_model=list[CategoryRead],
    status_code=status.HTTP_200_OK,
    summary="Список категорий",
)
async def list_categories(
    skip: int = 0,
    limit: int = 100,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.get_categories(skip=skip, limit=limit)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Получить категорию по id",
)
async def get_category_by_id(
    category_id: UUID,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.get_category_by_id_or_404(category_id=category_id)


@router.get(
    "/by-slug/{category_slug}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Получить категорию по slug",
)
async def get_category_by_slug(
    category_slug: str,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.get_category_by_slug_or_404(
        category_slug=category_slug
    )


@router.post(
    "/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=admin_deps,
    summary="Создать категорию",
)
async def create_category(
    data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.create_category(data=data)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    status_code=status.HTTP_200_OK,
    dependencies=admin_deps,
    summary="Обновить категорию",
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.update_category(category_id=category_id, data=data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=admin_deps,
    summary="Удалить категорию",
)
async def delete_category(
    category_id: UUID,
    category_service: CategoryService = Depends(get_category_service),
):
    await category_service.delete_category(category_id=category_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

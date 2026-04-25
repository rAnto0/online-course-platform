from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.schemas import courses as sch_courses
from app.services.courses import CourseService, get_course_service
from app.dependencies.auth import (
    get_current_user,
    require_course_owner_or_admin,
    require_authentication,
)

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)

authentication_deps = [Depends(require_authentication)]
course_owner_or_admin_deps = [Depends(require_course_owner_or_admin)]


# --- Courses ---
@router.get(
    "/",
    response_model=sch_courses.CourseListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список курсов",
)
async def list_courses(
    skip: int = 0,
    limit: int = 100,
    course_service: CourseService = Depends(get_course_service),
):
    items, total = await course_service.get_courses(skip=skip, limit=limit)

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post(
    "/by-ids",
    response_model=sch_courses.CourseBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить курсы по списку id",
)
async def get_courses_by_ids(
    data: sch_courses.CourseBatchRequest,
    course_service: CourseService = Depends(get_course_service),
) -> sch_courses.CourseBatchResponse:
    courses = await course_service.get_courses_by_ids(course_ids=data.course_ids)

    found_ids = {course.id for course in courses}
    missing_ids = [uid for uid in data.course_ids if uid not in found_ids]

    return sch_courses.CourseBatchResponse(found=courses, missing=missing_ids)


@router.get(
    "/{course_id}",
    response_model=sch_courses.CourseRead,
    status_code=status.HTTP_200_OK,
    summary="Получить курс по id",
)
async def get_course(
    course_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.get_course_or_404(course_id=course_id)


@router.get(
    "/{course_id}/content",
    response_model=sch_courses.CourseContentRead,
    status_code=status.HTTP_200_OK,
    summary="Получить полное дерево данных курса по id",
)
async def get_course_content(
    course_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.get_course_content_or_404(course_id=course_id)


@router.post(
    "/",
    response_model=sch_courses.CourseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=authentication_deps,
    summary="Создать курс",
)
async def create_course(
    data: sch_courses.CourseCreate,
    course_service: CourseService = Depends(get_course_service),
    user: dict[str, Any] = Depends(get_current_user),
):
    return await course_service.create_course(
        data=data,
        user=user,
    )


@router.put(
    "/{course_id}",
    response_model=sch_courses.CourseRead,
    status_code=status.HTTP_200_OK,
    dependencies=course_owner_or_admin_deps,
    summary="Обновить курс",
)
async def update_course(
    course_id: UUID,
    data: sch_courses.CourseUpdate,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.update_course(
        course_id=course_id,
        data=data,
    )


@router.patch(
    "/{course_id}/publish",
    response_model=sch_courses.CourseRead,
    status_code=status.HTTP_200_OK,
    dependencies=course_owner_or_admin_deps,
    summary="Опубликовать курс",
)
async def publish_course(
    course_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.publish_course(course_id=course_id)


@router.patch(
    "/{course_id}/archive",
    response_model=sch_courses.CourseRead,
    status_code=status.HTTP_200_OK,
    dependencies=course_owner_or_admin_deps,
    summary="Архивировать курс",
)
async def archive_course(
    course_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.archive_course(course_id=course_id)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=course_owner_or_admin_deps,
    summary="Удалить курс",
)
async def delete_course(
    course_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    await course_service.delete_course(course_id=course_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Sections ---
@router.get(
    "/{course_id}/sections",
    response_model=sch_courses.SectionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Секции курса",
)
async def list_sections(
    course_id: UUID,
    skip: int = 0,
    limit: int = 100,
    course_service: CourseService = Depends(get_course_service),
):
    items, total = await course_service.list_sections(
        course_id=course_id, skip=skip, limit=limit
    )

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/{course_id}/sections/{section_id}",
    response_model=sch_courses.SectionRead,
    status_code=status.HTTP_200_OK,
    summary="Получить секцию",
)
async def get_section(
    course_id: UUID,
    section_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.get_section_or_404(
        course_id=course_id, section_id=section_id
    )


@router.post(
    "/{course_id}/sections",
    response_model=sch_courses.SectionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=course_owner_or_admin_deps,
    summary="Создать секцию",
)
async def create_section(
    course_id: UUID,
    data: sch_courses.SectionCreate,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.create_section(course_id=course_id, data=data)


@router.put(
    "/{course_id}/sections/{section_id}",
    response_model=sch_courses.SectionRead,
    status_code=status.HTTP_200_OK,
    dependencies=course_owner_or_admin_deps,
    summary="Обновить секцию",
)
async def update_section(
    course_id: UUID,
    section_id: UUID,
    data: sch_courses.SectionUpdate,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.update_section(
        course_id=course_id, section_id=section_id, data=data
    )


@router.delete(
    "/{course_id}/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=course_owner_or_admin_deps,
    summary="Удалить секцию",
)
async def delete_section(
    course_id: UUID,
    section_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    await course_service.delete_section(course_id=course_id, section_id=section_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Lessons ---
@router.get(
    "/{course_id}/sections/{section_id}/lessons",
    response_model=sch_courses.LessonListResponse,
    status_code=status.HTTP_200_OK,
    summary="Уроки секции",
)
async def list_lessons(
    course_id: UUID,
    section_id: UUID,
    skip: int = 0,
    limit: int = 100,
    course_service: CourseService = Depends(get_course_service),
):
    items, total = await course_service.list_lessons(
        course_id=course_id, section_id=section_id, skip=skip, limit=limit
    )

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/{course_id}/sections/{section_id}/lessons/{lesson_id}",
    response_model=sch_courses.LessonRead,
    status_code=status.HTTP_200_OK,
    summary="Получить урок",
)
async def get_lesson(
    course_id: UUID,
    section_id: UUID,
    lesson_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.get_lesson_or_404(
        course_id=course_id, section_id=section_id, lesson_id=lesson_id
    )


@router.post(
    "/{course_id}/sections/{section_id}/lessons",
    response_model=sch_courses.LessonRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=course_owner_or_admin_deps,
    summary="Создать урок",
)
async def create_lesson(
    course_id: UUID,
    section_id: UUID,
    data: sch_courses.LessonCreate,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.create_lesson(
        course_id=course_id, section_id=section_id, data=data
    )


@router.put(
    "/{course_id}/sections/{section_id}/lessons/{lesson_id}",
    response_model=sch_courses.LessonRead,
    status_code=status.HTTP_200_OK,
    dependencies=course_owner_or_admin_deps,
    summary="Обновить урок",
)
async def update_lesson(
    course_id: UUID,
    section_id: UUID,
    lesson_id: UUID,
    data: sch_courses.LessonUpdate,
    course_service: CourseService = Depends(get_course_service),
):
    return await course_service.update_lesson(
        course_id=course_id,
        section_id=section_id,
        lesson_id=lesson_id,
        data=data,
    )


@router.delete(
    "/{course_id}/sections/{section_id}/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=course_owner_or_admin_deps,
    summary="Удалить урок",
)
async def delete_lesson(
    course_id: UUID,
    section_id: UUID,
    lesson_id: UUID,
    course_service: CourseService = Depends(get_course_service),
):
    await course_service.delete_lesson(
        course_id=course_id, section_id=section_id, lesson_id=lesson_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

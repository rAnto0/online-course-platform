from uuid import UUID

from fastapi import APIRouter, Header, Depends, Security, status

from app.core.security import oauth2_scheme
from app.schemas import progress as sch_progress
from app.services.progress import ProgressService, get_progress_service

# для Swagger(аутентификация осуществляется через api-gateway)
auth_deps = [Security(oauth2_scheme)]

router = APIRouter(prefix="/progress", tags=["Progress"], dependencies=auth_deps)


# --- Enrollments ---
@router.post(
    "/enrollments",
    response_model=sch_progress.EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Записать пользователя на курс",
)
async def create_enrollment(
    data: sch_progress.EnrollmentCreate,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.create_enrollment(data=data, user_id=user_id)


@router.get(
    "/enrollments/by-user",
    response_model=list[sch_progress.EnrollmentRead],
    status_code=status.HTTP_200_OK,
    summary="Список курсов на которые записан пользователь",
)
async def list_enrollments_by_user(
    user_id: UUID = Header(..., alias="X-User-Id"),
    skip: int = 0,
    limit: int = 100,
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.list_enrollments_by_user(
        user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/enrollments/by-course/{course_id}",
    response_model=sch_progress.EnrollmentRead,
    status_code=status.HTTP_200_OK,
    summary="Получить запись пользователя на курс",
)
async def get_enrollment_by_user_course(
    course_id: UUID,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.get_enrollment_by_user_course_or_404(
        user_id=user_id,
        course_id=course_id,
    )


@router.get(
    "/enrollments/{enrollment_id}",
    response_model=sch_progress.EnrollmentRead,
    status_code=status.HTTP_200_OK,
    summary="Получить запись о зачислении",
)
async def get_enrollment(
    enrollment_id: UUID,
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.get_enrollment_or_404(enrollment_id=enrollment_id)


@router.patch(
    "/enrollments/{enrollment_id}",
    response_model=sch_progress.EnrollmentRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить статус зачисления",
)
async def update_enrollment(
    enrollment_id: UUID,
    data: sch_progress.EnrollmentUpdate,
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.update_enrollment(
        enrollment_id=enrollment_id,
        data=data,
    )


# --- Course Progress ---
@router.get(
    "/course-progress/courses/{course_id}",
    response_model=sch_progress.CourseProgressRead,
    status_code=status.HTTP_200_OK,
    summary="Получить прогресс курса",
)
async def get_course_progress(
    course_id: UUID,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.get_course_progress_or_404(
        user_id=user_id,
        course_id=course_id,
    )


@router.put(
    "/course-progress/courses/{course_id}",
    response_model=sch_progress.CourseProgressRead,
    status_code=status.HTTP_200_OK,
    summary="Создать или обновить прогресс курса",
)
async def upsert_course_progress(
    course_id: UUID,
    data: sch_progress.CourseProgressUpsert,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.upsert_course_progress(
        user_id=user_id,
        course_id=course_id,
        data=data,
    )


# --- Lesson Progress ---
@router.post(
    "/lesson-progress/lessons/by-ids",
    response_model=sch_progress.LessonProgressBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить прогресс уроков по списку id",
)
async def get_lesson_progress_by_ids(
    data: sch_progress.LessonProgressBatchRequest,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    lessons = await progress_service.get_lesson_progress_by_ids(
        user_id=user_id,
        lesson_ids=data.lesson_ids,
    )

    found_ids = {lesson.lesson_id for lesson in lessons}
    missing_ids = [
        lesson_id for lesson_id in data.lesson_ids if lesson_id not in found_ids
    ]

    return sch_progress.LessonProgressBatchResponse(found=lessons, missing=missing_ids)


@router.get(
    "/lesson-progress/lessons/{lesson_id}",
    response_model=sch_progress.LessonProgressRead,
    status_code=status.HTTP_200_OK,
    summary="Получить прогресс урока",
)
async def get_lesson_progress(
    lesson_id: UUID,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.get_lesson_progress_or_404(
        user_id=user_id,
        lesson_id=lesson_id,
    )


@router.put(
    "/lesson-progress/lessons/{lesson_id}",
    response_model=sch_progress.LessonProgressRead,
    status_code=status.HTTP_200_OK,
    summary="Создать или обновить прогресс урока",
)
async def upsert_lesson_progress(
    lesson_id: UUID,
    data: sch_progress.LessonProgressUpsert,
    user_id: UUID = Header(..., alias="X-User-Id"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    return await progress_service.upsert_lesson_progress(
        user_id=user_id,
        lesson_id=lesson_id,
        data=data,
    )

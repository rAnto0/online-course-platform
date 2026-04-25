from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EnrollmentStatus, LessonProgressStatus


class EnrollmentBase(BaseModel):
    course_id: UUID


class EnrollmentCreate(EnrollmentBase):
    status: EnrollmentStatus | None = None


class EnrollmentUpdate(BaseModel):
    status: EnrollmentStatus | None = None


class EnrollmentRead(EnrollmentBase):
    user_id: UUID
    id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourseProgressBase(BaseModel):
    total_lessons: Annotated[
        int, Field(0, ge=0, description="Общее количество уроков")
    ] = 0
    progress_percent: Annotated[
        int, Field(0, ge=0, le=100, description="Процент прохождения курса")
    ] = 0
    last_lesson_id: UUID | None = None


class CourseProgressUpsert(CourseProgressBase):
    pass


class CourseProgressRead(CourseProgressBase):
    id: UUID
    user_id: UUID
    course_id: UUID
    updated_at: datetime

    model_config = {"from_attributes": True}


class LessonProgressBase(BaseModel):
    course_id: UUID
    section_id: UUID
    status: LessonProgressStatus | None = None
    progress_percent: Annotated[
        int | None,
        Field(None, ge=0, le=100, description="Процент прохождения урока"),
    ] = None


class LessonProgressUpsert(LessonProgressBase):
    pass


class LessonProgressRead(LessonProgressBase):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class LessonProgressBatchRequest(BaseModel):
    lesson_ids: Annotated[
        list[UUID],
        Field(
            ...,
            min_length=1,
            max_length=100,
            description="Список ID уроков для получения информации о них",
        ),
    ]


class LessonProgressBatchResponse(BaseModel):
    found: Annotated[
        list[LessonProgressRead],
        Field(description="Список найденных уроков"),
    ] = []
    missing: Annotated[
        list[UUID],
        Field(description="Список ID уроков, для которых не была найдена информация"),
    ] = []

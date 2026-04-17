from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CourseLevel, CourseStatus, LessonType
from app.schemas.pagination import PaginatedResponse


class CourseCreate(BaseModel):
    title: Annotated[str, Field(..., min_length=1, max_length=255)]
    description: str | None = None
    category_id: UUID | None = None
    level: CourseLevel | None = None
    price: int | None = None
    thumbnail_url: str | None = None

    model_config = {"str_strip_whitespace": True}


class CourseUpdate(BaseModel):
    title: Annotated[str | None, Field(None, min_length=1, max_length=255)] = None
    description: str | None = None
    category_id: UUID | None = None
    level: CourseLevel | None = None
    price: int | None = None
    thumbnail_url: str | None = None

    model_config = {"str_strip_whitespace": True}


class CourseRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    author_id: UUID
    category_id: UUID | None
    level: CourseLevel | None
    price: int | None
    status: CourseStatus
    thumbnail_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SectionCreate(BaseModel):
    title: Annotated[str, Field(..., min_length=1, max_length=255)]
    position: int | None = None

    model_config = {"str_strip_whitespace": True}


class SectionUpdate(BaseModel):
    title: Annotated[str | None, Field(None, min_length=1, max_length=255)] = None
    position: int | None = None

    model_config = {"str_strip_whitespace": True}


class SectionRead(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LessonCreate(BaseModel):
    title: Annotated[str, Field(..., min_length=1, max_length=255)]
    content: str | None = None
    lesson_type: LessonType | None = None
    video_url: str | None = None
    duration: int | None = None
    position: int | None = None

    model_config = {"str_strip_whitespace": True}


class LessonUpdate(BaseModel):
    title: Annotated[str | None, Field(None, min_length=1, max_length=255)] = None
    content: str | None = None
    lesson_type: LessonType | None = None
    video_url: str | None = None
    duration: int | None = None
    position: int | None = None

    model_config = {"str_strip_whitespace": True}


class LessonRead(BaseModel):
    id: UUID
    section_id: UUID
    title: str
    content: str | None
    lesson_type: LessonType
    video_url: str | None
    duration: int | None
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


CourseListResponse = PaginatedResponse[CourseRead]
SectionListResponse = PaginatedResponse[SectionRead]
LessonListResponse = PaginatedResponse[LessonRead]

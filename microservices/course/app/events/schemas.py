from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import CourseLevel, CourseStatus


class CoursePublishedEvent(BaseModel):
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


class UserRoleUpdatedEvent(BaseModel):
    user_id: UUID
    role: str
    course_id: UUID

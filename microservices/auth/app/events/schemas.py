from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.models.enums import UserRole


class UserCreatedEvent(BaseModel):
    id: UUID
    email: str
    role: UserRole
    created_at: datetime


class UserRoleUpdatedEvent(BaseModel):
    user_id: UUID
    role: str
    course_id: UUID

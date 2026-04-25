import pytest
from fastapi import HTTPException, status
from uuid import uuid4

from app.schemas.progress import LessonProgressUpsert
from app.services.progress import ProgressService


async def test_upsert_lesson_progress_requires_course_and_section_for_create(
    db_session,
):
    service = ProgressService(session=db_session)
    data = LessonProgressUpsert.model_construct(
        course_id=None,
        section_id=None,
        status=None,
        progress_percent=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upsert_lesson_progress(
            user_id=uuid4(),
            lesson_id=uuid4(),
            data=data,
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "course_id и section_id обязательны" in exc_info.value.detail

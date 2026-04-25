from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.enums import EnrollmentStatus, LessonProgressStatus
from app.models.progress import CourseProgress, Enrollment, LessonProgress


@pytest.fixture
def user_id_factory():
    def _factory():
        return uuid4()

    return _factory


@pytest_asyncio.fixture
async def enrollment_factory(db_session, user_id_factory):
    async def _factory(**kwargs):
        defaults = {
            "user_id": user_id_factory(),
            "course_id": uuid4(),
            "status": EnrollmentStatus.ACTIVE,
        }
        enrollment_data = {**defaults, **kwargs}

        enrollment = Enrollment(**enrollment_data)
        db_session.add(enrollment)
        await db_session.commit()
        await db_session.refresh(enrollment)
        return enrollment

    return _factory


@pytest_asyncio.fixture
async def course_progress_factory(db_session, user_id_factory):
    async def _factory(**kwargs):
        defaults = {
            "user_id": user_id_factory(),
            "course_id": uuid4(),
            "total_lessons": 10,
            "progress_percent": 0,
            "last_lesson_id": None,
        }
        course_progress_data = {**defaults, **kwargs}

        course_progress = CourseProgress(**course_progress_data)
        db_session.add(course_progress)
        await db_session.commit()
        await db_session.refresh(course_progress)
        return course_progress

    return _factory


@pytest_asyncio.fixture
async def lesson_progress_factory(db_session, user_id_factory):
    async def _factory(**kwargs):
        defaults = {
            "user_id": user_id_factory(),
            "course_id": uuid4(),
            "section_id": uuid4(),
            "lesson_id": uuid4(),
            "status": LessonProgressStatus.NOT_STARTED,
            "progress_percent": 0,
        }
        lesson_progress_data = {**defaults, **kwargs}

        lesson_progress = LessonProgress(**lesson_progress_data)
        db_session.add(lesson_progress)
        await db_session.commit()
        await db_session.refresh(lesson_progress)
        return lesson_progress

    return _factory


@pytest.fixture
def enrollment_create_data_factory():
    def _factory(**kwargs):
        base_data = {
            "course_id": str(uuid4()),
            "status": EnrollmentStatus.ACTIVE.value,
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def course_progress_upsert_data_factory():
    def _factory(**kwargs):
        base_data = {
            "total_lessons": 12,
            "progress_percent": 15,
            "last_lesson_id": str(uuid4()),
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def lesson_progress_upsert_data_factory():
    def _factory(**kwargs):
        base_data = {
            "course_id": str(uuid4()),
            "section_id": str(uuid4()),
            "status": LessonProgressStatus.NOT_STARTED.value,
            "progress_percent": 0,
        }
        return {**base_data, **kwargs}

    return _factory

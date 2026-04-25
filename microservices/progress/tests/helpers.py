from sqlalchemy import select

from app.models.progress import CourseProgress, Enrollment, LessonProgress


async def assert_enrollment_in_db(db_session, enrollment_id, **expected):
    result = await db_session.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id)
    )
    enrollment = result.scalars().first()
    assert enrollment is not None
    for key, value in expected.items():
        assert getattr(enrollment, key) == value
    return enrollment


async def assert_course_progress_in_db(db_session, course_progress_id, **expected):
    result = await db_session.execute(
        select(CourseProgress).where(CourseProgress.id == course_progress_id)
    )
    course_progress = result.scalars().first()
    assert course_progress is not None
    for key, value in expected.items():
        assert getattr(course_progress, key) == value
    return course_progress


async def assert_lesson_progress_in_db(db_session, lesson_progress_id, **expected):
    result = await db_session.execute(
        select(LessonProgress).where(LessonProgress.id == lesson_progress_id)
    )
    lesson_progress = result.scalars().first()
    assert lesson_progress is not None
    for key, value in expected.items():
        assert getattr(lesson_progress, key) == value
    return lesson_progress

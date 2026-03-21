from sqlalchemy import select

from app.helpers.slug import slugify_name
from app.models.categories import Category
from app.models.course import Course, Lesson, Section


async def assert_category_in_db(db_session, name: str) -> Category:
    """Утверждение: категория с указанным именем существует и slug корректный."""
    result = await db_session.execute(select(Category).where(Category.name == name))
    category = result.scalars().first()
    assert category is not None
    assert category.slug == slugify_name(name)
    return category


async def assert_course_in_db(db_session, course_id, **expected):
    """Утверждение: курс существует и поля совпадают."""
    result = await db_session.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    assert course is not None
    for key, value in expected.items():
        assert getattr(course, key) == value
    return course


async def assert_section_in_db(db_session, section_id, **expected):
    """Утверждение: секция существует и поля совпадают."""
    result = await db_session.execute(select(Section).where(Section.id == section_id))
    section = result.scalars().first()
    assert section is not None
    for key, value in expected.items():
        assert getattr(section, key) == value
    return section


async def assert_lesson_in_db(db_session, lesson_id, **expected):
    """Утверждение: урок существует и поля совпадают."""
    result = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()
    assert lesson is not None
    for key, value in expected.items():
        assert getattr(lesson, key) == value
    return lesson

from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.helpers.slug import slugify_name
from app.models.categories import Category
from app.models.course import Course, Lesson, Section
from app.models.enums import CourseLevel, CourseStatus, LessonType


@pytest.fixture
def user_factory():
    def _factory(role: str = "student", user_id: UUID | None = None) -> dict:
        return {"id": user_id or uuid4(), "role": role}

    return _factory


@pytest_asyncio.fixture
async def category_factory(db_session, faker):
    """Фабрика для создания тестовых категорий"""

    async def _factory(**kwargs):
        name = kwargs.pop("name", f"Category {faker.word()} {faker.pyint()}")
        defaults = {
            "name": name,
            "slug": kwargs.pop("slug", slugify_name(name)),
        }
        category_data = {**defaults, **kwargs}

        category = Category(**category_data)
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        return category

    return _factory


@pytest_asyncio.fixture
async def course_factory(db_session, faker, user_owner, category_factory):
    """Фабрика для создания тестовых курсов"""

    async def _factory(**kwargs):
        category = kwargs.pop("category", None)
        if category is None and kwargs.get("category_id") is None:
            category = await category_factory()

        defaults = {
            "title": f"Course {faker.sentence(nb_words=3)}",
            "description": faker.text(max_nb_chars=200),
            "author_id": user_owner["id"],
            "category_id": category.id if category is not None else None,
            "level": CourseLevel.BEGINNER,
            "price": faker.pyint(min_value=0, max_value=50000),
            "status": CourseStatus.DRAFT,
            "thumbnail_url": f"https://example.com/{faker.uuid4()}",
        }
        course_data = {**defaults, **kwargs}

        course = Course(**course_data)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)
        return course

    return _factory


@pytest_asyncio.fixture
async def section_factory(db_session, faker, course_factory):
    """Фабрика для создания тестовых секций"""

    async def _factory(**kwargs):
        course = kwargs.pop("course", None)
        if course is None and kwargs.get("course_id") is None:
            course = await course_factory()

        defaults = {
            "course_id": course.id if course is not None else kwargs.get("course_id"),
            "title": f"Section {faker.sentence(nb_words=2)}",
            "position": faker.pyint(min_value=0, max_value=20),
        }
        section_data = {**defaults, **kwargs}

        section = Section(**section_data)
        db_session.add(section)
        await db_session.commit()
        await db_session.refresh(section)
        return section

    return _factory


@pytest_asyncio.fixture
async def lesson_factory(db_session, faker, section_factory):
    """Фабрика для создания тестовых уроков"""

    async def _factory(**kwargs):
        section = kwargs.pop("section", None)
        if section is None and kwargs.get("section_id") is None:
            section = await section_factory()

        defaults = {
            "section_id": (
                section.id if section is not None else kwargs.get("section_id")
            ),
            "title": f"Lesson {faker.sentence(nb_words=2)}",
            "content": faker.text(max_nb_chars=200),
            "lesson_type": LessonType.TEXT,
            "video_url": None,
            "duration": faker.pyint(min_value=1, max_value=7200),
            "position": faker.pyint(min_value=0, max_value=50),
        }
        lesson_data = {**defaults, **kwargs}

        lesson = Lesson(**lesson_data)
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        return lesson

    return _factory


@pytest.fixture
def category_create_data_factory(faker):
    """Фабрика данных для создания категории"""

    def _factory(**kwargs):
        base_data = {
            "name": f"Category {faker.word()} {faker.pyint()}",
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def category_update_data_factory(faker):
    """Фабрика данных для обновления категории"""

    def _factory(**kwargs):
        base_data = {
            "name": f"Updated {faker.word()} {faker.pyint()}",
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def course_create_data_factory(faker):
    """Фабрика данных для создания курса"""

    def _factory(**kwargs):
        base_data = {
            "title": f"Course {faker.sentence(nb_words=3)}",
            "description": faker.text(max_nb_chars=200),
            "category_id": None,
            "level": CourseLevel.BEGINNER.value,
            "price": faker.pyint(min_value=0, max_value=50000),
            "thumbnail_url": f"https://example.com/{faker.uuid4()}",
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def course_update_data_factory(faker):
    """Фабрика данных для обновления курса"""

    def _factory(**kwargs):
        base_data = {
            "title": f"Updated {faker.sentence(nb_words=3)}",
            "description": faker.text(max_nb_chars=200),
            "level": CourseLevel.INTERMEDIATE.value,
            "price": faker.pyint(min_value=0, max_value=50000),
            "thumbnail_url": f"https://example.com/{faker.uuid4()}",
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def section_create_data_factory(faker):
    """Фабрика данных для создания секции"""

    def _factory(**kwargs):
        base_data = {
            "title": f"Section {faker.sentence(nb_words=2)}",
            "position": faker.pyint(min_value=0, max_value=20),
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def section_update_data_factory(faker):
    """Фабрика данных для обновления секции"""

    def _factory(**kwargs):
        base_data = {
            "title": f"Updated {faker.sentence(nb_words=2)}",
            "position": faker.pyint(min_value=0, max_value=20),
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def lesson_create_data_factory(faker):
    """Фабрика данных для создания урока"""

    def _factory(**kwargs):
        base_data = {
            "title": f"Lesson {faker.sentence(nb_words=2)}",
            "content": faker.text(max_nb_chars=200),
            "lesson_type": LessonType.TEXT.value,
            "video_url": None,
            "duration": faker.pyint(min_value=1, max_value=7200),
            "position": faker.pyint(min_value=0, max_value=50),
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def lesson_update_data_factory(faker):
    """Фабрика данных для обновления урока"""

    def _factory(**kwargs):
        base_data = {
            "title": f"Updated {faker.sentence(nb_words=2)}",
            "content": faker.text(max_nb_chars=200),
            "lesson_type": LessonType.VIDEO.value,
            "video_url": f"https://example.com/{faker.uuid4()}",
            "duration": faker.pyint(min_value=1, max_value=7200),
            "position": faker.pyint(min_value=0, max_value=50),
        }
        return {**base_data, **kwargs}

    return _factory

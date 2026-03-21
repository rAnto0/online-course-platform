from typing import Any, Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.categories import Category
from app.models.course import Course, Lesson, Section
from app.models.enums import CourseStatus
from app.schemas.courses import (
    CourseCreate,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
    SectionCreate,
    SectionUpdate,
)
from app.validations.request import validate_non_empty_body


class CourseService:
    """Сервис курсов, секций и уроков.

    Инкапсулирует CRUD для Course, Section, Lesson, а также проверки
    связанных сущностей и уникальности позиций.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Courses ---
    async def get_courses(self, skip: int = 0, limit: int = 100) -> Sequence[Course]:
        """Возвращает список курсов с пагинацией."""
        query = select(Course).order_by(Course.created_at).offset(skip).limit(limit)
        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_course_or_404(self, course_id: UUID) -> Course:
        """Возвращает курс по id или 404."""
        result = await self.session.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()
        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден"
            )

        return course

    async def create_course(
        self,
        data: CourseCreate,
        user: dict[str, Any],
    ) -> Course:
        """Создаёт курс и возвращает созданную сущность."""
        if data.category_id is not None:
            await self._ensure_category_exists(category_id=data.category_id)

        course_kwargs = {
            "title": data.title,
            "description": data.description,
            "author_id": user["id"],
            "category_id": data.category_id,
            "level": data.level,
            "price": data.price,
            "thumbnail_url": data.thumbnail_url,
        }
        course = Course(**course_kwargs)
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)

        return course

    async def update_course(self, course_id: UUID, data: CourseUpdate) -> Course:
        """Обновляет курс по id и возвращает обновлённую сущность."""
        course = await self.get_course_or_404(course_id=course_id)

        update_data = validate_non_empty_body(data, exclude_none=False)

        if "title" in update_data and update_data["title"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заголовок не может быть пустым",
            )
        if "category_id" in update_data and update_data["category_id"] is not None:
            await self._ensure_category_exists(category_id=update_data["category_id"])

        for key, value in update_data.items():
            setattr(course, key, value)

        await self.session.commit()
        await self.session.refresh(course)

        return course

    async def delete_course(self, course_id: UUID) -> None:
        """Удаляет курс по id."""
        course = await self.get_course_or_404(course_id=course_id)
        await self.session.delete(course)
        await self.session.commit()

    async def publish_course(self, course_id: UUID) -> Course:
        """Публикует курс."""
        course = await self.get_course_or_404(course_id=course_id)
        if course.status != CourseStatus.PUBLISHED:
            missing_fields: list[str] = []
            if not course.description or not course.description.strip():
                missing_fields.append("description")
            if course.category_id is None:
                missing_fields.append("category_id")
            if course.level is None:
                missing_fields.append("level")
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Нельзя опубликовать курс. "
                        "Заполните поля: " + ", ".join(missing_fields)
                    ),
                )

            section_exists = await self.session.scalar(
                select(Section.id).where(Section.course_id == course_id).limit(1)
            )
            if section_exists is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя опубликовать курс. Добавьте хотя бы одну секцию.",
                )

            lesson_exists = await self.session.scalar(
                select(Lesson.id)
                .join(Section, Lesson.section_id == Section.id)
                .where(Section.course_id == course_id)
                .limit(1)
            )
            if lesson_exists is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя опубликовать курс. Добавьте хотя бы один урок.",
                )

            course.status = CourseStatus.PUBLISHED
            await self.session.commit()
            await self.session.refresh(course)
        return course

    async def archive_course(self, course_id: UUID) -> Course:
        """Архивирует курс."""
        course = await self.get_course_or_404(course_id=course_id)
        if course.status != CourseStatus.ARCHIVED:
            course.status = CourseStatus.ARCHIVED
            await self.session.commit()
            await self.session.refresh(course)

        return course

    # --- Sections ---
    async def list_sections(self, course_id: UUID) -> Sequence[Section]:
        """Возвращает список секций курса."""
        await self.get_course_or_404(course_id=course_id)
        query = (
            select(Section)
            .where(Section.course_id == course_id)
            .order_by(Section.position)
        )
        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_section_or_404(self, course_id: UUID, section_id: UUID) -> Section:
        """Возвращает секцию курса по id или 404."""
        result = await self.session.execute(
            select(Section).where(
                Section.id == section_id, Section.course_id == course_id
            )
        )
        section = result.scalar_one_or_none()
        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Секция не найдена"
            )

        return section

    async def create_section(self, course_id: UUID, data: SectionCreate) -> Section:
        """Создаёт секцию в курсе. Позиция может быть авто-сгенерирована."""
        await self.get_course_or_404(course_id=course_id)

        position = data.position
        if position is None:
            position = await self._next_section_position(course_id=course_id)
        else:
            await self._ensure_section_position_unique(
                course_id=course_id, position=position
            )

        section = Section(course_id=course_id, title=data.title, position=position)
        self.session.add(section)
        try:
            await self.session.commit()
            await self.session.refresh(section)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Секция с такой позицией уже существует",
            )

        return section

    async def update_section(
        self, course_id: UUID, section_id: UUID, data: SectionUpdate
    ) -> Section:
        """Обновляет секцию курса."""
        section = await self.get_section_or_404(
            course_id=course_id, section_id=section_id
        )

        update_data = validate_non_empty_body(data)

        if "position" in update_data:
            if update_data["position"] != section.position:
                await self._ensure_section_position_unique(
                    course_id=course_id,
                    position=update_data["position"],
                    exclude_section_id=section.id,
                )

        for key, value in update_data.items():
            setattr(section, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(section)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Секция с такой позицией уже существует",
            )

        return section

    async def delete_section(self, course_id: UUID, section_id: UUID) -> None:
        """Удаляет секцию курса."""
        section = await self.get_section_or_404(
            course_id=course_id, section_id=section_id
        )
        await self.session.delete(section)
        await self.session.commit()

    # --- Lessons ---
    async def list_lessons(self, course_id: UUID, section_id: UUID) -> Sequence[Lesson]:
        """Возвращает список уроков секции."""
        await self.get_section_or_404(course_id=course_id, section_id=section_id)
        query = (
            select(Lesson)
            .where(Lesson.section_id == section_id)
            .order_by(Lesson.position)
        )
        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_lesson_or_404(
        self, course_id: UUID, section_id: UUID, lesson_id: UUID
    ) -> Lesson:
        """Возвращает урок по id в рамках курса и секции или 404."""
        result = await self.session.execute(
            select(Lesson)
            .join(Section, Lesson.section_id == Section.id)
            .where(
                Lesson.id == lesson_id,
                Section.id == section_id,
                Section.course_id == course_id,
            )
        )
        lesson = result.scalar_one_or_none()
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден"
            )

        return lesson

    async def create_lesson(
        self, course_id: UUID, section_id: UUID, data: LessonCreate
    ) -> Lesson:
        """Создаёт урок в секции. Позиция может быть авто-сгенерирована."""
        await self.get_section_or_404(course_id=course_id, section_id=section_id)

        position = data.position
        if position is None:
            position = await self._next_lesson_position(section_id=section_id)
        else:
            await self._ensure_lesson_position_unique(
                section_id=section_id, position=position
            )

        lesson_kwargs = {
            "section_id": section_id,
            "title": data.title,
            "content": data.content,
            "video_url": data.video_url,
            "duration": data.duration,
            "position": position,
        }
        if data.lesson_type is not None:
            lesson_kwargs["lesson_type"] = data.lesson_type
        lesson = Lesson(**lesson_kwargs)
        self.session.add(lesson)
        try:
            await self.session.commit()
            await self.session.refresh(lesson)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Урок с такой позицией уже существует",
            )

        return lesson

    async def update_lesson(
        self,
        course_id: UUID,
        section_id: UUID,
        lesson_id: UUID,
        data: LessonUpdate,
    ) -> Lesson:
        """Обновляет урок в секции."""
        lesson = await self.get_lesson_or_404(
            course_id=course_id, section_id=section_id, lesson_id=lesson_id
        )

        update_data = validate_non_empty_body(data)

        if "position" in update_data:
            if update_data["position"] != lesson.position:
                await self._ensure_lesson_position_unique(
                    section_id=section_id,
                    position=update_data["position"],
                    exclude_lesson_id=lesson.id,
                )

        for key, value in update_data.items():
            setattr(lesson, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(lesson)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Урок с такой позицией уже существует",
            )

        return lesson

    async def delete_lesson(
        self, course_id: UUID, section_id: UUID, lesson_id: UUID
    ) -> None:
        """Удаляет урок из секции."""
        lesson = await self.get_lesson_or_404(
            course_id=course_id, section_id=section_id, lesson_id=lesson_id
        )
        await self.session.delete(lesson)
        await self.session.commit()

    # --- Helpers ---
    async def _ensure_category_exists(self, category_id: UUID) -> None:
        """Проверяет существование категории, иначе 400."""
        result = await self.session.execute(
            select(Category.id).where(Category.id == category_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Категория не найдена",
            )

    async def _next_section_position(self, course_id: UUID) -> int:
        """Возвращает следующую позицию секции в курсе."""
        result = await self.session.execute(
            select(func.max(Section.position)).where(Section.course_id == course_id)
        )
        max_pos = result.scalar_one_or_none()

        return 0 if max_pos is None else max_pos + 1

    async def _next_lesson_position(self, section_id: UUID) -> int:
        """Возвращает следующую позицию урока в секции."""
        result = await self.session.execute(
            select(func.max(Lesson.position)).where(Lesson.section_id == section_id)
        )
        max_pos = result.scalar_one_or_none()

        return 0 if max_pos is None else max_pos + 1

    async def _ensure_section_position_unique(
        self,
        course_id: UUID,
        position: int,
        exclude_section_id: UUID | None = None,
    ) -> None:
        """Проверяет уникальность позиции секции в курсе."""
        query = select(Section.id).where(
            Section.course_id == course_id, Section.position == position
        )
        if exclude_section_id:
            query = query.where(Section.id != exclude_section_id)
        result = await self.session.execute(query)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Секция с такой позицией уже существует",
            )

    async def _ensure_lesson_position_unique(
        self,
        section_id: UUID,
        position: int,
        exclude_lesson_id: UUID | None = None,
    ) -> None:
        """Проверяет уникальность позиции урока в секции."""
        query = select(Lesson.id).where(
            Lesson.section_id == section_id, Lesson.position == position
        )
        if exclude_lesson_id:
            query = query.where(Lesson.id != exclude_lesson_id)
        result = await self.session.execute(query)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Урок с такой позицией уже существует",
            )


async def get_course_service(
    session: AsyncSession = Depends(get_async_session),
) -> CourseService:
    """DI-фабрика для CourseService."""
    return CourseService(session=session)

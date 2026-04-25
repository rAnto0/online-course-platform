from datetime import datetime
from typing import Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.progress import Enrollment, CourseProgress, LessonProgress
from app.models.enums import EnrollmentStatus, LessonProgressStatus
from app.schemas.progress import (
    EnrollmentCreate,
    EnrollmentUpdate,
    CourseProgressUpsert,
    LessonProgressUpsert,
)
from app.validations.request import validate_non_empty_body


class ProgressService:
    """Сервис прогресса

    Управляет записями Enrollment, CourseProgress и LessonProgress.

    Attributes:
        session (AsyncSession): Асинхронная сессия БД
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Enrollments ---
    async def list_enrollments_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Enrollment]:
        query = (
            select(Enrollment)
            .where(Enrollment.user_id == user_id)
            .order_by(Enrollment.enrolled_at)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)

        return result.scalars().all()

    async def get_enrollment_or_404(self, enrollment_id: UUID) -> Enrollment:
        result = await self.session.execute(
            select(Enrollment).where(Enrollment.id == enrollment_id)
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись о зачислении не найдена",
            )

        return enrollment

    async def get_enrollment_by_user_course_or_404(
        self,
        user_id: UUID,
        course_id: UUID,
    ) -> Enrollment:
        result = await self.session.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
            )
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись о зачислении не найдена",
            )

        return enrollment

    async def create_enrollment(
        self, data: EnrollmentCreate, user_id: UUID
    ) -> Enrollment:
        status_value = data.status or EnrollmentStatus.ACTIVE
        enrollment = Enrollment(
            user_id=user_id,
            course_id=data.course_id,
            status=status_value,
        )
        if status_value == EnrollmentStatus.COMPLETED:
            enrollment.completed_at = datetime.utcnow()

        self.session.add(enrollment)
        try:
            await self.session.commit()
            await self.session.refresh(enrollment)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь уже записан на курс",
            )

        return enrollment

    async def update_enrollment(
        self,
        enrollment_id: UUID,
        data: EnrollmentUpdate,
    ) -> Enrollment:
        enrollment = await self.get_enrollment_or_404(enrollment_id)
        update_data = validate_non_empty_body(data)

        if "status" in update_data:
            enrollment.status = update_data["status"]
            if enrollment.status == EnrollmentStatus.COMPLETED:
                if enrollment.completed_at is None:
                    enrollment.completed_at = datetime.utcnow()
            else:
                enrollment.completed_at = None

        await self.session.commit()
        await self.session.refresh(enrollment)

        return enrollment

    # --- Course Progress ---
    async def get_course_progress_or_404(
        self,
        user_id: UUID,
        course_id: UUID,
    ) -> CourseProgress:
        result = await self.session.execute(
            select(CourseProgress).where(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course_id,
            )
        )
        course_progress = result.scalar_one_or_none()
        if course_progress is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Прогресс курса не найден",
            )

        return course_progress

    async def upsert_course_progress(
        self,
        user_id: UUID,
        course_id: UUID,
        data: CourseProgressUpsert,
    ) -> CourseProgress:
        update_data = validate_non_empty_body(data, exclude_none=False)

        result = await self.session.execute(
            select(CourseProgress).where(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course_id,
            )
        )
        course_progress = result.scalar_one_or_none()

        if course_progress is None:
            course_progress = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                total_lessons=update_data.get("total_lessons", 0) or 0,
                progress_percent=update_data.get("progress_percent", 0) or 0,
                last_lesson_id=update_data.get("last_lesson_id"),
            )
            self.session.add(course_progress)
        else:
            for key, value in update_data.items():
                setattr(course_progress, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(course_progress)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Прогресс курса уже существует",
            )

        return course_progress

    # --- Lesson Progress ---
    async def get_lesson_progress_by_ids(
        self, user_id: UUID, lesson_ids: list[UUID]
    ) -> Sequence[LessonProgress]:
        result = await self.session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
        )

        return result.scalars().all()

    async def get_lesson_progress_or_404(
        self,
        user_id: UUID,
        lesson_id: UUID,
    ) -> LessonProgress:
        result = await self.session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
            )
        )
        lesson_progress = result.scalar_one_or_none()
        if lesson_progress is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Прогресс урока не найден",
            )

        return lesson_progress

    async def upsert_lesson_progress(
        self,
        user_id: UUID,
        lesson_id: UUID,
        data: LessonProgressUpsert,
    ) -> LessonProgress:
        update_data = validate_non_empty_body(data, exclude_none=False)

        result = await self.session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id,
            )
        )
        lesson_progress = result.scalar_one_or_none()

        if lesson_progress is None:
            if (
                update_data.get("course_id") is None
                or update_data.get("section_id") is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="course_id и section_id обязательны для создания прогресса урока",
                )

            lesson_progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                course_id=update_data["course_id"],
                section_id=update_data["section_id"],
                status=update_data.get("status") or LessonProgressStatus.NOT_STARTED,
                progress_percent=update_data.get("progress_percent") or 0,
            )
            self._apply_lesson_status(lesson_progress)
            self.session.add(lesson_progress)
        else:
            for key, value in update_data.items():
                setattr(lesson_progress, key, value)
            self._apply_lesson_status(lesson_progress)

        try:
            await self.session.commit()
            await self.session.refresh(lesson_progress)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Прогресс урока уже существует",
            )

        return lesson_progress

    def _apply_lesson_status(self, lesson_progress: LessonProgress) -> None:
        now = datetime.utcnow()
        if lesson_progress.status == LessonProgressStatus.NOT_STARTED:
            lesson_progress.started_at = None
            lesson_progress.completed_at = None
        elif lesson_progress.status == LessonProgressStatus.IN_PROGRESS:
            if lesson_progress.started_at is None:
                lesson_progress.started_at = now
            lesson_progress.completed_at = None
        elif lesson_progress.status == LessonProgressStatus.COMPLETED:
            if lesson_progress.started_at is None:
                lesson_progress.started_at = now
            if lesson_progress.completed_at is None:
                lesson_progress.completed_at = now


async def get_progress_service(
    session: AsyncSession = Depends(get_async_session),
) -> ProgressService:
    return ProgressService(session=session)

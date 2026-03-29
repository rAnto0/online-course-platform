from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .enums import EnrollmentStatus, LessonProgressStatus


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(
        PGENUM(EnrollmentStatus, name="enrollment_statuses", create_type=True),
        nullable=False,
        default=EnrollmentStatus.ACTIVE,
        server_default=EnrollmentStatus.ACTIVE.value,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),
        Index("ix_enrollments_user_id", "user_id"),
        Index("ix_enrollments_course_id", "course_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Enrollment(id={self.id}, user_id={self.user_id}, course_id={self.course_id}, "
            f"status='{self.status}')>"
        )


class CourseProgress(Base):
    __tablename__ = "course_progress"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    total_lessons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_lesson_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_course_progress_user_course"),
        Index("ix_course_progress_user_id", "user_id"),
        Index("ix_course_progress_course_id", "course_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CourseProgress(id={self.id}, user_id={self.user_id}, course_id={self.course_id}, "
            f"total_lessons={self.total_lessons}, progress_percent={self.progress_percent})>"
        )


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[LessonProgressStatus] = mapped_column(
        PGENUM(LessonProgressStatus, name="lesson_progress_statuses", create_type=True),
        nullable=False,
        default=LessonProgressStatus.NOT_STARTED,
        server_default=LessonProgressStatus.NOT_STARTED.value,
    )
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
        Index("ix_lesson_progress_user_id", "user_id"),
        Index("ix_lesson_progress_course_id", "course_id"),
        Index("ix_lesson_progress_section_id", "section_id"),
        Index("ix_lesson_progress_lesson_id", "lesson_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<LessonProgress(id={self.id}, user_id={self.user_id}, lesson_id={self.lesson_id}, "
            f"status='{self.status}', progress_percent={self.progress_percent})>"
        )

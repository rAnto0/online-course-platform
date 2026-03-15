from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM as PGENUM, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .enums import CourseLevel, CourseStatus, LessonType

if TYPE_CHECKING:
    from .categories import Category


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    author_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id")
    )
    level: Mapped[CourseLevel | None] = mapped_column(
        PGENUM(CourseLevel, name="course_levels", create_type=True)
    )
    price: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[CourseStatus] = mapped_column(
        PGENUM(CourseStatus, name="course_statuses", create_type=True),
        nullable=False,
        default=CourseStatus.DRAFT,
        server_default=CourseStatus.DRAFT.value,
    )
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category: Mapped["Category | None"] = relationship(back_populates="courses")
    sections: Mapped[list["Section"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Section.position",
    )

    __table_args__ = (
        Index("ix_courses_author_id", "author_id"),
        Index("ix_courses_category_id", "category_id"),
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, title='{self.title}', status='{self.status}')>"


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    course_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    course: Mapped["Course"] = relationship(back_populates="sections")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Lesson.position",
    )

    __table_args__ = (
        UniqueConstraint("course_id", "position", name="uq_sections_course_id_position"),
        Index("ix_sections_course_id", "course_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Section(id={self.id}, course_id={self.course_id}, title='{self.title}')>"
        )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    section_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sections.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    lesson_type: Mapped[LessonType] = mapped_column(
        PGENUM(LessonType, name="lesson_types", create_type=True),
        nullable=False,
        default=LessonType.TEXT,
        server_default=LessonType.TEXT.value,
    )
    video_url: Mapped[str | None] = mapped_column(String(512))
    duration: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    section: Mapped["Section"] = relationship(back_populates="lessons")

    __table_args__ = (
        UniqueConstraint("section_id", "position", name="uq_lessons_section_id_position"),
        Index("ix_lessons_section_id", "section_id"),
    )

    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, section_id={self.section_id}, title='{self.title}')>"

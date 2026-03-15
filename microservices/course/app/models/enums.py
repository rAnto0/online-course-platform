from enum import Enum


class CourseLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class CourseStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class LessonType(str, Enum):
    VIDEO = "VIDEO"
    TEXT = "TEXT"
    QUIZ = "QUIZ"

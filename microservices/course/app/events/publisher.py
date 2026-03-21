import logging
from uuid import UUID

from app.broker.rabbitmq import rabbitmq
from app.core.config import settings
from app.events.schemas import CoursePublishedEvent, UserRoleUpdatedEvent
from app.models.course import Course

logger = logging.getLogger("app.events.publisher")

async def publish_course_published(course: Course):
    if not settings.ENABLE_EVENTS or not settings.RABBITMQ_URL:
        return

    event = CoursePublishedEvent(
        id=course.id,
        title=course.title,
        description=course.description,
        author_id=course.author_id,
        category_id=course.category_id,
        level=course.level,
        price=course.price,
        status=course.status,
        thumbnail_url=course.thumbnail_url,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )

    try:
        await rabbitmq.publish(
            exchange_name=settings.RABBITMQ_EXCHANGE,
            routing_key="course.published",
            message=event.model_dump(mode="json"),
        )
        logger.info(f"Course published event published for course {course.id}")
    except Exception:
        logger.exception("Failed to publish course.published event")


async def publish_user_role_updated(user_id: UUID, role: str, course_id: UUID):
    if not settings.ENABLE_EVENTS or not settings.RABBITMQ_URL:
        return

    event = UserRoleUpdatedEvent(
        user_id=user_id,
        role=role,
        course_id=course_id,
    )

    try:
        await rabbitmq.publish(
            exchange_name=settings.RABBITMQ_EXCHANGE,
            routing_key="user.role.updated",
            message=event.model_dump(mode="json"),
        )
        logger.info(
            "User role updated event published",
            extra={"user_id": str(user_id), "role": role},
        )
    except Exception:
        logger.exception("Failed to publish user.role.updated event")

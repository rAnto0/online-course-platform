import logging

from app.broker.rabbitmq import RabbitMQ
from app.core.config import settings
from app.events.schemas import UserCreatedEvent
from app.models.users import User

logger = logging.getLogger("app.events.publisher")

rabbitmq = RabbitMQ(settings.RABBITMQ_URL, settings.RABBITMQ_EXCHANGE)


async def publish_user_created(user: User):
    if not settings.ENABLE_EVENTS or not settings.RABBITMQ_URL:
        return

    event = UserCreatedEvent(
        id=user.id,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )

    try:
        await rabbitmq.publish(
            routing_key="user.created",
            message=event.model_dump(mode="json"),
        )
        logger.info(f"User created event published for user {user.id}")
    except Exception:
        logger.exception("Failed to publish user.created event")

import json
import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.core.config import settings
from app.core.database import async_session_factory
from app.events.schemas import UserRoleUpdatedEvent
from app.models.enums import UserRole
from app.models.users import User
from app.broker.rabbitmq import rabbitmq

logger = logging.getLogger("app.events.consumer")


async def start_user_role_updated_consumer() -> None:
    exchange = await rabbitmq.get_exchange(
        settings.COURSE_EVENTS_EXCHANGE,
        channel_type="consumer",
    )
    if not rabbitmq.consumer_channel:
        raise RuntimeError("RabbitMQ channel not initialized")

    queue = await rabbitmq.consumer_channel.declare_queue(
        settings.COURSE_EVENTS_QUEUE,
        durable=True,
    )
    await queue.bind(exchange, routing_key="user.role.updated")

    await queue.consume(_handle_user_role_updated, no_ack=False)
    logger.info(
        "User role updated consumer started",
        extra={"queue": settings.COURSE_EVENTS_QUEUE},
    )


async def _handle_user_role_updated(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body)
            event = UserRoleUpdatedEvent.model_validate(payload)
        except Exception:
            logger.exception("Failed to parse user.role.updated event")
            return

        try:
            new_role = UserRole(event.role)
        except ValueError:
            logger.warning("Unknown role in event: %s", event.role)
            return

        async with async_session_factory() as session:
            user = await session.get(User, event.user_id)
            if user is None:
                logger.warning("User not found for role update: %s", event.user_id)
                return

            if user.role == new_role:
                return

            user.role = new_role
            await session.commit()
            logger.info(
                "User role updated",
                extra={
                    "user_id": str(event.user_id),
                    "role": event.role,
                    "course_id": str(event.course_id),
                },
            )

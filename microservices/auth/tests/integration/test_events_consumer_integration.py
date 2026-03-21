import asyncio
import json
from uuid import uuid4

import aio_pika
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.users import User


@pytest.mark.asyncio
async def test_user_role_updated_event_via_rabbitmq(db_session, monkeypatch):
    from app.broker.rabbitmq import rabbitmq
    from app.core.config import settings
    from app.events import consumer as consumer_module

    if not settings.RABBITMQ_URL:
        pytest.skip("RABBITMQ_URL is not set")

    session_factory = async_sessionmaker(bind=db_session.bind, expire_on_commit=False)
    monkeypatch.setattr(consumer_module, "async_session_factory", session_factory)

    queue_name = f"auth.course.events.test.{uuid4()}"
    monkeypatch.setattr(settings, "COURSE_EVENTS_QUEUE", queue_name)

    await rabbitmq.connect()
    try:
        await consumer_module.start_user_role_updated_consumer()

        user = User(
            username="user_role_int_test",
            email="user_role_int_test@example.com",
            hashed_password=get_password_hash("TestPass123!"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        user_id = user.id

        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.COURSE_EVENTS_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key="user.role.updated")
        payload = {
            "user_id": str(user_id),
            "role": "teacher",
            "course_id": str(uuid4()),
        }
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                content_type="application/json",
            ),
            routing_key="user.role.updated",
        )
        await connection.close()

        updated = None
        for _ in range(30):
            updated = await db_session.get(User, user_id, populate_existing=True)
            if updated and updated.role == UserRole.TEACHER:
                break
            await asyncio.sleep(0.2)

        assert updated is not None
        assert updated.role == UserRole.TEACHER
    finally:
        try:
            cleanup_conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            cleanup_channel = await cleanup_conn.channel()
            cleanup_queue = await cleanup_channel.declare_queue(
                queue_name, passive=True
            )
            await cleanup_queue.delete(if_unused=False, if_empty=False)
            await cleanup_conn.close()
        except Exception:
            pass
        await rabbitmq.close()

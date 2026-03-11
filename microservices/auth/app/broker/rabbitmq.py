import json
from typing import Optional

import aio_pika
import logging


logger = logging.getLogger("app.broker.rabbitmq")


class RabbitMQ:
    def __init__(self, url: str, exchange_name: str):
        self.url = url
        self.exchange_name = exchange_name
        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.exchange: Optional[aio_pika.abc.AbstractExchange] = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()

        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("RabbitMQ connected", extra={"exchange": self.exchange_name})

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        self.channel = None
        self.connection = None
        self.exchange = None

    async def publish(self, routing_key: str, message: dict):
        if not self.exchange:
            raise RuntimeError("RabbitMQ is not connected")

        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(message, default=str).encode(),
                content_type="application/json",
            ),
            routing_key=routing_key,
        )
        logger.debug(
            f"Message published to {routing_key}, body size: {len(json.dumps(message))}"
        )

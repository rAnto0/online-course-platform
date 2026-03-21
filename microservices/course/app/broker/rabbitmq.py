import json
import logging
from typing import Optional

import aio_pika

from app.core.config import settings


logger = logging.getLogger("app.broker.rabbitmq")


class RabbitMQ:
    def __init__(self, url: str):
        self.url = url
        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.publisher_channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.consumer_channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.exchanges: dict[tuple[str, str], aio_pika.abc.AbstractExchange] = {}

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.publisher_channel = await self.connection.channel()
        self.consumer_channel = await self.connection.channel()
        logger.info("RabbitMQ connected")

    async def close(self):
        if self.publisher_channel:
            await self.publisher_channel.close()
        if self.consumer_channel and self.consumer_channel is not self.publisher_channel:
            await self.consumer_channel.close()
        if self.connection:
            await self.connection.close()
        self.publisher_channel = None
        self.consumer_channel = None
        self.connection = None
        self.exchanges = {}

    async def get_exchange(
        self, exchange_name: str, channel_type: str = "publisher"
    ) -> aio_pika.abc.AbstractExchange:
        if channel_type not in ("publisher", "consumer"):
            raise ValueError("channel_type must be 'publisher' or 'consumer'")

        channel = (
            self.publisher_channel
            if channel_type == "publisher"
            else self.consumer_channel
        )
        if not channel:
            raise RuntimeError("RabbitMQ is not connected")

        key = (exchange_name, channel_type)
        exchange = self.exchanges.get(key)
        if exchange is None:
            exchange = await channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            self.exchanges[key] = exchange
        return exchange

    async def publish(self, exchange_name: str, routing_key: str, message: dict):
        exchange = await self.get_exchange(exchange_name, channel_type="publisher")

        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(message, default=str).encode(),
                content_type="application/json",
            ),
            routing_key=routing_key,
        )
        logger.debug(
            f"Message published to {routing_key}, body size: {len(json.dumps(message))}"
        )


rabbitmq = RabbitMQ(settings.RABBITMQ_URL)

import asyncio
import json
import os

import aio_pika
from aiormq import AMQPConnectionError
from loguru import logger

from common.domain.services.send_to_queue_service import ISendToQueueService


class SendToQueueService(ISendToQueueService):
    def __init__(self, routing_key: str = "task_queue"):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.routing_key = routing_key
        self.connection = None
        self.channel = None

    async def connect(self, max_retries=5, retry_delay=2):
        # Reuse connection
        if self.connection and not self.connection.is_closed:
            return

        for attempt in range(max_retries):
            try:
                logger.info("Establishing RabbitMQ connection...")
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
                self.channel = await self.connection.channel()
                return
            except AMQPConnectionError as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))
                else:
                    raise

    async def send_message(self, message: dict, max_retries=5, retry_delay=2):
        await self.connect()
        for attempt in range(max_retries):
            try:
                await self.channel.default_exchange.publish(
                    aio_pika.Message(body=json.dumps(message).encode()),
                    routing_key=self.routing_key,
                )
                logger.info(f"Message sent to {self.routing_key}")
                return
            except Exception as e:
                logger.error(f"Publish attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))
                else:
                    raise

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ 連接已關閉")

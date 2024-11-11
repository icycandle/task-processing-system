import asyncio
import json
import os
from typing import AsyncIterator, Callable, Coroutine

import aio_pika
from aiormq import AMQPConnectionError
from loguru import logger

BATCH_SIZE = 32
BATCH_TIMEOUT = 0.1  # seconds




async def batch_generator(
    async_iterable, batch_size: int, batch_timeout: float
) -> AsyncIterator[list[aio_pika.IncomingMessage]]:
    batch: list[aio_pika.IncomingMessage] = []
    start_time = asyncio.get_event_loop().time()

    async for item in async_iterable:
        batch.append(item)

        # When batch size is reached, yield the batch
        if len(batch) >= batch_size:
            yield batch
            batch = []
            start_time = asyncio.get_event_loop().time()  # Reset timer for next batch
        else:
            # Check if time limit has been exceeded for this batch
            time_elapsed = asyncio.get_event_loop().time() - start_time
            if time_elapsed >= batch_timeout:
                yield batch
                batch = []
                start_time = asyncio.get_event_loop().time()

    # Yield any remaining items as the last batch
    if batch:
        yield batch


class ConsumeQueueService:
    def __init__(self, routing_key: str = "task_queue", prefetch_count: int = 100):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.connection = None
        self.channel = None
        self.routing_key = routing_key
        self.prefetch_count = prefetch_count
        self.rabbitmq_connected = False
        self.max_retries = 10
        self.retry_delay = 1

    async def connect(self):
        for attempt in range(self.max_retries):
            try:
                logger.info(f"嘗試連接 RabbitMQ... (第 {attempt + 1} 次)")
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url, timeout=30)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=self.prefetch_count)
                self.rabbitmq_connected = True
                logger.info("成功連接到 RabbitMQ")
                return
            except AMQPConnectionError as e:
                self.rabbitmq_connected = False
                logger.error(f"RabbitMQ 連接錯誤: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)

    async def consume(self, handler_function: callable):
        await self.connect()
        queue = await self.channel.declare_queue(self.routing_key, durable=True)
        logger.info("Waiting for messages...")

        async for batch in batch_generator(queue.iterator(), BATCH_SIZE, BATCH_TIMEOUT):
            try:
                # Process the batch using the handler function, which returns success_task_ids
                success_task_ids = await handler_function(batch)

                # Acknowledge or requeue each message based on success_task_ids
                for message in batch:
                    message_content = json.loads(message.body)
                    task_id = message_content.get("task_id")

                    if task_id in success_task_ids:
                        await message.ack()
                    else:
                        await message.nack(requeue=True)

            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                # If there's an exception in processing, requeue all messages
                await asyncio.gather(*[message.nack(requeue=True) for message in batch])

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.rabbitmq_connected = False

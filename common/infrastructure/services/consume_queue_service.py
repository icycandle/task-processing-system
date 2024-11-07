import asyncio
import os

import aio_pika
from aiormq import AMQPConnectionError
from loguru import logger

from common.applications.use_case.consumer.task_processing import TaskProcessUseCase
from common.domain.services.consume_queue_service import IConsumeQueueService
from common.infrastructure.database import get_db
from common.infrastructure.repo.task_repo import TaskRepository


class ConsumeQueueService(IConsumeQueueService):
    def __init__(self, routing_key: str = "task_queue"):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.connection = None
        self.channel = None
        self.rabbitmq_connected = False
        self.routing_key = routing_key
        self.max_retries = 5
        self.retry_delay = 5

    async def connect(self):
        for attempt in range(self.max_retries):
            try:
                logger.info(f"嘗試連接 RabbitMQ... (第 {attempt + 1} 次)")
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url, timeout=30)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)
                self.rabbitmq_connected = True
                logger.info("成功連接到 RabbitMQ")
                return
            except AMQPConnectionError as e:
                self.rabbitmq_connected = False
                logger.error(f"RabbitMQ 連接錯誤: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)

    async def consume(self):
        await self.connect()

        queue = await self.channel.declare_queue(self.routing_key, durable=True)

        async with queue.iterator() as queue_iter:
            logger.info("消費者已啟動，等待消息...")
            async for message in queue_iter:
                await self.process_message(message)

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            async for session in get_db():
                logger.info("成功獲取資料庫 session")
                await TaskProcessUseCase(
                    task_repository=TaskRepository(db_session=session),
                ).task_processing(message)

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.rabbitmq_connected = False

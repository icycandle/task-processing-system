import asyncio
import json

from loguru import logger

from common.constants import MOCK_PROCESSING_TIME
from common.domain.models import TaskStatus
from common.domain.repo.task_repo import ITaskRepository, TaskNotFoundError

rabbitmq_connected = False
routing_key = "task_queue"


class ProcessService:
    def __init__(self, sleep_time: int = MOCK_PROCESSING_TIME):
        self.sleep_time = sleep_time

    async def run(self):
        await asyncio.sleep(self.sleep_time)


class TaskProcessUseCase:
    def __init__(
        self,
        task_repository: ITaskRepository,
        process_service: ProcessService | None = None,
    ):
        self.repo = task_repository

        self.process_service = process_service if process_service else ProcessService()

    async def task_processing(self, message):
        logger.info(f"收到消息: {message.body}")

        try:
            message_content = json.loads(message.body)
            task_id = message_content["task_id"]
        except Exception as e:
            logger.exception(e)
            return

        logger.info(f"處理任務 ID: {task_id}")

        try:
            domain_task = await self.repo.get_task(task_id)
            logger.info(f"從資料庫獲取任務 {task_id=} 狀態: {domain_task.status}")
        except TaskNotFoundError:
            logger.error(f"任務 {task_id=} 不存在")
            return

        logger.info(f"{domain_task.status=}")

        if not domain_task or domain_task.status != TaskStatus.PENDING:
            return

        domain_task.mark_processing()
        await self.repo.update_task(domain_task)

        # Processing
        await self.process_service.run()

        # update
        domain_task = await self.repo.get_task(task_id)
        if domain_task.status != TaskStatus.CANCELED:
            domain_task.mark_completed()
            await self.repo.update_task(domain_task)

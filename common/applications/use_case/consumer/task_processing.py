import asyncio
import json
from datetime import datetime

from aio_pika import IncomingMessage
from loguru import logger

from common.constants import MOCK_PROCESSING_TIME
from common.domain.models import Task, TaskStatus
from common.domain.repo.task_repo import ITaskRepository
from common.domain.services.prometheus_service import IPrometheusMetricsService

rabbitmq_connected = False
routing_key = "task_queue"


class TaskProcessUseCase:
    def __init__(
        self,
        task_repository: ITaskRepository,
        metrics: IPrometheusMetricsService,
        sleep_time: float = MOCK_PROCESSING_TIME,
    ):
        self.repo = task_repository
        self.metrics = metrics

        self.sleep_time = sleep_time

    async def task_processing(self, task: Task) -> int | None:
        """避免在這 method 直接進行 database query"""
        started_processing_at = datetime.now().timestamp()

        await self.metrics.inc_label("received")
        logger.info(f"開始處理任務: {task.id}")

        if task.status != TaskStatus.PENDING:
            logger.warning(f"跳過非 PENDING 狀態的任務 {task.id}")
            return


        task.mark_processing()
        await self.repo.update_task(task)

        await asyncio.sleep(self.sleep_time)

        if task.status == TaskStatus.CANCELED:
            return

        task.mark_completed()

        end_processing_at = datetime.now().timestamp()
        processing_duration = end_processing_at - started_processing_at
        self.metrics.observe_processing_time(processing_duration)

        execution_duration = end_processing_at - task.created_at.timestamp()
        self.metrics.observe_execution_time(execution_duration)
        await self.metrics.inc_label("success")

        return task.id


    # TODO: 介面上出現 `IncomingMessage` 不太合適，應該移往 infra 或 main.py, 只需要接受 task_ids 並回傳 success_task_ids
    async def process_batch(self, messages: list[IncomingMessage]) -> list[int]:
        """
        目前效能瓶頸是 database IO, 透過 batch query & batch update 來減少 database IO

        """
        task_ids: list[int] = []
        for message in messages:
            try:
                message_content = json.loads(message.body)
                task_id = message_content["task_id"]
                task_ids.append(task_id)
            except Exception as e:
                logger.exception(f"解析消息時出現錯誤: {e}")
                continue

        tasks = await self.repo.get_tasks_by_ids(task_ids)

        # 發揮 async 的 concurrency 優勢
        processing_tasks = [self.task_processing(task) for task in tasks]
        completed_tasks = await asyncio.gather(*processing_tasks, return_exceptions=True)

        await self.repo.update_tasks(tasks)

        success_task_ids = []
        for message, result in zip(messages, completed_tasks):
            if isinstance(result, Exception):
                continue

            if isinstance(result, int):
                continue

            success_task_ids.append(result)

        return success_task_ids

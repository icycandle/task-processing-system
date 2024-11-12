from common.domain.models import Task, TaskStatus
from common.domain.repo.task_repo import ITaskRepository
from common.domain.services.send_to_queue_service import ISendToQueueService
from common.domain.services.task_cancellation_cache import ITaskCancellationCache


class CreateTaskUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        task_queue_service: ISendToQueueService,
    ):
        self.task_repo = task_repo
        self.task_queue_service = task_queue_service

    async def create_task(self, payload: str) -> Task:
        task = await self.task_repo.create_task(payload)
        await self.task_queue_service.send_message(
            message={
                "task_id": task.id,
                "payload": task.payload,
            },
        )
        return task


class CancelTaskUseCase:
    def __init__(self, task_repo: ITaskRepository, cancellation_cache: ITaskCancellationCache):
        self.task_repo = task_repo
        self.cancellation_cache = cancellation_cache

    async def cancel_task(self, task_id: int) -> Task:
        task = await self.task_repo.get_task(task_id)

        if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            raise ValueError("Cannot cancel a completed or already canceled task")

        # 注意這邊是 double write, 會有資料一致性相關的 edge case
        task.cancel()
        await self.task_repo.update_task(task)

        # 設置取消標記
        await self.cancellation_cache.set_task_cancelled(task_id)

        return task

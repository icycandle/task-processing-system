import redis

from common.domain.services.task_cancellation_cache import ITaskCancellationCache


class TaskCancellationCache(ITaskCancellationCache):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def set_task_cancelled(self, task_id: int):
        """設置任務取消標記"""
        await self.redis_client.set(f"task:{task_id}:cancel", "1", ex=3600)

    async def is_task_cancelled(self, task_id: int) -> bool:
        """檢查任務是否被取消"""
        return await self.redis_client.exists(f"task:{task_id}:cancel") > 0

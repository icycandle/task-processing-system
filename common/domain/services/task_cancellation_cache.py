from abc import ABC, abstractmethod


class ITaskCancellationCache(ABC):

    @abstractmethod
    async def set_task_cancelled(self, task_id: int):
        """設置任務取消標記"""
        pass

    @abstractmethod
    async def is_task_cancelled(self, task_id: int) -> bool:
        """檢查任務是否被取消"""
        pass

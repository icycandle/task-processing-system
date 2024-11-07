from abc import ABC, abstractmethod

from common.domain.models import Task


class TaskNotFoundError(Exception):
    task_id: str


class ITaskRepository(ABC):
    @abstractmethod
    async def create_task(self, payload: str) -> Task:
        """建立新任務"""
        pass

    @abstractmethod
    async def get_task(self, task_id: int) -> Task:
        """獲取指定任務"""
        pass

    @abstractmethod
    async def update_task(self, domain_task: Task) -> None:
        """更新任務狀態"""
        pass

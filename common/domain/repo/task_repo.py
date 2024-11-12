from abc import ABC, abstractmethod
from dataclasses import dataclass

from common.domain.models import Task


@dataclass
class TaskNotFoundError(Exception):
    task_id: int


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

    @abstractmethod
    async def get_tasks_by_ids(self, task_ids: list[int]) -> list[Task]:
        """batch get tasks by ids"""
        pass

    @abstractmethod
    async def update_tasks(self, tasks: list[Task]) -> None:
        """batch update tasks"""
        pass

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.domain.models import Task
from common.domain.repo.task_repo import ITaskRepository, TaskNotFoundError
from common.infrastructure.db_schema import TaskORM


class TaskRepository(ITaskRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__()
        self.db = db_session

    async def create_task(self, payload: str) -> Task:
        domain_task = Task(payload=payload)
        logger.info(f"create_task: {domain_task}")
        task_orm = TaskORM(payload=domain_task.payload, status=domain_task.status.value)
        self.db.add(task_orm)
        await self.db.commit()
        await self.db.refresh(task_orm)
        domain_task.id = task_orm.id
        return domain_task

    async def get_task(self, task_id: int) -> Task:
        stmt = select(TaskORM).where(TaskORM.id == task_id)
        result = await self.db.execute(stmt)
        task_orm = result.scalar_one_or_none()
        if not task_orm:
            raise TaskNotFoundError()
        await self.db.refresh(task_orm)
        return Task(id=task_orm.id, payload=task_orm.payload, status=task_orm.status)

    async def update_task(self, domain_task: Task):
        stmt = select(TaskORM).where(TaskORM.id == domain_task.id)
        result = await self.db.execute(stmt)
        task_orm = result.scalar_one_or_none()
        if task_orm:
            task_orm.status = domain_task.status.value
            await self.db.commit()

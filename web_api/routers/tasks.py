from fastapi import APIRouter, Depends

from common.applications.use_case.web_api.task_create import CancelTaskUseCase, CreateTaskUseCase
from common.infrastructure.dependencies import get_cancel_task_use_case, get_create_task_use_case, get_task_repo
from common.infrastructure.repo.task_repo import TaskRepository
from web_api.domain.models import TaskPayload, TaskResponse

task_router = APIRouter()


@task_router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_payload: TaskPayload,
    create_task_use_case: CreateTaskUseCase = Depends(get_create_task_use_case),
):
    domain_task = await create_task_use_case.create_task(
        payload=task_payload.payload,
    )

    return TaskResponse(task_id=domain_task.id, status=domain_task.status)


@task_router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: int,
    cancel_task_use_case: CancelTaskUseCase = Depends(get_cancel_task_use_case),
):
    task = await cancel_task_use_case.cancel_task(
        task_id=task_id,
    )
    return TaskResponse(task_id=task.id, status=task.status)


@task_router.get("/tasks/{task_id}/status", response_model=TaskResponse)
async def get_task_status(task_id: int, task_repo: TaskRepository = Depends(get_task_repo)):
    domain_task = await task_repo.get_task(task_id)
    return TaskResponse(task_id=domain_task.id, status=domain_task.status)

from fastapi import Depends, FastAPI
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from common.applications.use_case.web_api.task_create import CancelTaskUseCase, CreateTaskUseCase
from common.domain.models import OperationNotAllowed
from common.domain.repo.task_repo import TaskNotFoundError
from common.infrastructure.dependencies import get_cancel_task_use_case, get_create_task_use_case, get_task_repo
from common.infrastructure.repo.task_repo import TaskRepository
from web_api.domain.models import TaskPayload, TaskResponse

app = FastAPI()


@app.exception_handler(TaskNotFoundError)
async def task_not_found_exception_handler(request: Request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Task with ID {exc.task_id} not found"},
    )


@app.exception_handler(OperationNotAllowed)
async def operation_not_allowed_handler(request: Request, exc: OperationNotAllowed):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_payload: TaskPayload,
    create_task_use_case: CreateTaskUseCase = Depends(get_create_task_use_case),
):
    domain_task = await create_task_use_case.create_task(
        payload=task_payload.payload,
    )

    return TaskResponse(task_id=domain_task.id, status=domain_task.status)


@app.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: int,
    # db: AsyncSession = Depends(get_db),
    cancel_task_use_case: CancelTaskUseCase = Depends(get_cancel_task_use_case),
):
    task = await cancel_task_use_case.cancel_task(
        task_id=task_id,
    )
    return TaskResponse(task_id=task.id, status=task.status)


@app.get("/tasks/{task_id}/status", response_model=TaskResponse)
async def get_task_status(task_id: int, task_repo: TaskRepository = Depends(get_task_repo)):
    domain_task = await task_repo.get_task(task_id)
    return TaskResponse(task_id=domain_task.id, status=domain_task.status)

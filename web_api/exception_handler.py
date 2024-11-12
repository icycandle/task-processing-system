from fastapi import FastAPI
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from common.domain.models import OperationNotAllowed
from common.domain.repo.task_repo import TaskNotFoundError


def apply_exception_handler(app: FastAPI):
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

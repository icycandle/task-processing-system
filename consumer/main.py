import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from loguru import logger
from sqlalchemy import text

from common.applications.use_case.consumer.task_processing import TaskProcessUseCase
from common.infrastructure.database import get_db
from common.infrastructure.dependencies import (
    get_consume_queue_service,
    get_prometheus_metrics_service,
    get_task_cancellation_cache,
)
from common.infrastructure.repo.task_repo import TaskRepository

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    consume_queue_service = get_consume_queue_service()
    metrics_service = get_prometheus_metrics_service()
    cancellation_cache = get_task_cancellation_cache()

    async for session in get_db():
        task_repository = TaskRepository(db_session=session)
        task_process_use_case = TaskProcessUseCase(
            task_repository=task_repository,
            metrics=metrics_service,
            cancellation_cache=cancellation_cache,
        )

        # Pass `task_process_use_case.process_batch` as the batch handler function
        consumer_task = asyncio.create_task(
            consume_queue_service.consume(handler_function=task_process_use_case.process_batch)
        )

        yield

        # Cleanup on shutdown
        consumer_task.cancel()
        await consume_queue_service.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    consume_queue_service = get_consume_queue_service()
    rabbitmq_status = consume_queue_service.rabbitmq_connected

    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
        database_status = True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        database_status = False

    if not rabbitmq_status or not database_status:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "rabbitmq_connected": rabbitmq_status,
                "database_connected": database_status,
            },
        )
    return {
        "status": "healthy",
        "rabbitmq_connected": rabbitmq_status,
        "database_connected": database_status,
    }

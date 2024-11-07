import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from loguru import logger
from sqlalchemy import text

from common.infrastructure.database import get_db
from common.infrastructure.dependencies import get_consume_queue_service

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    consume_queue_service = get_consume_queue_service()
    consumer_task = asyncio.create_task(consume_queue_service.consume())

    yield

    consumer_task.cancel()
    await consume_queue_service.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    consume_queue_service = get_consume_queue_service()
    rabbitmq_status = consume_queue_service.rabbitmq_connected

    try:
        async for session in get_db():
            await session.execute(text('SELECT 1'))
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

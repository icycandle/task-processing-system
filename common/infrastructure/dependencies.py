from functools import lru_cache

from fastapi import Depends

from common.applications.use_case.web_api.task_create import CancelTaskUseCase, CreateTaskUseCase
from common.infrastructure.database import get_db
from common.infrastructure.repo.task_repo import TaskRepository
from common.infrastructure.services.consume_queue_service import ConsumeQueueService
from common.infrastructure.services.prometheus_service import PrometheusMetricsService
from common.infrastructure.services.send_to_queue_service import SendToQueueService


def get_task_repo(db_session=Depends(get_db)) -> TaskRepository:
    return TaskRepository(db_session=db_session)


@lru_cache()
def get_send_to_queue_service() -> SendToQueueService:
    return SendToQueueService()


@lru_cache()
def get_consume_queue_service() -> ConsumeQueueService:
    return ConsumeQueueService()


# def get_task_process_use_case(db_session) -> TaskProcessUseCase:
#     return TaskProcessUseCase(
#         task_repository=get_task_repo(db_session=db_session),
#         metrics=get_prometheus_metrics_service(),
#     )


def get_create_task_use_case(
    task_repo=Depends(get_task_repo),
    task_queue_service=Depends(get_send_to_queue_service),
) -> CreateTaskUseCase:
    return CreateTaskUseCase(
        task_repo=task_repo,
        task_queue_service=task_queue_service,
    )


def get_cancel_task_use_case(task_repo=Depends(get_task_repo)) -> CancelTaskUseCase:
    return CancelTaskUseCase(
        task_repo=task_repo,
    )


@lru_cache()
def get_prometheus_metrics_service() -> PrometheusMetricsService:
    from loguru import logger

    logger.info("PrometheusMetricsService()")
    metrics_service = PrometheusMetricsService()
    logger.info("metrics_service.start_server()")
    # Start the Prometheus server only once
    metrics_service.start_server()
    return metrics_service

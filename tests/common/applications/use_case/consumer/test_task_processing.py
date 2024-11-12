from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from common.applications.use_case.consumer.task_processing import TaskProcessUseCase
from common.domain.models import Task, TaskStatus
from common.domain.repo.task_repo import ITaskRepository
from common.domain.services.prometheus_service import IPrometheusMetricsService
from common.infrastructure.services.task_cancellation_cache import TaskCancellationCache


class TestTaskProcessUseCase:

    @pytest.mark.asyncio
    async def test_task_processing_when_status_pending(self, mocker):
        # Arrange
        task_id = 1
        task = Task(id=task_id, payload="test", status=TaskStatus.PENDING, created_at=datetime.now())

        # Mock the TaskRepository
        mock_repo = AsyncMock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        # Mock the TaskCancellationCache
        mock_cancellation_cache = AsyncMock(spec=TaskCancellationCache)
        mock_cancellation_cache.is_task_cancelled.return_value = False

        # Mock the PrometheusMetricsService
        mock_metrics = Mock(spec=IPrometheusMetricsService)
        mock_metrics.inc_label.return_value = None
        mock_metrics.observe_processing_time.return_value = None
        mock_metrics.observe_execution_time.return_value = None

        # Instantiate the use case with all dependencies
        use_case = TaskProcessUseCase(
            task_repository=mock_repo,
            metrics=mock_metrics,
            cancellation_cache=mock_cancellation_cache,
            sleep_time=0,  # No sleep for testing
        )

        # Act
        await use_case.task_processing(task)

        # Assert
        assert task.status == TaskStatus.COMPLETED
        mock_repo.update_task.assert_any_call(task)
        mock_metrics.inc_label.assert_any_call("received")
        mock_metrics.inc_label.assert_any_call("success")
        mock_metrics.observe_processing_time.assert_called_once()
        mock_metrics.observe_execution_time.assert_called_once()
        mock_cancellation_cache.is_task_cancelled.assert_called_with(task_id)

    @pytest.mark.asyncio
    async def test_task_processing_with_cancellation_before_processing(self, mocker):
        # Arrange
        task_id = 2
        task = Task(id=task_id, payload="test", status=TaskStatus.PENDING, created_at=datetime.now())

        # Mock the TaskRepository
        mock_repo = AsyncMock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        # Mock the TaskCancellationCache to return True (task is cancelled)
        mock_cancellation_cache = AsyncMock(spec=TaskCancellationCache)
        mock_cancellation_cache.is_task_cancelled.return_value = True

        # Mock the PrometheusMetricsService
        mock_metrics = Mock(spec=IPrometheusMetricsService)
        mock_metrics.inc_label.return_value = None

        # Instantiate the use case with all dependencies
        use_case = TaskProcessUseCase(
            task_repository=mock_repo,
            metrics=mock_metrics,
            cancellation_cache=mock_cancellation_cache,
            sleep_time=0,
        )

        # Act
        await use_case.task_processing(task)

        # Assert
        mock_metrics.inc_label.assert_called_with("received")
        mock_cancellation_cache.is_task_cancelled.assert_called_with(task_id)

    @pytest.mark.asyncio
    async def test_task_processing_when_status_not_pending(self, mocker):
        # Arrange
        task_id = 3
        task = Task(id=task_id, payload="test", status=TaskStatus.PROCESSING)

        # Mock the TaskRepository
        mock_repo = AsyncMock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        # Mock the TaskCancellationCache (should not be called)
        mock_cancellation_cache = AsyncMock(spec=TaskCancellationCache)

        # Mock the PrometheusMetricsService
        mock_metrics = Mock(spec=IPrometheusMetricsService)

        # Instantiate the use case with all dependencies
        use_case = TaskProcessUseCase(
            task_repository=mock_repo,
            metrics=mock_metrics,
            cancellation_cache=mock_cancellation_cache,
            sleep_time=0,
        )

        # Act
        await use_case.task_processing(task)

        # Assert
        assert task.status == TaskStatus.PROCESSING  # Status remains unchanged
        mock_repo.update_task.assert_not_called()
        mock_cancellation_cache.is_task_cancelled.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_processing_when_status_canceled(self, mocker):
        # Arrange
        task_id = 4
        task = Task(id=task_id, payload="test", status=TaskStatus.CANCELED)

        # Mock the TaskRepository
        mock_repo = AsyncMock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        # Mock the TaskCancellationCache (should not be called)
        mock_cancellation_cache = AsyncMock(spec=TaskCancellationCache)

        # Mock the PrometheusMetricsService
        mock_metrics = Mock(spec=IPrometheusMetricsService)

        # Instantiate the use case with all dependencies
        use_case = TaskProcessUseCase(
            task_repository=mock_repo,
            metrics=mock_metrics,
            cancellation_cache=mock_cancellation_cache,
            sleep_time=0,
        )

        # Act
        await use_case.task_processing(task)

        # Assert
        assert task.status == TaskStatus.CANCELED
        mock_repo.update_task.assert_not_called()
        mock_cancellation_cache.is_task_cancelled.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_processing_with_cancellation_during_processing(self, mocker):
        # Arrange
        task_id = 6
        task = Task(id=task_id, payload="test", status=TaskStatus.PENDING, created_at=datetime.now())

        # Mock the TaskRepository
        mock_repo = AsyncMock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        # Mock the TaskCancellationCache to first return False, then True
        mock_cancellation_cache = AsyncMock(spec=TaskCancellationCache)
        mock_cancellation_cache.is_task_cancelled.side_effect = [False, True]

        # Mock the PrometheusMetricsService
        mock_metrics = Mock(spec=IPrometheusMetricsService)
        mock_metrics.inc_label.return_value = None
        mock_metrics.observe_processing_time.return_value = None
        mock_metrics.observe_execution_time.return_value = None

        # Instantiate the use case with all dependencies
        use_case = TaskProcessUseCase(
            task_repository=mock_repo,
            metrics=mock_metrics,
            cancellation_cache=mock_cancellation_cache,
            sleep_time=0,  # No sleep for testing
        )

        # Act
        await use_case.task_processing(task)

        # Assert
        # Since cancellation_cache returns True during processing, task should not be completed
        assert task.status == TaskStatus.CANCELED
        mock_repo.update_task.assert_any_call(task)
        mock_metrics.inc_label.assert_any_call("received")
        mock_metrics.observe_processing_time.assert_not_called()
        mock_metrics.observe_execution_time.assert_not_called()
        assert mock_cancellation_cache.is_task_cancelled.call_count == 2

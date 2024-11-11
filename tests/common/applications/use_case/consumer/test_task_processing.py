import json

import pytest

from common.applications.use_case.consumer.task_processing import TaskProcessUseCase
from common.domain.models import Task, TaskStatus
from common.domain.repo.task_repo import ITaskRepository, TaskNotFoundError
from common.domain.services.prometheus_service import IPrometheusMetricsService


class TestTaskProcessUseCase:

    @pytest.mark.asyncio
    async def test_task_processing_when_status_pending(self, mocker):
        # Arrange
        task_id = 1
        message = mocker.Mock()
        message.body = json.dumps({"task_id": task_id})

        task = Task(id=task_id, payload="test", status=TaskStatus.PENDING)
        mock_repo = mocker.Mock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        use_case = TaskProcessUseCase(
            task_repository=mock_repo, sleep_time=0, metrics=mocker.Mock(spec=IPrometheusMetricsService)
        )

        # Act
        await use_case.task_processing(message)

        # Assert
        assert task.status == TaskStatus.COMPLETED
        mock_repo.update_task.assert_called_with(task)

    @pytest.mark.asyncio
    async def test_task_processing_with_malformed_json(self, mocker):
        # Arrange
        message = mocker.Mock()
        message.body = "not a json"

        mock_repo = mocker.Mock(spec=ITaskRepository)

        use_case = TaskProcessUseCase(
            task_repository=mock_repo, sleep_time=0, metrics=mocker.Mock(spec=IPrometheusMetricsService)
        )

        # Act
        await use_case.task_processing(message)

        # Assert
        mock_repo.get_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_processing_when_task_id_missing(self, mocker):
        # Arrange
        message = mocker.Mock()
        message.body = json.dumps({})  # No task_id in the message content

        mock_repo = mocker.Mock(spec=ITaskRepository)

        use_case = TaskProcessUseCase(
            task_repository=mock_repo, sleep_time=0, metrics=mocker.Mock(spec=IPrometheusMetricsService)
        )

        # Act
        await use_case.task_processing(message)

        # Assert
        mock_repo.get_task.assert_not_called()
        mock_repo.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_processing_when_task_not_found(self, mocker):
        # Arrange
        task_id = 1
        message = mocker.Mock()
        message.body = json.dumps({"task_id": task_id})

        mock_repo = mocker.Mock(spec=ITaskRepository)
        mock_repo.get_task.side_effect = TaskNotFoundError

        use_case = TaskProcessUseCase(
            task_repository=mock_repo, sleep_time=0, metrics=mocker.Mock(spec=IPrometheusMetricsService)
        )

        # Act
        await use_case.task_processing(message)

        # Assert
        mock_repo.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_processing_when_status_not_pending(self, mocker):
        # Arrange
        task_id = 1
        message = mocker.Mock()
        message.body = json.dumps({"task_id": task_id})

        task = Task(id=task_id, payload="test", status=TaskStatus.PROCESSING)
        mock_repo = mocker.Mock(spec=ITaskRepository)
        mock_repo.get_task.return_value = task
        mock_repo.update_task.return_value = None

        use_case = TaskProcessUseCase(
            task_repository=mock_repo, sleep_time=0, metrics=mocker.Mock(spec=IPrometheusMetricsService)
        )

        # Act
        await use_case.task_processing(message)

        # Assert
        assert task.status == TaskStatus.PROCESSING
        mock_repo.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_processing_when_status_canceled(self, mocker):
        # Arrange
        task_id = 1
        message = mocker.Mock()
        message.body = json.dumps({"task_id": task_id})

        task = Task(id=task_id, payload="test", status=TaskStatus.CANCELED)
        mock_repo = mocker.AsyncMock(
            spec=ITaskRepository,
            get_task=mocker.AsyncMock(return_value=task),
            update_task=mocker.AsyncMock(),
        )

        use_case = TaskProcessUseCase(
            task_repository=mock_repo, sleep_time=0, metrics=mocker.Mock(spec=IPrometheusMetricsService)
        )

        # Act
        await use_case.task_processing(message)

        # Assert
        assert task.status == TaskStatus.CANCELED
        mock_repo.update_task.assert_not_called()

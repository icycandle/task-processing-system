import pytest

from common.applications.use_case.web_api.task_create import CreateTaskUseCase
from common.domain.models import Task, TaskStatus
from common.domain.repo.task_repo import ITaskRepository
from common.domain.services.send_to_queue_service import ISendToQueueService


class TestCreateTaskUseCase:

    @pytest.mark.asyncio
    async def test_create_task_with_valid_payload(self, mocker):
        # Arrange
        mock_task_repo = mocker.Mock(spec=ITaskRepository)
        mock_task_queue_service = mocker.Mock(spec=ISendToQueueService)
        use_case = CreateTaskUseCase(mock_task_repo, mock_task_queue_service)
        payload = "valid payload"
        expected_task = Task(id=1, payload=payload, status=TaskStatus.PENDING)

        mock_task_repo.create_task.return_value = expected_task

        # Act
        result = await use_case.create_task(payload)

        # Assert
        assert result == expected_task
        mock_task_repo.create_task.assert_called_once_with(payload)
        mock_task_queue_service.send_message.assert_called_once_with(
            message={"task_id": expected_task.id, "payload": expected_task.payload}
        )

    @pytest.mark.asyncio
    async def test_create_task_raises_exception_on_repo_failure(self, mocker):
        # Arrange
        mock_task_repo = mocker.Mock(spec=ITaskRepository)
        mock_task_queue_service = mocker.Mock(spec=ISendToQueueService)
        use_case = CreateTaskUseCase(mock_task_repo, mock_task_queue_service)
        payload = "valid payload"

        mock_task_repo.create_task.side_effect = Exception("Repository failure")

        # Act & Assert
        with pytest.raises(Exception, match="Repository failure"):
            await use_case.create_task(payload)

        mock_task_repo.create_task.assert_called_once_with(payload)
        mock_task_queue_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_task_handles_queue_exception(self, mocker):
        # Arrange
        mock_task_repo = mocker.Mock(spec=ITaskRepository)
        mock_task_queue_service = mocker.Mock(spec=ISendToQueueService)
        use_case = CreateTaskUseCase(mock_task_repo, mock_task_queue_service)
        payload = "valid payload"
        expected_task = Task(id=1, payload=payload, status=TaskStatus.PENDING)

        mock_task_repo.create_task.return_value = expected_task
        mock_task_queue_service.send_message.side_effect = Exception("Queue error")

        # Act & Assert
        with pytest.raises(Exception) as exc:
            await use_case.create_task(payload)

        assert str(exc.value) == "Queue error"
        mock_task_repo.create_task.assert_called_once_with(payload)
        mock_task_queue_service.send_message.assert_called_once_with(
            message={"task_id": expected_task.id, "payload": expected_task.payload}
        )

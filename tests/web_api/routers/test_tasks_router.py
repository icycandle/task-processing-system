from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from common.applications.use_case.web_api.task_create import CancelTaskUseCase, CreateTaskUseCase
from common.domain.models import Task, TaskStatus
from common.infrastructure.repo.task_repo import TaskNotFoundError
from web_api.main import create_app


@pytest.fixture
def client():
    app = create_app()
    client = TestClient(app)
    return client


def test_create_task_success(client, mocker):
    # arrange
    mock_task = Task(id=1, payload="test payload", status=TaskStatus.PENDING)
    mock_create_task_use_case = AsyncMock(spec=CreateTaskUseCase)
    mock_create_task_use_case.create_task.return_value = mock_task

    def override_create_task_use_case():
        return mock_create_task_use_case

    app = client.app
    from common.infrastructure.dependencies import get_create_task_use_case

    app.dependency_overrides[get_create_task_use_case] = override_create_task_use_case

    # act
    response = client.post("/tasks", json={"payload": "test payload"})

    # assert
    assert response.status_code == 200
    assert response.json() == {"task_id": 1, "status": "PENDING"}


def test_create_task_invalid_payload(client):
    response = client.post("/tasks", json={"payload": ""})
    assert response.status_code == 422  # 参数验证错误


def test_cancel_task_success(client, mocker):
    # arrange
    mock_task = Task(id=1, payload="test payload", status=TaskStatus.PENDING)
    mock_cancel_task_use_case = CancelTaskUseCase(
        task_repo=mocker.Mock(
            get_task=AsyncMock(return_value=mock_task),
            update_task=AsyncMock(),
        ),
        cancellation_cache=mocker.Mock(set_task_cancelled=mocker.AsyncMock()),
    )

    def override_cancel_task_use_case():
        return mock_cancel_task_use_case

    app = client.app
    from common.infrastructure.dependencies import get_cancel_task_use_case

    app.dependency_overrides[get_cancel_task_use_case] = override_cancel_task_use_case

    # act
    response = client.post("/tasks/1/cancel")

    # assert
    assert response.status_code == 200
    assert response.json() == {"task_id": 1, "status": "CANCELED"}


def test_cancel_task_not_found(client, mocker):
    # arrange
    mock_cancel_task_use_case = CancelTaskUseCase(
        task_repo=mocker.Mock(get_task=AsyncMock(side_effect=TaskNotFoundError(task_id=1))),
        cancellation_cache=mocker.Mock(),
    )

    def override_cancel_task_use_case():
        return mock_cancel_task_use_case

    app = client.app
    from common.infrastructure.dependencies import get_cancel_task_use_case

    app.dependency_overrides[get_cancel_task_use_case] = override_cancel_task_use_case

    # act
    response = client.post("/tasks/1/cancel")

    # assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Task with ID 1 not found"}


def test_get_task_status_success(client, mocker):
    # arrange
    mock_task = Task(id=1, payload="test payload", status=TaskStatus.COMPLETED)

    mock_task_repo = AsyncMock()
    mock_task_repo.get_task.return_value = mock_task

    def override_get_task_repo():
        return mock_task_repo

    app = client.app
    from common.infrastructure.dependencies import get_task_repo

    app.dependency_overrides[get_task_repo] = override_get_task_repo

    # act
    response = client.get("/tasks/1/status")

    # assert
    assert response.status_code == 200
    assert response.json() == {"task_id": 1, "status": "COMPLETED"}


def test_get_task_status_not_found(client, mocker):
    # arrange
    mock_task_repo = AsyncMock()
    mock_task_repo.get_task.side_effect = TaskNotFoundError(task_id=1)

    def override_get_task_repo():
        return mock_task_repo

    app = client.app
    from common.infrastructure.dependencies import get_task_repo

    app.dependency_overrides[get_task_repo] = override_get_task_repo

    # act
    response = client.get("/tasks/1/status")

    # assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Task with ID 1 not found"}

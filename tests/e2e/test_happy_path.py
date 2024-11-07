import asyncio
from time import monotonic

import pytest
from httpx import AsyncClient

from common.constants import MOCK_PROCESSING_TIME


@pytest.mark.asyncio
async def test_e2e_task_processing_happy_path(setup_test_env):
    # AsyncClient(app=web_app)
    async with AsyncClient(base_url="http://localhost:8000") as ac:
        response = await ac.post("/tasks", json={"payload": "test payload"})
        assert response.status_code == 200
        data = response.json()
        task_id = data["task_id"]
        assert data["status"] == "PENDING"

        # 模擬 Client 輪詢，直到狀態變成 PROCESSING 或超過 1 秒
        wait_seconds = 10
        start_time = monotonic()
        while monotonic() - start_time < wait_seconds:
            response = await ac.get(f"/tasks/{task_id}/status")
            assert response.status_code == 200
            data = response.json()

            if data["status"] == "PROCESSING":
                break
            await asyncio.sleep(1)  # 等待 100 毫秒再檢查一次
        else:
            # 如果 1 秒內沒有達到 PROCESSING 狀態，測試失敗
            pytest.fail(f"Task did not reach 'PROCESSING' status within {wait_seconds} seconds")

        # 等待任務處理完成
        await asyncio.sleep(MOCK_PROCESSING_TIME + 0.1)

        response = await ac.get(f"/tasks/{task_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_e2e_task_cancellation(setup_test_env):
    async with AsyncClient(base_url="http://localhost:8000") as ac:
        # Step 1: Create a new task
        create_response = await ac.post("/tasks", json={"payload": "cancel test payload"})
        assert create_response.status_code == 200
        task_data = create_response.json()
        task_id = task_data["task_id"]
        assert task_data["status"] == "PENDING"

        # Step 2: Cancel the task
        cancel_response = await ac.post(f"/tasks/{task_id}/cancel")
        assert cancel_response.status_code == 200
        cancel_data = cancel_response.json()
        assert cancel_data["status"] == "CANCELED"

        # Step 3: Verify task is canceled and does not proceed to processing
        await asyncio.sleep(MOCK_PROCESSING_TIME)  # Wait briefly to ensure no processing
        status_response = await ac.get(f"/tasks/{task_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "CANCELED"

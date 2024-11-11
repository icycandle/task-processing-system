from time import sleep

from locust import HttpUser, between, task


class TaskProcessingUser(HttpUser):
    # 設定 request 間隔時間（以秒為單位）
    wait_time = between(1, 3)

    @task
    def create_task(self):
        response = self.client.post("/tasks", json={"payload": "performance test payload"})
        if response.status_code == 200:
            task_id = response.json().get("task_id")
            self.check_task_status(task_id)

    def check_task_status(self, task_id):
        for _ in range(10):  # 最多嘗試 10 次
            response = self.client.get(f"/tasks/{task_id}/status")
            if response.status_code == 200 and response.json().get("status") == "COMPLETED":
                break
            # 使用 sleep 控制等待時間
            sleep(1)

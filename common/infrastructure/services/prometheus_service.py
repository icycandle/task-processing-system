from loguru import logger
from prometheus_client import Counter, Histogram, start_http_server

from common.domain.services.prometheus_service import IPrometheusMetricsService


class PrometheusMetricsService(IPrometheusMetricsService):
    def __init__(self):
        # 定義指標，並註冊標籤
        self.task_counter = Counter("tasks_processed", "Total number of tasks processed", ["status"])
        self.task_processing_time = Histogram("task_processing_seconds", "Time spent processing tasks")
        self.task_execution_time = Histogram("task_execution_seconds", "Time from task creation to completion")

        # 預先初始化需要的標籤，確保不會在運行時出現未定義標籤的錯誤
        self.task_counter.labels(status="received")
        self.task_counter.labels(status="success")
        self.task_counter.labels(status="failed")  # 可以預設其他可能的狀態

    def start_server(self, port: int = 8002):
        logger.info("Start Prometheus metrics server...")
        start_http_server(port)
        logger.info("Success Start Prometheus metrics server")

    async def inc_label(self, label: str):
        # 使用已經註冊的標籤來增加計數
        self.task_counter.labels(status=label).inc()

    def observe_processing_time(self, duration: float):
        # 記錄處理時間
        self.task_processing_time.observe(duration)

    def observe_execution_time(self, duration: float):
        # 記錄每個任務從創建到完成的總執行時間
        self.task_execution_time.observe(duration)

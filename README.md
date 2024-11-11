# Task Processing System

## Project Structure

- **common/**：包含共享的 domain model、 repo 和 infra。
- **web_api/**：提供任務建立和取消的 Web API。
- **consumer/**：任務消費者，處理訊息佇列中的任務。
- **tests/**：包含端對端（E2E）測試。
- **migrations/**： database migration file, 使用 alembic。
- **Dockerfile**：用於建立 Docker 映像。
- **docker-compose.yml**：用於啟動整個系統的 Docker Compose 配置。

## Install and Run

1. **Run docker compose**

```bash
docker-compose up --build
```

2. **Run e2e test**

```bash
pytest tests/e2e/test_e2e.py
```

# Performance Test

## 進入 Grafana 主頁
1. 開啟瀏覽器並前往 Grafana 頁面，位於 http://localhost:3000
2. 在 Grafana 頁面左側，選擇 Data Sources。 
  - 點擊 Add data source，在列表中選擇 Prometheus。 
  - 在 HTTP URL 欄位中，輸入 Prometheus 的 URL http://prometheus:9090
  - 點擊 Save & Test，確認連接成功。 
3. 新增儀表板
  - 可以 import `grafana/ConsumerSuccess-1731396473547.json`
  - 如果打算手動創建 Dashboard 的內容 ，返回 Grafana 主頁，選擇 Dashboard，然後點擊 Add new panel。
  - 在新面板中，選擇 Query 區域，使用以下 Query 來顯示系統 metrics
    - consumer 消化速度: `rate(tasks_processed_total{status="success"}[1m])`
    - Task life-cycle 平均時間: `rate(task_execution_seconds_sum[1m]) / rate(task_execution_seconds_count[1m])`


## 使用 locust 產生 request
1. 執行 `locust -f tests/performance/locustfile.py --host=http://localhost:8000`
2. 在 http://localhost:8089 觸發 Performance Test 
